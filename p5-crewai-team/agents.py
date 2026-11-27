from crewai import Agent
from llm import llm
from prompts import ANALYST_PROMPT, MANAGER_PROMPT, RESEARCHER_PROMPT, WRITER_PROMPT
from tools import web_search


researcher = Agent(
    role="Company Research Agent",
    goal="Gather accurate, sourced, evidence-based information about the given company.",
    backstory=RESEARCHER_PROMPT,
    llm=llm,
    tools=[web_search],
    max_iter=8,
    allow_delegation=False,
    verbose=True,
)

analyst = Agent(
    role="Business Analyst",
    goal="Identify likely AI needs and one outreach angle, based only on the research notes.",
    backstory=ANALYST_PROMPT,
    llm=llm,
    allow_delegation=False,
    verbose=True,
)

writer = Agent(
    role="Business Writer",
    goal="Write a one-page company brief in Markdown from the research and analysis.",
    backstory=WRITER_PROMPT,
    llm=llm,
    allow_delegation=False,
    verbose=True,
)

manager = Agent(
    role="Research Team Coordinator",
    goal="Get a one-page company brief produced by delegating to the team, in order.",
    backstory=MANAGER_PROMPT,
    llm=llm,
    allow_delegation=True,
    verbose=True,
)