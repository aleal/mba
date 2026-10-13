# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, agora organizada em MVC.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (`joao@email.com` / `123456`, `maria@email.com` / `senha123`; desligue com `SEED_DEMO_DATA=false`). As senhas são gravadas com hash.

A configuração vem de variáveis de ambiente, documentadas em `.env.example`. Exemplos:

```bash
PORT=8080 HOST=0.0.0.0 python app.py                       # outra porta / expor na rede
SECRET_KEY=... SEED_ADMIN_PASSWORD=... python app.py        # segredos fora do código
```

> No macOS a porta 5000 costuma estar ocupada pelo AirPlay Receiver; use `PORT=5050`.

### Rotas administrativas

`POST /admin/reset-db` e `POST /admin/query` exigem o header `X-Admin-Token` igual a `ADMIN_TOKEN` e ficam desligadas por padrão:

```bash
ADMIN_TOKEN=um-token-forte ENABLE_ADMIN_RESET=true ENABLE_ADMIN_QUERY=true python app.py
curl -X POST -H 'X-Admin-Token: um-token-forte' -H 'Content-Type: application/json' \
     -d '{"sql": "SELECT COUNT(*) AS n FROM pedidos"}' http://127.0.0.1:5000/admin/query
```

`/admin/query` aceita apenas uma instrução `SELECT`, executada com o SQLite em modo somente leitura.

## Estrutura

```
app.py                      # entry point: create_app() + app.run()
src/
├── app.py                  # composition root (config, banco, controllers, blueprints, erros)
├── errors.py               # exceções de domínio (AppError, ValidationError, NotFoundError...)
├── config/settings.py      # variáveis de ambiente
├── database/
│   ├── connection.py       # conexão por requisição (flask.g) e schema
│   └── seed.py             # dados iniciais
├── models/                 # SQL parametrizado, serialização e regras de domínio
├── controllers/            # casos de uso e validação de entrada
├── views/                  # blueprints (rotas finas)
├── services/               # notificações
└── middlewares/            # handler de erros e autenticação admin
```
