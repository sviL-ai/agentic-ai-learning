import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

BASE_URL = os.environ["LLM_GATEWAY_BASE_URL"]   # your gateway's /v1 URL
API_KEY = os.environ["LLM_GATEWAY_API_KEY"]

def get_llm():
    return ChatOpenAI(model="auto", base_url=BASE_URL, api_key=API_KEY)

def get_embeddings():
    return OpenAIEmbeddings(
        model="auto",
        base_url=BASE_URL,
        api_key=API_KEY,
        check_embedding_ctx_length=False,   # needed for most non-OpenAI gateways
        chunk_size=20,
    )