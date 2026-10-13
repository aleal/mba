#!/usr/bin/env bash
# Smoke test dos projetos refatorados: sobe a API com banco temporário, exercita
# todas as rotas originais e mostra status + início da resposta.
#
# Uso: scripts/smoke.sh <code-smells-project|ecommerce-api-legacy|task-manager-api>
# Pré-requisito: dependências instaladas (.venv com requirements.txt, ou node_modules).
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${1:?informe o projeto}"
DIR="$ROOT/$PROJECT"
TMP="$(mktemp -d)"
PORT="${PORT:-5077}"
BASE="http://127.0.0.1:$PORT"
ADMIN_TOKEN="smoke-admin-token"
PID=""

cleanup() {
  if [ -n "$PID" ]; then kill "$PID" 2>/dev/null; wait "$PID" 2>/dev/null; fi
  rm -rf "$TMP"
}
trap cleanup EXIT

# req MÉTODO PATH [CORPO_JSON] [HEADER...]
req() {
  local method="$1" path="$2" body="${3:-}"
  shift 3 2>/dev/null || shift $#
  local args=(-s -o "$TMP/resp" -w "%{http_code}" -X "$method" -H "Content-Type: application/json")
  for h in "$@"; do args+=(-H "$h"); done
  [ -n "$body" ] && args+=(-d "$body")
  local code
  code=$(curl "${args[@]}" "$BASE$path")
  printf "%-6s %-36s -> %s  %s\n" "$method" "$path" "$code" "$(head -c 110 "$TMP/resp" | tr '\n' ' ')"
}

wait_ready() {
  for _ in $(seq 40); do
    curl -s -o /dev/null "$BASE$1" && return 0
    sleep 0.5
  done
  echo "ERRO: a aplicação não subiu"; cat "$TMP/server.log"; exit 1
}

cd "$DIR" || exit 1
echo "== $PROJECT (porta $PORT) =="

case "$PROJECT" in
  code-smells-project)
    PORT=$PORT DATABASE_PATH="$TMP/loja.db" ADMIN_TOKEN=$ADMIN_TOKEN ENABLE_ADMIN_QUERY=true ENABLE_ADMIN_RESET=true \
      .venv/bin/python app.py > "$TMP/server.log" 2>&1 & PID=$!
    wait_ready /health
    req GET /
    req GET /health
    req GET /produtos
    req GET "/produtos/busca?q=Mouse&preco_max=100"
    req GET /produtos/1
    req GET /produtos/999
    req POST /produtos '{"nome":"Caneca d'"'"'Água","preco":30,"estoque":5,"categoria":"geral"}'
    req PUT /produtos/11 '{"nome":"Caneca","preco":31,"estoque":5,"categoria":"geral"}'
    req GET /usuarios
    req GET /usuarios/2
    req POST /usuarios '{"nome":"Ana","email":"ana@x.com","senha":"s3nh4"}'
    req POST /login '{"email":"ana@x.com","senha":"s3nh4"}'
    req POST /login "{\"email\":\"admin@loja.com' --\",\"senha\":\"x\"}"
    req POST /pedidos '{"usuario_id":2,"itens":[{"produto_id":2,"quantidade":2}]}'
    req POST /pedidos '{"usuario_id":2,"itens":[{"produto_id":2,"quantidade":-5}]}'
    req GET /pedidos
    req GET /pedidos/usuario/2
    req PUT /pedidos/1/status '{"status":"aprovado"}'
    req GET /relatorios/vendas
    req DELETE /produtos/11
    req POST /admin/query '{"sql":"SELECT COUNT(*) AS n FROM produtos"}'
    req POST /admin/query '{"sql":"SELECT COUNT(*) AS n FROM produtos"}' "X-Admin-Token: $ADMIN_TOKEN"
    req POST /admin/reset-db ''
    req POST /admin/reset-db '' "X-Admin-Token: $ADMIN_TOKEN"
    ;;

  ecommerce-api-legacy)
    PORT=$PORT ADMIN_TOKEN=$ADMIN_TOKEN node src/app.js > "$TMP/server.log" 2>&1 & PID=$!
    wait_ready /api/admin/financial-report
    req POST /api/checkout '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
    req POST /api/checkout '{"usr":"João","eml":"joao@teste.com","pwd":"123","c_id":1,"card":"5111222233334444"}'
    req POST /api/checkout '{"usr":"X","eml":"x@t.com","pwd":"x","c_id":99,"card":"4111"}'
    req POST /api/checkout '{"usr":"X"}'
    req GET /api/admin/financial-report ''
    req GET /api/admin/financial-report '' "X-Admin-Token: $ADMIN_TOKEN"
    req DELETE /api/users/1 ''
    req DELETE /api/users/1 '' "X-Admin-Token: $ADMIN_TOKEN"
    req GET /api/admin/financial-report '' "X-Admin-Token: $ADMIN_TOKEN"
    ;;

  task-manager-api)
    export PORT DATABASE_URL="sqlite:///$TMP/tasks.db"
    .venv/bin/python seed.py | tail -4
    .venv/bin/python app.py > "$TMP/server.log" 2>&1 & PID=$!
    wait_ready /health
    req GET /
    req GET /health
    req GET /tasks
    req GET /tasks/1
    req GET /tasks/999
    req GET "/tasks/search?q=login&status=in_progress"
    req GET /tasks/stats
    req POST /tasks '{"title":"Nova task","priority":2,"user_id":1,"category_id":1,"tags":["a","b"],"due_date":"2026-12-01"}'
    req POST /tasks '{"title":"x"}'
    req PUT /tasks/11 '{"status":"in_progress"}'
    req DELETE /tasks/11
    req GET /users
    req GET /users/1
    req GET /users/1/tasks
    req POST /users '{"name":"Ana","email":"ana@x.com","password":"abcd"}'
    req PUT /users/4 '{"name":"Ana B"}'
    req POST /login '{"email":"joao@email.com","password":"1234"}'
    TOKEN=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['token'])" "$TMP/resp")
    req GET /reports/summary
    req GET /reports/user/1
    req GET /categories
    req POST /categories '{"name":"QA","color":"#123456"}'
    req PUT /categories/5 '{"name":"QA2"}'
    req DELETE /categories/5 ''
    req DELETE /categories/5 '' "Authorization: Bearer $TOKEN"
    req DELETE /users/4 '' "Authorization: Bearer fake-jwt-token-1"
    req DELETE /users/4 '' "Authorization: Bearer $TOKEN"
    ;;

  *) echo "projeto desconhecido: $PROJECT"; exit 1 ;;
esac

echo "-- log do servidor (tracebacks: $(grep -c Traceback "$TMP/server.log")) --"
tail -n 3 "$TMP/server.log" | sed -E $'s/\x1b\\[[0-9;]*m//g'
