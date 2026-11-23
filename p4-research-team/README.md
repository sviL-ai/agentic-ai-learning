# p4: Multi-agent company research team

A coordinator agent that turns a company name into a one-page company brief
(overview, products and services, likely AI needs, outreach angle). It uses the
**subagents-as-tools** pattern: three specialist agents (researcher, analyst,
writer) are wrapped as tools, and the coordinator calls them in order. They
share one state, so large text never passes through the coordinator.

## Architecture

```
 user: "I need a brief on <company>"
          │
          ▼
 ┌──────────────────────────────┐
 │ Coordinator (create_agent)   │  checkpointer: SqliteSaver (thread_id per run)
 │ limit: 8 model calls per run │  state: TeamState
 └──┬────────────┬────────────┬─┘
    ▼            ▼            ▼
 research_    analyze_     write_
 company      company      brief            each tool wraps a create_agent
    │            │            │
 researcher   analyst       writer
 web_search   (no tools)    save_brief
 limit 8      limit 3       limit 5
```

### Shared state (`TeamState`)

| Field | Written by | Read by |
|---|---|---|
| `messages` | everyone | coordinator |
| `company` | `research_company` | `write_brief` |
| `research_notes` | `research_company` | `analyze_company`, `write_brief` |
| `analysis` | `analyze_company` | `write_brief` |
| `brief` | `write_brief` | `main.py` |

Specialist tools return a `Command(update=...)` so their output lands in these
fields, plus a short `ToolMessage` so the coordinator's tool call is answered.

### Files

| File | Purpose |
|---|---|
| `state.py` | `TeamState` shared state |
| `model.py` | shared LLM gateway model |
| `prompts.py` | system prompts for all four agents |
| `tools.py` | `web_search` (Tavily) and `save_brief` |
| `subagent_tools.py` | researcher, analyst and writer agents, and the tools that wrap them |
| `coordinator.py` | coordinator agent, SQLite checkpointer, call limit |
| `main.py` | entry point: one request, one run, one `thread_id` |
| `trace_run.py` | prints a readable trace of a saved run from the checkpoints |

## How to run

```powershell
uv sync
uv run python main.py
```

Briefs are written to `briefs/<company>.md`. The run prints its `thread_id`.

To print the trace of a saved run:

```powershell
uv run python trace_run.py <thread_id>
```

## The three briefs

- [Company 1](briefs/<company-1>.md)
- [Company 2](briefs/<company-2>.md)
- [Company 3](briefs/<company-3>.md)

## Trace of one run

LangSmith trace: [[link](https://smith.langchain.com/public/6bb0e741-1528-484b-98d9-a271552a768a/r/01a206d7-2da4-7c42-a435-df4db77d6ed6?start_time=2026-11-23T05%3A18%3A14.947251Z)]


### Coordinator trace (from the checkpoints)

```
HUMAN: I need a brief on iLeaf solutions
COORDINATOR calls: research_company({'company': 'iLeaf solutions'})
TOOL RESULT (research_company): Research on iLeaf solutions is complete and saved to research_notes.
    state written: company (15 chars), research_notes (8234 chars)
COORDINATOR calls: analyze_company({})
TOOL RESULT (analyze_company): Analysis is complete and saved to analysis.
    state written: analysis (3715 chars)
COORDINATOR calls: write_brief({})
TOOL RESULT (write_brief): Brief written and saved. Do not call any more tools...
    state written: brief (2273 chars)
COORDINATOR replies: The company brief for iLeaf solutions is ready.
```

The raw checkpoint history has 17 snapshots for these 9 events.
`ModelCallLimitMiddleware` adds a checkpoint before and after every model
call, and those snapshots add no new message. `trace_run.py` hides them.
Each tool was called exactly once, in order, and each state field was written
exactly once.

The checkpoints only show the coordinator. What happens **inside** each
specialist (the searches, the model calls, the `save_brief` call) is visible in
the LangSmith trace, where each specialist run is nested under its tool call.

## Handoffs explained

| # | Handoff | What is passed | How | State after |
|---|---|---|---|---|
| 1 | User → coordinator | A natural-language request | `invoke` with a message | `messages` |
| 2 | Coordinator → researcher | Only the company name | Tool-call argument. The researcher starts a fresh conversation and does not see the coordinator's history | unchanged |
| 3 | Researcher → coordinator | A short confirmation | `ToolMessage` inside a `Command` | `company`, `research_notes` written |
| 4 | Coordinator → analyst | Nothing | `analyze_company()` has no arguments; it reads `research_notes` from state via `runtime.state` | unchanged |
| 5 | Analyst → coordinator | A short confirmation | `Command` | `analysis` written |
| 6 | Coordinator → writer | Nothing | `write_brief()` reads `research_notes`, `analysis` and `company` from state | unchanged |
| 7 | Writer → file and state | The finished brief | The writer calls `save_brief`, which writes `briefs/<company>.md`; the wrapper copies the brief from that tool call into state | `brief` written |
| 8 | Coordinator → user | One sentence | `main.py` prints the brief from `out["brief"]`, not from the coordinator's message | unchanged |

**Why it is built this way**

- **Handoffs 3, 5 and 7 pass big text through state, not through the
  coordinator.** The coordinator only sees short confirmations, so its context
  stays small. The 8,234-character research notes never enter its messages.
- **Handoffs 4 and 6 pass nothing.** The analyst and writer read what they
  need from state. Their tools refuse to run (and say which step is missing)
  if the earlier fields are empty, which protects against calls in the wrong
  order.
- **Every `Command` includes a `ToolMessage`.** The coordinator's tool call
  must be answered or the next model call fails. The confirmation text also
  says what to do next ("Next step: call analyze_company"), which keeps the
  coordinator moving in order.
- **Each specialist has its own prompt and tools.** Only the researcher has
  `web_search`, and only the writer has `save_brief`. The analyst has no tools
  because its job is pure reasoning over the notes.

## Guards

| Guard | Where | Purpose |
|---|---|---|
| `ModelCallLimitMiddleware(run_limit=8)` | coordinator | caps one run at 8 model calls |
| `ModelCallLimitMiddleware(run_limit=8)` | researcher | caps searches inside one research call |
| `ModelCallLimitMiddleware(run_limit=3)` | analyst | caps a stuck analysis |
| `ModelCallLimitMiddleware(run_limit=5)` | writer | allows write plus save plus confirmation, nothing more |
| Ordering guards in `analyze_company` and `write_brief` | tools | refuse to run if inputs are missing |
| `main.py` checks `out["brief"]` | entry point | a run only counts as success if the brief exists in state |
| `SqliteSaver` + `thread_id` | coordinator | every step is saved and can be inspected or resumed |

The limits sit about 2x above a normal run, so normal runs never hit them and
a runaway stops quickly. A limit only caps the agent it is attached to, which
is why each specialist has its own. The coordinator's limit alone would not
stop a researcher stuck inside one tool call.