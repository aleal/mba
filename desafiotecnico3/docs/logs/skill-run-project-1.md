# Execução da skill `/refactor-arch` — code-smells-project

Saída do Claude Code em modo headless (`claude -p "/refactor-arch"`, seguido de `claude -p "y" --resume <sessão>`).

## Fases 1 e 2 (análise e auditoria, pausa para confirmação)

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (version not declared)
Framework:     Flask 3.1.1
Dependencies:  flask==3.1.1, flask-cors==5.0.1, sqlite3 (stdlib)
Database:      SQLite (`loja.db`), raw driver `sqlite3` with handwritten SQL and a single global connection
Domain:        E-commerce API (produtos, usuários, pedidos/itens de pedido, relatório de vendas)
Architecture:  Pseudo-camadas — `models.py`/`controllers.py` look like layers, but `models.py` holds SQL plus business rules (total, estoque, desconto), `controllers.py` does validation, rules, notifications and SQL (health), and `app.py` has routes with raw SQL
Entry point:   app.py (`python app.py` → 0.0.0.0:5000, debug=True)
Source files:  4 files analyzed (~780 lines)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 routes
================================

| Method | Path | Handler |
|---|---|---|
| GET | `/` | app.py:32 `index` |
| GET | `/produtos` | controllers.py:5 `listar_produtos` (app.py:11) |
| GET | `/produtos/busca` | controllers.py:111 `buscar_produtos` (app.py:12) |
| GET | `/produtos/<id>` | controllers.py:14 `buscar_produto` (app.py:13) |
| POST | `/produtos` | controllers.py:24 `criar_produto` (app.py:14) |
| PUT | `/produtos/<id>` | controllers.py:64 `atualizar_produto` (app.py:15) |
| DELETE | `/produtos/<id>` | controllers.py:98 `deletar_produto` (app.py:16) |
| GET | `/usuarios` | controllers.py:128 `listar_usuarios` (app.py:18) |
| GET | `/usuarios/<id>` | controllers.py:136 `buscar_usuario` (app.py:19) |
| POST | `/usuarios` | controllers.py:146 `criar_usuario` (app.py:20) |
| POST | `/login` | controllers.py:167 `login` (app.py:21) |
| POST | `/pedidos` | controllers.py:188 `criar_pedido` (app.py:23) |
| GET | `/pedidos` | controllers.py:229 `listar_todos_pedidos` (app.py:24) |
| GET | `/pedidos/usuario/<usuario_id>` | controllers.py:222 `listar_pedidos_usuario` (app.py:25) |
| PUT | `/pedidos/<pedido_id>/status` | controllers.py:237 `atualizar_status_pedido` (app.py:26) |
| GET | `/relatorios/vendas` | controllers.py:257 `relatorio_vendas` (app.py:28) |
| GET | `/health` | controllers.py:264 `health_check` (app.py:30) |
| POST | `/admin/reset-db` ⚠️ **destructive** | app.py:48 `reset_database` |
| POST | `/admin/query` ⚠️ **arbitrary SQL** | app.py:60 `executar_query` |

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1 (SQLite via sqlite3)
Files:   4 analyzed | ~780 lines of code
Date:    2026-10-13

## Summary
CRITICAL: 9 | HIGH: 6 | MEDIUM: 5 | LOW: 5

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP02 | SQL Injection | models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-166, 174, 188, 192, 220, 224, 279-281, 289-297 |
| 2 | CRITICAL | AP04 | Dangerous endpoints with no protection | app.py:47-57, 59-78 |
| 3 | CRITICAL | AP05 | Password returned in user responses | models.py:83, 99 |
| 4 | CRITICAL | AP05 | Health check exposes secret_key and internal config | controllers.py:285-289 |
| 5 | CRITICAL | AP06 | Passwords stored and compared in plain text | models.py:109-111, 126-129; database.py:75-83 |
| 6 | CRITICAL | AP01 | Hardcoded secrets and credentials | app.py:7; controllers.py:289; database.py:76 |
| 7 | CRITICAL | AP10 | Order created without transaction (raised: money/stock) | models.py:133-169 |
| 8 | CRITICAL | AP03 | God File — models.py | models.py:1-314 |
| 9 | CRITICAL | AP03 | Entry point with routes and raw SQL | app.py:1-88 |
| 10 | HIGH | AP11 | No authentication/authorization at all | app.py:11-30; controllers.py:167-186 |
| 11 | HIGH | AP12 | Insecure configuration (debug, CORS *, 0.0.0.0) | app.py:8-9, 88; database.py:5 |
| 12 | HIGH | AP15 | Missing input validation (raised: money flow) | controllers.py:43-46, 81-90, 169-170, 195-201, 239-240 |
| 13 | HIGH | AP07 | Fat Controller | controllers.py:24-62, 64-96, 237-255, 264-290 |
| 14 | HIGH | AP09 | Mutable global state (shared connection) | database.py:4-11 |
| 15 | HIGH | AP08 | Tight coupling with no DI / no app factory | models.py:5…286; controllers.py:3, 266; app.py:4-9, 49, 66 |
| 16 | MEDIUM | AP13 | N+1 queries | models.py:139-141, 154-156, 187-193, 219-225, 239-254 |
| 17 | MEDIUM | AP16 | Generic error handling that leaks details | controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292; app.py:77-78 |
| 18 | MEDIUM | AP19 | Missing referential integrity | database.py:36-53; models.py:65-70 |
| 19 | MEDIUM | AP14 | Duplicated code | models.py:12-21, 31-40, 304-313, 79-86, 95-102, 171-201, 203-233; controllers.py:28-46, 72-90 |
| 20 | MEDIUM | AP18 | Inline side effects (email/SMS/push) | controllers.py:208-210, 247-250 |
| 21 | LOW | AP20 | Magic numbers and strings | models.py:247-262; controllers.py:47-52, 242, 285-288; app.py:88 |
| 22 | LOW | AP23 | `print` instead of logging | controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-86 |
| 23 | LOW | AP22 | Unused imports | models.py:2; database.py:2 |
| 24 | LOW | AP21 | Poor naming | controllers.py:56, 160; models.py:187, 191, 219, 223 |
| 25 | LOW | AP24 | Verbose conditionals / meaningless returns | controllers.py:200; models.py:63, 70, 244-245 |

## Findings

### #1 [CRITICAL] SQL Injection (AP02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-166, 174, 188, 192, 220, 224, 279-281, 289-297
Description: Every query in `models.py` is built by string concatenation. The ones you can actually exploit with free text: `login_usuario` concatenates `email` and `senha` from the request body. `criar_produto`/`atualizar_produto` concatenate `nome`, `descricao` and `categoria`. `criar_usuario` concatenates `nome`, `email` and `senha`. `buscar_produtos` builds `LIKE '%" + termo + "%'` and `categoria` from the query string. `criar_pedido` concatenates `item["produto_id"]` and `item["quantidade"]` taken raw from the JSON, with no type check. The rest concatenate `str(id)`, which the `<int:>` converter protects today, but it's the same dangerous pattern.
Evidence:
```python
"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
```
Impact: login with `' OR '1'='1' --` gets in as the first user (the admin). The search allows `UNION SELECT` to read the whole `usuarios` table. Creating a product can run arbitrary writes.
Recommendation: use `?` placeholders with a parameter tuple in every query, including the dynamic search (Playbook P2).

### #2 [CRITICAL] Dangerous endpoints with no protection (AP04)
File: app.py:47-57, 59-78
Description: `POST /admin/reset-db` runs `DELETE` on all 4 tables. `POST /admin/query` runs `cursor.execute(query)` with the `sql` field from the body and commits anything that isn't a SELECT. Neither route has authentication, a role check or an environment flag.
Evidence:
```python
query = dados.get("sql", "")
...
cursor.execute(query)
```
Impact: any anonymous client can wipe the database, read every password (`SELECT * FROM usuarios`) or change any data.
Recommendation: remove `/admin/query` (arbitrary SQL execution has no safe version). Put `/admin/reset-db` behind an admin-token middleware plus an environment flag (Playbook P10).

### #3 [CRITICAL] Password returned in user responses (AP05)
File: models.py:83, 99
Description: `get_todos_usuarios` and `get_usuario_por_id` serialize `"senha": row["senha"]`, and `GET /usuarios` and `GET /usuarios/<id>` return it to the client without authentication. Since passwords are in plain text (#5), the real password is what leaks.
Evidence:
```python
"senha": row["senha"],
```
Impact: anyone can harvest every user's credentials, including the admin's, with one GET. Serious LGPD exposure.
Recommendation: a user serializer that never includes `senha` (Playbook P9).

### #4 [CRITICAL] Health check exposes secret_key and internal config (AP05)
File: controllers.py:285-289
Description: `GET /health` returns `"secret_key": "minha-chave-super-secreta-123"`, `"db_path": "loja.db"`, `"debug": True` and `"ambiente": "producao"` in a public response.
Evidence:
```python
"db_path": "loja.db",
"debug": True,
"secret_key": "minha-chave-super-secreta-123"
```
Impact: the Flask signing key leaks (session forgery) and the response gives an attacker a map of the infrastructure.
Recommendation: the health check returns only status, DB connectivity and counts. Drop secrets and config (Playbook P9).

### #5 [CRITICAL] Passwords stored and compared in plain text (AP06)
File: models.py:109-111, 126-129; database.py:75-83
Description: `criar_usuario` writes `senha` to the table as received. `login_usuario` compares `WHERE ... senha = '<senha>'` in SQL. The seed inserts `admin123`, `123456` and `senha123` in plain text.
Evidence:
```python
"INSERT INTO usuarios (nome, email, senha, tipo) VALUES ('" + nome + "', '" + email + "', '" + senha + "', '" + tipo + "')"
```
Impact: any database leak (and #2/#3 make that trivial) exposes passwords people reuse on other services.
Recommendation: `werkzeug.security.generate_password_hash` on write and `check_password_hash` on login, with lookup by email only. The seed also uses hashes (Playbook P9).

### #6 [CRITICAL] Hardcoded secrets and credentials (AP01)
File: app.py:7; controllers.py:289; database.py:76
Description: `SECRET_KEY = "minha-chave-super-secreta-123"` is a literal in `app.py`, and the same value is repeated in the health check. The admin seed creates `admin@loja.com` / `admin123` on every new database.
Evidence:
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```
Impact: the secret is in the repository. Rotating it requires a deploy. The admin credential is publicly known.
Recommendation: a `config` module that reads `SECRET_KEY`, `DATABASE_PATH`, `ADMIN_TOKEN` and so on from environment variables, plus a `.env.example` (Playbook P1).

### #7 [CRITICAL] Order created without transaction (AP10)
File: models.py:133-169
Description: `criar_pedido` checks stock in one loop, then runs `INSERT pedidos`, N × `INSERT itens_pedido` and N × `UPDATE produtos SET estoque` with a single final `commit()` and no `rollback`. If an exception happens mid-way (for example a bad `quantidade`), the partial writes stay pending on the **global shared connection** (#14), and the next `commit()` from any other request persists them. Checking stock and decrementing it are not atomic either, so concurrent orders can oversell. Raised from HIGH to CRITICAL because it's a money and stock flow.
Evidence:
```python
cursor.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (" + ...
pedido_id = cursor.lastrowid
```
Impact: orphan orders with no items, stock decremented with no order, overselling.
Recommendation: wrap the whole flow in one transaction (`with conn:` / explicit rollback on error). Decrement with a `WHERE estoque >= ?` condition (Playbook P11).

### #8 [CRITICAL] God File — models.py (AP03)
File: models.py:1-314
Description: a 314-line file covering 4 domains (produtos, usuários, pedidos, relatório) that mixes SQL access, row→dict serialization and business rules: the stock check and order total (139-146) and the discount tiers on revenue (256-262).
Evidence:
```python
if faturamento > 10000:
    desconto = faturamento * 0.1
```
Impact: you can't test the discount or order rules without a real database. Any change touches a module shared by every domain.
Recommendation: split into one model/repository per entity (`models/produto.py`, `usuario.py`, `pedido.py`) and move rules to controllers/services (Playbook P3, P4).

### #9 [CRITICAL] Entry point with routes and raw SQL (AP03)
File: app.py:1-88
Description: `app.py` holds configuration (7-9), registration of 16 routes (11-30), an inline route (`index`, 32-45), two admin routes with raw SQL (47-78) and the server boot (80-88). Everything is created when the module is imported, with no `create_app()`.
Evidence:
```python
cursor.execute("DELETE FROM itens_pedido")
```
Impact: you can't build the app with a different config (tests or another environment), and data access leaks into the entry point.
Recommendation: an `app/__init__.py` with `create_app(config)`, routes in blueprints, and a thin `app.py` that keeps `python app.py` (Playbook P3, P5).

### #10 [HIGH] No authentication/authorization at all (AP11)
File: app.py:11-30; controllers.py:167-186
Description: no route checks identity or role. `DELETE /produtos/<id>`, `PUT /produtos/<id>`, `PUT /pedidos/<id>/status`, `GET /usuarios` and `GET /relatorios/vendas` (financial data) are open. `/login` only returns user data and issues no token or session, so authentication doesn't exist.
Evidence:
```python
return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
```
Impact: any client can change prices, delete products, approve or cancel orders and read the revenue figures.
Recommendation: at minimum, an admin-token middleware (`ADMIN_TOKEN` from the env) on the administrative routes. No full login system will be invented (Playbook P10).

### #11 [HIGH] Insecure configuration (AP12)
File: app.py:8-9, 88; database.py:5
Description: `DEBUG = True` and `app.run(host="0.0.0.0", port=5000, debug=True)` are fixed in code. `CORS(app)` has no origin list. `db_path = "loja.db"` is fixed.
Evidence:
```python
app.run(host="0.0.0.0", port=5000, debug=True)
```
Impact: the Werkzeug debugger exposed on every interface allows remote code execution. Open CORS lets any site call the API.
Recommendation: read `DEBUG`, `HOST`, `PORT`, `CORS_ORIGINS` and `DATABASE_PATH` from the environment with safe defaults (Playbook P1).

### #12 [HIGH] Missing input validation (AP15)
File: controllers.py:43-46, 81-90, 169-170, 195-201, 239-240
Description: `preco < 0` and `estoque < 0` compare values straight from the JSON, so a string causes a `TypeError` → 500. `atualizar_produto` skips the `categoria` whitelist and the name length checks that `criar_produto` applies. `login` and `atualizar_status_pedido` call `dados.get` without checking for `None` (body missing → 500). In `criar_pedido`, the `itens` are not validated: `quantidade` can be negative or non-numeric. Raised from MEDIUM to HIGH because of the money flow: a **negative quantity creates an order with a negative total and increases stock**.
Evidence:
```python
usuario_id = dados.get("usuario_id")
itens = dados.get("itens", [])
```
Impact: corrupted stock and revenue, plus 500s for trivial input.
Recommendation: shared validators per entity (create = update) and positive-integer checks on `produto_id`/`quantidade` (Playbook P13).

### #13 [HIGH] Fat Controller (AP07)
File: controllers.py:24-62, 64-96, 237-255, 264-290
Description: the handlers do parsing, validation, domain rules (valid categories, valid status transitions, notifications on approve/cancel) and formatting in one body. `health_check` runs SQL directly on the connection. These are actually HTTP views carrying business rules.
Evidence:
```python
categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
```
Impact: the rules can only be tested through HTTP and get duplicated between create and update.
Recommendation: thin routes (views) → controllers with the rules → models (Playbook P4).

### #14 [HIGH] Mutable global state (AP09)
File: database.py:4-11
Description: a single module-level connection `db_connection`, assigned with `global` and created with `check_same_thread=False`, is shared by every request and thread of the Flask server.
Evidence:
```python
global db_connection
db_connection = sqlite3.connect(db_path, check_same_thread=False)
```
Impact: race conditions, and transactions from one request leak into another (see #7).
Recommendation: one connection per request in `flask.g`, closed in `teardown_appcontext`, with the path coming from config (Playbook P6).

### #15 [HIGH] Tight coupling with no DI / no app factory (AP08)
File: models.py:5, 25, 44, 55, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286; controllers.py:3, 266; app.py:4-9, 49, 66
Description: every model function calls the singleton `get_db()` directly. Controllers import `models` and `get_db` as concrete modules. The app is built when `app.py` is imported.
Impact: you can't swap the database or point at a test database without monkeypatching.
Recommendation: a composition root in `create_app()`, with the connection provided by the request context (Playbook P5).

### #16 [MEDIUM] N+1 queries (AP13)
File: models.py:139-141, 154-156, 187-193, 219-225, 239-254
Description: `get_pedidos_usuario`/`get_todos_pedidos` run one query per order (items) plus one per item (product name): 1 + N + N×M. `criar_pedido` looks up each product twice. `relatorio_vendas` runs 5 separate queries, 3 of them `COUNT ... WHERE status = 'x'`.
Evidence:
```python
cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
```
Impact: latency grows linearly with order volume.
Recommendation: one `JOIN itens_pedido + produtos` with an `IN` filter, and `GROUP BY status` in the report (Playbook P7).

### #17 [MEDIUM] Generic error handling that leaks details (AP16)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292; app.py:77-78
Description: 17 copies of `except Exception as e: return jsonify({"erro": str(e)}), 500`, with no logging and with the internal exception text (SQL, `NoneType`...) sent to the client.
Impact: SQLite messages and schema leak out, and errors look different across endpoints.
Recommendation: central `errorhandler` (domain errors → 4xx, unexpected → logged 500 with a generic message) (Playbook P8).

### #18 [MEDIUM] Missing referential integrity (AP19)
File: database.py:36-53; models.py:65-70
Description: `pedidos.usuario_id`, `itens_pedido.pedido_id` and `itens_pedido.produto_id` have no `FOREIGN KEY`. `deletar_produto` does a physical `DELETE` even when the product is referenced in `itens_pedido`. Orders then show `"Desconhecido"` (models.py:196, 228).
Impact: order history loses its product link, and orders can point at users that don't exist.
Recommendation: declare the FKs and enable `PRAGMA foreign_keys=ON`, keeping delete compatible with the current contract (Playbook P11).

### #19 [MEDIUM] Duplicated code (AP14)
File: models.py:12-21, 31-40, 304-313, 79-86, 95-102, 171-201, 203-233; controllers.py:28-46, 72-90
Description: the product dict is built 3 times and the user dict twice. `get_pedidos_usuario` and `get_todos_pedidos` are identical except for the `WHERE`. Required-field and range validation is copied between `criar_produto` and `atualizar_produto`, and has already diverged (#12).
Impact: fixes have to be made in N places (the `senha` leak sits in 2 copies).
Recommendation: `row → dict` serializers per entity and a single validator (Playbook P13).

### #20 [MEDIUM] Inline side effects (AP18)
File: controllers.py:208-210, 247-250
Description: `criar_pedido` "sends" email, SMS and push with `print` in the middle of the handler. `atualizar_status_pedido` notifies on approve/cancel, and the message says "Devolver estoque" but no stock is returned.
Evidence:
```python
print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + ...)
```
Impact: you can't turn notifications off in tests, a real integration failure would take the request down, and cancelling doesn't restore stock.
Recommendation: a `notifications` service called by the controller after commit (Playbook P4).

### #21 [LOW] Magic numbers and strings (AP20)
File: models.py:247-262; controllers.py:47-52, 242, 285-288; app.py:88
Description: discount tiers `10000/5000/1000` and rates `0.1/0.05/0.02`, the status literals `'pendente'/'aprovado'/'cancelado'`, name limits `2/200`, inline lists of categories and statuses, `"1.0.0"`, port `5000`.
Impact: business rules hidden in literals.
Recommendation: named constants in the domain module (Playbook P13).

### #22 [LOW] `print` instead of logging (AP23)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-86
Description: events and errors go to stdout with `print`, including the user's email on login success and failure (179, 182). The boot banner also uses `print("=" * 50)`.
Impact: no levels, no structure, and PII in logs.
Recommendation: `logging` with a module logger (Playbook P14).

### #23 [LOW] Unused imports (AP22)
File: models.py:2; database.py:2
Description: `import sqlite3` in `models.py` and `import os` in `database.py` are never used (confirmed with grep).
Impact: noise and false coupling.
Recommendation: remove them (Playbook P14).

### #24 [LOW] Poor naming (AP21)
File: controllers.py:56, 160; models.py:187, 191, 219, 223
Description: `id` shadows the builtin in handlers and models, and the extra cursors are called `cursor2`/`cursor3`.
Impact: worse readability. Shadowing `id` is error-prone.
Recommendation: `produto_id`, `usuario_id`, plus descriptive names, without changing the API contract (Playbook P14).

### #25 [LOW] Verbose conditionals / meaningless returns (AP24)
File: controllers.py:200; models.py:63, 70, 244-245
Description: `if not itens or len(itens) == 0` is redundant. `atualizar_produto`/`deletar_produto` always `return True`. `if faturamento is None: faturamento = 0` could be `COALESCE`.
Impact: noise, and return values that suggest a check that doesn't exist.
Recommendation: simplify (Playbook P14).

## Deprecated APIs
Nenhuma API deprecated encontrada. Verificado: `Model.query.get`/Query API legacy (no ORM), `engine.execute`, `datetime.utcnow`/`utcfromtimestamp`, `@app.before_first_request`, `flask.json.JSONEncoder`/`app.json_encoder`, `from flask import escape/Markup`, `pkg_resources`, marshmallow `missing=`/`default=`. Flask 3.1 APIs in use (`add_url_rule`, `jsonify`, `request.get_json`) are current.

## Architecture Notes
- Current: pseudo-layers. The layer names exist, but `models.py` is a God File (SQL + rules + serialization), `controllers.py` mixes HTTP with domain rules, `app.py` has routes with raw SQL, and the database is a global singleton.
- Target: `app.py` (thin) → `app/__init__.py:create_app` + `config.py` + `app/database.py` (per-request connection) + `app/models/*` (parameterized SQL, serializers) + `app/controllers/*` (rules, validation) + `app/routes/*` (blueprints) + `app/middlewares/*` (errors, admin auth) + `app/services/notifications.py`.

================================
Total: 25 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

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
```
app.py                          # thin entry point: create_app() + app.run()
.env.example  .gitignore  requirements.txt  README.md
src/
├── app.py                      # create_app(): composition root
├── errors.py                   # AppError, ValidationError, UnauthorizedError, ForbiddenError, NotFoundError
├── config/settings.py
├── database/
│   ├── connection.py           # one connection per request (flask.g), schema with FKs
│   └── seed.py                 # seed with hashed passwords
├── models/
│   ├── produto_model.py  usuario_model.py  pedido_model.py
│   └── admin_model.py    sistema_model.py
├── controllers/
│   ├── produto_controller.py  usuario_controller.py  pedido_controller.py
│   ├── sistema_controller.py  admin_controller.py   validators.py
├── views/
│   ├── produto_routes.py  usuario_routes.py  pedido_routes.py
│   ├── sistema_routes.py  admin_routes.py    response.py
├── services/notification_service.py
└── middlewares/
    ├── error_handler.py
    └── auth.py
```

## Findings Resolved
#1 AP02 — SQL Injection — every query uses `?` placeholders; the search builds fixed clauses plus a parameter list (P2)
#2 AP04 — Dangerous endpoints — `/admin/*` require `X-Admin-Token` and are off by default (`ENABLE_ADMIN_RESET/QUERY`); `/admin/query` accepts a single SELECT under `PRAGMA query_only` (P10)
#3 AP05 — Password in responses — `usuario_to_dict` with public fields only; `senha` never leaves the model (P9)
#4 AP05 — Health exposing secrets — `secret_key`, `db_path` and `debug` removed; DB errors don't leak details (P9)
#5 AP06 — Plain-text passwords — `werkzeug.security` hashes on create, in the seed and on login; legacy plain-text passwords are migrated on the next login (P9)
#6 AP01 — Hardcoded secrets — `Settings` reads from the env; random `SECRET_KEY` if missing; admin password via `SEED_ADMIN_PASSWORD` (random otherwise) (P1)
#7 AP10 — Order without transaction — `with db:` covering order + items + stock; conditional decrement `estoque >= ?` with rollback (P11)
#8 AP03 — God File models.py — split into one model per entity; rules moved to model functions and controllers (P3)
#9 AP03 — Entry point with SQL — `app.py` is 9 lines; routes in blueprints; `create_app()` (P3/P5)
#10 AP11 — No auth — administrative routes protected by token (P10). See the residual risk under Validation.
#11 AP12 — Insecure config — debug off, bind 127.0.0.1, CORS restricted to `CORS_ORIGINS`, port and DB from the env (P1)
#12 AP15 — Missing validation — shared `validar_produto` for create/update, type checks, positive integer `quantidade`/`produto_id`, user must exist, `None` body handled (P13)
#13 AP07 — Fat Controller — views only delegate; controllers orchestrate; discount, total and status rules live in `pedido_model` (P4)
#14 AP09 — Global state — global connection and `check_same_thread=False` removed; one connection per request closed on teardown (P6)
#15 AP08 — Coupling — controllers get `get_db` and the notifier by injection in the composition root; models get `db` in the constructor (P5)
#16 AP13 — N+1 — orders via one `LEFT JOIN`; products via `IN (...)`; report in a single aggregate query (P7)
#17 AP16 — Generic errors — central handler (`AppError` → 4xx with the original format, unexpected → logged generic 500); the 17 `try/except` blocks removed (P8)
#18 AP19 — Referential integrity — FKs declared plus `PRAGMA foreign_keys=ON`; product delete is a soft delete (`ativo=0`), so order history keeps the name (P11)
#19 AP14 — Duplication — single serializers (`produto_to_dict`, `usuario_to_dict`), single validator, one order query with an optional filter (P13)
#20 AP18 — Inline side effects — `NotificationService` injected and called after commit (P4)
#21 AP20 — Magic numbers — `FAIXAS_DESCONTO`, `STATUS_VALIDOS`, `CATEGORIAS_VALIDAS`, `NOME_MIN/MAX` and others as constants (P13)
#22 AP23 — print — `logging` with levels; email no longer written to logs (P14)
#23 AP22 — Unused imports — removed along with the old files; AST check found nothing left (P14)
#24 AP21 — Naming — `produto_id`/`usuario_id` instead of `id`; `cursor2/3` gone (P14)
#25 AP24 — Verbose conditionals — redundant checks and `return True` removed; `COALESCE` in SQL (P14)

## Intentional Contract Changes
- `GET /usuarios` and `GET /usuarios/<id>` no longer return `senha`.
- `GET /health` no longer returns `secret_key`, `db_path` or `debug`. `ambiente` now comes from `APP_ENV`.
- `POST /admin/reset-db` and `POST /admin/query` return **403** without a valid `X-Admin-Token` or with their flag off. `/admin/query` only accepts one SELECT, so writes now get 400.
- `POST /login` with an injection payload now gets **401**; before it was 200, which was the auth bypass.
- `POST /produtos` with an apostrophe in a text field now gets **201**; before it was 500.
- Invalid input that used to give 500 or save bad data now gets 400/404:
  - negative or non-integer `quantidade`;
  - non-numeric `preco`;
  - order for a user that doesn't exist;
  - `PUT /pedidos/<id>/status` on a missing order (404; before it was a silent 200);
  - `PUT /produtos` with an invalid category or name (same rules as create);
  - bad `preco_min/max`;
  - empty body on `/login` and `/status`.
- CORS is restricted to `CORS_ORIGINS`, and the default bind is 127.0.0.1 (`HOST=0.0.0.0` brings back the old behaviour).
- `DELETE /produtos/<id>` is now a soft delete. Responses are identical: after the delete you still get 404 and the product is gone from listings.

## Validation
  ✓ Application boots without errors (`python app.py`, with `PORT=5055` because macOS AirPlay holds port 5000)
  ✓ All endpoints respond correctly (35/40 requests identical to the baseline, covering all 19 routes; the other 5 are exactly the intentional changes above: health, 2× usuarios, apostrophe, SQLi login. The `/relatorios/vendas` values match to the cent.)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (re-scan for AP01/02/04/05/06/09/12/13/23; the hits were reviewed and are false positives)
  ✓ Admin routes: 403 without a token, 403 with a token and the flag off, original behaviour with token plus flag
  ✓ Forced oversell → 400 and full rollback (0 orders, 0 items, stock unchanged)
  ✓ Legacy plain-text password logs in and is rewritten as scrypt
  ✓ Unexpected error → generic JSON 500, stack trace only in the log
  ✓ `compileall` OK; temp DB, temp dir and `__pycache__` removed; port freed
  ⚠ Residual risk (AP11): `PUT/DELETE /produtos`, `PUT /pedidos/<id>/status`, `GET /usuarios` and `GET /relatorios/vendas` are still public. The API has no identity system (`/login` issues no token), and the catalog says not to invent one. Closing this needs a product decision on real authentication.
  ⚠ Business gap carried over from the original: cancelling an order **does not return stock**. The old code only printed "Devolver estoque". I didn't invent the rule; it needs a decision.

## How to run
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python app.py                       # http://127.0.0.1:5000
PORT=5050 .venv/bin/python app.py             # macOS with AirPlay on port 5000
ADMIN_TOKEN=xyz ENABLE_ADMIN_RESET=true ENABLE_ADMIN_QUERY=true .venv/bin/python app.py   # turns on /admin/*
```
================================
````
