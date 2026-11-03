import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy, ProviderStrategy
from langchain.chat_models import init_chat_model

repo_root = Path(__file__).resolve().parents[1]
load_dotenv(repo_root / ".env")

model = init_chat_model(
    "auto",
    model_provider="openai",
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
    base_url=os.environ["LLM_GATEWAY_BASE_URL"],
)


# The shape we want the final answer to have.
class ContactInfo(BaseModel):
    name: str = Field(description="Person's name")
    email: str = Field(description="Person's email address")


text = "Please reach out to Asha at asha@example.com about the invoice."


# 1. response_format with ToolStrategy
#    The schema is given to the model as a hidden "tool". Works with any model that can call tools.
#    handle_errors: if the model's output doesn't match the schema, retry instead of crashing.
agent = create_agent(
    model,
    tools=[],
    response_format=ToolStrategy(
        schema=ContactInfo,
        handle_errors=True,   # True = retry with a default error message
    ),
)
result = agent.invoke({"messages": [{"role": "user", "content": text}]})
print("ToolStrategy     :", result["structured_response"])


# 2. response_format with ProviderStrategy
#    Uses the provider's own built-in structured output feature. Usually more reliable,
#    but only works if your model/gateway supports it.
agent2 = create_agent(
    model,
    tools=[],
    response_format=ProviderStrategy(ContactInfo),
)
result2 = agent2.invoke({"messages": [{"role": "user", "content": text}]})
print("ProviderStrategy :", result2["structured_response"])