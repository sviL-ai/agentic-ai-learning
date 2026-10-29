from openai import OpenAI
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables from the root .env file
repo_root = Path(__file__).resolve().parents[1]
load_dotenv(repo_root / ".env")

client = wrap_openai(
    OpenAI(
        api_key=os.environ["LLM_GATEWAY_API_KEY"],
        base_url=os.environ["LLM_GATEWAY_BASE_URL"],
))

@traceable(run_type="tool")  # trace this as a tool span
def get_context(question: str) -> str:
    # In a real app, this would query a knowledge base or vector store
    return "LangSmith traces are stored for 14 days on the Developer plan."

@traceable  # capture the full pipeline as a single trace
def assistant(question: str) -> str:
    context = get_context(question)
    response = client.chat.completions.create(
        model="auto",
        messages=[
            {
                "role": "system",
                "content": f"Answer using the context below.\n\nContext: {context}",
            },
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    print(assistant("How long are LangSmith traces stored?"))