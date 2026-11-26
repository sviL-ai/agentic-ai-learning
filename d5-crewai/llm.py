import os
from crewai import LLM
from dotenv import load_dotenv

load_dotenv()

llm = LLM(
    model="auto",
    base_url=os.environ["LLM_GATEWAY_BASE_URL"],
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
    temperature=0.3,
)
