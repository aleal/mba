import os

from langchain_openai import ChatOpenAI
from search import search_prompt
from dotenv import load_dotenv  
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import chain

from vendor import select_vendor

load_dotenv()

@chain
def check_env_vars(a:any) -> any:
    for k in ("GOOGLE_API_KEY", "PGVECTOR_URL", "PGVECTOR_COLLECTION", "GOOGLE_EMBEDDING_MODEL"):
        if not os.getenv(k):
            raise RuntimeError(f"Environment variable {k} is not set")
    return a

@chain 
def input_question(a:any) -> str:
    question = None
    while not question:
        question = input("Digite sua pergunta: ").strip()
        if not question:
            print("Pergunta não pode ser vazia. Por favor, digite uma pergunta.")
    return question

def select_model():
    vendor = select_vendor()
    match vendor:
        case "google":
            return ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_CHAT_MODEL"), temperature=0.5)
        case "openai":
            return ChatOpenAI(model=os.getenv("OPENAI_CHAT_MODEL"), temperature=0.5)
        case _:
            raise RuntimeError(f"Vendor {vendor} not supported")

def main():
    question_chain = check_env_vars | input_question
    question = question_chain.invoke({})
    prompt = search_prompt(question)
    chat_chain = select_model() | StrOutputParser()
    result = chat_chain.invoke(prompt)
    print(result)

if __name__ == "__main__":
    while True:
        main()
        if input("Deseja continuar? (s/n)").lower() != "s":
            break