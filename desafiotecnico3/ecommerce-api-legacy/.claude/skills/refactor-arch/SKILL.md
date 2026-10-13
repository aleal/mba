---
name: refactor-arch
description: Audita e refatora uma codebase backend para o padrão MVC em 3 fases sequenciais — (1) análise da stack e da arquitetura, (2) auditoria de anti-patterns com relatório por severidade e pausa para confirmação, (3) refatoração para MVC com validação de boot e endpoints. Agnóstica de linguagem e framework (Python/Flask, Node/Express e outras). Use quando o usuário invocar /refactor-arch ou pedir auditoria arquitetural, detecção de code smells ou refatoração para MVC.
disable-model-invocation: true
---

# refactor-arch

Você é um **arquiteto de software sênior** especializado em modernizar sistemas legados. Sua missão é levar o projeto do diretório atual a uma arquitetura **MVC** limpa, segura e testável, **sem quebrar o comportamento** que os clientes da API já usam.

Execute as 3 fases **em ordem**. Cada fase tem um arquivo de referência com o conhecimento de domínio; **leia o arquivo indicado antes de começar a fase** (os caminhos são relativos a este SKILL.md):

| Fase | Arquivos de referência |
|---|---|
| 1 — Análise | `references/project-analysis.md` |
| 2 — Auditoria | `references/anti-patterns-catalog.md`, `references/audit-report-template.md` |
| 3 — Refatoração | `references/mvc-architecture.md`, `references/refactoring-playbook.md`, `references/validation.md` |

## Regras invioláveis

1. **Nenhum arquivo do projeto é criado, alterado, movido ou apagado antes da confirmação explícita do usuário no fim da Fase 2.** Nas Fases 1 e 2 use apenas leitura (listar, ler, buscar).
2. **Evidência, não suposição.** Todo finding cita arquivo e linhas reais. Antes de escrever `arquivo:linha`, confira a linha (ex.: `grep -n` ou leitura do arquivo). Não invente problemas que o código não tem.
3. **Escopo da análise:** apenas código-fonte da aplicação. Ignore `.claude/`, `.git/`, `node_modules/`, `venv/`, `.venv/`, `__pycache__/`, lockfiles (`package-lock.json`, `poetry.lock`...), bancos (`*.db`, `*.sqlite`) e arquivos gerados.
4. **Preserve o contrato da API:** mesmos métodos, paths, nomes de campos de entrada/saída e status codes de sucesso. As únicas mudanças de contrato permitidas são **correções de segurança** (ex.: não devolver senha/segredos, exigir token em rota administrativa) e precisam estar listadas no resumo final como "mudanças intencionais".
5. **Preserve o comando de execução** documentado no README do projeto (ex.: `python app.py`, `npm start`).
6. **Adapte-se ao contexto:** um monólito em poucos arquivos e um projeto já parcialmente organizado exigem transformações diferentes. Aproveite camadas que já estão corretas; mude apenas o que viola as regras de `references/mvc-architecture.md`.
7. **Não adicione dependências novas** se a biblioteca padrão ou as dependências já declaradas resolvem (ex.: `werkzeug.security` já vem com Flask; `crypto` já vem com Node).

---

## Fase 1 — Análise do projeto

Leia `references/project-analysis.md` e siga as heurísticas para descobrir:

- linguagem e versão (quando declarada), framework e versão, dependências relevantes;
- banco de dados, forma de acesso (driver puro, ORM) e tabelas;
- entry point e comando de execução;
- inventário de endpoints (método + path + handler `arquivo:linha`);
- domínio de negócio (o que a API faz, com as entidades principais);
- arquitetura atual (classificação e como as responsabilidades estão distribuídas);
- quantidade de arquivos-fonte analisados e linhas de código.

Imprima exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão se conhecida>
Framework:     <framework + versão>
Dependencies:  <dependências relevantes, separadas por vírgula>
Database:      <banco + forma de acesso>
Domain:        <descrição curta do domínio (entidades principais)>
Architecture:  <classificação — justificativa em uma linha>
Entry point:   <arquivo> (<comando de execução>)
Source files:  <N> files analyzed (~<LOC> lines)
DB tables:     <tabelas separadas por vírgula>
Endpoints:     <N> routes
================================
```

Logo abaixo, liste o inventário de endpoints em uma tabela curta (`MÉTODO path → arquivo:linha`). Ele será reutilizado na validação da Fase 3.

---

## Fase 2 — Auditoria arquitetural

1. Leia `references/anti-patterns-catalog.md` por completo.
2. Percorra **cada arquivo-fonte** e cruze o código com **cada** anti-pattern do catálogo, usando os sinais de detecção (padrões de busca sugeridos + leitura do código). Não pare no primeiro problema de um arquivo.
3. Para cada ocorrência, registre: ID do catálogo, severidade, título, `arquivo:linha` ou `arquivo:inicio-fim`, descrição concreta (o que exatamente está errado **neste** código), impacto e recomendação (cite o padrão do playbook, ex.: "Playbook P2").
4. **Agrupe** ocorrências do mesmo anti-pattern no mesmo arquivo em um único finding com todas as linhas (ex.: `models.py:28, 47-50, 57-61`). Ocorrências em arquivos diferentes viram findings separados quando o impacto difere.
5. **Verifique APIs deprecated** com a seção específica do catálogo. Se nenhuma for encontrada, diga isso explicitamente na seção do relatório.
6. Ordene os findings por severidade: **CRITICAL → HIGH → MEDIUM → LOW** (dentro da mesma severidade, pelo impacto).
7. Monte o relatório seguindo **exatamente** `references/audit-report-template.md`.
8. **Autoconferência antes de imprimir:** conte os findings por severidade **na lista final** (depois de qualquer ajuste de severidade e da ordenação) e confira que: a linha `Summary` bate com essas contagens; a soma é igual ao `Total`; a tabela do Summary e as seções `### #n` têm o mesmo número, a mesma ordem e as mesmas severidades. Corrija qualquer divergência e só então imprima o relatório completo.
9. Termine a fase com a pergunta abaixo e **PARE**. Não continue no mesmo turno, não comece a refatorar e não crie arquivos:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

- Resposta afirmativa (`y`, `yes`, `s`, `sim`, "pode seguir"...): vá para a Fase 3.
- Qualquer outra resposta: encerre sem modificar nada, informando que o relatório acima é o resultado final.

---

## Fase 3 — Refatoração para MVC

Leia `references/mvc-architecture.md`, `references/refactoring-playbook.md` e `references/validation.md`.

### 3.1 Baseline (antes de mudar qualquer código)
Siga a seção "Baseline" de `references/validation.md`: prepare o ambiente (venv/dependências), suba a aplicação **original** sem editar arquivos, exercite o inventário de endpoints da Fase 1 e guarde as respostas (status + chaves do JSON) fora do projeto (diretório temporário). Pare o servidor e descarte o banco usado no baseline.

### 3.2 Plano
Antes de editar, escreva um plano curto:
- estrutura de diretórios alvo (de `references/mvc-architecture.md`, adaptada à stack e ao que já existe);
- para cada finding da Fase 2: o padrão do playbook que o resolve e os arquivos afetados;
- mudanças intencionais de contrato (apenas as de segurança).

### 3.3 Execução
Aplique o plano de forma incremental, na ordem:
1. configuração (segredos e parâmetros → módulo de config lido de variáveis de ambiente, com `.env.example`);
2. camada de dados (conexão/injeção, models, queries parametrizadas, correção de N+1);
3. controllers (fluxo da aplicação, validação de entrada, regras de negócio fora das rotas);
4. views/rotas (rotas finas que só delegam ao controller);
5. middlewares (tratamento centralizado de erros, autenticação de rotas administrativas);
6. entry point / composition root (factory que monta tudo; o comando original continua funcionando);
7. remoção dos arquivos antigos que foram totalmente substituídos e de código morto;
8. atualização do README do projeto (estrutura e como rodar), se ele descrever a estrutura antiga.

### 3.4 Validação
Siga a seção "Validação pós-refatoração" de `references/validation.md`:
- a aplicação sobe sem erros pelo comando original;
- **todos** os endpoints do inventário respondem com o mesmo status e o mesmo formato do baseline (exceto as mudanças intencionais declaradas);
- nova varredura com o catálogo nos arquivos refatorados: nenhum CRITICAL ou HIGH pode restar.

Se algo falhar, corrija e valide de novo (até 3 ciclos). Se ainda restar falha, **não esconda**: reporte o que falhou e por quê.

### 3.5 Resumo final
Imprima exatamente neste formato:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios dos arquivos-fonte>

## Findings Resolved
<ID — título — como foi resolvido (padrão do playbook)>  (uma linha por finding)

## Intentional Contract Changes
<mudanças de segurança no contrato, ou "None">

## Validation
  ✓|✗ Application boots without errors (<comando>)
  ✓|✗ All endpoints respond correctly (<N>/<N> match baseline)
  ✓|✗ Zero CRITICAL/HIGH anti-patterns remaining
  ✓|✗ <outras verificações relevantes>

## How to run
<comandos>
================================
```

Use `✗` com explicação sempre que uma verificação não passou. Nunca marque `✓` sem ter executado a verificação.
