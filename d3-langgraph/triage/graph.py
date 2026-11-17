from langgraph.graph import StateGraph, START, END
from state import TriageState
from nodes import classify, billing, tech, general, draft_reply, human_review, send

def route(state: TriageState) -> str:
    return state["category"]

def after_review(state: TriageState) -> str:
    return "send" if state["approved"] else END

def build():
    g = StateGraph(TriageState)
    for name, fn in [("classify", classify), ("billing", billing), ("tech", tech),
                     ("general", general), ("draft_reply", draft_reply),
                     ("human_review", human_review), ("send", send)]:
        g.add_node(name, fn)

    g.add_edge(START, "classify")
    g.add_conditional_edges("classify", route,
        {"billing": "billing", "tech": "tech", "general": "general"})
    for n in ("billing", "tech", "general"):
        g.add_edge(n, "draft_reply")
    g.add_edge("draft_reply", "human_review")
    g.add_conditional_edges("human_review", after_review, {"send": "send", END: END})
    g.add_edge("send", END)
    return g