# task-manager-api

API de Task Manager em Python/Flask (tarefas, usuários, categorias e relatórios), organizada em MVC.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: ajuste SECRET_KEY, PORT, CORS_ORIGINS...
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (configurável por `HOST`/`PORT`). O `seed.py` popula o banco SQLite (`tasks.db`, configurável por `DATABASE_URL`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

No macOS a porta 5000 costuma estar ocupada pelo AirPlay Receiver: use `PORT=5055 python app.py`.

## Configuração

Todas as variáveis estão documentadas em `.env.example` (lido automaticamente via `python-dotenv`). Em produção, defina sempre `SECRET_KEY`; sem ela, uma chave aleatória é gerada a cada boot e os tokens emitidos deixam de valer no restart. Debug fica desligado por padrão (`FLASK_DEBUG=false`) e o CORS só libera as origens de `CORS_ORIGINS`.

## Autenticação

`POST /login` devolve um `token` assinado (válido por `TOKEN_MAX_AGE_SECONDS`). Envie-o como `Authorization: Bearer <token>` nas operações administrativas:

- `DELETE /users/<id>` e `DELETE /categories/<id>` exigem um usuário `admin`;
- criar usuário com `role` diferente de `user`, ou alterar `role`/`active` em `PUT /users/<id>`, exige um usuário `admin`.

Senhas são gravadas com `werkzeug.security` (scrypt). Hashes MD5 da versão antiga continuam aceitos e são regravados no primeiro login válido.

## Estrutura

```
app.py                  # entry point + create_app() (composition root)
database.py             # instância SQLAlchemy + mixin de persistência
seed.py                 # dados de exemplo
config/
  settings.py           # Settings lidas de variáveis de ambiente
  constants.py          # status, prioridades, roles, limites
models/                 # entidades, consultas e regras de domínio (Task, User, Category)
controllers/            # casos de uso + validação de entrada
routes/                 # blueprints finos (views HTTP)
middlewares/
  error_handler.py      # exceções de domínio + handler central de erros (JSON)
  auth.py               # token Bearer, require_admin
services/
  token_service.py      # tokens assinados (itsdangerous)
  notification_service.py  # e-mail de task atribuída (desligado por padrão)
utils/dates.py          # utcnow() e parse de datas
```
