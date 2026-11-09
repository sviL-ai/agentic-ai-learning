# d2-middleware: controlling the agent loop with custom middleware

A LangChain agent (`create_agent`) with four pieces of middleware that hook into
the agent loop. Each one is demonstrated with a run in LangSmith.

**Tools:** `get_order_status` (safe), `send_email` (risky, needs approval)

## Use cases and traces

| # | Middleware | What it does | LangSmith trace |
|---|-----------|--------------|-----------------|
| 1 | `@before_model` message trimmer | Keeps the first message plus the last 4 before each model call | [View trace](https://smith.langchain.com/public/05bb8b53-244a-4ea6-92ef-4bc3ca2db67d/r/01a1bfdd-2e7b-77e1-8ea0-a16672e918af?start_time=2026-11-09T10%3A31%3A46.036325Z) |
| 2 | `wrap_tool_call` logger (success) | Logs tool name, args, duration and error for a successful call | [View trace](https://smith.langchain.com/public/48957b33-8750-42f7-9f2b-bbd3c4976975/r/01a1bfdf-de99-7c10-8fad-9e7ab8b7c5a7?start_time=2026-11-09T10%3A34%3A42.20171Z) |
| 3 | `wrap_tool_call` logger (error) | Same log for a tool that raises an error | [View trace](https://smith.langchain.com/public/0b9a65eb-6cf7-44a7-9036-9239c824cc81/r/01a1bfe2-0422-7f81-91f9-4a69d53a4d49?start_time=2026-11-09T10%3A37%3A02.870794Z) |
| 4 | `@dynamic_prompt` (admin) | System prompt for the `admin` role, read from runtime context | [View trace](https://smith.langchain.com/public/648111c7-a26f-4891-9039-30d6fc789113/r/01a1bfe3-373f-7c00-84ba-863d6694abaa?start_time=2026-11-09T10%3A38%3A21.501091Z) |
| 5 | `@dynamic_prompt` (customer) | Same question, different system prompt for the `customer` role | [View trace](https://smith.langchain.com/public/07e3e035-3c6b-4478-bc80-ef9fdef772ff/r/01a1bfe5-392c-73a2-8a8e-1e501634b1b8?start_time=2026-11-09T10%3A40%3A33.068555Z) |
| 6 | `HumanInTheLoopMiddleware` (approve) | `send_email` pauses, reviewer approves, tool runs with the original args | [Before interruption](https://smith.langchain.com/public/dc1ab473-e6ed-4dee-b8bc-d88bf65ebfa2/r/01a1bfe5-f768-7cd3-adfb-18fe8dda82d2?start_time=2026-11-09T10%3A41%3A21.768158Z) [After interruption](https://smith.langchain.com/public/aaf912ae-cff4-4a37-b19d-6c8e88f6d06e/r/01a1bfe5-fe24-7671-bc29-403c4cbfe9b5?start_time=2026-11-09T10%3A41%3A23.48797Z) |
| 7 | `HumanInTheLoopMiddleware` (edit) | Reviewer changes the recipient, tool runs with the edited args | [Before interruption](https://smith.langchain.com/public/1c0fd939-0902-4a9b-b8e5-3c244814d192/r/01a1bfed-3cad-7d13-9d68-0b4a122b1d67?start_time=2026-11-09T10%3A49%3A18.253564Z) [After interruption](https://smith.langchain.com/public/89b6817b-87f5-4778-99fb-fabbf64b5a08/r/01a1bfed-44d3-7ee0-b8ae-4a32c31fc1f5?start_time=2026-11-09T10%3A49%3A20.33955Z) |
| 8 | `HumanInTheLoopMiddleware` (reject) | Reviewer rejects, the tool never runs | [Before interruption](https://smith.langchain.com/public/5a743ce5-9eee-47e6-bb2e-8edcbe550b58/r/01a1bfef-ab4c-7dc1-bfdf-c79d5830cac2?start_time=2026-11-09T10%3A51%3A57.64274Z) [After interruption](https://smith.langchain.com/public/84f7b707-b078-422d-a154-e12e082060db/r/01a1bff0-c3e6-7fd1-a872-c5ce0219ee79?start_time=2026-11-09T10%3A53%3A09.46762Z) |
