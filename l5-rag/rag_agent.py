from pathlib import Path

from langchain.agents import create_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import create_retriever_tool

# importing rag.py runs ingestion (skipped if the DB exists) and gives us the retriever + model
from rag import model, retriever

# 1. turn the retriever into a tool
search_docs = create_retriever_tool(
    retriever,
    name="search_company_docs",
    description=(
        "Search the company policy documents (leave, expenses, remote work, IT security). "
        "Use it for any question about company rules. Input is a short search query."
    ),
    # what the agent sees for each chunk -> includes the source for citations
    document_prompt=PromptTemplate.from_template("[source: {source}]\n{page_content}"),
)

# 2. give the tool to an agent
agent = create_agent(
    model,
    tools=[search_docs],
    system_prompt=(
        "You are an HR assistant. For company-policy questions, use the search tool "
        "and answer ONLY from what it returns. If the docs don't contain the answer, "
        "say you don't know. Cite the source file names you used. "
        "For greetings or general chat, answer directly without searching."
    ),
)


def ask(question: str) -> None:
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    print("\n" + "=" * 60)
    print("Q:", question)

    # show what the agent decided to do
    searches = 0
    for m in result["messages"]:
        for call in getattr(m, "tool_calls", []) or []:
            searches += 1
            print(f"  [search #{searches}] query = {call['args'].get('query')!r}")
    if searches == 0:
        print("  [no search]")

    print("A:", result["messages"][-1].content)


if __name__ == "__main__":
    # ask("Hi there!")                                                         # should NOT search
    # ask("How many days of annual leave do I get?")                           # one search
    # ask("Can I carry over leave, and how many sick days do I get?")          # likely two searches
    ask("If I fly for 8 hours, which class can I book and what meal limit applies? How many days of annual leave do I get?")  # likely two searches
    # ask("What is the policy on pets in the office?")                         # search, then "I don't know"