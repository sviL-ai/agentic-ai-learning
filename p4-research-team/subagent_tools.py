import sqlite3
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from model import model
from prompts import RESEARCHER_PROMPT, ANALYST_PROMPT, WRITER_PROMPT
from tools import web_search, save_brief

conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)


researcher = create_agent(
    model,
    tools=[web_search],
    system_prompt=RESEARCHER_PROMPT,
    middleware=[ModelCallLimitMiddleware(run_limit=8, exit_behavior="end")],
    name="researcher",
)

analyst = create_agent(
    model,
    tools=[],
    system_prompt=ANALYST_PROMPT,
    middleware=[ModelCallLimitMiddleware(run_limit=3, exit_behavior="end")],
    name="analyst",
)

writer = create_agent(
    model,
    tools=[save_brief],
    system_prompt=WRITER_PROMPT,
    middleware=[ModelCallLimitMiddleware(run_limit=3, exit_behavior="end")],
    name="writer",
)

@tool
def research_company(company: str, runtime: ToolRuntime) -> Command:
    """Research a company on the web and save the findings to shared state.

    Call this FIRST, before analysis or writing. It gathers the company
    overview, products and services, industry, size and recent news.

    Args:
        company: The company name to research, e.g. "Acme Corp".
    """
    result = researcher.invoke(
        {"messages": [{"role": "user", "content": f"Research the company: {company}"}]}
    )
    notes = result["messages"][-1].content

    return Command(
        update={
            "company": company,
            "research_notes": notes,
            "analysis": "",
            "brief": "",
            "messages": [
                ToolMessage(
                    content=f"Research on {company} is complete and saved to research_notes.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )

@tool
def analyze_company(runtime: ToolRuntime) -> Command:
    """Analyse the saved research notes and identify the company's likely AI
    needs and the best outreach angle. Saves the result to shared state.

    Call this SECOND, only after research_company has finished. It takes no
    arguments because it reads the research notes from shared state.
    """
    notes = runtime.state.get("research_notes")

    # Ordering guard: refuse politely if research hasn't happened yet.
    if not notes:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="No research notes yet. Call research_company first.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    result = analyst.invoke(
        {"messages": [{"role": "user", "content": f"Research notes:\n\n{notes}"}]}
    )
    analysis = result["messages"][-1].content

    return Command(
        update={
            "analysis": analysis,
            "messages": [
                ToolMessage(
                    content="Analysis is complete and saved to analysis.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )

@tool
def write_brief(runtime: ToolRuntime) -> Command:
    """Write the final one-page company brief from the saved research notes
    and analysis, and save it to shared state and to a file.

    Call this LAST, only after research_company and analyze_company have
    both finished. It takes no arguments because it reads shared state.
    """
    notes = runtime.state.get("research_notes")
    analysis = runtime.state.get("analysis")
    company = runtime.state.get("company", "company")

    # Ordering guard: both inputs must exist.
    if not notes or not analysis:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="Missing inputs. Call research_company, then analyze_company, before write_brief.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    prompt = f"Company: {company}\n\nResearch notes:\n{notes}\n\nAnalysis:\n{analysis}"
    result = writer.invoke({"messages": [{"role": "user", "content": prompt}]})

    # Find the brief the writer passed to save_brief
    brief = None
    for m in result["messages"]:
        if m.type == "ai":
            for tc in m.tool_calls:
                if tc["name"] == "save_brief":
                    brief = tc["args"].get("content")

    # If the writer never saved, report failure and leave state untouched
    if not brief:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="The writer did not save a brief. Call write_brief once more.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    return Command(
        update={
            "brief": brief,
            "messages": [
                ToolMessage(
                    content="Brief written and saved. Do not call any more tools. Reply with one short sentence.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )