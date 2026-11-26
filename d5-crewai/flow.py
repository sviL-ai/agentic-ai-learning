import argparse
import os
from pydantic import BaseModel
from crewai.flow.flow import Flow, listen, router, start, or_
from crewai.flow.persistence import persist
from crew import build_crew

class ArticleState(BaseModel):
    topic: str = ""
    feedback: str = "none"   # reviewer feedback fed into the next attempt
    draft: str = ""
    score: int = 0
    attempts: int = 0
    max_attempts: int = 3    # loop budget, so rework can't run forever
    min_score: int = 8       # below this the draft counts as weak

@persist()
class ArticleFlow(Flow[ArticleState]):

    @start()
    def intake(self):
        print(f"\n[flow] run id: {self.state.id}")
        print(f"\n[flow] starting on topic: {self.state.topic}")

    @listen(or_(intake, "rework"))
    def run_crew(self):
        nxt = self.state.attempts + 1
        if os.environ.get("CRASH_ON_ATTEMPT") == str(nxt):   # demo only
            raise RuntimeError(f"simulated crash before attempt {nxt}")

        self.state.attempts = nxt
        print(f"\n[flow] crew attempt {nxt}")
        try:
            result = build_crew().kickoff(
                inputs={"topic": self.state.topic, "feedback": self.state.feedback}
            )
        except Exception as e:  # e.g. the writer exhausted its guardrail retries
            print(f"[flow] crew failed: {e}")
            self.state.score = 0
            self.state.feedback = f"The previous attempt failed validation: {e}"
            return
        self.state.draft = result.tasks_output[1].raw   # the writer's draft
        self.state.score = result.pydantic.score        # the reviewer's verdict
        self.state.feedback = result.pydantic.feedback

    @router(run_crew)
    def check_quality(self):
        print(f"[flow] score {self.state.score} (need {self.state.min_score})")
        if self.state.score >= self.state.min_score:
            return "approved"
        if self.state.attempts >= self.state.max_attempts:
            return "give_up"
        return "rework"

    @listen("approved")
    def publish(self):
        print(f"\n[flow] APPROVED after {self.state.attempts} attempt(s)\n")
        return self.state.draft

    @listen("give_up")
    def escalate(self):
        print(f"\n[flow] gave up after {self.state.attempts} attempts, last score {self.state.score}")
        return self.state.draft


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", metavar="RUN_ID", help="resume from a saved run id")
    parser.add_argument("--topic", default="retrieval-augmented generation")
    parser.add_argument("--min-score", type=int, default=9)
    args = parser.parse_args()

    flow = ArticleFlow()
    if args.resume:
        result = flow.kickoff(restore_from_state_id=args.resume)
    else:
        result = flow.kickoff(inputs={"topic": args.topic, "min_score": args.min_score})

    print("\n=== FINAL DRAFT ===\n", result)