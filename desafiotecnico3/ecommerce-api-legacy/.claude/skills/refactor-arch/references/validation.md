# Validação (Fase 3)

A refatoração só está concluída quando há **evidência executada** de que: (1) a aplicação sobe pelo comando original, (2) todos os endpoints respondem como antes, (3) não restam anti-patterns CRITICAL/HIGH. Nunca marque `✓` sem ter rodado a verificação.

## 1. Preparar o ambiente de execução

**Python**
1. Escolha o interpretador mais novo disponível que atenda `>= 3.10` (teste `python3.14`, `python3.13`, `python3.12`, `python3.11`, `python3.10`, `python3`, nessa ordem, com `--version`).
2. Crie a venv **no projeto** se não existir: `<python> -m venv .venv` (confira se `.venv/` está no `.gitignore`; se não estiver, avise no resumo).
3. `.venv/bin/pip install -q -r requirements.txt`. Se uma versão fixada não instalar na versão do Python disponível, registre isso e use a menor versão compatível, informando no resumo.

**Node.js**
1. `node --version`; `npm ci` se houver lockfile, senão `npm install`. Não altere o lockfile sem necessidade.

**Porta livre:** antes de subir, verifique a porta padrão (`lsof -nP -iTCP:<porta> -sTCP:LISTEN` ou uma conexão de teste). Se estiver ocupada (no macOS a 5000 costuma ser do AirPlay Receiver), use outra porta livre para a validação, sem mudar o default do projeto.

## 2. Baseline (antes de qualquer mudança)

O objetivo é registrar como a aplicação **original** responde, para comparar depois.

1. **Isolamento:** copie o projeto para um diretório temporário (`mktemp -d`), excluindo `.git`, `.claude`, `.venv`/`venv`, `node_modules` e bancos (`*.db`). Rode o baseline **na cópia**, para não sujar o projeto com bancos e logs. Reaproveite as dependências do projeto (Python: o interpretador `.venv/bin/python` do projeto; Node: link simbólico para `node_modules`).
2. **Subir o original sem editar código:**
   - Flask com `app` em nível de módulo: `<venv-python> -m flask --app app run --port <porta>` (permite trocar a porta sem editar arquivos).
   - Script com `if __name__ == "__main__":` que faz inicializações extras: rode `python app.py` se a porta padrão estiver livre.
   - Node: o comando de `npm start`. Se a porta estiver fixa no código e ocupada, altere a porta **apenas na cópia temporária**.
   - Se o README manda rodar um seed antes (ex.: `python seed.py`), rode-o antes do baseline, também na cópia.
3. Espere a aplicação ficar pronta (polling na rota raiz ou de health, até ~20s).
4. Rode o **script de smoke test** (seção 4) com o cenário do inventário de endpoints e salve o resultado em `<tmp>/baseline.json`.
5. Pare o servidor (mate pelo PID que você iniciou) e mantenha só o `baseline.json`.

## 3. Montar o cenário de requisições

Para **cada endpoint do inventário da Fase 1**, inclua pelo menos uma requisição. Use payloads de `*.http`/README quando existirem; senão, derive dos campos lidos no código.

Ordem segura (os dados criados por um passo alimentam os seguintes):
1. Raiz e health.
2. `GET` de listagem e de detalhe (IDs que existem nos seeds).
3. Casos de erro já tratados pela API original: detalhe com ID inexistente (404), criação com payload inválido (400).
4. `POST` de criação → guarde o ID retornado para os próximos passos (`{{id}}` no cenário).
5. `PUT`/`PATCH` sobre o recurso criado.
6. Endpoints de relatório/agregação.
7. Por último, os destrutivos: `DELETE` do recurso criado e rotas de reset/admin.

Endpoints perigosos (execução de SQL, reset de banco): no baseline, execute-os com uma operação inofensiva (ex.: `SELECT 1`), sempre na cópia temporária. Depois da refatoração, se eles passaram a exigir token (Playbook P10), teste **duas vezes**: sem token (espera-se 403, mudança intencional) e com token válido e a feature habilitada por variável de ambiente (espera-se o comportamento original).

## 4. Script de smoke test (modelo)

Salve no diretório temporário (não no projeto) e adapte o `SCENARIO`. Usa apenas a biblioteca padrão do Python, então funciona para validar APIs de qualquer stack.

```python
#!/usr/bin/env python3
"""Uso: smoke.py <base_url> <saida.json> [header=valor ...]"""
import json, sys, urllib.request, urllib.error

BASE, OUT = sys.argv[1].rstrip("/"), sys.argv[2]
EXTRA_HEADERS = dict(h.split("=", 1) for h in sys.argv[3:])

# (nome, método, path, corpo JSON ou None, variável onde guardar um id da resposta ou None, caminho do id)
SCENARIO = [
    ("root", "GET", "/", None, None, None),
    ("create", "POST", "/items", {"name": "Teste"}, "item_id", ["dados", "id"]),
    ("get_created", "GET", "/items/{item_id}", None, None, None),
    ("delete_created", "DELETE", "/items/{item_id}", None, None, None),
]

def shape(value):
    """Formato estrutural: chaves e tipos, sem valores (timestamps e ids variam)."""
    if isinstance(value, dict):
        return {k: shape(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [shape(value[0])] if value else []
    return type(value).__name__

vars_, results = {}, []
for name, method, path, body, save_as, id_path in SCENARIO:
    url = BASE + path.format(**vars_)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json", **EXTRA_HEADERS})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            status, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read()
    try:
        payload = json.loads(raw or b"null")
    except ValueError:
        payload = raw.decode(errors="replace")[:200]
    if save_as and isinstance(payload, (dict, list)):
        cur = payload
        for key in id_path:
            cur = cur[key]
        vars_[save_as] = cur
    results.append({"name": name, "method": method, "path": path, "status": status,
                    "shape": shape(payload) if not isinstance(payload, str) else "text",
                    "sample": payload if isinstance(payload, str) else None})
    print(f"{status} {method} {path}")

json.dump(results, open(OUT, "w"), indent=2, ensure_ascii=False)
```

## 5. Validação pós-refatoração

1. **Boot:** suba a aplicação refatorada pelo **comando original** (ex.: `python app.py`, `npm start`), com banco novo e isolado (variável de ambiente apontando para um banco temporário quando o banco for arquivo) e porta livre via variável `PORT`. Rode o seed antes, se o projeto exigir. O processo precisa ficar de pé sem stack trace no log de inicialização.
2. **Endpoints:** rode o mesmo cenário e salve em `<tmp>/after.json`.
3. **Comparação** (para cada passo do cenário):
   - status igual ao baseline;
   - `shape` igual ao baseline, **exceto** campos sensíveis removidos de propósito (ex.: `senha`, `password`, `secret_key`), que devem ser listados em "Intentional Contract Changes";
   - para endpoints protegidos (P10): 403 sem token **e** comportamento original com token.
   Um diff inesperado é falha: corrija o código e repita a validação.
4. **Erros:** confirme que um erro forçado (ID inexistente, payload inválido) devolve JSON no formato da API e que o log mostra o erro sem vazar detalhes para o cliente.
5. **Re-varredura:** busque de novo, nos arquivos novos, os sinais de AP01, AP02, AP04, AP05, AP06, AP09 e AP13 do catálogo (ex.: `grep -rnE "execute\(.*\+|f\"SELECT|\\$\{.*\}.*(SELECT|INSERT)"`, literais de segredo, `global `, query em loop). Nenhum CRITICAL/HIGH pode restar.
6. **Compilação/sintaxe:** Python `<venv-python> -m compileall -q src` (ou os pacotes do projeto); Node `node --check` em cada arquivo `.js` alterado.

## 6. Limpeza

- Mate todos os processos de servidor que você iniciou (pelo PID) e confirme que a porta foi liberada.
- Apague os diretórios temporários e os bancos criados pela validação.
- Não deixe no projeto bancos, logs ou scripts de teste criados pela validação (a venv/node_modules podem ficar se estiverem no `.gitignore`).

## 7. Como reportar no resumo final

Na seção "Validation" do resumo da Fase 3, inclua:
- comando de boot usado e resultado;
- `<N>/<N> endpoints match baseline`, listando os que diferem e por quê (apenas mudanças intencionais);
- resultado da re-varredura (contagem por severidade restante);
- qualquer verificação que não pôde ser executada, marcada com `✗` e o motivo.
