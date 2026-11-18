# agent.py
import sqlite3
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from config import get_llm
from tools import search_docs
from langgraph.checkpoint.sqlite import SqliteSaver
from tools import search_docs, draft_email

TOOLS = [search_docs, draft_email]

llm = get_llm().bind_tools(TOOLS)      # tells the LLM which tools exist

SYSTEM = """You are an assistant for iLeaf Solutions' sales and delivery team.
Answer questions about iLeaf's past projects using ONLY what search_docs returns.

Rules:
- Always call search_docs before answering a question about iLeaf's work.
  If the first results don't answer it, search again with different words.
- Cite as you go: after each claim, put the case study name in brackets,
  like [LeadChirp: A Voice Agent That Qualifies Its Own Pipeline].
- End with a "Sources" list: one line per case study used, with its URL.
- If the search results don't contain the answer, say you couldn't find it.
  Never guess or use outside knowledge about iLeaf's projects.
- To write or send an email, use draft_email. Search first so the email
  contains real facts from the case studies. A human reviews every email, so
  never say it was sent until the tool result says so. If the reviewer rejects
  it, tell the user and offer to revise.
- If the tool result says the reviewer edited the email, that edit is intentional:
  report what was actually sent and do not apologise or offer to resend the original."""


def agent(state: MessagesState):
    reply = llm.invoke([SystemMessage(SYSTEM)] + state["messages"])
    return {"messages": [reply]}


builder = StateGraph(MessagesState)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)   # -> "tools" or END
builder.add_edge("tools", "agent")
conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
graph = builder.compile(checkpointer=SqliteSaver(conn))