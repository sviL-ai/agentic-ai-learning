# tools.py
import json
from config import get_embeddings
from datetime import datetime
from langgraph.types import interrupt
from langchain_core.tools import tool
from langchain_chroma import Chroma

# open the cabinet we built in ingest.py (no re-embedding of documents)
_store = Chroma(
    collection_name="ileaf",
    embedding_function=get_embeddings(),
    persist_directory="chroma_db",
)


@tool
def search_docs(query: str) -> str:
    """Search iLeaf Solutions' case studies for facts about past projects:
    what was built, for which client or industry, the technology used, and the
    results. Use this for ANY question about iLeaf's work. Pass a short,
    specific search phrase."""
    results = _store.similarity_search(query, k=4)
    if not results:
        return "No relevant documents found."

    blocks = []
    for i, doc in enumerate(results, 1):
        title = doc.metadata.get("title", "untitled")
        url = doc.metadata.get("source", "")
        blocks.append(f"SOURCE: {title} | {url}\n{doc.page_content}")
    return "\n\n---\n\n".join(blocks)

def _send(to: str, subject: str, body: str):
    """Fake 'send': appends to a file. Swap for SMTP / an email API later."""
    with open("outbox.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"sent_at": datetime.now().isoformat(),
                            "to": to, "subject": subject, "body": body}) + "\n")
        
@tool
def draft_email(to: str, subject: str, body: str) -> str:
    """Write an email and send it ONLY after a human reviewer approves.
    Use when the user asks you to email, draft, or write to someone.
    Ground the body in facts from search_docs; do not invent project details.
    You need the recipient's address; ask the user if it wasn't given."""

    # --- pause here; nothing above this line may have side effects ---
    decision = interrupt({
        "type": "email_approval",
        "to": to, "subject": subject, "body": body,
        "options": ["approve", "edit", "reject"],
    })

    action = decision.get("action")
    if action == "reject":
        return f"Email NOT sent. Reviewer rejected it. Reason: {decision.get('reason') or 'none given'}"
    if action == "edit":
        subject = decision.get("subject") or subject
        body = decision.get("body") or body
        to = decision.get("to") or to
    elif action != "approve":
        return f"Email NOT sent. Unknown decision: {action!r}"

    _send(to, subject, body)
    note = " (edited by reviewer)" if action == "edit" else ""
    return f"Email sent to {to} with subject '{subject}'{note}."