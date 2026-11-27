from crewai import Task

from agents import analyst, researcher, writer

research_task = Task(
    description=(
        'The user request is: "{request}". Work out which company it refers to '
        "and research that company."
    ),
    expected_output="Structured research findings in the format given in your instructions.",
    agent=researcher,
)

analysis_task = Task(
    description="Analyse the research notes about the company the user asked for.",
    expected_output="Analysis with the sections: Likely AI needs, Outreach angle, Gaps.",
    agent=analyst,
    context=[research_task],
)

writing_task = Task(
    description="Write the one-page company brief for the company in the research notes.",
    expected_output=(
        "A Markdown brief of about 350 words with the sections: Overview, "
        "Products and services, Likely AI needs, Outreach angle."
    ),
    agent=writer,
    context=[research_task, analysis_task],
)