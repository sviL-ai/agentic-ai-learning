# Legal Chatbot (LangGraph)

A chatbot restricted to Indian law, rebuilt in LangGraph from a Flowise chatflow.

## Workflow

```
User question → agent (LLM) ──needs sources?──→ web search (Exa/Tavily) ──┐
                    ↑                                              │
                    └──────────────────────────────────────────────┘
                    │
                    └── answer (with citations)
```

1. The user asks a question. Conversation history is kept per session (memory).
2. The agent, guided by the legal-domain system prompt, decides whether to search the web.
3. If it searches, results come back to the agent, which can search again or answer.
4. Out-of-scope (non-legal) questions are politely declined by the prompt.

## Run

```powershell
uv add langgraph langchain-openai langchain-tavily exa-py python-dotenv
uv run agent.py
```

## View the Flowise vs LangGraph comparison

Download [`comparison.html`](comparison.html) and open it in your browser to see both systems' answers.