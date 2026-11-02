import os
from dotenv import load_dotenv
from pathlib import Path
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool, BaseTool, StructuredTool
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

# 1. @tool: decorate a function. Name, type hints, and docstring become the schema.
@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# 2. StructuredTool: build a tool from an existing function, no decorator.
def multiply(a: int, b: int) -> int:
    return a * b
 
multiply_tool = StructuredTool.from_function(
    func=multiply,
    name="multiply",
    description="Multiply two numbers.",
)

# 3. BaseTool: subclass for full control.
class SubtractInput(BaseModel):
    a: int = Field(description="Number to subtract from")
    b: int = Field(description="Number to subtract")
 
class SubtractTool(BaseTool):
    name: str = "subtract"
    description: str = "Subtract b from a."
    args_schema: type[BaseModel] = SubtractInput
 
    def _run(self, a: int, b: int) -> int:
        return a - b
 
subtract_tool = SubtractTool()

model_with_tools = model.bind_tools([add, multiply_tool, subtract_tool])

response = model_with_tools.invoke(
                                    # "What will you get if you add five and nine",
                                    # "How much is left if 2 oranges are taken from 9 oranges",
                                    "What is 6 times 6"
                                    )

# It shows if correct tool has been selected, not the final answer
for tool_call in response.tool_calls:
    # View tool calls made by the model
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")