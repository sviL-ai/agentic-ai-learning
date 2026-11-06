import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_classic.chains import ConversationChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate

load_dotenv()

SYSTEM_PROMPT = (
    "You are a friendly assistant. Keep answers short. "
    "Use what the user told you earlier in the conversation."
)

init_chat_model(
    "auto",
    model_provider="openai",
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
    base_url=os.environ["LLM_GATEWAY_BASE_URL"]
)

# ConversationChain requires exactly these two variables: history, input
prompt = PromptTemplate(
    input_variables=["history", "input"],
    template=SYSTEM_PROMPT + "\n\nConversation so far:\n{history}\n\nHuman: {input}\nAI:",
)

chain = ConversationChain(
    llm=init_chat_model(),
    memory=ConversationBufferMemory(),   # lives inside this Python process
    prompt=prompt,
)

print("Legacy chatbot. Type 'exit' to quit, 'mem' to see the raw history.")
while True:
    text = input("you> ").strip()
    if text == "exit":
        break
    if text == "mem":
        print(chain.memory.buffer)   # the plain string that gets pasted into {history}
        continue
    print("bot>", chain.invoke({"input": text})["response"])