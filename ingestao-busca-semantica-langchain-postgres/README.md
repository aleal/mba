# Desafio Técnico: Ingestão e Busca Semântica com LangChain e Postgres

## Objetivo
Você deve entregar um software capaz de:

Ingestão: Ler um arquivo PDF e salvar suas informações em um banco de dados PostgreSQL com extensão pgVector.
Busca: Permitir que o usuário faça perguntas via linha de comando (CLI) e receba respostas baseadas apenas no conteúdo do PDF.

## Tecnologias obrigatórias
Linguagem: Python
Framework: LangChain
Banco de dados: PostgreSQL + pgVector
Execução do banco de dados: Docker & Docker Compose (docker-compose fornecido no repositório de exemplo)


## Como rodar a aplicação

### Requisitos

python >= 3.10
docker (versão utilizada 28.3.2)
libpq (postgres - versão utilizada 17.6) 

### Variáveis de ambiente adicionar ao .env
```shell
MODEL_VENDOR=<'google' or 'openai'>
GOOGLE_API_KEY=
OPENAI_API_KEY=
GOOGLE_EMBEDDING_MODEL='models/embedding-001'
OPENAI_EMBEDDING_MODEL='text-embedding-3-small'
OOGLE_CHAT_MODEL='gemini-2.5-flash-lite'
OPENAI_CHAT_MODEL='gpt-5-nano'
PGVECTOR_URL=postgresql+psycopg://postgres:postgres@host.docker.internal:5432/rag
PGVECTOR_COLLECTION=ai_collection
PDF_PATH="document.pdf"
```

### Rodando tudo (ingestão + chat) 
```shell
make run
# ou
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker compose up -d
python3 src/ingest.py
python3 src/chat.py
docker compose down
```

### Rodar passo-a-passo
#### Python env
```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Iniciando o PGVector
```shell
docker compose up -d
```

#### Ingestão do arquivo
```shell
python3 src/ingest.py
```    

#### Busca no modelo
```shell
python3 src/chat.py
```

#### Desligando o PGVector
```shell
docker compose down
```

