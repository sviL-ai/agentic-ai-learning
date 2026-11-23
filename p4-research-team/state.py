from langchain.agents import AgentState

class TeamState(AgentState):
    company: str
    research_notes: str
    analysis: str
    brief: str