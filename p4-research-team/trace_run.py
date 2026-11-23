import sys
from coordinator import coordinator

config = {"configurable": {"thread_id": sys.argv[1]}}
history = list(coordinator.get_state_history(config))[::-1]  # oldest first

FIELDS = ["company", "research_notes", "analysis", "brief"]
prev = {}

for snap in history:
    vals = snap.values
    msgs = vals.get("messages", [])
    step = snap.metadata.get("step")

    line = "(start)"
    if msgs:
        m = msgs[-1]
        if m.type == "human":
            line = f"HUMAN: {str(m.content)[:80]}"
        elif m.type == "ai" and m.tool_calls:
            calls = ", ".join(f"{tc['name']}({tc['args']})" for tc in m.tool_calls)
            line = f"COORDINATOR calls: {calls}"
        elif m.type == "ai":
            line = f"COORDINATOR replies: {str(m.content)[:80]}"
        elif m.type == "tool":
            line = f"TOOL RESULT ({m.name}): {str(m.content)[:80]}"

    changed = [f for f in FIELDS if vals.get(f) and vals.get(f) != prev.get(f)]
    print(f"step {step}: {line}   [next: {snap.next}]")
    if changed:
        sizes = ", ".join(f"{f} ({len(vals[f])} chars)" for f in changed)
        print(f"         state written: {sizes}")
    prev = {f: vals.get(f) for f in FIELDS}