from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from graph import build

app = build().compile(checkpointer=InMemorySaver())

def cfg(thread):  return {"configurable": {"thread_id": thread}}
def short(s, n=70): return s.strip().replace("\n", " ")[:n]
def banner(t):    print(f"\n{'=' * 8} {t} {'=' * 8}")

def run(inp, config):
    """Stream one run, print what each node wrote, return the interrupt payload (None if finished)."""
    payload = None
    for chunk in app.stream(inp, config, stream_mode="updates"):
        for node, update in chunk.items():
            if node == "__interrupt__":
                payload = update[0].value
                print("   ** PAUSED at human_review **")
            else:
                print(f"   {node:12} wrote {list(update.keys())}")
    return payload

# ---------------------------------------------------------------
banner("1. TYPED STATE + CONDITIONAL ROUTING + THREADS")
# Each ticket gets its own thread_id. Watch which branch node fires per input.
tickets = {
    "billing-thread": "I was charged twice for my invoice this month",
    "tech-thread":    "The app crashes with error 500 when I upload a file",
    "general-thread": "What are your support hours?",
}
for thread, text in tickets.items():
    print(f"\n[{thread}] {text}")
    p = run({"messages": [("user", text)]}, cfg(thread))
    print(f"   category={p['category']} | draft: {short(p['draft'])}")

print("\nThread isolation (saved state per thread):")
for thread in tickets:
    s = app.get_state(cfg(thread))
    print(f"   {thread:15} messages={len(s.values['messages'])} "
          f"category={s.values['category']} next={s.next}")

# ---------------------------------------------------------------
banner("2. INTERRUPT + Command(resume=...)")
s = app.get_state(cfg("billing-thread"))
print("billing-thread paused. next =", s.next, "| sent =", s.values.get("sent"))

print("\n[billing-thread] resume: approve with an edited reply")
run(Command(resume={"action": "approve", "text": "Hi! We've refunded the duplicate charge."}),
    cfg("billing-thread"))
print("   sent =", app.get_state(cfg("billing-thread")).values.get("sent"))

print("\n[tech-thread] resume: reject")
run(Command(resume={"action": "reject"}), cfg("tech-thread"))
s = app.get_state(cfg("tech-thread")).values
print("   approved =", s.get("approved"), "| sent =", s.get("sent"))
# general-thread is deliberately left paused

# ---------------------------------------------------------------
banner("3. TIME TRAVEL on billing-thread")
c = cfg("billing-thread")
target = next(s for s in app.get_state_history(c) if s.next == ("billing",))
print("target checkpoint (classify done, billing not yet run):",
      target.config["configurable"]["checkpoint_id"])

print("\nREPLAY unchanged  (classify must NOT appear below)")
p = run(None, target.config)
print(f"   category={p['category']} | new draft: {short(p['draft'])}")

print("\nFORK: change the decision billing -> tech")
fork_cfg = app.update_state(target.config, {"category": "tech"}, as_node="classify")
p = run(None, fork_cfg)
print(f"   category={p['category']} | draft: {short(p['draft'])}")
print("\n   resume the forked branch (approve)")
run(Command(resume={"action": "approve"}), c)

# ---------------------------------------------------------------
banner("4. CHECKPOINT TREE for billing-thread (newest first)")
for s in app.get_state_history(c):
    cid = s.config["configurable"]["checkpoint_id"][-6:]
    pid = (s.parent_config or {}).get("configurable", {}).get("checkpoint_id", "")[-6:] or "-"
    print(f"   id=..{cid} parent=..{pid:6} next={str(s.next):18} category={s.values.get('category')}")