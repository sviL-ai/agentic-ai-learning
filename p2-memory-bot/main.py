import argparse, os
from dotenv import load_dotenv
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import SummarizationMiddleware, dynamic_prompt, ModelRequest
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres import PostgresSaver
from langchain.tools import tool, ToolRuntime
from langgraph.store.postgres import PostgresStore

class MemoryState(AgentState):
    user_id: str

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--thread", required=True, help="thread_id to resume or start")
parser.add_argument("--user", required=True, help="user_id for this run")
args = parser.parse_args()


model = init_chat_model(
    "auto",
    model_provider="openai",
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
    base_url=os.environ["LLM_GATEWAY_BASE_URL"]
)

@tool
def whoami(runtime: ToolRuntime) -> str:
    """Return the id of the current user."""
    return f"The current user_id is {runtime.state['user_id']}"

@tool
def save_preference(key: str, value: str, runtime: ToolRuntime) -> str:
    """Save a lasting user preference. Use key 'name' for what to call the user
    and key 'tone' for how they want answers written (e.g. short, casual, formal)."""
    uid = runtime.state["user_id"]
    runtime.store.put(("users", uid, "preferences"), key, {"value": value})
    return f"Saved {key} = {value}"

@dynamic_prompt
def memory_prompt(request: ModelRequest) -> str:
    uid = request.state.get("user_id", "unknown")
    items = request.runtime.store.search(("users", uid, "preferences"))
    prefs = {i.key: i.value["value"] for i in items}

    prompt = (
        "You are a helpful assistant. When the user tells you their name or how "
        "they like answers written, call save_preference right away."
    )
    if prefs:
        lines = "\n".join(f"- {k}: {v}" for k, v in prefs.items())
        prompt += f"\n\nKnown preferences for this user. Follow them:\n{lines}"
    return prompt

summarizer = SummarizationMiddleware(
    model=model,
    trigger=("messages", 6),      # fire when the chat reaches 6 messages
    keep=("messages", 2),         # keep the last 2 messages verbatim
)

with PostgresSaver.from_conn_string(os.environ["DB_URI_p2"]) as checkpointer, PostgresStore.from_conn_string(os.environ["DB_URI_p2"]) as store:
    checkpointer.setup()  # creates the tables, safe to run every time
    store.setup() 

    agent = create_agent(
        model,
        tools=[whoami, save_preference],
        middleware=[summarizer, memory_prompt],
        state_schema=MemoryState,
        checkpointer=checkpointer,
        store=store
    )

    config = {"configurable": {"thread_id": args.thread}}
    print(f"Thread: {args.thread}  (type 'exit' to quit)")

    while True:
        text = input("you> ").strip()
        if text.lower() in {"exit", "quit"}:
            break
        if text == "/state":
            print("saved state:", agent.get_state(config).values.get("user_id"))
            continue
        if text == "/messages":
            msgs = agent.get_state(config).values["messages"]
            print(f"{len(msgs)} messages:")
            for m in msgs:
                print(f"  [{m.type}] {str(m.content)[:80]}")
            continue
        if text == "/prefs":
            items = store.search(("users", args.user, "preferences"))
            print({i.key: i.value["value"] for i in items} or "no preferences saved")
            continue
        result = agent.invoke({"messages": [{"role": "user", "content": text}], "user_id": args.user}, config)
        print("bot>", result["messages"][-1].content)