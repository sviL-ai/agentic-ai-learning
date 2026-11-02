from langchain_core.messages import (
    SystemMessage, HumanMessage, AIMessage, ToolMessage, trim_messages,
)

# 1. A conversation is just a list of message objects.
messages = [
    SystemMessage("You are a helpful assistant."),               # rules for the model
    HumanMessage("What's the weather in Paris?"),                # user input
    AIMessage("", tool_calls=[                                   # model asks for a tool
        {"name": "get_weather", "args": {"city": "Paris"}, "id": "call_1", "type": "tool_call"}
    ]),
    ToolMessage("18C, sunny", tool_call_id="call_1"),            # tool result (same id as the call)
    AIMessage("It's 18C and sunny in Paris."),                   # model's final answer
    HumanMessage("And in Tokyo?"),                               # new user question
]

print("--- the conversation ---")
for m in messages:
    print(type(m).__name__, "->", m.content or m.tool_calls)

# 2. content_blocks: a standard, typed view of what is inside an AIMessage.
print("\n--- content_blocks ---")
print("tool-call message:", messages[2].content_blocks)
print("text message     :", messages[4].content_blocks)

# 3. trim_messages: cut old history so the list stays small.
trimmed = trim_messages(
    messages,
    max_tokens=4,          # keep at most 4 messages...
    token_counter=len,     # ...counting each message as 1
    strategy="last",       # keep the most recent ones
    include_system=True,   # always keep the SystemMessage
    start_on="human",      # history must start with a user message
)

print("\n--- after trim_messages ---")
for m in trimmed:
    print(type(m).__name__, "->", m.content)