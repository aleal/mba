import os
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.runnables import chain

from vendor import select_vendor

PROMPT_TEMPLATE = """
CONTEXTO:

{context}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{question}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

class SearchChainContext:
    def __init__(self):
        self.question = None
        self.store = None
        self.context = None
        self.embeddings = None

def search_prompt(question = None):
    chain_context = SearchChainContext()
    chain_context.question = question
    chain = select_embeddings | setup_vector_store | build_context
    result = chain.invoke(chain_context)
    return PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["question", "context"]
                         ).format(question=question, context=result.context)

@chain
def select_embeddings(chain_context:SearchChainContext) -> SearchChainContext:
    vendor = select_vendor()
    match vendor:
        case "google":
            chain_context.embeddings = GoogleGenerativeAIEmbeddings(model=os.getenv("GOOGLE_EMBEDDING_MODEL"))
        case "openai":
            chain_context.embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL"))
        case _:
            raise RuntimeError(f"Vendor {vendor} not supported")
    return chain_context

@chain
def setup_vector_store(chain_context:SearchChainContext) -> SearchChainContext:
    chain_context.store = PGVector(
        embeddings=chain_context.embeddings,
        collection_name=os.getenv("PGVECTOR_COLLECTION"),
        connection=os.getenv("PGVECTOR_URL"),
        use_jsonb=True,
    )
    return chain_context

@chain
def build_context(chain_context:SearchChainContext) -> SearchChainContext:
    results = chain_context.store.similarity_search_with_score(chain_context.question, k=10)
    context = ""
    for i in range(len(results)):
        context += results[i][0].page_content + "\n"
    chain_context.context = context
    return chain_context