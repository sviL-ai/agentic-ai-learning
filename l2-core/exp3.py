from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.messages import SystemMessage, HumanMessage, AIMessage

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a support agent for {company}. Be concise."),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])

messages = prompt.invoke({
    "company": "Acme",
    "history": [
        HumanMessage("Where is order 7?"),
        AIMessage("It's in transit."),
    ],
    "question": "Okay, and can I return order 123?",
}).to_messages()

print(messages)