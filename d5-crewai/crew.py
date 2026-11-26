from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process
from llm import llm
from guardrails import validate_draft


class Review(BaseModel):
    score: int        # 1-10
    feedback: str     # specific, actionable improvements


def build_crew() -> Crew:
    researcher = Agent(
        role="Research Analyst",
        goal="Collect accurate, relevant facts about {topic}",
        backstory="You are a careful analyst who separates well-established facts from speculation.",
        llm=llm, verbose=True,
    )
    writer = Agent(
        role="Content Writer",
        goal="Turn research notes into a clear, engaging short article about {topic}",
        backstory="You write concise, well-structured explainers for a technical but busy audience.",
        llm=llm, verbose=True,
    )
    reviewer = Agent(
        role="Editor and Reviewer",
        goal="Critically assess a draft for accuracy, clarity and completeness",
        backstory="You are a tough but fair editor who gives specific, actionable feedback.",
        llm=llm, verbose=True,
    )

    research_task = Task(
        description="Research {topic}. List 6-8 key facts, each with a one-line explanation.",
        expected_output="A bullet list of 6-8 facts with short explanations.",
        agent=researcher,
    )
    write_task = Task(
        description=(
            "Using the research notes, write an article of about 300 words on {topic} "
            "with an intro, body and conclusion. "
            "Reviewer feedback on a previous draft (ignore if it says 'none'): {feedback}"
        ),
        expected_output="An article of about 300 words in markdown, ending with a '## Key Takeaways' section.",
        agent=writer,
        context=[research_task],
        guardrail=validate_draft,
        guardrail_max_retries=3,
    )
    review_task = Task(
        description="Review the draft. Give a score from 1-10 and specific feedback on what to improve.",
        expected_output="A score (1-10) and actionable feedback.",
        agent=reviewer,
        context=[write_task],
        output_pydantic=Review,
    )

    return Crew(
        agents=[researcher, writer, reviewer],
        tasks=[research_task, write_task, review_task],
        process=Process.sequential,
        verbose=True,
    )