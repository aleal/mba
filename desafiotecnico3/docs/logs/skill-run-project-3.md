# Execução da skill `/refactor-arch` — task-manager-api

Saída do Claude Code em modo headless (`claude -p "/refactor-arch"`, seguido de `claude -p "y" --resume <sessão>`).

## Fases 1 e 2 (análise e auditoria, pausa para confirmação)

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3 (no version declared; local interpreter is 3.9.6)
Framework:     Flask 3.0.0
Dependencies:  Flask-SQLAlchemy 3.1.1, Flask-CORS 4.0.0, marshmallow 3.20.1 (unused), requests 2.31.0 (unused), python-dotenv 1.0.0 (unused), smtplib (stdlib)
Database:      SQLite (`sqlite:///tasks.db`) via the SQLAlchemy ORM (Flask-SQLAlchemy)
Domain:        Task Manager (tasks, users, categories, productivity reports)
Architecture:  Partial layers — `models/`, `routes/`, `services/`, `utils/` exist, but `routes/*.py` handle validation, business rules, queries and serialization; `services/` and `utils/helpers.py` are never used; config is hardcoded in `app.py`; there is no central error handler
Entry point:   app.py (`python seed.py && python app.py`)
Source files:  15 files analyzed (~1158 lines)
DB tables:     users, tasks, categories
Endpoints:     22 routes
================================

**Endpoint inventory** (⚠ = destructive)

| Method | Path | Handler |
|---|---|---|
| GET | `/health` | app.py:22 |
| GET | `/` | app.py:26 |
| GET | `/tasks` | routes/task_routes.py:11 |
| GET | `/tasks/<id>` | routes/task_routes.py:65 |
| POST | `/tasks` | routes/task_routes.py:85 |
| PUT | `/tasks/<id>` | routes/task_routes.py:156 |
| DELETE ⚠ | `/tasks/<id>` | routes/task_routes.py:225 |
| GET | `/tasks/search` | routes/task_routes.py:240 |
| GET | `/tasks/stats` | routes/task_routes.py:273 |
| GET | `/users` | routes/user_routes.py:10 |
| GET | `/users/<id>` | routes/user_routes.py:27 |
| POST | `/users` | routes/user_routes.py:42 |
| PUT | `/users/<id>` | routes/user_routes.py:92 |
| DELETE ⚠ | `/users/<id>` (also deletes all the user's tasks) | routes/user_routes.py:134 |
| GET | `/users/<id>/tasks` | routes/user_routes.py:153 |
| POST | `/login` | routes/user_routes.py:185 |
| GET | `/reports/summary` | routes/report_routes.py:12 |
| GET | `/reports/user/<id>` | routes/report_routes.py:103 |
| GET | `/categories` | routes/report_routes.py:157 |
| POST | `/categories` | routes/report_routes.py:167 |
| PUT | `/categories/<id>` | routes/report_routes.py:190 |
| DELETE ⚠ | `/categories/<id>` | routes/report_routes.py:211 |

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (SQLite via SQLAlchemy)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-10-13

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 7 | LOW: 5

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP05 | Hash de senha exposto nas respostas | models/user.py:21 |
| 2 | CRITICAL | AP06 | Senhas com MD5 sem salt | models/user.py:29, 32 |
| 3 | CRITICAL | AP01 | `SECRET_KEY` hardcoded | app.py:13 |
| 4 | CRITICAL | AP01 | Credenciais SMTP hardcoded | services/notification_service.py:7-10 |
| 5 | HIGH | AP11 | Token falso, escalada de role e rotas destrutivas sem auth | routes/user_routes.py:52, 71-72, 119-122, 134-151, 210 |
| 6 | HIGH | AP12 | Debug ligado, CORS aberto, config fixa | app.py:11, 15, 34 |
| 7 | HIGH | AP07 | Fat controllers em tasks/users | routes/task_routes.py:85-154, 156-223; routes/user_routes.py:42-90, 92-132 |
| 8 | HIGH | AP07 | Agregações de relatório nas rotas + CRUD de categorias fora do lugar | routes/report_routes.py:12-101, 103-155, 157-223 |
| 9 | HIGH | AP08 | Sem app factory / sem injeção de dependência | app.py:9-31; seed.py:2; services/notification_service.py:5-17 |
| 10 | MEDIUM | AP15 | Validação de entrada ausente/inconsistente | routes/task_routes.py:96, 113, 167, 182, 261, 264; routes/user_routes.py:64, 102-103, 115, 124-125; routes/report_routes.py:180, 196-202 |
| 11 | MEDIUM | AP13 | Queries N+1 | routes/task_routes.py:41-57, 275-279; routes/user_routes.py:22; routes/report_routes.py:15-28, 55-56, 163 |
| 12 | MEDIUM | AP19 | Tasks órfãs ao apagar categoria; cascade manual | routes/report_routes.py:211-223; routes/user_routes.py:140-142 |
| 13 | MEDIUM | AP16 | `except:` genérico e sem handler central | routes/task_routes.py:62, 137, 151, 204, 221, 236; routes/user_routes.py:87, 130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 49, 88 |
| 14 | MEDIUM | AP14 | Regra de "atrasada", serialização e enums duplicados | routes/task_routes.py:17-39, 71-80, 110, 177, 283-287; routes/user_routes.py:61, 106, 162-180; routes/report_routes.py:33-36, 132-135; models/task.py:39, 50-60; utils/helpers.py:57-108 |
| 15 | MEDIUM | AP17 | APIs deprecated (`Query.get`, `datetime.utcnow`) | ver seção Deprecated APIs |
| 16 | MEDIUM | AP18 | Serviço de notificação com SMTP síncrono, não injetado | services/notification_service.py:12-25 |
| 17 | LOW | AP22 | Imports não usados e código morto | app.py:7; routes/*.py; models/task.py:3, 38-60; utils/helpers.py; services/ |
| 18 | LOW | AP23 | `print` no lugar de logging | routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39-41 |
| 19 | LOW | AP20 | Magic numbers e magic strings | routes/task_routes.py:96, 99, 104, 113; routes/user_routes.py:64, 115; routes/report_routes.py:24-28, 45, 129 |
| 20 | LOW | AP24 | Condicionais verbosas e aninhadas | models/task.py:40-60; models/user.py:35-38; routes/task_routes.py:30-39, 141, 210; utils/helpers.py:21-23, 53-55, 103 |
| 21 | LOW | AP21 | Nomenclatura ruim | routes/report_routes.py:24-28; models/category.py:14; utils/helpers.py:57, 83 |

## Findings

### #1 [CRITICAL] Exposição de dados sensíveis — hash de senha nas respostas (AP05)
File: models/user.py:21
Description: `User.to_dict()` inclui `'password': self.password`. Esse dict é devolvido por `GET /users/<id>` (routes/user_routes.py:33), `POST /users` (:85), `PUT /users/<id>` (:129) e `POST /login` (:209). O próprio `/login` devolve o hash para quem se autentica.
Evidence:
```python
'password': self.password,
```
Impact: qualquer cliente lê o hash MD5 de qualquer usuário via `GET /users/<id>`. Somado ao #2, a senha original é recuperada em segundos com rainbow tables.
Recommendation: remover `password` da serialização e manter um `to_dict()` público único (Playbook P9).

### #2 [CRITICAL] Armazenamento inseguro de senhas — MD5 sem salt (AP06)
File: models/user.py:29, 32
Description: `set_password` e `check_password` usam `hashlib.md5(pwd.encode()).hexdigest()`, um hash rápido e sem salt. A severidade base é HIGH; subi para CRITICAL porque está no fluxo de autenticação e, combinado com o #1, o hash fica exposto publicamente.
Evidence:
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
Impact: senhas iguais geram hashes iguais e caem em segundos por lookup (`1234` → `81dc9bdb...`).
Recommendation: `werkzeug.security.generate_password_hash`/`check_password_hash` (já vem com o Flask), com verificação de fallback para os hashes MD5 legados e re-hash no login (Playbook P9).

### #3 [CRITICAL] Segredo hardcoded — SECRET_KEY (AP01)
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` está fixo no código e versionado no repositório.
Evidence:
```python
app.config['SECRET_KEY'] = 'super-secret-key-123'
```
Impact: quem tem acesso ao repo consegue forjar sessões e cookies assinados. Trocar a chave exige deploy.
Recommendation: ler de `SECRET_KEY` via variável de ambiente em um módulo de config, com `.env.example` (Playbook P1).

### #4 [CRITICAL] Credenciais SMTP hardcoded (AP01)
File: services/notification_service.py:7-10
Description: o construtor de `NotificationService` fixa host, porta, usuário `taskmanager@gmail.com` e senha `'senha123'`.
Evidence:
```python
self.email_user = 'taskmanager@gmail.com'
self.email_password = 'senha123'
```
Impact: a conta de e-mail fica comprometida para qualquer pessoa com acesso ao código e pode ser usada para spam ou phishing em nome do produto.
Recommendation: mover para config via env (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`) e injetar no serviço (Playbook P1).

### #5 [HIGH] Autenticação falsa e autorização ausente (AP11)
File: routes/user_routes.py:52, 71-72, 119-122, 134-151, 210
Description: `/login` devolve `'fake-jwt-token-' + str(user.id)`, um token previsível e nunca verificado. `POST /users` aceita `role` livre (`'admin'` incluso), e `PUT /users/<id>` permite trocar o role de qualquer um. Nenhuma rota exige autenticação, nem as destrutivas (`DELETE /users/<id>` apaga o usuário e todas as tasks dele).
Evidence:
```python
'token': 'fake-jwt-token-' + str(user.id)
```
Impact: qualquer cliente anônimo se cadastra como admin, promove contas e apaga usuários e tasks.
Recommendation: token assinado (HMAC com `SECRET_KEY` via `itsdangerous`, que já vem com o Flask) e um decorator `require_auth`/`require_admin` nas rotas destrutivas e de mudança de role (Playbook P10).

### #6 [HIGH] Configuração insegura (AP12)
File: app.py:11, 15, 34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` está fixo; `CORS(app)` libera todas as origens; o URI do banco (`sqlite:///tasks.db`) também está fixo.
Evidence:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```
Impact: o debugger do Werkzeug exposto na rede permite execução remota de código. Com CORS aberto, qualquer site chama a API.
Recommendation: `DEBUG`, `HOST`, `PORT`, `DATABASE_URL` e `CORS_ORIGINS` vindos de env com defaults seguros: debug off, host `127.0.0.1` (Playbook P1).

### #7 [HIGH] Regra de negócio nas rotas de tasks e users (AP07)
File: routes/task_routes.py:85-154, 156-223; routes/user_routes.py:42-90, 92-132
Description: `create_task` (70 linhas) e `update_task` (68 linhas) juntam validação, existência de usuário/categoria, parsing de data, conversão de tags, persistência e log. `create_user`/`update_user` fazem o mesmo com regex de e-mail, unicidade e whitelist de role. Não existe camada de controller/service.
Impact: as regras não podem ser testadas sem HTTP, e criar e atualizar já divergem (o PUT não converte nem trata tipos como o POST).
Recommendation: extrair para controllers (`TaskController`, `UserController`) com validação centralizada e deixar as rotas finas (Playbook P4).

### #8 [HIGH] Agregações de relatório dentro das rotas (AP07)
File: routes/report_routes.py:12-101, 103-155, 157-223
Description: `summary_report` (90 linhas) calcula contagens por status/prioridade, atrasadas, atividade de 7 dias e produtividade por usuário dentro do handler. `user_report` repete a lógica. O CRUD de categorias (domínio diferente) também está neste arquivo de relatórios.
Impact: regras de métricas não são reutilizáveis nem testáveis, e o módulo mistura dois domínios.
Recommendation: `ReportController` com agregação via queries agrupadas; mover categorias para `category_routes`/`CategoryController` (Playbook P4).

### #9 [HIGH] Acoplamento forte sem injeção de dependência (AP08)
File: app.py:9-31; seed.py:2; services/notification_service.py:5-17
Description: o `app` é criado na importação do módulo, sem `create_app()`. `db.create_all()` roda como efeito colateral do import (app.py:30-31), e `seed.py` depende disso via `from app import app`. `NotificationService` instancia `smtplib.SMTP` direto, com config própria.
Impact: impossível criar o app com outra config (testes, banco em memória) ou trocar o transporte de e-mail.
Recommendation: app factory `create_app(config)` como composition root; serviços recebem a config por injeção (Playbook P5).

### #10 [MEDIUM] Validação de entrada ausente ou inconsistente (AP15)
File: routes/task_routes.py:96, 113, 167, 182, 261, 264; routes/user_routes.py:64, 102-103, 115, 124-125; routes/report_routes.py:180, 196-202
Description: `priority < 1` com `"3"` (string) lança `TypeError` e vira 500 (:113, :182). `len(data['title'])` com `null` também quebra (:167). Em `/tasks/search`, `int(priority)`/`int(user_id)` sem tratamento (:261, :264) dão 500 para `?priority=abc`. `PUT /categories` não checa `data is None` (:196). `color` não é validada, apesar de existir `is_valid_color`. `name` e `active` do usuário são aceitos sem tipo.
Evidence:
```python
if priority < 1 or priority > 5:
```
Impact: entrada inválida vira 500 em vez de 400, e dados malformados chegam ao banco.
Recommendation: validadores únicos por entidade, chamados pelos controllers, que respondam 400 de forma consistente (Playbook P13).

### #11 [MEDIUM] Queries N+1 (AP13)
File: routes/task_routes.py:41-57, 275-279; routes/user_routes.py:22; routes/report_routes.py:15-28, 55-56, 163
Description: `GET /tasks` faz `User.query.get` e `Category.query.get` por task (1+2N). `GET /users` faz `len(u.tasks)` lazy por usuário. `summary_report` dispara 12 `COUNT`s separados mais um `Task.query.filter_by(user_id=...)` por usuário. `GET /categories` faz um `count()` por categoria.
Impact: o número de queries cresce linearmente com os dados, e a latência acompanha.
Recommendation: `joinedload`/`selectinload` nos relacionamentos e `GROUP BY` com `func.count` nos agregados (Playbook P7).

### #12 [MEDIUM] Integridade referencial ausente (AP19)
File: routes/report_routes.py:211-223; routes/user_routes.py:140-142
Description: `DELETE /categories/<id>` apaga a categoria e deixa `tasks.category_id` apontando para um id inexistente (o SQLite não aplica FK por padrão). `DELETE /users/<id>` faz o cascade à mão, em loop.
Impact: tasks órfãs com `category_id` inválido distorcem relatórios.
Recommendation: tratar os filhos no controller (desvincular `category_id` das tasks) em uma única transação, e substituir o loop por delete em lote (Playbook P11).

### #13 [MEDIUM] Tratamento de erros genérico (AP16)
File: routes/task_routes.py:62, 137, 151, 204, 221, 236; routes/user_routes.py:87, 130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 49, 88
Description: 15 `except:`/`except Exception` espalhados. `get_tasks` engole qualquer exceção e responde `{'error': 'Erro interno'}` sem log. Não há `errorhandler` central, e cada rota repete `rollback` + `jsonify(...), 500`.
Impact: bugs somem sem rastro, e o formato de erro depende de qual handler respondeu.
Recommendation: exceções de domínio (`NotFound`, `ValidationError`, `Conflict`) mais handler central registrado na factory, com log (Playbook P8).

### #14 [MEDIUM] Código duplicado (AP14)
File: routes/task_routes.py:17-39, 71-80, 110, 177, 283-287; routes/user_routes.py:61, 106, 162-180; routes/report_routes.py:33-36, 132-135; models/task.py:39, 50-60; utils/helpers.py:57-108
Description: a regra "atrasada" aparece em 6 handlers, enquanto `Task.is_overdue()` existe e não é usado. A serialização de task é refeita à mão em `get_tasks` e `get_user_tasks`, apesar de `Task.to_dict()`. A lista de status aparece em 4 lugares. O regex de e-mail se repete, enquanto `validate_email` e `process_task_data` existem e não são usados.
Impact: qualquer mudança de regra precisa ser feita em vários pontos, e as versões já divergem.
Recommendation: uma fonte de verdade para regras (model), enums (constantes) e serialização (Playbook P13).

### #15 [MEDIUM] Uso de APIs deprecated (AP17)
File: routes/task_routes.py, routes/user_routes.py, routes/report_routes.py, models/*.py, utils/helpers.py, services/notification_service.py (linhas na seção abaixo)
Description: 16 chamadas `Model.query.get(id)` (legacy no SQLAlchemy 2.0, gera `LegacyAPIWarning`) e 20+ usos de `datetime.utcnow()` (deprecated no Python 3.12).
Impact: avisos hoje e quebra em upgrades futuros do SQLAlchemy/Python.
Recommendation: `db.session.get(Model, id)` e um helper `utcnow()` baseado em `datetime.now(timezone.utc)`, mantendo datetimes naive para não mudar o formato das respostas (Playbook P12).

### #16 [MEDIUM] Efeito colateral com SMTP síncrono, sem injeção (AP18)
File: services/notification_service.py:12-25
Description: `send_email` abre conexão SMTP síncrona dentro do processo da requisição, e `notifications` é uma lista em memória da instância. O serviço não é injetado nem chamado por nenhuma rota.
Impact: se for ligado como está, uma falha ou lentidão no SMTP trava a requisição, e o histórico se perde a cada restart.
Recommendation: serviço configurado por injeção na factory, com transporte desligável (Playbook P4).

### #17 [LOW] Imports não usados e código morto (AP22)
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:7-8; models/task.py:3, 38-48; models/user.py:34-38; utils/helpers.py:2-7, 9-116; services/notification_service.py
Description: `os, sys, json` (app.py), `json, os, sys, time` (task_routes), `hashlib, json` (user_routes), `json, format_date, calculate_percentage` (report_routes) e `json` (models/task.py) nunca são usados. `Task.validate_status/validate_priority`, `User.is_admin`, praticamente todo `utils/helpers.py` e `NotificationService` não têm nenhuma referência.
Impact: ruído, e falsa impressão de que a validação existe.
Recommendation: remover ou passar a usar de fato (Playbook P14).

### #18 [LOW] `print` no lugar de logging (AP23)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39-41
Description: eventos e erros vão para stdout via `print`, sem nível nem logger.
Impact: impossível filtrar ou desligar, e erros se misturam com eventos de rotina.
Recommendation: `logging.getLogger(__name__)` com níveis (Playbook P14).

### #19 [LOW] Magic numbers e magic strings (AP20)
File: routes/task_routes.py:96, 99, 104, 113; routes/user_routes.py:64, 115; routes/report_routes.py:24-28, 45, 129
Description: `3`/`200` (título), `1`/`5` (prioridade), `4` (senha), `7` (dias), `<= 2` (alta prioridade) e strings de status soltas. As constantes `MIN_TITLE_LENGTH` etc. existem em `utils/helpers.py:110-116`, mas ninguém as usa.
Impact: limites diferentes podem ser aplicados por engano em cada rota.
Recommendation: constantes de domínio em um único módulo (Playbook P13).

### #20 [LOW] Condicionais verbosas e aninhadas (AP24)
File: models/task.py:40-60; models/user.py:35-38; routes/task_routes.py:30-39, 141, 210; utils/helpers.py:21-23, 53-55, 103
Description: `if x: return True else: return False`, `is_overdue` com 4 níveis de `if` e `type(tags) == list` em vez de `isinstance`.
Impact: leitura difícil.
Recommendation: expressões booleanas diretas e `isinstance` (Playbook P14).

### #21 [LOW] Nomenclatura ruim (AP21)
File: routes/report_routes.py:24-28; models/category.py:14; utils/helpers.py:57, 83
Description: `p1..p5` para contagens por prioridade, `d` como dict de retorno e `p` para prioridade. `process_task_data` não processa nada, só valida.
Impact: intenção obscura.
Recommendation: renomear apenas as variáveis internas, sem tocar no contrato (Playbook P14).

## Deprecated APIs
| Location | Deprecated API | Modern replacement |
|---|---|---|
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 | `Model.query.get(id)` (legacy no SQLAlchemy 2.0) | `db.session.get(Model, id)` |
| models/task.py:15, 16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; utils/helpers.py:38; services/notification_service.py:35; seed.py:66-74 | `datetime.utcnow()` (deprecated no Python 3.12) | `datetime.now(timezone.utc)` (helper que devolve naive UTC para preservar o formato) |

Também verificado, sem ocorrências: `before_first_request`, `flask.json.JSONEncoder`, `from flask import escape/Markup`, `engine.execute`, marshmallow `missing=`/`default=`, `pkg_resources`.

## Architecture Notes
- Current: camadas parciais. As pastas existem, mas `routes/*.py` são fat controllers (validação + regras + queries + serialização); `services/` e `utils/` são código morto; config e segredos estão hardcoded e não há app factory.
- Target: `config.py` (env) → `create_app()` em `app/__init__.py` → `routes/` (blueprints finos) → `controllers/` (regras + validação) → `models/` (SQLAlchemy + regras de entidade) + `middlewares/` (erros, auth) + `services/` (notificação injetada); o comando `python app.py` continua funcionando.

================================
Total: 21 findings
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
task-manager-api/
├── app.py                      # entry point + create_app() (composition root)
├── database.py                 # db = SQLAlchemy() + PersistenceMixin (get_by_id/count/save/delete)
├── seed.py
├── requirements.txt
├── .env.example
├── config/
│   ├── settings.py             # Settings lidas do ambiente (python-dotenv)
│   └── constants.py            # status, prioridades, roles, limites
├── models/
│   ├── task.py                 # Task + is_overdue, consultas agregadas, task_statistics
│   ├── user.py                 # User + hash werkzeug, migração MD5, consultas
│   └── category.py
├── controllers/
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   ├── report_controller.py
│   ├── validators.py
│   └── common.py
├── routes/                     # views: blueprints finos
│   ├── __init__.py (respond)
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── category_routes.py      # saiu de report_routes.py
│   ├── report_routes.py
│   └── system_routes.py        # / e /health (saíram de app.py)
├── middlewares/
│   ├── error_handler.py
│   └── auth.py
├── services/
│   ├── token_service.py
│   └── notification_service.py
└── utils/dates.py              # substitui utils/helpers.py (removido)
```

## Findings Resolved
#1 AP05 — Hash de senha nas respostas — `User.to_dict()` não inclui mais `password` (P9)
#2 AP06 — MD5 sem salt — `generate_password_hash`/`check_password_hash` do werkzeug (scrypt). Hashes MD5 legados ainda são aceitos e regravados no primeiro login (P9)
#3 AP01 — SECRET_KEY hardcoded — lida de `SECRET_KEY` no ambiente; se ausente, é gerada aleatoriamente (P1)
#4 AP01 — Credenciais SMTP hardcoded — `SMTP_*` vindos do ambiente e injetados via `NotificationService.from_config` (P1)
#5 AP11 — Token falso / escalada de role — token assinado com `itsdangerous` e expiração; `require_admin` em `DELETE /users` e `DELETE /categories`; definir role e alterar role/active exige admin (P10)
#6 AP12 — Config insegura — debug desligado e host `127.0.0.1` por padrão; CORS restrito a `CORS_ORIGINS`; `DATABASE_URL`/`PORT` vindos do ambiente (P1)
#7 AP07 — Fat controllers de tasks/users — `TaskController`/`UserController` + `validators.py`; rotas com 1 linha (P4)
#8 AP07 — Relatórios nas rotas — `ReportController` + agregações no model; categorias com rotas e controller próprios (P4)
#9 AP08 — Sem DI/factory — `create_app()` injeta notifier, token service e controllers nos builders de blueprint; `seed.py` continua com `from app import app, db` (P5)
#10 AP15 — Validação inconsistente — validador único para criar e atualizar, com as mesmas mensagens; prioridade/ids/filtros/tags/cor/active com tipo checado: entradas que davam 500 agora dão 400 (P13)
#11 AP13 — N+1 — `joinedload` e `GROUP BY`; consultas constantes, sem crescer com os dados: `/tasks`, `/users` e `/categories` = 1 query cada; `/reports/summary` = 9; `/tasks/stats` = 3 (P7)
#12 AP19 — Órfãos — deletar categoria desvincula `category_id` das tasks; deletar usuário apaga as tasks em lote; ambos na mesma transação (P11)
#13 AP16 — Erros genéricos — exceções de domínio + `register_error_handlers` (JSON `{'error': ...}`, log com stack, 500 sem detalhes para o cliente); nenhum `except:` restante (P8)
#14 AP14 — Duplicação — `Task.is_overdue`, `to_dict`/`to_summary_dict`, `completion_rate` e constantes têm agora uma fonte única (P13)
#15 AP17 — Deprecated — `db.session.get` / `db.select` no lugar de `Model.query.*`; helper `utcnow()` no lugar de `datetime.utcnow()` (P12)
#16 AP18 — SMTP inline — `NotificationService` injetado e ligado à atribuição de task; desligado por padrão (só loga); falha no envio não derruba a requisição (P4)
#17 AP22 — Código morto — removidos imports sem uso, `utils/helpers.py`, `validate_status`/`validate_priority`, a lista em memória do notifier e as dependências `marshmallow`/`requests`, que não eram usadas (P14)
#18 AP23 — print — `logging` configurado na factory; `print` só sobrou na saída CLI do `seed.py` (P14)
#19 AP20 — Magic numbers — `config/constants.py` (P13)
#20 AP24 — Condicionais verbosas — expressões booleanas diretas e `isinstance` (P14)
#21 AP21 — Nomenclatura — `p1..p5`, `d`, `p` e `process_task_data` eliminados (P14)

## Intentional Contract Changes
- `password` saiu das respostas de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`.
- `token` do `/login` agora é um token assinado (o campo continua existindo) e deve ser enviado como `Authorization: Bearer <token>`.
- `DELETE /users/<id>` e `DELETE /categories/<id>`: 401 sem token válido e 403 se o usuário não for admin.
- `POST /users` com `role` ≠ `user` e `PUT /users/<id>` alterando `role`/`active`: 403 se quem chama não for admin.
- Entradas inválidas que antes estouravam 500 agora retornam 400. Exemplos: `priority: "abc"`, `?priority=abc`, `PUT /categories` com corpo `null`, `color` inválida.
- Erros do framework (404 de rota, 405, 415) agora respondem em JSON `{'error': ...}` em vez de HTML.

## Validation
  ✓ Application boots without errors (`PORT=5055 DATABASE_URL=sqlite:///<tmp>/after.db python seed.py && python app.py`, sem stack trace no log)
  ✓ All endpoints respond correctly (47/47 requisições batem com o baseline em status, formato e mensagem de erro, cobrindo as 22 rotas; a única diferença é a remoção intencional de `password` em 6 respostas)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (re-varredura sem segredos literais, `debug=True`, CORS aberto, `Model.query`, `except:` ou token falso. O único `hashlib.md5` restante verifica hashes legados; pyflakes sem nenhum aviso real)
  ✓ Cenário de segurança: sem token → 401; token forjado `fake-jwt-token-1` → 401; não-admin → 403; anônimo criando ou promovendo admin → 403; admin → 201/200
  ✓ Migração transparente: usuário com hash MD5 loga (200) e passa a ter hash `scrypt:` no banco
  ✓ Deletar categoria deixa 0 tasks com `category_id` órfão
  ✓ Erro forçado → `500 {'error': 'Erro interno'}` para o cliente, traceback só no log
  ✓ `compileall` sem erros; servidor parado; temporários, bancos e `__pycache__` removidos; `.venv/` está no `.gitignore`

## How to run
```bash
pip install -r requirements.txt
cp .env.example .env        # defina SECRET_KEY em produção
python seed.py
python app.py               # macOS: PORT=5055 python app.py (AirPlay ocupa a 5000)
```
================================
````
