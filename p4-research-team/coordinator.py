import sqlite3
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langgraph.checkpoint.sqlite import SqliteSaver

from model import model
from prompts import COORDINATOR_PROMPT
from state import TeamState
from subagent_tools import research_company, analyze_company, write_brief

conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

coordinator = create_agent(
    model,
    tools=[research_company, analyze_company, write_brief],
    system_prompt=COORDINATOR_PROMPT,
    state_schema=TeamState,
    checkpointer=checkpointer,
    middleware=[ModelCallLimitMiddleware(run_limit=8, exit_behavior="end")],
    name="coordinator",
)

