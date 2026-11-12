# p2-memory-bot

An agent that remembers, the production way. It combines three kinds of memory on one Postgres database:

| Layer | Scope | Tool |
|---|---|---|
| Short-term | one thread | `PostgresSaver` + `thread_id` |
| Context control | one long thread | `SummarizationMiddleware` |
| Long-term | one user, all threads | `PostgresStore` |

A custom `user_id` field is added to the agent state with `state_schema`.

## Setup

```bash
docker compose up -d        # Postgres 16 on localhost:5433
```

`.env`:

```
DB_URI_p2=postgresql://postgres:postgres@localhost:5433/p2memory?sslmode=disable
LLM_GATEWAY_API_KEY=...
LLM_GATEWAY_BASE_URL=...
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=...
```

## Run

```bash
uv run main.py --thread <thread_id> --user <user_id>
```

In-chat commands:

| Command | Shows |
|---|---|
| `/state` | the `user_id` saved in the thread's checkpoint |
| `/messages` | message count and a preview of each message |
| `/prefs` | the preferences saved in the store for this user |

## 1. Restart + resume (short-term memory)

The conversation is checkpointed to Postgres. Stopping the app and starting it again on the same `thread_id` continues the conversation.

```bash
uv run main.py --thread restart-demo --user u1
# PASTE: your first message, the reply, then exit

uv run main.py --thread restart-demo --user u1
# PASTE: the question that tests recall, and the reply
```

![Restart and resume](docs/short-term-memory.png)

**What to notice:** the second run is a new process, yet the bot still knows what was said in the first one. The state lives in Postgres, not in memory.

## 2. Summarised long chat

`SummarizationMiddleware` is configured with `trigger=("messages", 6)` and `keep=("messages", 2)`. The values are small on purpose, so it fires in a short chat. When the message list reaches the trigger, older messages are replaced by a summary and the last two stay verbatim.


![Summary, first snapshot](docs/summary1.png)

![Summary, second snapshot](docs/summary2.png)

**What to notice:**
- The first message in the thread changes from the user's own words to a summary.
- The recall questions after the drop show which facts survived the summary


## 3. Preference remembered across threads (long-term memory)

Preferences are saved with a `save_preference` tool into `PostgresStore`, under the namespace `("users", user_id, "preferences")`. Before every model call, a dynamic prompt reads that namespace and adds the preferences to the system prompt.

```bash
uv run main.py --thread pref-a --user u1
# you> Call me Ravi, and keep your answers short and casual.
# you> /prefs
# PASTE: {'name': 'Ravi', 'tone': 'short and casual'}

uv run main.py --thread pref-b --user u1      # new thread, same user
# you> Explain what a database index is.
# PASTE: reply that greets Ravi and stays short

uv run main.py --thread pref-c --user u2      # different user
# you> Explain what a database index is.
# PASTE: neutral reply, no name
```

![Preference across threads](docs/long-term-memory.png)

**What to notice:**
- `pref-b` has none of the earlier conversation in its history, yet it knows the name and tone. They came from the store, not the checkpointer.
- `pref-c` shows that preferences are isolated per `user_id`.


## Reset the demo

```bash
docker compose down -v && docker compose up -d     # wipes threads and preferences
```