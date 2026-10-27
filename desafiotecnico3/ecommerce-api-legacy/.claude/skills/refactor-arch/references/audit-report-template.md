# Template do relatório de auditoria (Fase 2)

O relatório é impresso no terminal e precisa poder ser salvo como Markdown sem edição. Siga a estrutura abaixo **na ordem**, sem pular seções.

## Regras de preenchimento

1. **Ordenação:** todos os CRITICAL, depois HIGH, depois MEDIUM, depois LOW. Numere os findings em sequência (`#1`, `#2`...) depois de ordenar.
2. **Localização exata:** `File:` sempre com caminho relativo à raiz do projeto e linhas reais: `arquivo:linha`, `arquivo:inicio-fim` ou lista `arquivo:12, 47-50`. Nunca "vários lugares".
3. **Descrição concreta:** cite o identificador, o valor ou a construção encontrada (ex.: "`SECRET_KEY` = `'minha-chave...'`", "concatena `email` e `senha` na query de login"). Não use frases genéricas como "código ruim".
4. **Evidência:** um trecho curto (até 3 linhas) do código original em bloco de código, quando ajudar a entender.
5. **Recomendação:** ação concreta + referência ao playbook (`Playbook P<n>`).
6. **Summary:** os números precisam bater com a lista de findings. Se você ajustar a severidade de um finding (subir/descer um nível), recalcule as contagens e reordene a lista **depois** do ajuste. `CRITICAL + HIGH + MEDIUM + LOW = Total`.
7. **APIs deprecated:** sempre presentes como seção, mesmo vazia (dizendo o que foi verificado).
8. **Idioma:** cabeçalhos e rótulos fixos em inglês, exatamente como no template (`Summary`, `File:`, `Description:`...). Títulos dos findings, descrições, impactos e recomendações em **português do Brasil**, a menos que o usuário escreva em outro idioma na invocação da skill.

## Template

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório do projeto>
Stack:   <Linguagem> + <Framework> (<banco>)
Files:   <N> analyzed | ~<LOC> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP02 | SQL Injection | models.py:28, 47-50 |
| ... | | | | |

## Findings

### #1 [CRITICAL] <Título do anti-pattern> (<ID>)
File: <arquivo:linhas>
Description: <o que está errado neste código, citando identificadores>
Evidence:
```<linguagem>
<até 3 linhas do código original>
```
Impact: <consequência concreta para segurança, manutenção ou dados>
Recommendation: <ação concreta> (Playbook P<n>)

### #2 [HIGH] ...

## Deprecated APIs
| Location | Deprecated API | Modern replacement |
|---|---|---|
| <arquivo:linha> | <API> | <substituto> |

<ou: "Nenhuma API deprecated encontrada. Verificado: <lista do que foi checado>.">

## Architecture Notes
- Current: <classificação da Fase 1 e o principal problema estrutural>
- Target: <estrutura MVC proposta em uma linha>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````

## Exemplo de finding bem escrito

```markdown
### #2 [CRITICAL] SQL Injection (AP02)
File: db/customer_repo.py:14, 31-33, 52
Description: 3 queries montadas por concatenação de strings. A de autenticação (`find_by_credentials`) concatena `username` e `password` vindos do corpo da requisição; a busca concatena `q` da query string em `LIKE '%...%'`.
Evidence:
```python
"SELECT * FROM customers WHERE username = '" + username + "' AND password = '" + password + "'"
```
Impact: autenticação com `' OR '1'='1' --` entra sem senha; a busca permite ler qualquer tabela via UNION.
Recommendation: usar placeholders `?` com tupla de parâmetros em todas as queries (Playbook P2).
```

## Exemplo de finding ruim (não faça)

```markdown
### [HIGH] Problemas de segurança
File: vários arquivos
Description: O código tem várias falhas de segurança.
```
Falta ID, linhas, identificadores, impacto e recomendação acionável.
