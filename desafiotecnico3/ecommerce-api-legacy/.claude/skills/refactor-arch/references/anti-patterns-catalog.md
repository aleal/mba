# Catálogo de anti-patterns (Fase 2)

Cada entrada tem: **ID**, **severidade**, **sinais de detecção** (o que procurar no código, com padrões de busca para várias stacks), **por que importa** e o **padrão do playbook** que corrige (`references/refactoring-playbook.md`).

Os padrões de busca são pontos de partida para `grep -n`. **Sempre confirme lendo o trecho**: um match não é um finding até você entender o contexto.

## Escala de severidade

| Severidade | Critério |
|---|---|
| **CRITICAL** | Falha grave de segurança ou arquitetura: expõe dados sensíveis, permite injeção/execução arbitrária, ou viola completamente a separação de responsabilidades (God Class com banco + regras + rotas). |
| **HIGH** | Violação forte de MVC/SOLID que dificulta muito manutenção e testes: regras de negócio nos controllers/rotas, acoplamento sem injeção de dependência, estado global mutável, fluxo de escrita sem transação. |
| **MEDIUM** | Padronização, duplicação, performance moderada: N+1, validação ausente, tratamento de erros inconsistente, APIs deprecated, efeitos colaterais inline. |
| **LOW** | Legibilidade: nomes ruins, magic numbers, imports não usados, `print`/`console.log` como log. |

Ajuste de severidade: suba um nível quando o problema estiver em fluxo de dinheiro, autenticação ou dados pessoais. Desça um nível quando o código for claramente script de desenvolvimento (ex.: seed) e não rodar em produção. Justifique o ajuste na descrição.

## Índice

| ID | Anti-pattern | Severidade | Playbook |
|---|---|---|---|
| AP01 | Credenciais e segredos hardcoded | CRITICAL | P1 |
| AP02 | SQL Injection (SQL montado com concatenação/interpolação) | CRITICAL | P2 |
| AP03 | God Class / God File | CRITICAL | P3 |
| AP04 | Endpoint perigoso sem proteção (execução arbitrária, reset de dados) | CRITICAL | P10 |
| AP05 | Exposição de dados sensíveis em respostas ou logs | CRITICAL | P9 |
| AP06 | Armazenamento inseguro de senhas | CRITICAL/HIGH | P9 |
| AP07 | Regra de negócio em controller/rota (Fat Controller) | HIGH | P4 |
| AP08 | Acoplamento forte sem injeção de dependência | HIGH | P5 |
| AP09 | Estado global mutável | HIGH | P6 |
| AP10 | Escrita em múltiplos passos sem transação / callback hell | HIGH | P11 |
| AP11 | Autenticação/autorização ausente ou falsa | HIGH | P10 |
| AP12 | Configuração insegura (debug ligado, CORS aberto, bind 0.0.0.0 fixo) | HIGH | P1 |
| AP13 | Queries N+1 | MEDIUM | P7 |
| AP14 | Código duplicado (serialização, validação, regras) | MEDIUM | P13 |
| AP15 | Validação de entrada ausente ou inconsistente | MEDIUM | P13 |
| AP16 | Tratamento de erros genérico, silencioso ou que vaza detalhes | MEDIUM | P8 |
| AP17 | Uso de APIs deprecated | MEDIUM | P12 |
| AP18 | Efeitos colaterais inline (e-mail/SMS/notificação no meio do fluxo) | MEDIUM | P4 |
| AP19 | Integridade referencial ausente (dados órfãos) | MEDIUM | P11 |
| AP20 | Magic numbers e magic strings | LOW | P13 |
| AP21 | Nomenclatura ruim | LOW | P14 |
| AP22 | Imports não usados e código morto | LOW | P14 |
| AP23 | `print`/`console.log` no lugar de logging | LOW | P14 |
| AP24 | Condicionais verbosas e aninhamento desnecessário | LOW | P14 |

---

## CRITICAL

### AP01 — Credenciais e segredos hardcoded
**Sinais de detecção**
- Literais atribuídos a chaves de configuração sensíveis: `SECRET_KEY`, `password`, `pass`, `pwd`, `token`, `api_key`, `apiKey`, `secret`, `private_key`, `dbPass`, `smtp`, `gateway`.
- Busca: `grep -nEi "(secret|passw|pwd|pass|token|api_?key|private).{0,20}[:=] *['\"][^'\"]{3,}" --include=*.py --include=*.js`
- Prefixos de chaves reais: `pk_live_`, `sk_live_`, `AKIA`, `ghp_`, `xox`.
- Objetos de config com segredos literais (`const config = { dbPass: "..." }`), classes que guardam senha SMTP no construtor.
- Segredo devolvido por um endpoint (ex.: health check com `secret_key`): também é AP05.

**Por que importa:** qualquer pessoa com acesso ao repositório (ou à resposta da API) obtém o segredo. A rotação exige deploy.

**Não é finding:** placeholders óbvios em `.env.example`, leitura de `os.environ`/`process.env` sem default sensível.

### AP02 — SQL Injection
**Sinais de detecção**
- SQL montado com concatenação ou interpolação de valores vindos de fora:
  - Python: `"SELECT ... " + var`, `f"SELECT ... {var}"`, `"... %s" % var`, `.format(` dentro de `execute(`.
  - JS: `` `SELECT ... ${var}` ``, `"SELECT ..." + var` passados a `db.run/get/all/query`.
- Busca: `grep -nE "(execute|run|get|all|query)\(.*(\+|f\"|f'|\\$\{|%)" ` e `grep -nE "(SELECT|INSERT|UPDATE|DELETE).*['\"] *\+"`
- `LIKE '%" + termo + "%'` montado à mão.
- Até `str(id)` concatenado é finding (o padrão é perigoso e se espalha), mas a descrição deve dizer quais campos são texto livre do usuário (os exploráveis de fato).

**Por que importa:** permite ler, alterar ou apagar qualquer dado (ex.: login com `' OR '1'='1`).

**Não é finding:** placeholders (`?`, `%s` passado como parâmetro separado, `:nome`), ORM com filtros (`filter_by`, `Model.query.filter(Model.campo == valor)`), `.like(f'%{q}%')` do SQLAlchemy (o ORM parametriza o valor).

### AP03 — God Class / God File
**Sinais de detecção**
- Um arquivo ou classe com 3 ou mais destas responsabilidades: definição de schema/DDL, seeds, conexão com o banco, queries, regras de negócio, validação, registro de rotas, formatação de resposta, configuração.
- Classe "Manager"/"Helper"/"Utils" com métodos `initDb`, `setupRoutes`, `processX`.
- Arquivo com mais de ~250 linhas cobrindo vários domínios (produtos + usuários + pedidos no mesmo módulo).
- Entry point que, além de montar o app, contém rotas com SQL direto.

**Por que importa:** impossível testar em isolamento; qualquer mudança afeta tudo; conflitos constantes entre desenvolvedores.

### AP04 — Endpoint perigoso sem proteção
**Sinais de detecção**
- Rota que executa SQL ou comando recebido no corpo/query: `cursor.execute(dados["sql"])`, `db.exec(req.body.query)`, `eval(`, `exec(`, `child_process.exec(`, `subprocess.*shell=True`.
- Rotas administrativas destrutivas (`/admin/reset-db`, `DELETE` em massa, `drop`) sem autenticação nem flag de ambiente.
- Rotas `/admin/*` sem nenhum middleware ou checagem de papel.

**Por que importa:** qualquer cliente consegue apagar ou exfiltrar o banco inteiro.

### AP05 — Exposição de dados sensíveis em respostas ou logs
**Sinais de detecção**
- Serialização que inclui senha/hash: `"senha": row["senha"]`, `'password': self.password`, `SELECT *` de usuários devolvido direto.
- Respostas com configuração interna: `secret_key`, `db_path`, `debug`, connection strings.
- Logs com dados de cartão, senhas ou chaves: `console.log(\`... ${card} ... ${apiKey}\`)`, `print("senha", ...)`.
- `return jsonify({"erro": str(e)})` com detalhes de exceção do banco para o cliente (também AP16).

**Por que importa:** vazamento de credenciais e dados pessoais (LGPD/PCI). Número de cartão em log viola PCI-DSS.

### AP06 — Armazenamento inseguro de senhas
**Severidade:** CRITICAL para texto puro, codificação reversível (base64) ou "cripto" caseira. HIGH para hash rápido sem salt (MD5, SHA1, SHA256 puro).

**Sinais de detecção**
- `INSERT` de senha recebida sem passar por função de hash; comparação `WHERE senha = '...'`.
- `hashlib.md5(`, `hashlib.sha1(`, `createHash('md5')`, `createHash('sha1')` aplicados a senha.
- Funções caseiras: `Buffer.from(pwd).toString('base64')`, loops que "embaralham" a senha.
- Senha default quando o usuário não informa (`pwd || "123456"`).

**Por que importa:** um vazamento do banco expõe as senhas dos usuários, que costumam ser reutilizadas em outros serviços.

---

## HIGH

### AP07 — Regra de negócio em controller/rota (Fat Controller)
**Sinais de detecção**
- Handler de rota com cálculos de domínio (totais, descontos, faixas de preço, transições de status), loops de agregação, regras condicionais extensas.
- Handler que faz validação + regra + query + serialização + notificação no mesmo corpo (mais de ~40 linhas).
- Mesma regra de domínio repetida em várias rotas (ex.: cálculo de "atrasado" copiado em 4 handlers).

**Por que importa:** a regra não pode ser reutilizada nem testada sem HTTP; duplicação gera divergência.

### AP08 — Acoplamento forte sem injeção de dependência
**Sinais de detecção**
- Funções que chamam `get_db()`/singleton global diretamente em vez de receber a dependência.
- Classes que instanciam dependências concretas no construtor (`this.db = new sqlite3.Database(...)`, `self.server = smtplib.SMTP(...)`).
- Rotas registradas por um objeto que também é dono do banco (`manager.setupRoutes(app)`).
- Ausência de app factory / composition root: tudo é criado na importação do módulo.

**Por que importa:** impossível trocar banco, mockar em testes ou configurar por ambiente.

### AP09 — Estado global mutável
**Sinais de detecção**
- Python: variáveis de módulo reatribuídas com `global x`; conexão única compartilhada (`db_connection = None` + `global`); listas/dicts de módulo usados como cache ou fila.
- JS: `let` de módulo alterado por funções (`let globalCache = {}`, `let totalRevenue = 0`) e exportado.
- `sqlite3.connect(..., check_same_thread=False)` compartilhado entre threads.

**Por que importa:** condições de corrida, vazamento de dados entre requisições, comportamento impossível de reproduzir em testes.

### AP10 — Escrita em múltiplos passos sem transação / callback hell
**Sinais de detecção**
- Sequência de `INSERT`/`UPDATE` relacionados (pedido + itens + estoque; matrícula + pagamento + auditoria) sem `BEGIN/COMMIT/ROLLBACK` ou `with transaction`.
- `return` de erro no meio de um loop depois de já ter escrito parte dos dados.
- JS: callbacks aninhados em 3 ou mais níveis (`db.get(..., () => { db.run(..., () => { db.run(...` ), erros de callback ignorados (`(err) => { res.send(...) }` sem checar `err`).

**Por que importa:** falhas parciais deixam o banco inconsistente (pagamento sem matrícula, estoque baixado sem pedido).

### AP11 — Autenticação/autorização ausente ou falsa
**Sinais de detecção**
- Tokens fixos ou previsíveis: `'fake-jwt-token-' + id`, `token = "123"`.
- Rotas que alteram ou apagam dados de outros usuários sem checagem de identidade/papel.
- Campo `role`/`tipo` aceito livremente no cadastro (qualquer um se registra como `admin`).
- Relatórios financeiros/administrativos sem proteção.

**Por que importa:** qualquer cliente executa ações privilegiadas.

**Observação:** se o projeto não tem nenhum sistema de autenticação, registre o problema e, na Fase 3, proteja ao menos as rotas destrutivas/administrativas (P10). Não invente um sistema de login completo.

### AP12 — Configuração insegura
**Sinais de detecção**
- `debug=True` / `app.config["DEBUG"] = True` fixo; `app.run(host="0.0.0.0", debug=True)`.
- `CORS(app)` sem origens, `cors()` sem opções, `Access-Control-Allow-Origin: *` com credenciais.
- Porta, URL de banco e flags fixas no código, sem variável de ambiente.

**Por que importa:** o debugger do Werkzeug com `debug=True` permite execução de código remoto; CORS aberto expõe a API a qualquer site.

---

## MEDIUM

### AP13 — Queries N+1
**Sinais de detecção**
- Query dentro de loop que percorre o resultado de outra query: `for row in rows: cursor.execute(...)`, `rows.forEach(r => db.get(...))`.
- ORM: acesso a relacionamento ou `Model.query.get(x.fk_id)` dentro de loop; `len(u.tasks)` para cada usuário; `.count()` por item.
- Várias queries `COUNT(*) ... WHERE status = 'x'` para cada valor, quando um `GROUP BY` resolve.

**Por que importa:** o número de queries cresce com os dados (1 + N, ou 1 + N + N×M); a latência explode em produção.

### AP14 — Código duplicado
**Sinais de detecção**
- Blocos de 5 ou mais linhas idênticos ou quase idênticos: montagem de dict a partir de `row` repetida em várias funções; mesma validação em criar e atualizar.
- Lista de valores válidos repetida em vários arquivos (`['pending', 'in_progress', 'done', 'cancelled']`).
- Funções utilitárias que existem (ex.: `process_task_data`, `validate_email`) mas não são usadas, com a lógica reimplementada nas rotas.

**Por que importa:** correções precisam ser feitas em N lugares; versões divergem.

### AP15 — Validação de entrada ausente ou inconsistente
**Sinais de detecção**
- `request.get_json()`/`req.body` usado sem checar tipo e presença (`dados.get(...)` sem `if not dados`; `None.get` quebra com 500).
- Validação em criar mas não em atualizar (ou vice-versa).
- Comparação numérica com valor que pode ser string (`if preco < 0` com `preco` vindo do JSON sem conversão; `int(request.args[...])` sem tratar erro).
- Campos de enum (status, role, categoria) sem whitelist.

**Por que importa:** entradas inválidas viram erro 500, dados corrompidos ou bypass de regra.

### AP16 — Tratamento de erros genérico, silencioso ou que vaza detalhes
**Sinais de detecção**
- `except:` puro ou `except Exception` que engole o erro sem log.
- O mesmo `try/except` com `return jsonify({"erro": str(e)}), 500` repetido em todos os handlers (sem handler central).
- JS: callback com `err` ignorado; ausência de middleware `(err, req, res, next)`; respostas de erro em texto puro misturadas com JSON.

**Por que importa:** erros somem ou vazam stack/SQL para o cliente; formato de erro inconsistente para os consumidores da API.

### AP17 — Uso de APIs deprecated
**Sinais de detecção:** busque cada item da tabela abaixo. Informe a versão a partir da qual a API é deprecated e o substituto moderno.

| Stack | API obsoleta (buscar) | Status | Substituto moderno |
|---|---|---|---|
| SQLAlchemy 2.x / Flask-SQLAlchemy 3.x | `Model.query.get(id)` | Legacy desde SQLAlchemy 2.0 (gera `LegacyAPIWarning`) | `db.session.get(Model, id)` |
| SQLAlchemy 2.x | `Model.query.filter_by(...).first()` em código novo | Query API legacy | `db.session.execute(db.select(Model).filter_by(...)).scalar_one_or_none()` |
| SQLAlchemy 2.x | `engine.execute(`, `session.execute("SQL string")` | Removido no 2.0 | `connection.execute(text("..."), params)` |
| Python 3.12+ | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | Deprecated no 3.12 | `datetime.now(timezone.utc)`, `datetime.fromtimestamp(ts, timezone.utc)` |
| Flask 2.3+ | `@app.before_first_request` | Removido no 2.3 | inicialização dentro de `create_app()` |
| Flask 2.2+ | `flask.json.JSONEncoder`, `app.json_encoder` | Removido no 2.3 | `app.json = CustomJSONProvider(app)` |
| Flask | `from flask import escape`, `Markup` | Removido no 3.0 | `from markupsafe import escape, Markup` |
| marshmallow 3.13+ | `fields.X(missing=...)`, `default=` | Deprecated | `load_default=`, `dump_default=` |
| Python | `pkg_resources` | Deprecated (setuptools) | `importlib.metadata` / `importlib.resources` |
| Node.js | `new Buffer(` | Deprecated (DEP0005) | `Buffer.from(` / `Buffer.alloc(` |
| Node.js | `url.parse(` | Legacy | `new URL(` |
| Node.js | `crypto.createCipher(` | Removido no Node 22 | `crypto.createCipheriv(` |
| Node.js | `fs.exists(` | Deprecated | `fs.existsSync(` / `fs.promises.access(` |
| Express | `require('body-parser')` só para JSON | Desnecessário desde Express 4.16 | `express.json()`, `express.urlencoded()` |
| Express 4→5 | `res.send(status, body)`, `res.json(obj, status)`, `req.param()`, `app.del(` | Deprecated no 4, removido no 5 | `res.status(s).json(obj)`, `req.params/req.query`, `app.delete(` |
| npm | `request`, `node-uuid` | Pacotes deprecated | `fetch` nativo (Node 18+), `crypto.randomUUID()` |
| Node sqlite3 | API só de callbacks em código novo | Padrão legado | `util.promisify` ou wrapper com Promises + `async/await` |

**Severidade:** MEDIUM. Pode subir para HIGH se a API já foi **removida** na versão que o projeto declara (quebra no upgrade), ou descer para LOW se for apenas estilo.

**Se nada for encontrado:** escreva no relatório "Nenhuma API deprecated encontrada", listando o que foi verificado.

### AP18 — Efeitos colaterais inline
**Sinais de detecção**
- `print("ENVIANDO EMAIL ...")`, `print("ENVIANDO SMS ...")`, chamadas SMTP/HTTP de notificação dentro do handler ou do model.
- Service de notificação existente mas não injetado nem usado.

**Por que importa:** mistura fluxo de negócio com I/O externo; impossível desligar em testes; falha no envio derruba a requisição.

### AP19 — Integridade referencial ausente
**Sinais de detecção**
- `DELETE` de entidade pai sem tratar filhos (matrículas, pagamentos, tasks): o próprio código às vezes admite ("ficaram sujos no banco").
- Tabelas com colunas `*_id` sem `FOREIGN KEY` nem `ON DELETE`.
- Delete em cascata manual em loop (também AP13).

**Por que importa:** registros órfãos corrompem relatórios e somas financeiras.

---

## LOW

### AP20 — Magic numbers e magic strings
**Sinais:** limites e faixas literais em regras (`if faturamento > 10000: desconto = faturamento * 0.1`), status como strings soltas repetidas, tamanhos mínimos (`len(senha) < 4`), portas e caminhos literais, regra de negócio por prefixo (`cc.startsWith("4")`).

### AP21 — Nomenclatura ruim
**Sinais:** variáveis de 1 a 3 letras fora de loops curtos (`u`, `e`, `p`, `cid`, `cc`, `t`, `d`); nomes que mentem (`badCrypto`, `process_task_data` que não processa); campos de API abreviados (`usr`, `eml`, `pwd`, `c_id`); mistura de idiomas no mesmo módulo. **Não renomeie campos do contrato da API**: renomeie só as variáveis internas.

### AP22 — Imports não usados e código morto
**Sinais:** `import os, sys, json, time` sem uso; funções nunca chamadas; módulos utilitários inteiros sem referência; variáveis atribuídas e nunca lidas. Confirme com busca pelo nome no projeto antes de reportar.

### AP23 — `print`/`console.log` no lugar de logging
**Sinais:** `print(` e `console.log(` para eventos de aplicação e erros; banners de inicialização com `print("=" * 50)`. Use o logger da linguagem com níveis.

### AP24 — Condicionais verbosas e aninhamento desnecessário
**Sinais:** `if cond: return True else: return False`; `if` aninhados em 3 ou mais níveis que poderiam ser uma expressão booleana; `type(x) == list` em vez de `isinstance`.
