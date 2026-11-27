import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["LLM_GATEWAY_BASE_URL"],
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
)

for i in range(3):
    r = client.chat.completions.create(
        model="auto",
        messages=[{"role": "user", "content": "Reply with exactly one word: pong"}],
        temperature=0.3,
    )
    print(i, "model:", r.model, "| usage:", r.usage)