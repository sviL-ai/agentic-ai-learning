import time
import uuid

from coordinator import coordinator


def main():
    user = input("What would you like a brief on? ").strip()
    if not user:
        print("No input given.")
        return

    thread_id = f"brief-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    print("thread_id:", thread_id)
    config = {"configurable": {"thread_id": thread_id}}

    start = time.time()
    out = coordinator.invoke(
        {"messages": [{"role": "user", "content": user}]},
        config,
    )
    elapsed = time.time() - start

    print("\nCoordinator:", out["messages"][-1].content)

    brief = out.get("brief")
    if brief:
        print("\n" + brief)
    else:
        print("\n(No brief was produced. See the coordinator's reply above.)")

    print(f"\nthread_id: {thread_id}  |  {elapsed:.0f}s")


if __name__ == "__main__":
    main()