import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

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

agent = create_agent(
    model=model,                     
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),      
)

def ask(text: str, thread_id: str) -> str:
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": text}]},  # only the NEW message
        config,
    )
    return result["messages"][-1].content

def show_state(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    for m in agent.get_state(config).values.get("messages", []):
        print(f"  [{m.type}] {m.content}")

if __name__ == "__main__":
    thread = input("thread id (e.g. alice): ").strip() or "default"
    print(f"Agent chatbot on thread '{thread}'. 'exit' quits, 'mem' shows state, 'switch' changes thread.")
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