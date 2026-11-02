import os
from dotenv import load_dotenv
from pathlib import Path
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from pydantic import BaseModel, Field


# Load environment variables
repo_root = Path(__file__).resolve().parents[1]
load_dotenv(repo_root / ".env")

# ---------------------init_chat_model---------------------
model = init_chat_model(
    "auto",
    model_provider="openai",
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
    base_url=os.environ["LLM_GATEWAY_BASE_URL"],
)

# ---------------------invoke, stream, batch---------------------

# invoke
# response = model.invoke("Explain what an AI agent is in one sentence.")
# print(response.content)

# stream
# for chunk in model.stream("Explain what an AI agent is in one sentence."):
#     print(chunk.text, end="|", flush=True)/

# batch
# responses = model.batch(["Explain an AI Agent in one sentence",
#                          "How is an agent different from LLM calling?"])
# for response in responses:
#     print(response.content)

# ---------------------bind_tools---------------------
# @tool
# def addition(a:int, b:int) -> int:
#     """Get the sum of two numbers"""
#     return a+b

# model_with_tools = model.bind_tools([addition])

# messages = [HumanMessage("What will you get if you add five and nine")]
# ai_msg = model_with_tools.invoke(messages)
# messages.append(ai_msg)

# for tool_call in ai_msg.tool_calls:
#     # View tool calls made by the model
#     print(f"Tool: {tool_call['name']}")
#     print(f"Args: {tool_call['args']}")
#     result = addition.invoke(tool_call["args"])
#     messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))

# final = model_with_tools.invoke(messages)
# print(final.content)   # something like "5 + 9 = 14"

# ---------------------with_structured_output---------------------
class Answer(BaseModel):
    topic: str = Field(description="Main topic of the question")
    difficulty: str = Field(description="easy, medium, or hard")

structured_model = model.with_structured_output(Answer)
result = structured_model.invoke("What is an AI agent?")
print(result)            # Answer(topic='AI agents', difficulty='easy')
