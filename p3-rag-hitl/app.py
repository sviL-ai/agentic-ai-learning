# app.py
import argparse
import uuid
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from agent import graph


def waiting_draft(config):
    """If this thread is paused for approval, return the email draft, else None."""
    for task in graph.get_state(config).tasks:
        if task.interrupts:
            return task.interrupts[0].value
    return None


def ask_human(draft):
    print(f"\n--- EMAIL FOR APPROVAL ---\nTo: {draft['to']}\nSubject: {draft['subject']}\n\n{draft['body']}\n")
    choice = input("[a]pprove / [e]dit / [r]eject / [l]ater: ").strip().lower()
    if choice == "a":
        return {"action": "approve"}
    if choice == "e":
        return {"action": "edit",
                "subject": input("New subject (Enter to keep): "),
                "body": input("New body (Enter to keep): "),
                "to": input("New to address (Enter to keep): ")}
    if choice == "r":
        return {"action": "reject", "reason": input("Reason: ")}
    return None  # later


ap = argparse.ArgumentParser()
ap.add_argument("--thread", help="resume an existing thread")
args = ap.parse_args()

thread_id = args.thread or f"chat-{uuid.uuid4().hex[:8]}"
config = {"configurable": {"thread_id": thread_id}}
print(f"thread: {thread_id}   (type 'exit' to quit)")

while True:
    draft = waiting_draft(config)
    if draft:                                   # paused: the human decides
        decision = ask_human(draft)
        if decision is None:
            print(f"Paused. Resume with: uv run python app.py --thread {thread_id}")
            break
        result = graph.invoke(Command(resume=decision), config)
    else:                                       # not paused: normal question
        q = input("\nyou> ").strip()
        if q == "exit":
            break
        if not q:
            continue
        result = graph.invoke({"messages": [HumanMessage(q)]}, config)

    if "__interrupt__" not in result:           # finished, print the answer
        print("\n" + result["messages"][-1].content)