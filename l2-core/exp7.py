import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import (
    RunnableParallel,
    RunnablePassthrough,
    RunnableSequence,
)

# Load environment variables
repo_root = Path(__file__).resolve().parents[1]
load_dotenv(repo_root / ".env")

llm = init_chat_model(
    "auto",
    model_provider="openai",
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
    base_url=os.environ["LLM_GATEWAY_BASE_URL"],
    temperature=0,
)

# Output parser
parser = StrOutputParser()

# Step 1: Summary chain. Input: {"country": ...}  ->  Output: summary text (a string)
summary_prompt = PromptTemplate.from_template(
    "Give a short and clear summary about {country}."
)
summary_chain = summary_prompt | llm | parser

# Step 2a: Quiz chain. Input: the summary text (a string)  ->  Output: quiz text
quiz_prompt = PromptTemplate.from_template(
    "Generate 5 interesting quiz questions based on the following text:\n\n{text}"
)
# The incoming value is a plain string, so we wrap it as {"text": <string>} for the prompt.
quiz_chain = {"text": RunnablePassthrough()} | quiz_prompt | llm | parser

# Step 2b: Run two things on the summary at the same time:
#   - "summary": RunnablePassthrough keeps the summary unchanged, so we don't lose it
#   - "quiz":    generates questions from that same summary
parallel_chain = RunnableParallel({
    "summary": RunnablePassthrough(),
    "quiz": quiz_chain,
})

# Step 1 feeds step 2
combined_chain = RunnableSequence(summary_chain, parallel_chain)

# Run the chain
result = combined_chain.invoke({"country": "Australia"})

# Print the output nicely
print("Summary:\n", result["summary"])
print("\nQuiz Questions:\n", result["quiz"])