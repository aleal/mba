# Execução da skill `/refactor-arch` — ecommerce-api-legacy

Saída do Claude Code em modo headless (`claude -p "/refactor-arch"`, seguido de `claude -p "y" --resume <sessão>`).

## Fases 1 e 2 (análise e auditoria, pausa para confirmação)

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js — versão não declarada no package.json)
Framework:     Express ^4.18.2
Dependencies:  express ^4.18.2, sqlite3 ^5.1.6
Database:      SQLite em memória (':memory:') via driver puro sqlite3 (SQL manual, callbacks)
Domain:        LMS com checkout (usuários, cursos, matrículas, pagamentos, logs de auditoria)
Architecture:  Monolítica / God Class — src/AppManager.js concentra conexão, DDL, seeds, rotas, validação, regras de checkout e relatório
Entry point:   src/app.js (npm start → node src/app.js, porta 3000)
Source files:  3 files analyzed (~180 lines)
DB tables:     users, courses, enrollments, payments, audit_logs
Endpoints:     3 routes
================================
```

| Método | Path | Handler | Observação |
|---|---|---|---|
| POST | `/api/checkout` | `src/AppManager.js:28` | grava dados (user/enrollment/payment/audit) |
| GET | `/api/admin/financial-report` | `src/AppManager.js:80` | admin, sem auth |
| DELETE | `/api/users/:id` | `src/AppManager.js:131` | ⚠️ **destrutivo**, sem auth |

Payloads de exemplo: `api.http` (checkout aprovado com cartão `4…`, recusado com `5…`).

````markdown
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
````

## Resposta do usuário

```
y
```

## Fase 3 (refatoração e validação)

````text
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── app.js                      # entry point (npm start → node src/app.js)
├── server.js                   # createApp(): composition root / DI
├── config/index.js             # process.env com defaults seguros
├── database/
│   ├── connection.js           # wrapper Promise + transaction() serializada (mutex)
│   └── schema.js               # DDL com FKs/ON DELETE CASCADE + seed (senha com hash)
├── models/                     # userModel, courseModel, enrollmentModel, paymentModel, auditLogModel
├── services/                   # checkoutService, paymentService, reportService, passwordService
├── controllers/                # checkoutController, reportController, userController
├── routes/                     # checkoutRoutes, adminRoutes, userRoutes (finas)
├── middlewares/                # auth.js (X-Admin-Token), errorHandler.js (asyncHandler + handler central)
└── utils/                      # logger.js, errors.js (AppError), validation.js
.env.example
(removidos: src/AppManager.js, src/utils.js)

## Findings Resolved
#1  AP01 — Segredos hardcoded — config/index.js lê env, sem defaults reais; .env.example (P1)
#2  AP05 — Cartão/chave em log — PaymentService loga só os 4 últimos dígitos (P9)
#3  AP06 — Senhas inseguras — crypto.scrypt + salt; seed com hash; fim da senha default "123456" (P9)
#4  AP04 — DELETE sem proteção — requireAdmin (X-Admin-Token, timingSafeEqual) (P10)
#5  AP11 — Relatório sem auth — mesmo requireAdmin (P10)
#6  AP10 — Checkout sem transação — async/await + db.transaction() com mutex; pagamento autorizado antes de qualquer escrita (P11)
#7  AP03 — God Class — AppManager dividido em database/models/services/controllers/routes (P3)
#8  AP15 — Validação ausente — validação de tipos/e-mail/inteiros no controller; card numérico agora dá 400 e não derruba mais o processo (P13)
#9  AP07 — Regras nas rotas — fluxo em CheckoutService/ReportService; controllers finos (P4)
#10 AP19 — Dados órfãos — FKs com ON DELETE CASCADE + PRAGMA foreign_keys=ON (P11)
#11 AP08 — Acoplamento — conexão aberta no entry point e injetada via createApp (P5)
#12 AP09 — Estado global — globalCache/totalRevenue removidos (sem consumidores) (P6)
#13 AP12 — Config fixa — PORT/DB_PATH via env (P1)
#14 AP13 — N+1 — uma única query com LEFT JOINs + agregação em memória (P7)
#15 AP16 — Erros silenciosos — asyncHandler + handler central; todo erro do banco propaga; 500 logado sem vazar detalhes (P8)
#16 AP17 — sqlite3 só com callbacks — wrapper com Promises em database/connection.js (P12)
#17 AP20 — Magic values — PAYMENT_STATUS, APPROVED_CARD_PREFIX, SALT_BYTES/KEY_LENGTH (P13)
#18 AP21 — Nomes ruins — name/email/password/courseId/cardNumber; contrato usr/eml/pwd/c_id/card mantido (P14)
#19 AP22 — Código morto — dbUser/dbPass/smtpUser/totalRevenue/logAndCache/badCrypto removidos (P14)
#20 AP23 — console.log — logger com níveis (LOG_LEVEL) (P14)

## Intentional Contract Changes
- GET /api/admin/financial-report e DELETE /api/users/:id exigem header X-Admin-Token = ADMIN_TOKEN; sem token ou com token errado → 403 "Acesso negado". Sem ADMIN_TOKEN configurado as duas rotas ficam sempre bloqueadas (fail-closed).
- O texto de sucesso do DELETE mudou de "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco." para "Usuário deletado." (status 200 e text/plain mantidos). A mensagem antiga deixou de ser verdade com o cascade. Não é uma mudança de segurança: reverta se algum cliente faz match nesse texto.
- Entradas inválidas que antes derrubavam o processo (ex.: card numérico) ou passavam sem checagem (e-mail inválido, :id não numérico) agora devolvem 400 "Bad Request".

## Validation
  ✓ Application boots without errors (npm start; log limpo, warning claro quando falta ADMIN_TOKEN)
  ✓ All endpoints respond correctly (7/7 com o mesmo status e formato do baseline; 6/7 com corpo idêntico, o DELETE só difere no texto intencional acima; os valores do relatório financeiro são idênticos ao baseline)
  ✓ Admin routes without token → 403 (2/2), with token → original behavior
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (re-varredura AP01/02/05/06/09/13: só 2 falsos positivos, um typeof e um loop de agregação em memória)
  ✓ node --check em todos os 23 arquivos .js
  ✓ Casos de borda: card numérico, JSON malformado e e-mail inválido → 400; checkout sem pwd → 200 (usuário criado sem senha); DELETE confirmado em cascata (sem aluno "Unknown" depois)
  ✓ 25 checkouts concorrentes → 25×200, receita e contagem de alunos batem com a conta (sem transações intercaladas)
  ✗ Caminho de 500 não exercitado ao vivo (não dá para forçar falha de banco sem editar código); o handler foi verificado só por leitura
  ✓ Cleanup: servidores mortos, porta 3000 livre, diretório temporário apagado

## How to run
npm install
ADMIN_TOKEN=um-token-secreto npm start      # opcional: PORT, DB_PATH, PAYMENT_GATEWAY_KEY, LOG_LEVEL
================================
````
