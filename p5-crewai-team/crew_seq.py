import sys

from crewai import Crew, Process

from agents import analyst, researcher, writer
from tasks import analysis_task, research_task, writing_task

crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, writing_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    request = " ".join(sys.argv[1:])
    result = crew.kickoff(inputs={"request": request})
    print(result.raw)