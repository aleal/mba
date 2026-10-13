# Arquitetura alvo: MVC para APIs backend (Fase 3)

Em uma API, a "View" não é HTML: é a **camada de apresentação HTTP**, ou seja, a definição das rotas e a forma da resposta (JSON). O padrão alvo é:

```
HTTP request
   │
   ▼
Views / Routes      → mapeiam método + path para um controller; serializam a resposta
   │
   ▼
Controllers         → fluxo da aplicação: lêem e validam a entrada, chamam models/services, escolhem status e payload
   │
   ├──► Services    → (opcional) regras que cruzam vários models ou integrações externas (e-mail, pagamento)
   ▼
Models              → dados e regras do domínio: entidades, queries, persistência, invariantes
   │
   ▼
Database / Config   → conexão e parâmetros injetados pelo composition root
```

## Responsabilidades por camada

| Camada | Faz | Não faz |
|---|---|---|
| **Config** | Lê variáveis de ambiente com defaults seguros para desenvolvimento; centraliza porta, URL do banco, flags, segredos, constantes de negócio configuráveis | Não tem lógica; nunca contém segredos reais como default |
| **Models** | Representa entidades; encapsula acesso a dados (queries parametrizadas ou ORM); regras intrínsecas da entidade (ex.: `is_overdue`, cálculo de total do pedido); serialização segura (`to_dict` sem campos sensíveis) | Não conhece HTTP (`request`, `req`, `res`, `jsonify`); não imprime nem envia e-mails |
| **Controllers** | Orquestram um caso de uso: validam a entrada, chamam models/services, mapeiam resultado para status + payload; lançam erros de domínio (`NotFoundError`, `ValidationError`) | Não montam SQL; não contêm regras de cálculo complexas reutilizáveis (elas vão para model/service); não registram rotas |
| **Views / Routes** | Declaram as rotas (blueprints, routers), extraem parâmetros do request e chamam o controller; devolvem a resposta JSON | Sem regra de negócio, sem query, sem `try/except` repetido |
| **Services** (opcional) | Integrações e efeitos colaterais (notificação, pagamento, cache) atrás de uma interface simples; regras que envolvem vários models | Não conhecem HTTP |
| **Middlewares** | Tratamento centralizado de erros; autenticação/autorização; logging de requisições | Não implementam casos de uso |
| **Entry point / composition root** | Cria a aplicação (factory), carrega config, cria a conexão, injeta dependências, registra rotas e middlewares, inicia o servidor | Sem rotas nem regras inline |

## Regras de dependência

1. Dependências apontam para baixo: `routes → controllers → (services) → models → database`. Nunca o contrário.
2. Models e services não importam o framework web.
3. Dependências externas (conexão, config, notificador) são **injetadas**: parâmetro de construtor/função ou extensão do app registrada no composition root. Nada de `global`.
4. Um arquivo por domínio em cada camada (`produto_model`, `produto_controller`, `produto_routes`). Evite um arquivo por camada com todos os domínios.
5. Erros de domínio são exceções tipadas, convertidas em HTTP **apenas** no handler central.
6. Constantes de domínio (status válidos, limites, faixas de desconto) ficam em um único lugar (config ou módulo de constantes do domínio).

## Layout alvo — Python / Flask

```
<projeto>/
├── app.py                      # entry point fino: from src.app import create_app; app = create_app(); app.run(...)
├── requirements.txt
├── .env.example                # variáveis documentadas, sem segredos reais
└── src/
    ├── __init__.py
    ├── app.py                  # create_app(): composition root
    ├── config/
    │   └── settings.py         # class Settings lendo os.environ
    ├── database/
    │   └── connection.py       # conexão por request/app context, schema e seed
    ├── models/
    │   └── <dominio>_model.py
    ├── controllers/
    │   └── <dominio>_controller.py
    ├── views/
    │   └── <dominio>_routes.py # Blueprints
    ├── services/               # opcional
    │   └── notification_service.py
    └── middlewares/
        ├── error_handler.py    # register_error_handlers(app) + exceções de domínio
        └── auth.py             # opcional: proteção de rotas administrativas
```

- Com **Flask-SQLAlchemy**, `database/` contém só a instância `db = SQLAlchemy()`, e os models continuam sendo classes `db.Model`.
- Com **sqlite3 puro**, use uma conexão por requisição (`flask.g` + `app.teardown_appcontext`) em vez de conexão global.
- Se o projeto tem scripts auxiliares (ex.: `seed.py`) que importam `app`, mantenha esse import funcionando (`app.py` continua expondo `app`).

## Layout alvo — Node.js / Express

```
<projeto>/
├── package.json                # "start" continua apontando para o entry point
├── .env.example
└── src/
    ├── app.js                  # entry point: carrega config, cria app (createApp) e chama listen
    ├── server.js / createApp.js# composition root (opcional separar)
    ├── config/
    │   └── index.js            # lê process.env com defaults seguros
    ├── database/
    │   └── connection.js       # abre o banco, schema/seed, helpers com Promise (run/get/all/transaction)
    ├── models/
    │   └── <dominio>Model.js   # classes/funções async que recebem db
    ├── controllers/
    │   └── <dominio>Controller.js
    ├── routes/                 # camada View (express.Router)
    │   └── <dominio>Routes.js
    ├── services/               # opcional (pagamento, notificação, cache)
    └── middlewares/
        ├── errorHandler.js     # (err, req, res, next) + classes de erro + asyncHandler
        └── auth.js             # opcional
```

- Converta callbacks em `async/await` (wrapper com Promise sobre o driver) ao mover o código.
- Use `express.json()` (não `body-parser`).
- Não adicione dependências (ex.: `dotenv`) se `process.env` resolve. Documente as variáveis no `.env.example` e no README.

## Projetos já parcialmente organizados

Quando o projeto já tem pastas como `models/`, `routes/`, `services/`, `utils/`:

1. **Mantenha o que está correto.** Models ORM bem definidos ficam onde estão (corrija só os problemas: serialização de senha, APIs deprecated, regras duplicadas).
2. **`routes/` já é a camada View:** não precisa ser renomeada. Ela deve ficar fina, delegando para controllers novos em `controllers/`.
3. **Crie as camadas que faltam:** `config/`, `controllers/`, `middlewares/error_handler`.
4. **Utilitários não usados:** integre-os (se resolverem duplicação, como uma função de validação já pronta) ou remova-os. Não deixe código morto.
5. **Services existentes não usados:** conecte-os ao fluxo via injeção (com envio desligado por config em desenvolvimento) ou remova-os, justificando.
6. Mudanças estruturais só quando resolverem um finding. Não mova arquivos por estética.

## Checklist da estrutura final

- [ ] Configuração em módulo próprio, sem segredos hardcoded (`.env.example` documenta as variáveis)
- [ ] Models abstraem os dados (nenhum SQL/ORM fora de models/database)
- [ ] Views/Routes separadas e finas
- [ ] Controllers concentram o fluxo de cada caso de uso
- [ ] Tratamento de erros centralizado (handler único, formato de erro consistente)
- [ ] Entry point claro (comando original funciona) e composition root explícito
- [ ] Sem estado global mutável; dependências injetadas
