# d1-chatbot: legacy memory vs v1 stateful agents

The same chatbot and system prompt, built three ways. Only the memory mechanism changes.

- **a)** `ConversationChain` + `ConversationBufferMemory` (legacy, `langchain-classic`)
- **b)** `create_agent` + `InMemorySaver` + `thread_id`
- **c)** `create_agent` + `PostgresSaver` (Docker Postgres) + `thread_id`

## Comparison

| | a) Legacy | b) v1 + InMemorySaver | c) v1 + PostgresSaver |
|---|---|---|---|
| Who owns history | memory object attached to the chain | agent state, saved by a checkpointer | agent state, saved by a checkpointer |
| Format of history | one text string pasted into the prompt | list of typed messages | list of typed messages |
| Separating conversations | none: one chain is one conversation | `thread_id` in the call config | `thread_id` in the call config |
| Where it is stored | RAM inside the chain | RAM inside the saver | Postgres (Docker volume) |
| Survives a restart | No | No | **Yes** |
| What changed vs previous step | n/a | memory moved from the chain to graph state | only the checkpointer, connection handling and a one-time `setup()` |
| Production fit | No: tied to one process and one conversation | No: fine for tests and demos | **Yes**, with a connection pool, history trimming and a retention policy |

## Takeaway

Going from (b) to (c) required no change to the agent's logic, because the agent only asks the checkpointer to save or load state for a `thread_id`. That separation of agent and storage is the main advantage of the v1 design over (a), where memory and chain are one object.

(c) survives a restart because the conversation state is written to Postgres, which runs in its own container with its own volume. When the app exits, the process memory is gone but the rows remain, and the next run with the same `thread_id` loads the last snapshot and continues the conversation.

For production I would use (c): a database-backed checkpointer, `thread_id` built from user and conversation ids, and trimming or summarizing of old messages so history does not grow without limit.