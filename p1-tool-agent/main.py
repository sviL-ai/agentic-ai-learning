import ast
import math
import os
import operator
import requests
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from tavily import TavilyClient

load_dotenv()

model = init_chat_model(
    "auto",
    model_provider="openai",
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
    base_url=os.environ["LLM_GATEWAY_BASE_URL"]
)

SYSTEM_PROMPT = """You are a research assistant. Use your tools for weather, arithmetic and
current facts instead of answering from memory. If a tool fails, fix your input and retry
once, then say what failed. Keep the answer short and cite source URLs for web claims."""

class FinalAnswer(BaseModel):
    answer: str = Field(description="Short final answer to the user's question")
    tools_used: list[str] = Field(description="Names of the tools called")
    sources: list[str] = Field(default_factory=list, description="URLs used, if any")

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
}
_CONSTANTS = {"pi": math.pi, "e": math.e}
 
 
def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name) and node.id in _CONSTANTS:
        return _CONSTANTS[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("Exponent too large.")
        return _BINARY_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _FUNCTIONS
        and not node.keywords
    ):
        return _FUNCTIONS[node.func.id](*[_eval_node(a) for a in node.args])
    raise ValueError("Unsupported expression.")
 
 
@tool
def calculator(expression: str) -> dict:
    """Evaluate a math expression exactly. Use this for ANY arithmetic instead
    of computing in your head (differences, percentages, unit conversions).
 
    Supports + - * / // % ** , parentheses, the constants pi and e, and the
    functions sqrt, abs, round, min, max, log, log10, sin, cos, tan.
 
    Args:
        expression: A plain math expression, e.g. "31.5 - 20" or "sqrt(144) * 3".
    """
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval_node(tree.body)
        return {"expression": expression, "result": result}
    except ZeroDivisionError:
        return {"error": "Division by zero."}
    except (ValueError, TypeError, SyntaxError, OverflowError) as e:
        # Returned as data so the agent can fix its expression and retry.
        return {"error": f"Could not evaluate '{expression}': {e}"}

@tool
def get_weather(city: str) -> dict:
    """Get the current real-time weather and today's forecast for a city.
 
    Args:
        city: City name only, e.g. "Kochi" or "Berlin". Do not include
              country or state (the geocoder matches city names best).
    """
    # Be forgiving if the model sends "Kochi, India": keep the part before the comma.
    name = city.split(",")[0].strip()
 
    try:
        # Step 1: city name -> coordinates
        geo = requests.get(
            GEOCODE_URL,
            params={"name": name, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        geo.raise_for_status()
        results = geo.json().get("results")
        if not results:
            return {"error": f"Could not find a place called '{name}'. Try a different spelling."}
        place = results[0]
 
        # Step 2: coordinates -> weather
        wx = requests.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                           "precipitation,weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": 1,
                "timezone": "auto",
            },
            timeout=10,
        )
        wx.raise_for_status()
        data = wx.json()
        cur, daily = data["current"], data["daily"]
 
        return {
            "location": f"{place['name']}, {place.get('admin1', '')}, {place.get('country', '')}",
            "observed_at": cur["time"],
            "temperature_c": cur["temperature_2m"],
            "feels_like_c": cur["apparent_temperature"],
            "humidity_percent": cur["relative_humidity_2m"],
            "wind_kmh": cur["wind_speed_10m"],
            "precipitation_mm": cur["precipitation"],
            "today_high_c": daily["temperature_2m_max"][0],
            "today_low_c": daily["temperature_2m_min"][0],
            "today_rain_chance_percent": daily["precipitation_probability_max"][0],
        }
 
    except requests.RequestException as e:
        # Return the error as data so the agent can explain or retry,
        # instead of crashing the whole run.
        return {"error": f"Weather service request failed: {e}"}
 

@tool
def web_search(query: str) -> dict:
    """Search the web for current or factual information (news, recent events,
    facts you are unsure about). Returns a short list of results, each with a
    title, url and content snippet.

    Args:
        query: A concise search query, e.g. "Kerala monsoon latest news".
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return {"error": "TAVILY_API_KEY is not set."}

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query, max_results=3, search_depth="basic")
    except Exception as e:
        return {"error": f"Web search failed: {e}"}

    return {
        "query": query,
        "results": [
            {"title": r["title"], "url": r["url"], "content": r["content"]}
            for r in response.get("results", [])
        ],
    }

agent = create_agent(
    model=model,
    tools=[calculator, get_weather, web_search],
    system_prompt=SYSTEM_PROMPT,
    response_format=FinalAnswer,
    name="p1_tool_agent",
)

question = "What’s the weather in Nowhereville123, and how many degrees warmer is it than 20°C? Also find one recent news headline about the Kerala monsoon."
result = agent.invoke(
    {"messages": [{"role": "user", "content": question}]},
    config={"recursion_limit": 15},
)

print(result["structured_response"])