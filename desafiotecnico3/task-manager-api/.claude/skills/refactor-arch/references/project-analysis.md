# Análise de projeto — heurísticas (Fase 1)

Objetivo: descobrir a stack, o domínio e a arquitetura atual **apenas lendo arquivos**. Sempre confirme uma hipótese com pelo menos um sinal no código (import, chamada, configuração), não só pelo nome do arquivo.

## 1. Inventário de arquivos

1. Liste os arquivos do projeto ignorando: `.git/`, `.claude/`, `node_modules/`, `venv/`, `.venv/`, `__pycache__/`, `dist/`, `build/`, `*.db`, `*.sqlite`, lockfiles e binários.
2. Arquivos-fonte = extensões de código (`.py`, `.js`, `.mjs`, `.cjs`, `.ts`, `.go`, `.rb`, `.java`, `.php`, `.cs`...). Conte também scripts auxiliares (ex.: `seed.py`), mas não testes de terceiros nem configs.
3. Conte linhas por arquivo (ex.: `wc -l`). Arquivos com mais de ~250 linhas ou com muitas responsabilidades são candidatos a God Class.

## 2. Linguagem, framework e dependências

| Sinal (manifesto) | Linguagem | Onde ver o framework e a versão |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | linha `flask==x.y.z`, `django`, `fastapi` |
| `package.json` | JavaScript/Node.js (TypeScript se houver `typescript`/`tsconfig.json`) | `dependencies`: `express`, `fastify`, `@nestjs/core`, `koa` |
| `go.mod` | Go | `require github.com/gin-gonic/gin`, `labstack/echo`, `net/http` |
| `pom.xml`, `build.gradle` | Java/Kotlin | `spring-boot-starter-web` |
| `Gemfile` | Ruby | `rails`, `sinatra` |
| `composer.json` | PHP | `laravel/framework`, `slim/slim` |

Confirmação no código:

| Framework | Sinais no código |
|---|---|
| Flask | `from flask import Flask`, `Flask(__name__)`, `@app.route`, `Blueprint(`, `app.add_url_rule(` |
| FastAPI | `FastAPI()`, `@app.get`, `APIRouter` |
| Django | `urls.py` com `path(`, `views.py`, `settings.py` |
| Express | `require('express')` / `import express`, `express()`, `app.get(`, `express.Router()` |
| Fastify / Koa / Nest | `fastify(`, `new Koa()`, `@Controller(` |

Dependências relevantes: liste as que afetam arquitetura e segurança (ORM, driver de banco, CORS, auth, validação, HTTP client, e-mail). Ignore utilitários de desenvolvimento.

A versão do framework vem do manifesto. Se estiver como range (`^4.18.2`), informe como declarado.

## 3. Banco de dados e acesso a dados

| Sinal | Banco / acesso |
|---|---|
| `import sqlite3`, `sqlite3.connect(` | SQLite, driver puro (SQL manual) |
| `require('sqlite3')`, `new sqlite3.Database(` | SQLite, driver puro (callbacks) |
| `':memory:'` | banco em memória (dados somem a cada boot) |
| `flask_sqlalchemy`, `db.Model`, `db.Column` | SQLAlchemy ORM via Flask-SQLAlchemy |
| `SQLALCHEMY_DATABASE_URI` | URL de conexão: `sqlite:///`, `postgresql://`, `mysql://` |
| `psycopg2`, `pg`, `mysql2`, `pymongo`, `mongoose`, `prisma`, `sequelize`, `typeorm` | Postgres / MySQL / Mongo / ORMs |

Tabelas: procure `CREATE TABLE <nome>` (SQL manual) ou `__tablename__ = '<nome>'` / nome da classe do model (ORM) ou `mongoose.model('<Nome>'`.

## 4. Entry point e comando de execução

- Python: arquivo com `if __name__ == "__main__":` + `app.run(...)`, ou `create_app()`; comando no README (`python app.py`, `flask run`).
- Node: campo `main` e `scripts.start` do `package.json`; arquivo com `app.listen(`.
- Anote host e porta (`app.run(port=...)`, `app.listen(port)`, `config.port`) e se o debug está ligado.

## 5. Inventário de endpoints

Busque todas as formas de registrar rotas e anote `MÉTODO path → handler (arquivo:linha)`:

- Flask: `@app.route('/x', methods=[...])`, `@bp.route(...)`, `app.add_url_rule('/x', 'nome', handler, methods=[...])`. Sem `methods` = `GET`. Para blueprints, some o `url_prefix` de `Blueprint(...)`/`register_blueprint(...)`.
- Express: `app.get|post|put|patch|delete('/x', ...)`, `router.<método>(...)`, prefixo de `app.use('/prefixo', router)`.
- Outros: decorators (`@Get`), arquivos de rotas (`urls.py`, `routes.rb`).

Marque endpoints **destrutivos ou perigosos** (resetam/apagam dados, executam SQL ou comandos arbitrários). Eles exigem cuidado especial na validação da Fase 3.

Procure também arquivos de exemplo de requisição (`*.http`, `*.rest`, coleções Postman, README). Eles mostram payloads válidos para a validação.

## 6. Domínio de negócio

Deduza o domínio a partir de: nomes de tabelas e models, rotas, seeds e README. Descreva em uma frase com as entidades principais. Exemplos:
- tabelas `produtos`, `pedidos`, `itens_pedido` → "E-commerce API (produtos, pedidos, usuários)";
- `courses`, `enrollments`, `payments` + rota `/checkout` → "LMS com checkout (cursos, matrículas, pagamentos)";
- `tasks`, `categories`, `users` + `/reports` → "Task Manager (tarefas, categorias, usuários, relatórios)".

## 7. Classificação da arquitetura atual

Mapeie onde cada responsabilidade vive: **roteamento**, **regras de negócio**, **acesso a dados**, **validação**, **configuração**, **tratamento de erros**, **efeitos colaterais** (e-mail, notificação).

| Classificação | Sinais |
|---|---|
| **Monolítica / God Class** | Uma classe ou arquivo concentra rotas + SQL + regras (ex.: `class AppManager` com `initDb()` e `setupRoutes()`); poucos arquivos grandes |
| **Pseudo-camadas** | Arquivos com nomes de camada (`models.py`, `controllers.py`), mas as responsabilidades vazam: SQL concatenado nos "models", validação e regras nos "controllers", rotas e SQL no entry point |
| **Camadas parciais** | Pastas `models/`, `routes/`, `services/`, `utils/` existem, mas as rotas fazem tudo (validação, regras, queries, serialização), services não são usados, falta config e handler de erros centralizados |
| **MVC adequado** | Rotas finas → controllers → models; config isolada; erros centralizados; dependências injetadas |

Escreva a classificação com uma justificativa de uma linha que cite arquivos concretos, por exemplo: `Monolítica — AppManager.js concentra schema, seeds, rotas e regras de checkout`.

## 8. Checklist de saída da Fase 1

- [ ] Linguagem e framework confirmados por manifesto **e** por código
- [ ] Banco e tabelas identificados
- [ ] Entry point e comando de execução
- [ ] Todos os endpoints inventariados com `arquivo:linha` e os perigosos marcados
- [ ] Domínio descrito com entidades
- [ ] Arquitetura classificada com justificativa
- [ ] Contagem de arquivos e linhas condizente com o inventário
