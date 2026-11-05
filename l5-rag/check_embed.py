import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

embeddings = OpenAIEmbeddings(
    model="auto",   # replace with a real embedding model name if this fails
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
    base_url=os.environ["LLM_GATEWAY_BASE_URL"],
    check_embedding_ctx_length=False,   # send plain text, not token IDs
)

vec = embeddings.embed_query("How many days of annual leave do I get?")
print("dimensions:", len(vec))
print("first 5 numbers:", vec[:5])