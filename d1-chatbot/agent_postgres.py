import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.postgres import PostgresSaver

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

DB_URI = os.environ["DB_URI_d1"]

def run(checkpointer):
    agent = create_agent(
        model=model,
        tools=[],
        system_prompt=SYSTEM_PROMPT,   # same prompt as (a) and (b)
        checkpointer=checkpointer,     # the only conceptual change from (b)
    )

    def ask(text, thread_id):
        config = {"configurable": {"thread_id": thread_id}}
        result = agent.invoke(
            {"messages": [{"role": "user", "content": text}]}, config
        )
        return result["messages"][-1].content

    def show_state(thread_id):
        config = {"configurable": {"thread_id": thread_id}}
        for m in agent.get_state(config).values.get("messages", []):
            print(f"  [{m.type}] {m.content}")

    thread = input("thread id (e.g. alice): ").strip() or "default"
    print(f"Postgres-backed chatbot, thread '{thread}'. 'exit', 'mem', 'switch'.")
    while True:
        text = input(f"{thread}> ").strip()
        if text == "exit":
            break
        if text == "mem":
            show_state(thread)
            continue
        if text == "switch":
            thread = input("new thread id: ").strip() or "default"
            continue
        print("bot>", ask(text, thread))

if __name__ == "__main__":
    # The connection must stay open for as long as the agent is used,
    # so everything runs inside this `with` block.
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()   # creates tables; safe to run every time
        run(checkpointer)