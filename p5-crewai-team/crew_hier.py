import sys

from crewai import Crew, Process

from agents import analyst, manager, researcher, writer
from tasks import research_task, analysis_task, writing_task

crew = Crew(
    agents=[researcher, analyst, writer],  # the manager is NOT listed here
    tasks=[research_task, analysis_task, writing_task],
    process=Process.hierarchical,
    manager_agent=manager,
    verbose=True,
)

if __name__ == "__main__":
    request = " ".join(sys.argv[1:])
    result = crew.kickoff(inputs={"request": request})
    print(result.raw)