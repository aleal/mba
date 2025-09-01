import os
from re import S
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.runnables import chain
from langchain_openai import OpenAIEmbeddings

from vendor import select_vendor

load_dotenv()

class ChainContext:
    def __init__(self):
        self.pdf_path = None
        self.documents = None
        self.splits = None
        self.enriched = None
        self.embeddings = None
        self.store = None

@chain
def check_env_vars(context:ChainContext) -> ChainContext:
    for k in ("GOOGLE_API_KEY", "PGVECTOR_URL", "PGVECTOR_COLLECTION", "GOOGLE_EMBEDDING_MODEL"):
        if not os.getenv(k):
            raise RuntimeError(f"Environment variable {k} is not set")
    return context

@chain
def load_pdf(context:ChainContext) -> ChainContext:
    loader = PyPDFLoader(context.pdf_path)
    documents = loader.load()
    context.documents = documents
    return context

@chain
def split_pdf(context:ChainContext) -> ChainContext:
    splits = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=150, 
            add_start_index=False
        ).split_documents(context.documents)
    context.splits = splits
    return context

@chain
def enrich_documents(context:ChainContext) -> ChainContext:
    context.enriched = [
        Document(
            page_content=d.page_content,
            metadata={k: v for k, v in d.metadata.items() if v not in ("", None)}
        )
        for d in context.splits
    ] 
    return context

@chain
def select_embeddings(context:ChainContext) -> ChainContext:
    vendor = select_vendor()
    match vendor:
        case "google":
            context.embeddings = GoogleGenerativeAIEmbeddings(model=os.getenv("GOOGLE_EMBEDDING_MODEL"))
        case "openai":
            context.embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL"))
        case _:
            raise RuntimeError(f"Vendor {vendor} not supported")
    return context

@chain
def setup_vector_store(context:ChainContext) -> ChainContext:
    context.store = PGVector(
        embeddings=context.embeddings,
        collection_name=os.getenv("PGVECTOR_COLLECTION"),
        connection=os.getenv("PGVECTOR_URL"),
        use_jsonb=True,
    )
    return context

@chain  
def add_documents(context:ChainContext) -> ChainContext:
    enriched = context.enriched
    ids = [f"doc-{i}" for i in range(len(enriched))]
    context.store.add_documents(documents=enriched, ids=ids)
    return context

PDF_PATH = os.getenv("PDF_PATH")

def ingest_pdf():
    chain = check_env_vars | load_pdf | split_pdf | enrich_documents | \
            select_embeddings | setup_vector_store | add_documents
    context = ChainContext()
    context.pdf_path = PDF_PATH
    chain.invoke(context)
    print("Documents ingested successfully.")

if __name__ == "__main__":
    ingest_pdf()