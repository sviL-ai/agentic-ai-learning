from pydantic import BaseModel
from langchain_core.messages import SystemMessage
from llm import llm
from state import TriageState, Category
from langgraph.types import interrupt

class Classification(BaseModel):
    category: Category

# function_calling is the most widely supported method on gateways
classifier = llm.with_structured_output(Classification, method="function_calling")

def classify(state: TriageState) -> dict:
    print("   [classify] calling LLM")
    result = classifier.invoke([
        SystemMessage(content=(
            "Classify the customer's support message as exactly one of: "
            "billing (payments, invoices, refunds), "
            "tech (bugs, errors, how-to), "
            "general (anything else)."
        )),
        *state["messages"],
    ])
    return {"category": result.category}   # a partial update, not the full state

def billing(state: TriageState) -> dict:
    return {"context": "You are a billing support agent. Be precise about money, "
                       "never promise refunds without approval."}

def tech(state: TriageState) -> dict:
    return {"context": "You are a technical support agent. Ask for error messages "
                       "and steps to reproduce; give concrete troubleshooting steps."}

def general(state: TriageState) -> dict:
    return {"context": "You are a friendly general support agent. Keep answers short."}

def draft_reply(state: TriageState) -> dict:
    reply = llm.invoke([SystemMessage(content=state["context"]), *state["messages"]])
    return {"messages": [reply], "draft": reply.content}

def human_review(state: TriageState) -> dict:
    print("   [human_review] node started")      # you'll see this print twice
    decision = interrupt({
        "category": state["category"],
        "draft": state["draft"],
        "question": "Approve, edit, or reject this reply?",
    })
    # decision is whatever we pass to Command(resume=...)
    if decision["action"] == "reject":
        return {"approved": False}
    return {"approved": True, "final": decision.get("text") or state["draft"]}

def send(state: TriageState) -> dict:
    print(f"   [send] SENDING: {state['final'][:80]}")   # fake side effect
    return {"sent": True}