================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express ^4.18.2 (SQLite em memória via sqlite3)
Files:   3 analyzed | ~180 lines of code
Date:    2026-10-13

## Summary
CRITICAL: 7 | HIGH: 6 | MEDIUM: 2 | LOW: 5

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP01 | Credenciais e segredos hardcoded | src/utils.js:2-4 |
| 2 | CRITICAL | AP05 | Número do cartão e chave do gateway em log | src/AppManager.js:45 |
| 3 | CRITICAL | AP06 | Armazenamento inseguro de senhas | src/utils.js:17-23; src/AppManager.js:18, 68 |
| 4 | CRITICAL | AP04 | Endpoint destrutivo sem proteção | src/AppManager.js:131-137 |
| 5 | CRITICAL | AP11 | Relatório financeiro sem autenticação | src/AppManager.js:80-129 |
| 6 | CRITICAL | AP10 | Checkout em múltiplos passos sem transação / callback hell | src/AppManager.js:37-77 |
| 7 | CRITICAL | AP03 | God Class AppManager | src/AppManager.js:4-139 |
| 8 | HIGH | AP15 | Validação de entrada ausente (derruba o processo) | src/AppManager.js:29-35, 46, 132 |
| 9 | HIGH | AP07 | Regras de negócio dentro das rotas | src/AppManager.js:28-78, 80-129 |
| 10 | HIGH | AP19 | Integridade referencial ausente (dados órfãos) | src/AppManager.js:12-15, 131-137 |
| 11 | HIGH | AP08 | Acoplamento forte sem injeção de dependência | src/AppManager.js:5-8; src/app.js:8-10 |
| 12 | HIGH | AP09 | Estado global mutável | src/utils.js:9-15, 25 |
| 13 | HIGH | AP12 | Configuração fixa no código | src/utils.js:6; src/AppManager.js:7 |
| 14 | MEDIUM | AP13 | Queries N+1 no relatório financeiro | src/AppManager.js:83-106 |
| 15 | MEDIUM | AP16 | Tratamento de erros silencioso e inconsistente | src/AppManager.js:35, 38, 41, 57, 92-93, 104-106, 133-135 |
| 16 | LOW | AP17 | API de callbacks do sqlite3 (padrão legado) | src/AppManager.js:37-133 |
| 17 | LOW | AP20 | Magic numbers e magic strings | src/AppManager.js:46, 68, 108; src/utils.js:6, 19 |
| 18 | LOW | AP21 | Nomenclatura ruim | src/AppManager.js:26, 29-33; src/utils.js:17 |
| 19 | LOW | AP22 | Imports não usados e código morto | src/AppManager.js:2; src/utils.js:2-3, 5, 10, 25 |
| 20 | LOW | AP23 | console.log no lugar de logging | src/app.js:13; src/utils.js:13; src/AppManager.js:45 |

## Findings

### #1 [CRITICAL] Credenciais e segredos hardcoded (AP01)
File: src/utils.js:2-4
Description: O objeto `config` contém literais de credenciais: `dbPass` = `"senha_super_secreta_prod_123"`, `dbUser` = `"admin_master"` e `paymentGatewayKey` = `"pk_live_1234567890abcdef"` (prefixo de chave live). Nada é lido de `process.env`.
Evidence:
```js
dbPass: "senha_super_secreta_prod_123", 
paymentGatewayKey: "pk_live_1234567890abcdef",
```
Impact: qualquer pessoa com acesso ao repositório obtém a chave do gateway de pagamento e a senha do banco "de produção"; rotação exige commit + deploy.
Recommendation: mover para módulo `config` lido de variáveis de ambiente, sem defaults sensíveis, com `.env.example` de placeholders (Playbook P1).

### #2 [CRITICAL] Exposição de dados sensíveis em logs (AP05)
File: src/AppManager.js:45
Description: o checkout loga o número completo do cartão (`cc`) junto com `config.paymentGatewayKey` em texto puro a cada compra.
Evidence:
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
Impact: violação direta de PCI-DSS (PAN em log) e vazamento da chave do gateway para qualquer agregador de logs.
Recommendation: remover o log; se necessário registrar apenas os 4 últimos dígitos mascarados, nunca a chave (Playbook P9).

### #3 [CRITICAL] Armazenamento inseguro de senhas (AP06)
File: src/utils.js:17-23; src/AppManager.js:18, 68
Description: `badCrypto` repete os 2 primeiros caracteres do base64 da senha e corta em 10 caracteres — o "hash" depende só dos ~2 primeiros bytes da senha (senhas `"senhaforte"` e `"se"` colidem). O seed grava `'123'` em texto puro (linha 18) e, sem `pwd`, o checkout cria a conta com senha default `"123456"` (linha 68).
Evidence:
```js
hash += Buffer.from(pwd).toString('base64').substring(0, 2);
let hash = badCrypto(p || "123456");
```
Impact: com o banco vazado, as senhas são triviais de recuperar/forjar; contas criadas sem senha têm senha conhecida por todos.
Recommendation: usar `crypto.scrypt` (nativo do Node) com salt aleatório por usuário; não criar senha default (Playbook P9).

### #4 [CRITICAL] Endpoint destrutivo sem proteção (AP04)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` apaga qualquer usuário sem nenhuma autenticação ou checagem de papel.
Evidence:
```js
app.delete('/api/users/:id', (req, res) => {
    this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
```
Impact: qualquer cliente anônimo apaga todos os usuários iterando ids.
Recommendation: proteger com middleware de autenticação administrativa (token via variável de ambiente) (Playbook P10).

### #5 [CRITICAL] Relatório financeiro sem autenticação (AP11)
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` devolve receita por curso e nome de cada aluno com valor pago, sem qualquer controle de acesso. Severidade elevada de HIGH para CRITICAL por expor dados financeiros e pessoais.
Evidence:
```js
app.get('/api/admin/financial-report', (req, res) => {
```
Impact: exposição pública de faturamento e dados pessoais (LGPD).
Recommendation: aplicar o mesmo middleware de autenticação administrativa do #4 (Playbook P10).

### #6 [CRITICAL] Checkout em múltiplos passos sem transação / callback hell (AP10)
File: src/AppManager.js:37-77
Description: o checkout encadeia 5 níveis de callbacks e executa `INSERT users` → `INSERT enrollments` → `INSERT payments` → `INSERT audit_logs` sem `BEGIN/COMMIT/ROLLBACK`. Se o insert de pagamento falhar (linha 55), a matrícula já foi gravada; o erro do audit log (linha 57) é ignorado. Severidade elevada de HIGH para CRITICAL por ser fluxo de dinheiro.
Evidence:
```js
this.db.run("INSERT INTO enrollments ...", [userId, cid], function(err) {
    self.db.run("INSERT INTO payments ...", [enrId, course.price, status], function(err) {
```
Impact: matrículas sem pagamento (acesso grátis ao curso) e usuários criados em checkouts que falharam.
Recommendation: wrapper com Promises + `async/await` e transação única envolvendo todas as escritas (Playbook P11).

### #7 [CRITICAL] God Class AppManager (AP03)
File: src/AppManager.js:4-139
Description: a classe `AppManager` acumula conexão com o banco (l.7), DDL (l.12-16), seeds (l.18-21), registro de rotas (l.25-137), validação (l.35), regra de pagamento (l.46), criação de usuário, auditoria e agregação do relatório.
Evidence:
```js
initDb() { ... CREATE TABLE ... INSERT INTO ... }
setupRoutes(app) { app.post('/api/checkout', ...
```
Impact: nada pode ser testado isoladamente; qualquer mudança em uma rota mexe no arquivo que contém o schema.
Recommendation: separar em config / database / models / controllers / routes / middlewares (Playbook P3).

### #8 [HIGH] Validação de entrada ausente (AP15)
File: src/AppManager.js:29-35, 46, 132
Description: o checkout só checa truthiness de `usr`, `eml`, `c_id`, `card`. Não valida tipo: um `card` numérico (ex.: `"card": 4111`) faz `cc.startsWith` lançar `TypeError` dentro do callback do sqlite — exceção não capturada que **derruba o processo Node inteiro**. `eml` sem formato, `c_id` sem conversão, `:id` do DELETE sem validação. Severidade elevada de MEDIUM para HIGH: qualquer cliente anônimo derruba a API no fluxo de pagamento.
Evidence:
```js
if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");
let status = cc.startsWith("4") ? "PAID" : "DENIED";
```
Impact: DoS trivial com um único request; dados inválidos no banco.
Recommendation: validar presença e tipo (strings, inteiro positivo, e-mail) no controller antes de qualquer acesso ao banco, respondendo 400 (Playbook P13).

### #9 [HIGH] Regras de negócio dentro das rotas (AP07)
File: src/AppManager.js:28-78, 80-129
Description: o handler de checkout (51 linhas) faz validação, busca de curso, find-or-create de usuário, hash, aprovação do pagamento, matrícula, pagamento, auditoria, cache e resposta. O handler do relatório (50 linhas) faz a agregação de receita e a montagem dos alunos com contadores manuais.
Impact: regras de pagamento e de receita não são reutilizáveis nem testáveis sem HTTP.
Recommendation: mover o fluxo para `CheckoutController` / `ReportController` e o acesso a dados para models; rotas só delegam (Playbook P4).

### #10 [HIGH] Integridade referencial ausente (AP19)
File: src/AppManager.js:12-15, 131-137
Description: `enrollments.user_id`, `enrollments.course_id` e `payments.enrollment_id` não têm `FOREIGN KEY`; o DELETE de usuário não trata matrículas e pagamentos — a própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco". Elevado de MEDIUM para HIGH: os órfãos entram no relatório financeiro como aluno `'Unknown'` com receita contabilizada.
Evidence:
```js
res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
```
Impact: relatórios financeiros com dados corrompidos.
Recommendation: declarar FKs com `ON DELETE CASCADE` + `PRAGMA foreign_keys = ON`, ou remover filhos na mesma transação (Playbook P11).

### #11 [HIGH] Acoplamento forte sem injeção de dependência (AP08)
File: src/AppManager.js:5-8; src/app.js:8-10
Description: o construtor de `AppManager` instancia `new sqlite3.Database(':memory:')` diretamente, e o mesmo objeto que é dono do banco registra as rotas (`manager.setupRoutes(app)`). Não há composition root/factory.
Impact: impossível usar outro banco, mockar em teste ou subir o app sem abrir a conexão.
Recommendation: app factory que cria a conexão e injeta nos models/controllers (Playbook P5).

### #12 [HIGH] Estado global mutável (AP09)
File: src/utils.js:9-15, 25
Description: `let globalCache = {}` é mutado por `logAndCache` a cada checkout (`last_checkout_${userId}`) e exportado; nunca é lido nem limpo. `let totalRevenue = 0` é exportado por valor (cópia), então nunca reflete nada.
Evidence:
```js
let globalCache = {};
let totalRevenue = 0;
```
Impact: cresce sem limite (vazamento de memória por usuário) e cria estado compartilhado escondido entre requisições.
Recommendation: remover (nenhum consumidor); se cache for necessário, injetar um componente com escopo e limite (Playbook P6).

### #13 [HIGH] Configuração fixa no código (AP12)
File: src/utils.js:6; src/AppManager.js:7
Description: `port: 3000` e o caminho do banco `':memory:'` são literais sem leitura de variável de ambiente.
Impact: impossível configurar por ambiente sem editar código.
Recommendation: ler `PORT` e `DB_PATH` de `process.env` com defaults seguros (`3000`, `:memory:`) no módulo de config (Playbook P1).

### #14 [MEDIUM] Queries N+1 no relatório financeiro (AP13)
File: src/AppManager.js:83-106
Description: 1 query de cursos, depois 1 query de matrículas por curso e, para cada matrícula, 1 query de usuário + 1 de pagamento: 1 + C + 2E queries.
Evidence:
```js
courses.forEach(c => { this.db.all("SELECT * FROM enrollments WHERE course_id = ?", ...
    enrollments.forEach(enr => { this.db.get("SELECT name, email FROM users ...
```
Impact: latência cresce linearmente com matrículas; com milhares de alunos o relatório trava.
Recommendation: uma única query com `LEFT JOIN` courses → enrollments → users → payments e agregação em memória (Playbook P7).

### #15 [MEDIUM] Tratamento de erros silencioso e inconsistente (AP16)
File: src/AppManager.js:35, 38, 41, 57, 92-93, 104-106, 133-135
Description: erros respondem em texto puro (`"Bad Request"`, `"Erro DB"`) enquanto sucesso é JSON; `err` ignorado nas linhas 57, 92, 104, 106 e 133. Na l.92-93, um erro deixa `enrollments` `undefined` e `enrollments.length` lança exceção (crash). O DELETE sempre responde sucesso, mesmo com erro ou id inexistente. Não existe middleware `(err, req, res, next)`.
Impact: falhas somem ou derrubam o processo; clientes recebem formatos imprevisíveis.
Recommendation: controllers `async` propagando erros para um middleware central de erros com log (Playbook P8).

### #16 [LOW] API de callbacks do sqlite3 — padrão legado (AP17)
File: src/AppManager.js:37-133
Description: todo o acesso usa a API de callbacks do `sqlite3` (`db.get/run/all` com callback), causa raiz do callback hell do #6. Não foi removida; classificado como LOW (estilo/padrão legado).
Impact: fluxo assíncrono difícil de ler e de propagar erros.
Recommendation: wrapper com Promises (`util.promisify` / `new Promise`) + `async/await` (Playbook P12).

### #17 [LOW] Magic numbers e magic strings (AP20)
File: src/AppManager.js:46, 68, 108; src/utils.js:6, 19
Description: regra de aprovação por prefixo `cc.startsWith("4")`; status `"PAID"`/`"DENIED"` repetidos como strings soltas (l.46, 48, 108); senha default `"123456"`; porta `3000`; loop de `10000` iterações em `badCrypto`.
Impact: regra de negócio escondida e duplicada.
Recommendation: constantes nomeadas (`PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`) (Playbook P13).

### #18 [LOW] Nomenclatura ruim (AP21)
File: src/AppManager.js:26, 29-33; src/utils.js:17
Description: variáveis `u`, `e`, `p`, `cid`, `cc`; `const self = this`; função `badCrypto`; classe genérica `AppManager`. (Os campos de contrato `usr`, `eml`, `pwd`, `c_id`, `card` serão mantidos.)
Impact: leitura e revisão mais lentas.
Recommendation: nomes descritivos internos (`name`, `email`, `password`, `courseId`, `cardNumber`) (Playbook P14).

### #19 [LOW] Imports não usados e código morto (AP22)
File: src/AppManager.js:2; src/utils.js:2-3, 5, 10, 25
Description: `totalRevenue` é importado em AppManager e nunca usado; `dbUser`, `dbPass` e `smtpUser` não são referenciados em lugar nenhum; `globalCache` é escrito e nunca lido.
Impact: ruído e falsa impressão de funcionalidade (SMTP, banco autenticado).
Recommendation: remover (Playbook P14).

### #20 [LOW] console.log no lugar de logging (AP23)
File: src/app.js:13; src/utils.js:13; src/AppManager.js:45
Description: banner "Frankenstein LMS rodando...", `[LOG] Salvando no cache` e o log do cartão usam `console.log` sem nível.
Impact: sem níveis nem controle de verbosidade por ambiente.
Recommendation: logger mínimo com níveis (`console.info/warn/error` encapsulado) (Playbook P14).

## Deprecated APIs
| Location | Deprecated API | Modern replacement |
|---|---|---|
| src/AppManager.js:37-133 | sqlite3 API só de callbacks (padrão legado) | wrapper com Promises + `async/await` |

Verificado também, sem ocorrências: `new Buffer(` (usa `Buffer.from`, ok), `url.parse(`, `crypto.createCipher(`, `fs.exists(`, `body-parser`, `res.send(status, body)`, `res.json(obj, status)`, `req.param()`, `app.del(`, pacotes `request`/`node-uuid`.

## Architecture Notes
- Current: Monolítica / God Class — `AppManager.js` é dono do banco, do schema, dos seeds, das rotas e das regras; `utils.js` mistura config com segredos, estado global e "cripto".
- Target: `src/config` (env) → `src/database` (conexão Promise + schema/seed) → `src/models` → `src/controllers` → `src/routes` (finas) + `src/middlewares` (auth admin, erros), montados por `createApp()` com `src/app.js` mantido como entry point.

================================
Total: 20 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
