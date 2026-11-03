import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel

# Load environment variables
repo_root = Path(__file__).resolve().parents[1]
load_dotenv(repo_root / ".env")


llm_summary = init_chat_model(
            "auto",
            model_provider="openai",
            api_key=os.environ["LLM_GATEWAY_API_KEY"],
            base_url=os.environ["LLM_GATEWAY_BASE_URL"],
            temperature=0)

llm_quiz = init_chat_model(
            "auto",
            model_provider="openai",
            api_key=os.environ["LLM_GATEWAY_API_KEY"],
            base_url=os.environ["LLM_GATEWAY_BASE_URL"],
            temperature=0.9)

parser = StrOutputParser()

# Branch 1: summary
summary_prompt = PromptTemplate.from_template(
    "Give a short and clear summary about {country}."
)
summary_chain = summary_prompt | llm_summary | parser

# Branch 2: quiz
quiz_prompt = PromptTemplate.from_template(
    "Generate 5 interesting quiz questions based on {country}."
)
quiz_chain = quiz_prompt | llm_quiz | parser

# Run both branches at the same time on the same input
parallel_chain = RunnableParallel({
    "summary": summary_chain,
    "quiz": quiz_chain,
})

result = parallel_chain.invoke({"country": "Australia"})

# Print the output nicely
print("Summary:\n", result["summary"])
print("\nQuiz Questions:\n", result["quiz"])