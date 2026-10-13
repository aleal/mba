# Playbook de refatoração (Fase 3)

Padrões concretos de transformação, um por grupo de anti-patterns. Cada padrão traz **quando usar**, **passos** e exemplos **antes/depois** em Python e JavaScript. Os exemplos mostram a forma da transformação; adapte nomes, campos e mensagens ao projeto e **preserve o contrato da API** (paths, campos, status codes).

| Padrão | Resolve | Título |
|---|---|---|
| P1 | AP01, AP12 | Extrair configuração para módulo de config + variáveis de ambiente |
| P2 | AP02 | Parametrizar queries SQL |
| P3 | AP03 | Quebrar God Class/God File em Model + Controller + Routes |
| P4 | AP07, AP18 | Controller fino: regras no model/service, efeitos colaterais em service |
| P5 | AP08 | Injeção de dependência via app factory / composition root |
| P6 | AP09 | Eliminar estado global mutável |
| P7 | AP13 | Eliminar N+1 com JOIN, agregação ou eager loading |
| P8 | AP16 | Tratamento de erros centralizado |
| P9 | AP05, AP06 | Hash seguro de senha e serialização sem dados sensíveis |
| P10 | AP04, AP11 | Proteger rotas administrativas e perigosas |
| P11 | AP10, AP19 | Callbacks → async/await com transação e integridade referencial |
| P12 | AP17 | Substituir APIs deprecated |
| P13 | AP14, AP15, AP20 | Centralizar validação, constantes e serialização |
| P14 | AP21–AP24 | Higiene: nomes, logging, imports, condicionais |

---

## P1 — Extrair configuração para módulo de config

**Quando:** segredos, porta, URL do banco, debug ou CORS fixos no código.

**Passos:** criar o módulo de config que lê variáveis de ambiente → defaults seguros para desenvolvimento (debug desligado, segredo gerado ou exigido) → substituir todos os literais por leitura da config → criar `.env.example` documentando cada variável (sem valores reais) → nunca devolver config em respostas.

**Python — antes**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
CORS(app)
app.run(host="0.0.0.0", port=5000, debug=True)
```
**Python — depois**
```python
# src/config/settings.py
import os, secrets

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")

# src/app.py
app.config.from_object(Settings)
CORS(app, origins=Settings.CORS_ORIGINS)
```

**JavaScript — antes**
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234567890abcdef", port: 3000 };
```
**JavaScript — depois**
```js
// src/config/index.js
module.exports = Object.freeze({
  port: Number(process.env.PORT) || 3000,
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',   // obrigatório em produção
  smtpUser: process.env.SMTP_USER || '',
});
```

---

## P2 — Parametrizar queries SQL

**Quando:** qualquer SQL montado com `+`, f-string, `%` ou template string.

**Passos:** trocar valores por placeholders do driver (`?` no sqlite3, `%s` no psycopg2, `$1` no pg) → passar valores como tupla/array → para `LIKE`, montar o padrão no valor (`f"%{termo}%"`), não no SQL → para filtros opcionais, montar a lista de cláusulas fixas e a lista de parâmetros em paralelo → nomes de coluna/ordenação dinâmicos só via whitelist.

**Python — antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query = "SELECT * FROM produtos WHERE 1=1"
if termo:
    query += " AND (nome LIKE '%" + termo + "%')"
```
**Python — depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))

clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
if categoria:
    clauses.append("categoria = ?")
    params.append(categoria)
cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}", params)  # só cláusulas fixas no SQL
```

**JavaScript — antes**
```js
db.all(`SELECT * FROM users WHERE email = '${email}'`, cb);
```
**JavaScript — depois**
```js
const user = await db.get('SELECT * FROM users WHERE email = ?', [email]);
```

---

## P3 — Quebrar God Class / God File

**Quando:** um arquivo/classe tem schema + seed + queries + regras + rotas.

**Passos:** inventariar as responsabilidades do arquivo → mover DDL/seed/conexão para `database/` → um model por entidade com as queries → um controller por domínio com o fluxo de cada rota → um arquivo de rotas por domínio só com o mapeamento → composition root que conecta tudo → apagar o arquivo antigo quando vazio.

**JavaScript — antes**
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { this.db.run("CREATE TABLE users ..."); }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { this.db.get("SELECT * FROM courses ...", ...); });
    app.get('/api/admin/financial-report', (req, res) => { ... });
  }
}
```
**JavaScript — depois**
```js
// src/models/courseModel.js
class CourseModel {
  constructor(db) { this.db = db; }
  findActiveById(id) { return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]); }
}
// src/controllers/checkoutController.js
class CheckoutController {
  constructor({ checkoutService }) { this.checkoutService = checkoutService; }
  checkout = async (req, res) => {
    const result = await this.checkoutService.checkout(req.body);
    res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
  };
}
// src/routes/checkoutRoutes.js
module.exports = (controller) => express.Router().post('/api/checkout', asyncHandler(controller.checkout));
```

**Python — antes** (`models.py` com 4 domínios e `app.py` com rotas + SQL)
```python
# app.py
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    db = get_db(); db.cursor().execute("DELETE FROM pedidos"); ...
```
**Python — depois**
```python
# src/models/pedido_model.py   -> queries de pedidos
# src/controllers/admin_controller.py -> fluxo do reset
# src/views/admin_routes.py
admin_bp = Blueprint("admin", __name__)
admin_bp.add_url_rule("/admin/reset-db", view_func=admin_controller.reset_database, methods=["POST"])
```

---

## P4 — Controller fino e efeitos colaterais em service

**Quando:** cálculos de domínio, agregações ou notificações dentro do handler.

**Passos:** identificar a regra (ex.: faixas de desconto, "está atrasado?", total do pedido) → mover para método do model (regra da entidade) ou service (regra entre entidades) → controller só chama e escolhe a resposta → notificações viram chamadas a um `NotificationService` injetado (implementação que só faz log em desenvolvimento).

**Python — antes**
```python
def criar_pedido():
    ...
    resultado = models.criar_pedido(usuario_id, itens)
    print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + " criado")
    print("ENVIANDO SMS: Seu pedido foi recebido!")
```
**Python — depois**
```python
# controllers/pedido_controller.py
def criar_pedido(payload, pedido_model, notifier):
    dados = validar_pedido(payload)                       # ValidationError -> 400 no handler central
    pedido = pedido_model.criar(dados["usuario_id"], dados["itens"])
    notifier.pedido_criado(pedido["pedido_id"], dados["usuario_id"])
    return pedido

# services/notification_service.py
class NotificationService:
    def __init__(self, logger): self.logger = logger
    def pedido_criado(self, pedido_id, usuario_id):
        self.logger.info("notificacao pedido_criado pedido=%s usuario=%s", pedido_id, usuario_id)
```

**Python — antes** (mesma regra copiada em vários handlers)
```python
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
```
**Python — depois**
```python
# models/task.py
def is_overdue(self) -> bool:
    return bool(self.due_date) and self.due_date < utcnow() and self.status not in CLOSED_STATUSES

# controller
data["overdue"] = task.is_overdue()
```

---

## P5 — Injeção de dependência via composition root

**Quando:** funções chamam `get_db()` global, classes instanciam o próprio banco, objetos se registram sozinhos no app.

**Passos:** criar `create_app(settings)` / `createApp(config)` → criar a conexão e os serviços ali → passar as dependências para models/controllers (construtor ou closure) → as rotas recebem o controller pronto → o entry point só chama a factory.

**Python — depois**
```python
# src/app.py
def create_app(settings=Settings):
    app = Flask(__name__)
    app.config.from_object(settings)
    init_db(app)                                   # registra teardown e cria schema
    notifier = NotificationService(app.logger)
    app.register_blueprint(build_pedido_routes(PedidoController(notifier)))
    register_error_handlers(app)
    return app

# app.py (entry point, comando original preservado)
from src.app import create_app
app = create_app()
if __name__ == "__main__":
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
```

**JavaScript — depois**
```js
// src/app.js
const config = require('./config');
const { openDatabase } = require('./database/connection');
const { createApp } = require('./server');

(async () => {
  const db = await openDatabase(config.dbPath);
  const app = createApp({ db, config });
  app.listen(config.port, () => logger.info(`API rodando na porta ${config.port}`));
})();
```

---

## P6 — Eliminar estado global mutável

**Quando:** `global db_connection`, `let globalCache = {}`, contadores de módulo.

**Python — antes**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```
**Python — depois**
```python
from flask import current_app, g

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db(app):
    app.teardown_appcontext(close_db)
```

**JavaScript — antes**
```js
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }
module.exports = { globalCache };
```
**JavaScript — depois**
```js
class CacheService {
  #store = new Map();
  set(key, value) { this.#store.set(key, value); }
  get(key) { return this.#store.get(key); }
}
// uma instância criada no composition root e injetada onde for usada
```

---

## P7 — Eliminar N+1

**Quando:** query dentro de loop de outra query; relacionamento ORM acessado item a item; um `COUNT` por valor.

**SQL — antes**
```python
for row in pedidos:
    cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor.fetchall():
        cursor.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**SQL — depois** (1 query + agrupamento em memória)
```python
rows = db.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    ORDER BY p.id
""").fetchall()
pedidos = {}
for r in rows:
    pedido = pedidos.setdefault(r["id"], {...campos do pedido..., "itens": []})
    if r["produto_id"] is not None:
        pedido["itens"].append({...})
```

**SQLAlchemy — antes / depois**
```python
# antes: 1 + 2N queries
for t in Task.query.all():
    user = User.query.get(t.user_id)
    cat = Category.query.get(t.category_id)

# depois: 1 query com eager loading
from sqlalchemy.orm import joinedload
tasks = db.session.execute(
    db.select(Task).options(joinedload(Task.user), joinedload(Task.category))
).scalars().all()

# contagens: GROUP BY em vez de um COUNT por status
rows = db.session.execute(db.select(Task.status, db.func.count()).group_by(Task.status)).all()
by_status = {status: n for status, n in rows}
```

**JavaScript — antes / depois**
```js
// antes: forEach com db.get para usuário e pagamento de cada matrícula
// depois:
const rows = await db.all(`
  SELECT c.id AS course_id, c.title, u.name AS student, p.amount, p.status
  FROM courses c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u ON u.id = e.user_id
  LEFT JOIN payments p ON p.enrollment_id = e.id
  ORDER BY c.id`);
```

---

## P8 — Tratamento de erros centralizado

**Quando:** `try/except` copiado em todos os handlers, `except:` puro, `str(e)` enviado ao cliente, callbacks com `err` ignorado.

**Python — antes**
```python
def buscar_produto(id):
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```
**Python — depois**
```python
# src/middlewares/error_handler.py
class AppError(Exception):
    status_code = 400
    def __init__(self, message, status_code=None):
        super().__init__(message)
        if status_code: self.status_code = status_code

class NotFoundError(AppError): status_code = 404
class ValidationError(AppError): status_code = 400

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": str(err), "sucesso": False}), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("erro inesperado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500

# controller: sem try/except
def buscar_produto(id):
    produto = produto_model.buscar_por_id(id)
    if produto is None:
        raise NotFoundError("Produto não encontrado")
    return jsonify({"dados": produto, "sucesso": True}), 200
```
Preserve a **chave de erro original** do projeto (`erro`, `error`...) para não quebrar clientes. Para erros HTTP do próprio framework (404 de rota, 405), registre handlers para `HTTPException` que mantenham o status original.

**JavaScript — depois**
```js
// src/middlewares/errorHandler.js
class AppError extends Error { constructor(message, status = 400) { super(message); this.status = status; } }
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
function errorHandler(err, req, res, next) {
  if (err instanceof AppError) return res.status(err.status).send(err.message);   // mesmo formato da API original
  logger.error(err);
  res.status(500).send('Erro interno');
}
module.exports = { AppError, asyncHandler, errorHandler };
// registrado por último: app.use(errorHandler)
```

---

## P9 — Hash seguro de senha e serialização sem dados sensíveis

**Quando:** senha em texto puro, MD5/SHA1, "cripto" caseira; `to_dict` ou `SELECT *` devolvendo senha; segredo em resposta ou log.

**Python — antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}
```
**Python — depois**
```python
from werkzeug.security import generate_password_hash, check_password_hash   # já vem com Flask

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)

def to_dict(self):
    return {"id": self.id, "email": self.email}    # senha nunca sai do model
```
Para bases com senhas legadas (texto puro/MD5): no login, se o hash armazenado não tiver o formato novo, compare pelo método antigo e, se bater, **regrave com o hash novo** (migração transparente). Os seeds devem gravar senhas já com hash.

**JavaScript — antes**
```js
function badCrypto(pwd) { let h = ""; for (let i = 0; i < 10000; i++) h += Buffer.from(pwd).toString('base64').substring(0, 2); return h.substring(0, 10); }
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
**JavaScript — depois**
```js
const crypto = require('node:crypto');
function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `scrypt$${salt}$${hash}`;
}
logger.info(`Processando pagamento do cartão final ${card.slice(-4)}`);   // nunca o número completo nem a chave
```

---

## P10 — Proteger rotas administrativas e perigosas

**Quando:** `/admin/*` sem autenticação, execução de SQL/comandos vindos do request, reset de banco aberto, token falso.

**Regra:** **não remova a rota** (o contrato continua existindo). Proteja-a com um token administrativo lido da config e, para operações intrinsecamente perigosas, **desligue por padrão** com uma flag de ambiente. Execução de SQL arbitrário deve, no mínimo, aceitar só leitura (`SELECT`) e ficar desligada por padrão.

**Python — depois**
```python
# src/middlewares/auth.py
from functools import wraps
import hmac

def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        provided = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(provided, expected):
            raise ForbiddenError("Acesso administrativo negado")
        return view(*args, **kwargs)
    return wrapper

# rota
admin_bp.add_url_rule("/admin/query", view_func=require_admin_token(admin_controller.executar_query), methods=["POST"])

# controller: só SELECT, e só se ENABLE_ADMIN_QUERY=true
if not current_app.config["ENABLE_ADMIN_QUERY"]:
    raise ForbiddenError("Endpoint desabilitado")
if not sql.lstrip().upper().startswith("SELECT") or ";" in sql.rstrip().rstrip(";"):
    raise ValidationError("Apenas consultas SELECT simples são permitidas")
```

**JavaScript — depois**
```js
function requireAdmin(config) {
  return (req, res, next) => {
    const token = req.get('X-Admin-Token') || '';
    if (!config.adminToken || token !== config.adminToken) return next(new AppError('Acesso negado', 403));
    next();
  };
}
router.get('/api/admin/financial-report', requireAdmin(config), asyncHandler(controller.financialReport));
```
Tokens falsos (`'fake-jwt-token-' + id`) devem virar um token assinado/aleatório (ex.: `itsdangerous`/`secrets.token_urlsafe` guardado, ou HMAC com `SECRET_KEY`), mantendo o campo `token` na resposta.

---

## P11 — Callbacks → async/await com transação

**Quando:** callbacks aninhados, escrita em vários passos sem transação, deletes que deixam órfãos.

**JavaScript — antes**
```js
db.run("INSERT INTO enrollments ...", [userId, cid], function (err) {
  self.db.run("INSERT INTO payments ...", [this.lastID, price, status], function (err) {
    self.db.run("INSERT INTO audit_logs ...", [...], () => res.json({...}));
  });
});
```
**JavaScript — depois**
```js
// database/connection.js: wrapper com Promise
const run = (sql, params = []) => new Promise((resolve, reject) =>
  db.run(sql, params, function (err) { err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes }); }));

async function transaction(work) {
  await run('BEGIN');
  try { const r = await work(); await run('COMMIT'); return r; }
  catch (e) { await run('ROLLBACK'); throw e; }
}

// services/checkoutService.js
const enrollmentId = await transaction(async () => {
  const { lastID } = await enrollments.create(userId, courseId);
  await payments.create(lastID, course.price, 'PAID');
  await audit.log(`Checkout curso ${courseId} por ${userId}`);
  return lastID;
});
```
Com sqlite3 em Node, a conexão é única. Para não intercalar transações de requisições concorrentes, serialize as escritas transacionais (fila/mutex simples no módulo de conexão).

**Python — depois** (sqlite3)
```python
with db:   # commit automático, rollback em exceção
    cur = db.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)", (usuario_id, total))
    for item in itens:
        db.execute("INSERT INTO itens_pedido ... VALUES (?, ?, ?, ?)", (...))
        db.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (item["quantidade"], item["produto_id"]))
```

**Integridade referencial (delete):** apague dependentes na mesma transação (ou `ON DELETE CASCADE` quando o schema for criado pela aplicação), mantendo a resposta original.
```js
await transaction(async () => {
  await run('DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)', [id]);
  await run('DELETE FROM enrollments WHERE user_id = ?', [id]);
  await run('DELETE FROM users WHERE id = ?', [id]);
});
```

---

## P12 — Substituir APIs deprecated

Aplique a tabela do catálogo (AP17). Exemplos:

```python
# antes
task = Task.query.get(task_id)
created_at = datetime.utcnow()

# depois
task = db.session.get(Task, task_id)
from datetime import datetime, timezone
def utcnow():                     # helper único; mantém datetimes "naive" em UTC
    return datetime.now(timezone.utc).replace(tzinfo=None)
created_at = utcnow()
```
O `.replace(tzinfo=None)` preserva a compatibilidade com colunas `DateTime` sem timezone já gravadas (comparar aware com naive gera `TypeError`). Em colunas SQLAlchemy, use `default=utcnow` (a função, sem chamar).

```js
// antes
const b = new Buffer(str);
// depois
const b = Buffer.from(str);
```

---

## P13 — Centralizar validação, constantes e serialização

**Quando:** validação repetida em criar/atualizar, listas de valores válidos espalhadas, montagem de dict a partir de `row` copiada em várias funções, magic numbers de regra.

**Python — antes**
```python
if novo_status not in ["pendente", "aprovado", "enviado", "entregue", "cancelado"]: ...
if faturamento > 10000: desconto = faturamento * 0.1
elif faturamento > 5000: desconto = faturamento * 0.05
```
**Python — depois**
```python
# models/pedido_model.py (ou config/constants)
STATUS_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))   # (faturamento mínimo, percentual)

def calcular_desconto(faturamento):
    for minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * percentual
    return 0

# serialização única
PRODUTO_CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")
def produto_to_dict(row):
    return {campo: row[campo] for campo in PRODUTO_CAMPOS}
```

**Validador reutilizável (criar e atualizar)**
```python
def validar_produto(dados, parcial=False):
    if not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    obrigatorios = () if parcial else ("nome", "preco", "estoque")
    for campo in obrigatorios:
        if campo not in dados:
            raise ValidationError(f"{campo.capitalize()} é obrigatório")
    ...
```
Mantenha **as mesmas mensagens e status** que a API original devolvia nos casos que já eram validados.

---

## P14 — Higiene: nomes, logging, imports, condicionais

```python
# antes
import os, sys, json, time          # sem uso
print("Produto criado com ID: " + str(id))
def is_admin(self):
    if self.role == 'admin':
        return True
    else:
        return False
if type(tags) == list: ...

# depois
logger = logging.getLogger(__name__)
logger.info("produto criado id=%s", produto_id)
def is_admin(self) -> bool:
    return self.role == "admin"
if isinstance(tags, list): ...
```

```js
// antes
let u = req.body.usr; let e = req.body.eml; let cc = req.body.card;
// depois (o contrato usr/eml/card continua igual; só as variáveis internas mudam)
const { usr: name, eml: email, pwd: password, c_id: courseId, card } = req.body;
```

Configure o logging uma vez no composition root (`logging.basicConfig(level=...)` / um `logger.js` simples sobre `console` com níveis). Remova imports e funções sem uso depois de confirmar com busca no projeto.
