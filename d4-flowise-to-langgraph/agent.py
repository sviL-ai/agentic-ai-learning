"""Indian legal chatbot v1: LangGraph agent + Tavily search.

Graph:  START -> agent -> (tool calls?) -> tools -> agent -> ... -> END
Memory: InMemorySaver checkpointer, keyed by thread_id (replaces Flowise Buffer Memory).
"""

import os
import uuid

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from search_tool import build_search_tool
from prompt import PROMPT

load_dotenv()

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
TRUSTED_DOMAINS = [
    "indiankanoon.org",
    "indiacode.nic.in",
    "main.sci.gov.in",
    "sci.gov.in",
    "egazette.gov.in",
    "legislative.gov.in",
    "lawcommissionofindia.nic.in",
    "prsindia.org",
    "livelaw.in",
    "barandbench.com",
]

# --------------------------------------------------------------------------
# Model (OpenAI-compatible gateway)
# --------------------------------------------------------------------------
llm = ChatOpenAI(
    model="gemini-2.5-flash",
    base_url=os.environ["LLM_GATEWAY_BASE_URL"],
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
    temperature=0.2,
)

# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------
search_tool = build_search_tool(
    provider=os.getenv("SEARCH_PROVIDER", "exa"),  # "exa" or "tavily"
    # include_domains=TRUSTED_DOMAINS,
)
tools = [search_tool]
llm_with_tools = llm.bind_tools(tools)

# --------------------------------------------------------------------------
# Graph
# --------------------------------------------------------------------------
def agent(state: MessagesState):
    response = llm_with_tools.invoke([SystemMessage(content=PROMPT)] + state["messages"])
    return {"messages": [response]}


builder = StateGraph(MessagesState)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)  # -> "tools" or END
builder.add_edge("tools", "agent")

graph = builder.compile(checkpointer=InMemorySaver())


# --------------------------------------------------------------------------
# Terminal chat loop
# --------------------------------------------------------------------------
def ask(question: str, thread_id: str) -> str:
    result = graph.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": thread_id}},
    )
    content = result["messages"][-1].content
    if isinstance(content, list):  # some models return content blocks
        content = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return content


if __name__ == "__main__":
    thread_id = str(uuid.uuid4())
    print("Indian legal assistant. Type 'exit' to quit, 'new' for a fresh conversation.\n")
    while True:
        q = input("You: ").strip()
        if not q:
            continue
        if q.lower() in {"exit", "quit"}:
            break
        if q.lower() == "new":
            thread_id = str(uuid.uuid4())
            print("(new conversation)\n")
            continue
        print(f"\nAssistant: {ask(q, thread_id)}\n")