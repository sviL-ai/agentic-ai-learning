import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    base_url=os.environ["LLM_GATEWAY_BASE_URL"],
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
    model="auto",
    temperature=0,
)