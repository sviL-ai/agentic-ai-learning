# Crew + Flow with a guardrail, a router and persistence

A CrewAI project that writes a short article through a **researcher → writer → reviewer** crew, then wraps that crew in a **Flow** that sends weak drafts back for rework. The Flow's state is persisted, so an interrupted run can be resumed by its id.

## Setup

```powershell
mkdir d5-crewai
cd d5-crewai
uv init --bare --no-workspace --python 3.12
uv add crewai
```

## Run
 
```powershell
uv run flow.py                                   # fresh run
uv run flow.py --topic "vector databases" --min-score 8
uv run flow.py --resume <run-id>                 # resume a saved run
```

## How it works
 
**Crew (`crew.py`).** Three agents, three tasks, `Process.sequential`. Task order in the list is the execution order, and each task passes its output to the next through `context`. The reviewer returns a structured `Review` (`score`, `feedback`) via `output_pydantic`, so the router reads a field instead of parsing prose. `build_crew()` creates fresh agents and tasks on every call.
 
**Guardrail (`guardrails.py`).** A function on the writer's task checks that the draft is 250-350 words and has a `## Key Takeaways` section. On failure it returns `(False, feedback)` and the writer retries, up to `guardrail_max_retries=3`. That means up to 4 attempts in total (1 initial + 3 retries). If all fail, CrewAI raises an exception, which the Flow catches and treats as a score of 0.
 
**Flow (`flow.py`).** Typed state (`topic`, `feedback`, `draft`, `score`, `attempts`, `max_attempts`, `min_score`).
 
- `@start` `intake` prints the run id.
- `run_crew` runs the crew, listening to both `intake` and the `"rework"` label, which forms the loop.
- `@router` `check_quality` returns `"approved"` if `score >= min_score`, `"give_up"` once `attempts >= max_attempts`, otherwise `"rework"`.
- On rework, the reviewer's feedback is passed back into the writer's task through `{feedback}`.
**Persistence.** The class is decorated with `@persist()`, which saves the state to a local SQLite database as the Flow runs. `--resume <run-id>` calls `kickoff(restore_from_state_id=...)`, which loads the saved state and records the new run under a fresh `state.id` (a fork).

## Run where a guardrail and rework was forced

[View trace](https://app.crewai.com/crewai_plus/ephemeral_traces/cf3f325b-70dd-4da8-a137-50cc8285a43f)

What happened: The Flow started and ran the crew, but the `writer` failed the word-limit guardrail on all 4 attempts (1 initial + 3 retries), so the crew raised an error and the Flow recorded a score of 0. `check_quality` then routed to `rework`, and the same thing happened on two more crew attempts. Once `max_attempts` (3) was reached, the router returned `give_up` and `escalate` ran.