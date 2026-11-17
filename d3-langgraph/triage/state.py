from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

Category = Literal["billing", "tech", "general"]

class TriageState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    category: Category
    context: str
    draft: str
    final: str        # text the human approved (possibly edited)
    approved: bool
    sent: bool