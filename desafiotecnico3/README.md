# Criação de Skills — Refatoração Arquitetural Automatizada

Skill `refactor-arch` para o Claude Code que **analisa**, **audita** e **refatora para MVC** projetos backend legados, independente da stack. Ela foi executada nos 3 projetos do [repositório base](https://github.com/devfullcycle/mba-ia-refactor-projects-skill): dois em Python/Flask e um em Node.js/Express.

## Resumo dos resultados

✅ **Todos os critérios de aceite atingidos nos 3 projetos.**

| Projeto | Stack detectada | Findings (C / H / M / L) | Endpoints após a refatoração | Relatório |
|---|---|---|---|---|
| `code-smells-project` | Python + Flask 3.1.1 (sqlite3) | **25** (9 / 6 / 5 / 5) | 19/19 rotas respondendo; 35/40 requisições idênticas ao baseline, 5 diferenças são correções de segurança declaradas | [audit-project-1.md](reports/audit-project-1.md) |
| `ecommerce-api-legacy` | Node.js + Express 4 (sqlite3) | **20** (7 / 6 / 2 / 5) | 3/3 rotas; 7/7 requisições com mesmo status e formato do baseline | [audit-project-2.md](reports/audit-project-2.md) |
| `task-manager-api` | Python + Flask 3.0 (SQLAlchemy) | **21** (4 / 5 / 7 / 5) | 22/22 rotas; 47/47 requisições batem com o baseline | [audit-project-3.md](reports/audit-project-3.md) |

| Critério de aceite | P1 | P2 | P3 |
|---|---|---|---|
| Fase 1 detecta a stack corretamente | ✅ | ✅ | ✅ |
| Fase 2 encontra ≥ 5 findings | ✅ 25 | ✅ 20 | ✅ 21 |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | ✅ 15 | ✅ 13 | ✅ 9 |
| Fase 3: aplicação funciona após a refatoração | ✅ | ✅ | ✅ |

## Como executar (rápido)

```bash
git clone git@github.com:aleal/mba.git
cd mba/desafiotecnico3/code-smells-project    # ou ecommerce-api-legacy / task-manager-api
claude "/refactor-arch"                       # Fase 1 + Fase 2, pausa e pergunta [y/n]
# responda "y" para executar a Fase 3

# validar um projeto refatorado (sobe a API com banco temporário e chama todas as rotas)
cd .. && scripts/smoke.sh code-smells-project
```

## Índice

1. [Análise Manual](#análise-manual)
   - [Projeto 1 — code-smells-project](#projeto-1--code-smells-project-pythonflask)
   - [Projeto 2 — ecommerce-api-legacy](#projeto-2--ecommerce-api-legacy-nodejsexpress)
   - [Projeto 3 — task-manager-api](#projeto-3--task-manager-api-pythonflask)
2. [Construção da Skill](#construção-da-skill)
   - [Estrutura e decisões de design](#estrutura-e-decisões-de-design)
   - [Catálogo de anti-patterns](#catálogo-de-anti-patterns)
   - [Como a skill é agnóstica de tecnologia](#como-a-skill-é-agnóstica-de-tecnologia)
   - [Desafios encontrados](#desafios-encontrados)
3. [Resultados](#resultados)
   - [Resumo das auditorias](#resumo-das-auditorias)
   - [Antes e depois da estrutura](#antes-e-depois-da-estrutura)
   - [Checklists de validação](#checklists-de-validação)
   - [Logs das aplicações rodando](#logs-das-aplicações-rodando)
   - [Comportamento da skill em stacks diferentes](#comportamento-da-skill-em-stacks-diferentes)
   - [Riscos residuais](#riscos-residuais)
4. [Como Executar](#como-executar)
5. [Estrutura do repositório](#estrutura-do-repositório)

---

## Análise Manual

Feita **antes** de escrever a skill, lendo todo o código dos 3 projetos (~2.100 linhas). Os problemas abaixo são os de maior impacto; serviram de base para o catálogo de anti-patterns. As linhas se referem ao código **original** (commit inicial do repositório base).

### Projeto 1 — code-smells-project (Python/Flask)

API de e-commerce em 4 arquivos: `app.py` (config + rotas + SQL administrativo), `controllers.py`, `models.py` (314 linhas, 4 domínios) e `database.py` (conexão global + schema + seed).

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | SQL Injection em praticamente todas as queries (concatenação de strings) | `models.py:28, 47-50, 109-111, 126-129, 289-297` | O login (`109-111`) concatena `email` e `senha`: `admin@loja.com' --` entra sem senha. A busca permite `UNION` para ler qualquer tabela. |
| CRITICAL | Endpoint que executa SQL arbitrário e endpoint de reset, ambos sem autenticação | `app.py:47-57, 59-78` | Qualquer cliente anônimo lê, altera ou apaga o banco inteiro com um `POST /admin/query`. |
| CRITICAL | `SECRET_KEY` hardcoded e **devolvida** pelo `/health` junto com `db_path` e `debug` | `app.py:7`; `controllers.py:285-289` | A chave que assina sessões do Flask fica pública: permite forjar sessões. |
| CRITICAL | Senhas em texto puro, gravadas e **devolvidas** em `GET /usuarios` | `models.py:83, 99, 126-129`; `database.py:76-78` | Um GET anônimo devolve as senhas de todos os usuários. |
| CRITICAL | God File: `models.py` concentra SQL, serialização e regras de 4 domínios | `models.py:1-314` | Nenhuma regra (desconto, estoque) é testável sem banco; qualquer mudança toca todos os domínios. |
| HIGH | Criação de pedido sem transação (pedido, itens e estoque em passos soltos) | `models.py:133-169` | Falha no meio deixa pedido sem itens ou estoque baixado sem pedido; fluxo de dinheiro. |
| HIGH | Conexão SQLite global compartilhada entre threads (`global` + `check_same_thread=False`) | `database.py:4-11` | Estado global mutável: transações de requisições concorrentes se misturam. |
| HIGH | `debug=True` fixo e `CORS(app)` aberto | `app.py:8-9, 88` | O debugger do Werkzeug exposto em `0.0.0.0` permite execução remota de código. |
| MEDIUM | Queries N+1 na listagem de pedidos (1 + N pedidos + N×M itens) | `models.py:171-233` | `GET /pedidos` degrada linearmente com o histórico. |
| MEDIUM | `try/except` copiado em 17 handlers devolvendo `str(e)` ao cliente | `controllers.py:10-12, 21-22, ...` | Vaza detalhes do SQL (ajuda a explorar a injeção) e não há formato de erro único. |
| MEDIUM | Notificações (e-mail/SMS/push) como `print` dentro do handler | `controllers.py:208-210, 247-250` | Efeito colateral acoplado ao fluxo: impossível desligar em teste; falha no envio derrubaria a requisição. |
| LOW | Faixas de desconto e taxas como magic numbers | `models.py:256-262` | Regra de negócio escondida em literais; muda em código em vez de configuração. |
| LOW | `print` no lugar de logging, inclusive com email em cada login | `controllers.py:8, 57, 179, 182` | Sem níveis nem destino configurável; dado pessoal em log. |
| LOW | Imports não usados (`sqlite3` em models, `os` em database) | `models.py:2`; `database.py:2` | Ruído que esconde as dependências reais dos módulos. |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

LMS com checkout em 3 arquivos. Toda a aplicação vive na classe `AppManager` (banco em memória, DDL, seeds, rotas e regras).

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | Segredos de produção hardcoded (`dbPass`, `paymentGatewayKey: "pk_live_..."`) | `src/utils.js:1-7` | Chave de gateway de pagamento no repositório: qualquer pessoa com acesso ao código a usa. |
| CRITICAL | Número do cartão e chave do gateway impressos no log | `src/AppManager.js:45` | Viola PCI-DSS: o cartão completo fica em logs, que costumam ter acesso amplo. |
| CRITICAL | "Criptografia" caseira de senha (`badCrypto`: prefixo base64 repetido) e senha default `123456` | `src/utils.js:17-23`; `src/AppManager.js:18, 68` | Reversível na prática; o seed ainda grava senha em texto puro (`'123'`). |
| CRITICAL | God Class `AppManager`: conexão, schema, seed, rotas, validação e regras de checkout | `src/AppManager.js:4-139` | Nada é testável isoladamente; qualquer mudança mexe na classe inteira. |
| HIGH | Checkout em callbacks aninhados sem transação (matrícula → pagamento → auditoria) | `src/AppManager.js:37-77` | Falha intermediária deixa matrícula sem pagamento; erro da auditoria é ignorado (`57`). |
| HIGH | Relatório financeiro e `DELETE /api/users/:id` sem nenhuma autenticação | `src/AppManager.js:80, 131` | Qualquer cliente lê o faturamento e apaga usuários. |
| HIGH | Estado global mutável exportado (`globalCache`, `totalRevenue`) | `src/utils.js:9-10, 25` | Cache compartilhado entre requisições; `totalRevenue` exportado como primitivo nunca reflete atualizações. |
| MEDIUM | N+1 no relatório financeiro (1 + cursos + 2 × matrículas queries) e `err` ignorado nos callbacks | `src/AppManager.js:83-127` | Cresce com os dados; `enrollments` indefinido em erro derruba o processo. |
| MEDIUM | Delete de usuário deixa matrículas e pagamentos órfãos (a própria resposta admite) | `src/AppManager.js:131-136` | Relatórios financeiros passam a somar dados de usuários inexistentes. |
| MEDIUM | Validação ausente: `card` numérico quebra `cc.startsWith`, email sem formato, `c_id` sem tipo | `src/AppManager.js:35, 46` | Um JSON com `"card": 4111` derruba o servidor inteiro (exceção não tratada). |
| LOW | Nomes de 1-3 letras (`u`, `e`, `p`, `cid`, `cc`) e `badCrypto` | `src/AppManager.js:29-33`; `src/utils.js:17` | Leitura difícil num fluxo de pagamento. |
| LOW | `console.log` como logging | `src/app.js:13`; `src/utils.js:13`; `src/AppManager.js:45` | Sem níveis; foi justamente por um log que o cartão vazou. |
| LOW | Magic values: aprovação por prefixo `"4"`, loop de `10000`, porta `3000` | `src/AppManager.js:46`; `src/utils.js:6, 19` | Regra de pagamento escondida num literal. |

### Projeto 3 — task-manager-api (Python/Flask)

Já possui pastas `models/`, `routes/`, `services/` e `utils/`, mas as rotas fazem tudo e as camadas auxiliares não são usadas.

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | Hash da senha devolvido em todas as respostas de usuário (`to_dict` inclui `password`) | `models/user.py:21`; usado em `routes/user_routes.py:33, 85, 129, 209` | Qualquer `GET /users/<id>` ou login expõe o hash. |
| CRITICAL | Senha SMTP e `SECRET_KEY` hardcoded | `services/notification_service.py:7-10`; `app.py:13` | Credenciais de e-mail e chave de assinatura no repositório. |
| HIGH | Senhas com MD5 sem salt | `models/user.py:29, 32` | Quebrável por rainbow table em segundos após um vazamento. |
| HIGH | Token falso (`'fake-jwt-token-' + id`) e qualquer um pode se cadastrar como `admin` | `routes/user_routes.py:52, 71, 210` | Não existe autorização real: o "token" é previsível e o papel é auto-atribuído. |
| HIGH | Rotas gordas: validação, regras, queries e serialização dentro das rotas; regra de "atrasada" copiada 6 vezes apesar de `Task.is_overdue()` existir | `routes/task_routes.py:30-39, 71-80, 283-287`; `routes/report_routes.py:33-43` | Camadas existem só no nome; regras divergem entre endpoints. |
| MEDIUM | N+1: `User.query.get`/`Category.query.get` por task, `len(u.tasks)` por usuário, `count()` por categoria | `routes/task_routes.py:41-57`; `routes/user_routes.py:22`; `routes/report_routes.py:53-68, 163` | Listagens fazem 1 + 2N queries. |
| MEDIUM | APIs deprecated: `Model.query.get()` (legacy no SQLAlchemy 2.0) e `datetime.utcnow()` (deprecated no Python 3.12) | `routes/*.py` (16 ocorrências); `models/*.py` | Geram warnings hoje e quebram em upgrades. |
| MEDIUM | `except:` puro em 9 lugares e nenhum handler central | `routes/task_routes.py:62, 137, 204, 236`; `routes/user_routes.py:130, 149` | Erros somem sem log; `priority: "abc"` vira 500. |
| MEDIUM | `utils/helpers.py` (validação pronta, constantes) e `NotificationService` nunca usados | `utils/helpers.py:57-116`; `services/notification_service.py` | Código morto que duplica as regras das rotas. |
| LOW | Imports não usados em quase todos os arquivos (`os, sys, json, time`) | `app.py:7`; `routes/task_routes.py:7` | Ruído; esconde dependências reais. |
| LOW | Condicionais verbosas (`if x: return True else: return False`) e `type(x) == list` | `models/user.py:34-38`; `models/task.py:38-60` | Legibilidade. |
| LOW | Magic numbers: prioridades `1-5`, senha mínima `4`, `p1..p5` | `routes/task_routes.py:113`; `routes/user_routes.py:64`; `routes/report_routes.py:24-28` | Limites de negócio espalhados. |

---

## Construção da Skill

### Estrutura e decisões de design

```
.claude/skills/refactor-arch/
├── SKILL.md                              # orquestrador: regras invioláveis + as 3 fases + formatos de saída
└── references/
    ├── project-analysis.md               # Fase 1: heurísticas de stack, banco, endpoints, domínio e arquitetura
    ├── anti-patterns-catalog.md          # Fase 2: 24 anti-patterns com sinais de detecção e severidade
    ├── audit-report-template.md          # Fase 2: template do relatório + regras de preenchimento
    ├── mvc-architecture.md               # Fase 3: camadas, regras de dependência, layouts Flask/Express
    ├── refactoring-playbook.md           # Fase 3: 14 padrões de transformação com antes/depois
    └── validation.md                     # Fase 3: baseline, smoke test, comparação, limpeza
```

| Área de conhecimento exigida | Arquivo |
|---|---|
| Análise de projeto | `references/project-analysis.md` |
| Catálogo de anti-patterns | `references/anti-patterns-catalog.md` |
| Template de relatório | `references/audit-report-template.md` |
| Guidelines de arquitetura | `references/mvc-architecture.md` |
| Playbook de refatoração | `references/refactoring-playbook.md` |
| (extra) Validação | `references/validation.md` |

Decisões principais:

- **`SKILL.md` é o processo; as referências são o conhecimento.** O `SKILL.md` (146 linhas) diz *o que* fazer em cada fase e *qual* referência ler antes. Assim o contexto só recebe o conhecimento de uma fase quando ela começa (progressive disclosure), e o processo cabe numa leitura.
- **Regras invioláveis no topo:** nada é modificado antes da confirmação; todo finding cita linhas conferidas; o contrato da API (paths, campos, status) é preservado, e as únicas mudanças permitidas são correções de segurança, que precisam ser declaradas no resumo final.
- **`disable-model-invocation: true`:** a skill reescreve código, então só roda quando o usuário invoca `/refactor-arch` explicitamente, nunca por iniciativa do modelo.
- **Formatos de saída fixos** (blocos `PHASE 1`, `ARCHITECTURE AUDIT REPORT`, `PHASE 3`) e uma **autoconferência** antes de imprimir o relatório: contagens do Summary = seções = Total, ordenadas por severidade.
- **Pausa explícita na Fase 2:** a fase termina com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e a instrução de **parar o turno**. Só uma resposta afirmativa inicia a Fase 3.
- **Validação baseada em evidência:** antes de refatorar, a skill sobe a aplicação **original** numa cópia temporária, grava as respostas de todas as rotas (baseline) e, no fim, compara status e formato do JSON. A validação nunca pode marcar `✓` sem ter executado a verificação.
- **Endpoints perigosos são protegidos, não removidos** (Playbook P10). Remover `/admin/query` quebraria o critério "endpoints originais continuam respondendo"; protegê-lo com token e flag desligada por padrão resolve a falha e mantém o contrato.

### Catálogo de anti-patterns

24 anti-patterns (o mínimo exigido é 8), cada um com sinais de detecção concretos (padrões de `grep` para Python e JS, mais o que confirmar na leitura), o que **não** é finding (para evitar falsos positivos) e o padrão do playbook que o corrige:

| Severidade | Anti-patterns | Por que estão no catálogo |
|---|---|---|
| CRITICAL | AP01 Segredos hardcoded · AP02 SQL Injection · AP03 God Class · AP04 Endpoint perigoso sem proteção · AP05 Dados sensíveis em resposta/log · AP06 Senha insegura | Os problemas de segurança e de separação total de responsabilidades encontrados na análise manual dos 3 projetos |
| HIGH | AP07 Fat Controller · AP08 Acoplamento sem DI · AP09 Estado global · AP10 Escrita sem transação / callback hell · AP11 Auth ausente/falsa · AP12 Config insegura | As violações de MVC/SOLID da definição de HIGH do desafio, mais transação e auth, que apareceram em todos os projetos |
| MEDIUM | AP13 N+1 · AP14 Duplicação · AP15 Validação ausente · AP16 Erros genéricos · **AP17 APIs deprecated** · AP18 Efeitos colaterais inline · AP19 Dados órfãos | Performance e padronização; AP17 traz uma tabela de APIs obsoletas (SQLAlchemy, Python 3.12, Flask, Node, Express) com o substituto moderno |
| LOW | AP20 Magic numbers · AP21 Nomes ruins · AP22 Código morto · AP23 print/console.log · AP24 Condicionais verbosas | Legibilidade |

O playbook tem **14 padrões de transformação** (mínimo exigido: 8), cada um com exemplos de código antes/depois: P1 config por env, P2 queries parametrizadas, P3 quebra de God Class, P4 controller fino + services, P5 composition root/DI, P6 fim do estado global, P7 N+1 → JOIN/eager loading, P8 erro centralizado, P9 hash de senha e serialização segura, P10 proteção de rotas admin, P11 callbacks → async/await com transação, P12 APIs deprecated, P13 validação e constantes centralizadas, P14 higiene.

### Como a skill é agnóstica de tecnologia

- **Detecção por sinais, não por suposição:** a Fase 1 identifica a stack pelo manifesto (`requirements.txt`, `package.json`, `go.mod`, `pom.xml`...) **e** confirma por imports e chamadas no código. Ela cobre várias stacks além das 3 testadas (Django, FastAPI, Fastify, Gin, Spring...).
- **Sinais de detecção multi-linguagem:** cada anti-pattern traz padrões de busca para Python e JavaScript e a descrição do conceito, para o agente reconhecer o mesmo problema em outra sintaxe.
- **Arquitetura alvo descrita por responsabilidades,** com layouts concretos para Flask e Express e uma seção específica para **projetos já parcialmente organizados** (manter o que está correto, criar só as camadas que faltam, não mover arquivos por estética).
- **Validação independente da stack:** o script de smoke test do `validation.md` usa só a biblioteca padrão do Python e fala HTTP, então valida APIs em qualquer linguagem.
- **Prova:** a **mesma cópia** da skill (verificada com `diff -r`) rodou nos 3 projetos sem nenhum ajuste específico por projeto.

### Desafios encontrados

| Desafio | Como resolvi |
|---|---|
| **Iteração 1 no projeto 1:** o relatório tinha 24 findings, mas o Summary dizia 23. O modelo rebaixou um HIGH para MEDIUM e não recontou. | Adicionei ao `SKILL.md` uma etapa de **autoconferência** antes de imprimir (Summary = seções = Total, ordem por severidade) e reforcei a regra no template. Na iteração 2: 25 findings, tudo consistente. Os projetos 2 e 3 já saíram consistentes de primeira. |
| O idioma das descrições variou entre execuções (português na 1ª, inglês na 2ª) | Regra explícita no template: rótulos fixos em inglês, conteúdo em português do Brasil. |
| Remover endpoints perigosos quebraria "os endpoints originais continuam respondendo" | Playbook P10: proteger com token + flag desligada por padrão; a validação testa sem token (403) **e** com token (comportamento original). |
| No macOS a porta 5000 é ocupada pelo AirPlay Receiver (responde 403), o que confundiria a validação | `validation.md` exige checar a porta antes de subir e usar outra porta livre, e subir o original via `flask --app app run --port` sem editar código. As apps refatoradas leem `PORT` do ambiente. |
| Validar sem sujar o projeto (bancos SQLite criados no boot, dados de teste) | Baseline numa **cópia temporária** do projeto; validação final com banco temporário via variável de ambiente; seção de limpeza obrigatória. |
| Executar e comprovar a pausa da Fase 2 de forma reproduzível | Execução headless: `claude -p "/refactor-arch" --session-id <uuid>` termina na pergunta (conferido com `git status`: nenhum arquivo alterado) e `claude -p "y" --resume <uuid>` continua a mesma sessão na Fase 3. |
| Projeto 3 já organizado: risco de "refatorar por refatorar" | Seção "Projetos já parcialmente organizados" no `mvc-architecture.md`. A skill manteve `models/` e `routes/`, criou `config/`, `controllers/` e `middlewares/`, integrou o que era útil de `utils/helpers.py` e removeu o resto. |

---

## Resultados

### Resumo das auditorias

| Projeto | Arquivos / linhas analisados | CRITICAL | HIGH | MEDIUM | LOW | Total | APIs deprecated |
|---|---|---|---|---|---|---|---|
| code-smells-project | 4 / ~780 | 9 | 6 | 5 | 5 | **25** | nenhuma (seção lista o que foi verificado) |
| ecommerce-api-legacy | 3 / ~180 | 7 | 6 | 2 | 5 | **20** | API só de callbacks do `sqlite3` (padrão legado) |
| task-manager-api | 15 / ~1.160 | 4 | 5 | 7 | 5 | **21** | `Model.query.get()` (16×), `datetime.utcnow()` (20+×) |

Os 3 relatórios estão em [`reports/`](reports/) e cobrem todos os problemas da análise manual. A skill achou também problemas que eu não tinha listado, por exemplo: quantidade negativa num pedido **aumenta** o estoque (P1); um `card` numérico derruba o processo Node (P2); qualquer um pode se cadastrar como `admin` (P3).

### Antes e depois da estrutura

**Projeto 1 — code-smells-project** (de pseudo-camadas para MVC)

```
ANTES (4 arquivos)                  DEPOIS (34 arquivos)
app.py          config + rotas +    app.py                     entry point fino (python app.py)
                SQL admin           .env.example  .gitignore
controllers.py  validação + regras  src/
                + notificações      ├── app.py                 create_app(): composition root
models.py       SQL concatenado de  ├── config/settings.py     configuração por variáveis de ambiente
                4 domínios          ├── database/              conexão por request (flask.g), schema com FKs, seed com hash
database.py     conexão global +    ├── models/                produto, usuario, pedido, admin, sistema
                schema + seed       ├── controllers/           um por domínio + validators.py
                                    ├── views/                 blueprints por domínio + response.py
                                    ├── services/              notification_service.py
                                    ├── middlewares/           error_handler.py, auth.py (X-Admin-Token)
                                    └── errors.py              AppError, NotFoundError, ValidationError...
```

**Projeto 2 — ecommerce-api-legacy** (de God Class para MVC com services)

```
ANTES (3 arquivos)                  DEPOIS (25 arquivos)
src/app.js                          src/app.js                 entry point (npm start)
src/AppManager.js  God Class:       src/server.js              createApp(): composition root / DI
                   DB + schema +    src/config/index.js        process.env com defaults seguros
                   seed + rotas +   src/database/              wrapper com Promise + transaction() serializada; schema com FKs/CASCADE
                   checkout +       src/models/                user, course, enrollment, payment, auditLog
                   relatório        src/services/              checkout, payment, report, password (scrypt)
src/utils.js       segredos +       src/controllers/           checkout, report, user
                   cache global +   src/routes/                checkout, admin, user (finas)
                   badCrypto        src/middlewares/           auth.js (X-Admin-Token), errorHandler.js
                                    src/utils/                 logger, errors, validation
```

**Projeto 3 — task-manager-api** (de camadas parciais para MVC completo)

```
ANTES                               DEPOIS
app.py        config hardcoded      app.py                     create_app() + entry point
models/       ok, mas MD5 e         config/                    settings.py (env) + constants.py
              password no to_dict   models/                    mantidos; hash werkzeug, consultas agregadas, sem password
routes/       fazem tudo            controllers/               task, user, category, report + validators
              (validação, regras,   routes/                    blueprints finos; category_routes e system_routes separados
              queries, JSON)        middlewares/               error_handler.py, auth.py (token assinado)
services/     não usado             services/                  notification (injetado, desligado por padrão), token
utils/        não usado             utils/dates.py             utcnow() (substitui datetime.utcnow)
```

### Checklists de validação

| Item | P1 code-smells | P2 ecommerce | P3 task-manager |
|---|---|---|---|
| **Fase 1 — Análise** | | | |
| Linguagem detectada corretamente | ✅ Python | ✅ JavaScript (Node.js) | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express ^4.18.2 | ✅ Flask 3.0.0 + Flask-SQLAlchemy |
| Domínio descrito corretamente | ✅ E-commerce (produtos, usuários, pedidos) | ✅ LMS com checkout (cursos, matrículas, pagamentos) | ✅ Task Manager (tasks, usuários, categorias, relatórios) |
| Número de arquivos condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 |
| **Fase 2 — Auditoria** | | | |
| Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Findings ordenados CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 25 | ✅ 20 | ✅ 21 |
| Detecção de APIs deprecated (se aplicável) | ✅ verificado, nenhuma | ✅ callbacks sqlite3 | ✅ `Query.get`, `utcnow` |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3 — Refatoração** | | | |
| Estrutura de diretórios segue MVC | ✅ | ✅ | ✅ |
| Configuração extraída (sem hardcoded) | ✅ `src/config/settings.py` + `.env.example` | ✅ `src/config/index.js` + `.env.example` | ✅ `config/settings.py` + `.env.example` |
| Models abstraem os dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ `src/views/` | ✅ `src/routes/` | ✅ `routes/` |
| Controllers concentram o fluxo | ✅ | ✅ (+ services) | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `python app.py` | ✅ `npm start` | ✅ `python app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem | ✅ 19/19 rotas | ✅ 3/3 rotas | ✅ 22/22 rotas |

### Logs das aplicações rodando

- **Execução completa da skill** (Fases 1 e 2, confirmação, Fase 3 com o resumo de validação):
  [projeto 1](docs/logs/skill-run-project-1.md) · [projeto 2](docs/logs/skill-run-project-2.md) · [projeto 3](docs/logs/skill-run-project-3.md)
- **Smoke test independente** (`scripts/smoke.sh`, rodado por mim depois da skill, com banco temporário e todas as rotas):
  [projeto 1](docs/logs/smoke-code-smells-project.log) · [projeto 2](docs/logs/smoke-ecommerce-api-legacy.log) · [projeto 3](docs/logs/smoke-task-manager-api.log)

Trecho do smoke test do projeto 1 (SQL injection no login agora dá 401; a rota admin exige token):

```
POST   /login                               -> 401  {"erro":"Email ou senha inválidos","sucesso":false}
POST   /pedidos                             -> 201  {"dados":{"pedido_id":1,"total":179.8},"mensagem":"Pedido criado com sucesso","sucesso":true}
POST   /pedidos                             -> 400  {"erro":"Item inválido: produto_id e quantidade devem ser inteiros positivos"}
POST   /admin/query                         -> 403  {"erro":"Acesso administrativo negado"}
POST   /admin/query                         -> 200  {"dados":[{"n":11}],"sucesso":true}
-- log do servidor (tracebacks: 0) --
```

Nenhum dos 3 smoke tests teve resposta 5xx nem traceback no log do servidor.

### Comportamento da skill em stacks diferentes

- **Fase 1** classificou cada projeto de forma diferente e correta: *pseudo-camadas* (P1: nomes de camada, responsabilidades vazando), *monolítica/God Class* (P2) e *camadas parciais* (P3: pastas existem, rotas fazem tudo, services/utils não usados).
- **Fase 2** adaptou os sinais à sintaxe: concatenação de SQL em Python (P1), callbacks aninhados e `err` ignorado em Node (P2), N+1 via ORM (`Query.get` em loop, `len(u.tasks)`) em SQLAlchemy (P3). A detecção de APIs deprecated foi mais útil no P3 (SQLAlchemy 2.x e Python 3.12); no P1 a seção registra explicitamente que nada foi encontrado.
- **Fase 3** escolheu transformações diferentes por contexto:
  - **P1 (sqlite3 puro):** conexão por request com `flask.g` e queries com `?`.
  - **P2 (Node):** wrapper com Promise, `async/await`, transação serializada por mutex (testada com 25 checkouts concorrentes) e uma camada de services.
  - **P3 (já organizado):** manteve models e routes e só criou as camadas que faltavam.
- **Segurança vs. contrato:** nos 3 casos a skill listou as mudanças intencionais de contrato (ex.: `senha`/`password` removidos das respostas, rotas admin exigindo token) e manteve o resto idêntico ao baseline.

### Riscos residuais

Reportados pela própria skill no resumo da Fase 3 (ela foi instruída a não inventar um sistema de autenticação completo):

- **P1:** `PUT/DELETE /produtos`, `PUT /pedidos/<id>/status` e `GET /relatorios/vendas` continuam públicos, porque a API original não tem identidade de usuário. Cancelar um pedido continua não devolvendo estoque (comportamento original, depende de decisão de negócio).
- **P2:** checkout sem `pwd` cria usuário sem senha (antes usava a senha default `123456`). O caminho de erro 500 foi verificado só por leitura.
- **P3:** `DELETE /tasks/<id>` e edição de dados de outros usuários ainda não checam dono. Sem `SECRET_KEY` definida, os tokens são invalidados a cada restart.

---

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) instalado e autenticado (`claude --version`). Usei a versão 2.1.285.
- Python 3.10+ (usei 3.14) para os projetos 1 e 3.
- Node.js 18+ e npm (usei Node 26) para o projeto 2.
- `curl` para o script de smoke test.

### Executar a skill em cada projeto

A skill fica em `.claude/skills/refactor-arch/` dentro de cada projeto (cópias idênticas). Rode o Claude Code **dentro da pasta do projeto**:

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Em cada execução: a Fase 1 imprime o resumo do projeto, a Fase 2 imprime o relatório e pergunta `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar ou `n` para ficar só com o relatório.

Execução não interativa (como os logs deste repositório foram gerados):

```bash
SID=$(uuidgen | tr A-Z a-z)
claude -p "/refactor-arch" --session-id "$SID" --permission-mode auto   # Fases 1 e 2, para na pergunta
claude -p "y" --resume "$SID" --permission-mode auto                     # Fase 3
```

> Os projetos deste repositório **já estão refatorados**. Para rodar a skill sobre o código original, use o commit inicial do [repositório base](https://github.com/devfullcycle/mba-ia-refactor-projects-skill) e copie a pasta `.claude/skills/refactor-arch/` para dentro de cada projeto.

### Validar que a refatoração funcionou

```bash
# dependências (uma vez)
(cd code-smells-project && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt)
(cd task-manager-api   && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt)
(cd ecommerce-api-legacy && npm install)

# smoke test: sobe cada API com banco temporário, chama todas as rotas e encerra
scripts/smoke.sh code-smells-project
scripts/smoke.sh ecommerce-api-legacy
scripts/smoke.sh task-manager-api
```

O que conferir: todas as rotas respondem com os status esperados (2xx nos fluxos válidos, 4xx nos inválidos, 403/401 nas rotas protegidas sem credencial), nenhum 5xx, e `tracebacks: 0` no log do servidor.

Para subir manualmente, veja o README de cada projeto (`.env.example` lista as variáveis). No macOS, use `PORT=5055`, porque o AirPlay ocupa a porta 5000.

### Ordem sugerida

1. Ler o código dos projetos e registrar a análise manual.
2. Escrever `SKILL.md` e as referências em `code-smells-project/.claude/skills/refactor-arch/`.
3. Rodar no projeto 1, revisar o relatório, ajustar as referências e repetir até o relatório ficar correto. Então confirmar a Fase 3.
4. Copiar a skill para `ecommerce-api-legacy/` e `task-manager-api/` e rodar em cada um.
5. Salvar a saída da Fase 2 em `reports/audit-project-{1,2,3}.md` e validar com `scripts/smoke.sh`.

---

## Estrutura do repositório

```
desafiotecnico3/
├── README.md                     # esta documentação
├── code-smells-project/          # Projeto 1 refatorado (+ .claude/skills/refactor-arch/)
├── ecommerce-api-legacy/         # Projeto 2 refatorado (+ cópia da skill)
├── task-manager-api/             # Projeto 3 refatorado (+ cópia da skill)
├── reports/
│   ├── audit-project-1.md        # saída da Fase 2 no projeto 1
│   ├── audit-project-2.md        # saída da Fase 2 no projeto 2
│   └── audit-project-3.md        # saída da Fase 2 no projeto 3
├── scripts/smoke.sh              # smoke test dos projetos refatorados
└── docs/logs/                    # logs de execução da skill e dos smoke tests
```
