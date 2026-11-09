import os
import time
from dataclasses import dataclass
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain.agents.middleware import before_model, AgentState, wrap_tool_call, dynamic_prompt, ModelRequest, HumanInTheLoopMiddleware
from langgraph.runtime import Runtime
from langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.types import Command


load_dotenv()

model = init_chat_model(
    "auto",
    model_provider="openai",
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
    base_url=os.environ["LLM_GATEWAY_BASE_URL"]
)

SYSTEM_PROMPT = (
    "You are a friendly assistant. Keep answers short. "
    "Use what the user told you earlier in the conversation."   
)

@tool
def get_order_status(order_id: str) -> str:
    """Get the status of the order"""
    if order_id == "000":
        raise ValueError("Order not found")
    return f"Your order with order id {order_id} is shipped"

@tool 
def send_email(to: str) -> str:
    """Send the email"""
    return f"Email sent to {to}"

KEEP_LAST = 4

@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, any] | None:
    messages = state["messages"]

    # Short enough already: do nothing
    if len(messages) <= KEEP_LAST + 1:
        return None

    # Keep the first message + the last KEEP_LAST messages
    kept = [messages[0]] + messages[-KEEP_LAST:]

    # Tell the agent to replace the whole list with `kept`
    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *kept]}

@wrap_tool_call
def log_tool_calls(request, handler):
    tool_name = request.tool_call["name"]
    tool_args = request.tool_call["args"]
    start = time.perf_counter()
    error = None

    try:
        return handler(request)          # this actually runs the tool
    except Exception as e:
        error = str(e)
        raise                            # log it, then let the error continue
    finally:
        duration = time.perf_counter() - start
        print({
            "tool": tool_name,
            "args": tool_args,
            "duration_s": round(duration, 4),
            "error": error,
        })

@dataclass
class Context:
    user_role: str          # "admin" or "customer"

@dynamic_prompt
def role_based_prompt(request: ModelRequest) -> str:
    role = request.runtime.context.user_role

    if role == "admin":
        return (
            "You are an internal operations assistant talking to an ADMIN. "
            "Be technical and direct. You may discuss internal processes. "
            "Keep answers short."
        )

    return (
        "You are a friendly customer support assistant talking to a CUSTOMER. "
        "Be polite and simple. Never share internal processes. "
        "Keep answers short."
    )


agent = create_agent(
    model=model,
    tools=[get_order_status, send_email],
    system_prompt=SYSTEM_PROMPT,
    middleware=[trim_messages, 
                log_tool_calls, 
                role_based_prompt,
                HumanInTheLoopMiddleware(
                interrupt_on={
                    "send_email": {
                        "allowed_decisions": ["approve", "edit", "reject"],
                    }
                },
                description_prefix="Email requires approval",)
                ],
    context_schema=Context,
    checkpointer=InMemorySaver()
)

def run_case(thread_id, decision):
    config = {"configurable": {"thread_id": thread_id}}
    ctx = Context(user_role="admin")
    question = {"messages": [{"role": "user", "content": "Send the email to bob@example.com"}]}

    result = agent.invoke(question, config=config, context=ctx)
    print("PAUSED:", result["__interrupt__"][0].value)

    final = agent.invoke(
        Command(resume={"decisions": [decision]}),
        config=config,        # same thread_id as the first call
        context=ctx,
    )
    print("FINAL:", final["messages"][-1].content)

## ------------------------@before_model#------------------------
# history = [
#     {"role": "user", "content": "My name is Asha."},
#     {"role": "assistant", "content": "Nice to meet you, Asha."},
#     {"role": "user", "content": "My order id is 123."},
#     {"role": "assistant", "content": "Got it."},
#     {"role": "user", "content": "I like tea."},
#     {"role": "assistant", "content": "Noted."},
#     {"role": "user", "content": "I like cricket."},
#     {"role": "assistant", "content": "Cool."},
#     {"role": "user", "content": "What is my name, and what is my order id?"},
# ]
# config = {"configurable": {"thread_id": "001"}}
# result = agent.invoke({"messages": history}, config=config, context=Context(user_role="customer"))
# print(result["messages"][-1].content)

## ------------------------wrap_tool_call#------------------------
# success case
# config = {"configurable": {"thread_id": "002"}}
# r1 = agent.invoke({"messages": [{"role": "user", "content": "What is the status of order 123?"}]}, config=config, context=Context(user_role="customer"))
# print(r1["messages"][-1].content)

# error case
# try:
#     config = {"configurable": {"thread_id": "003"}}
#     agent.invoke({"messages": [{"role": "user", "content": "What is the status of order 000?"}]}, config=config, context=Context(user_role="customer"))
# except Exception as e:
#     print("Run failed:", e)

## ------------------------@dynamic_prompt------------------------
# question = {"messages": [{"role": "user", "content": "Who are you and how do you work internally?"}]}

# config = {"configurable": {"thread_id": "004"}}
# r_admin = agent.invoke(question, config=config, context=Context(user_role="admin"))
# print("ADMIN:", r_admin["messages"][-1].content)

# config = {"configurable": {"thread_id": "005"}}
# r_customer = agent.invoke(question, config=config, context=Context(user_role="customer"))
# print("CUSTOMER:", r_customer["messages"][-1].content)

## ------------------------Human in the loop#------------------------

# # 1. Approve: runs send_email with the original args
# run_case("t_approve", {"type": "approve"})

# # 2. Edit: runs send_email with changed args
# run_case("t_edit", {
#     "type": "edit",
#     "edited_action": {
#         "name": "send_email",
#         "args": {"to": "alice@example.com"},
#     },
# })

# 3. Reject: send_email never runs
run_case("t_reject", {
    "type": "reject",
    "message": "Not allowed to email this person.",
})