# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, refatorada para MVC.

## Como rodar

```bash
npm install
ADMIN_TOKEN=um-token-secreto npm start
```

A aplicação sobe em `http://localhost:3000`. Por padrão o banco SQLite é em memória e carrega seeds automaticamente no boot.

Variáveis de ambiente (veja `.env.example`):

| Variável | Default | Uso |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `DB_PATH` | `:memory:` | Arquivo SQLite (seeds só rodam em banco vazio) |
| `ADMIN_TOKEN` | vazio | Token do header `X-Admin-Token` nas rotas administrativas; vazio = sempre 403 |
| `PAYMENT_GATEWAY_KEY` | vazio | Chave do gateway de pagamento |
| `LOG_LEVEL` | `info` | `debug`, `info`, `warn`, `error` |

## Endpoints

| Método | Path | Auth |
|---|---|---|
| POST | `/api/checkout` | — |
| GET | `/api/admin/financial-report` | `X-Admin-Token` |
| DELETE | `/api/users/:id` | `X-Admin-Token` |

Exemplos de requisições estão em `api.http`.

## Estrutura

```
src/
├── app.js              # entry point: config, banco, createApp, listen
├── server.js           # composition root (injeção de dependências)
├── config/             # variáveis de ambiente
├── database/           # conexão com Promises/transação, schema e seed
├── models/             # acesso a dados por entidade
├── services/           # checkout, pagamento, relatório, hash de senha
├── controllers/        # validação de entrada e fluxo de cada caso de uso
├── routes/             # rotas Express (finas)
├── middlewares/        # autenticação admin e tratamento central de erros
└── utils/              # logger, erros e validadores
```
