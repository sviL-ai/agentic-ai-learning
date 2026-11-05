import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------- config ----------
here = Path(__file__).parent
load_dotenv(here.parent / ".env")

API_KEY = os.environ["LLM_GATEWAY_API_KEY"]
BASE_URL = os.environ["LLM_GATEWAY_BASE_URL"]
EMBED_MODEL = "auto"
CHAT_MODEL = "auto"

CHUNK_SIZE = 300      # characters per chunk
CHUNK_OVERLAP = 50    # characters shared between neighbouring chunks
TOP_K = 3             # chunks retrieved per question

DB_DIR = here / "chroma_db"
COLLECTION = "company_docs"
REBUILD = os.getenv("REBUILD", "0") == "1"   # REBUILD=1 forces re-ingestion

# ---------- embeddings + vector store ----------
embeddings = OpenAIEmbeddings(
    model=EMBED_MODEL,
    api_key=API_KEY,
    base_url=BASE_URL,
    check_embedding_ctx_length=False,   # gateway wants plain text, not token IDs
)


def get_store() -> Chroma:
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=embeddings,
        persist_directory=str(DB_DIR),
    )


vector_store = get_store()

if REBUILD:
    vector_store.delete_collection()
    vector_store = get_store()

# ---------- 1. ingestion (only if the store is empty) ----------
if vector_store._collection.count() == 0:
    # load: files -> Documents (text + metadata["source"])
    docs = DirectoryLoader(
        str(here / "docs"),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    ).load()

    # split: Documents -> smaller chunks (metadata is copied to every chunk)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(docs)

    # embed + store
    vector_store.add_documents(chunks)
    print(f"ingested {len(docs)} docs -> {len(chunks)} chunks (embedded and saved)")
else:
    print("loaded existing vector store from disk (no embedding needed)")

retriever = vector_store.as_retriever(search_kwargs={"k": TOP_K})

# ---------- 2. classic RAG chain ----------
model = init_chat_model(
    CHAT_MODEL,
    model_provider="openai",
    api_key=API_KEY,
    base_url=BASE_URL,
)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Answer the question using ONLY the context below. "
     "If the answer is not in the context, say \"I don't know based on the documents.\" "
     "Mention the source file name(s) you used.\n\n"
     "Context:\n{context}"),
    ("human", "{question}"),
])


def format_docs(docs) -> str:
    """Put each chunk in the prompt together with its source file name."""
    return "\n\n".join(
        f"[source: {Path(d.metadata['source']).name}]\n{d.page_content}" for d in docs
    )


answer_chain = (
    RunnableLambda(
        lambda x: {"context": format_docs(x["docs"]), "question": x["question"]}
    )
    | prompt
    | model
    | StrOutputParser()
)

# retrieve once, keep the docs (for citations), then generate the answer
rag_chain = (
    RunnableParallel(docs=retriever, question=RunnablePassthrough())
    | RunnablePassthrough.assign(answer=answer_chain)
)


def ask(question: str) -> None:
    result = rag_chain.invoke(question)
    print("\n" + "=" * 60)
    print("Q:", question)
    print("A:", result["answer"])
    print("Sources:")
    for d in result["docs"]:
        name = Path(d.metadata["source"]).name
        preview = d.page_content[:60].replace("\n", " ")
        print(f"  - {name} | {preview} ...")


if __name__ == "__main__":
    ask("How many days of annual leave do I get?")
    ask("What is the meal limit when travelling?")
    ask("Which days must I be in the office?")
    ask("What is the company's policy on pets in the office?")   # not in docs -> should say "I don't know"