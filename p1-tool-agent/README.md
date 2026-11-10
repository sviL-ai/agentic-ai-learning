# p1-tool-agent

A tool-calling agent built with LangChain `create_agent`. It has three real tools and returns a validated, structured final answer. Every run is traced in LangSmith.

## What it does

| Tool | Backend | Purpose |
|---|---|---|
| `get_weather(city)` | Open-Meteo geocoding + forecast APIs (no key) | Current weather and today's high/low for a city |
| `calculator(expression)` | Safe `ast` evaluator (no `eval`) | Exact arithmetic |
| `web_search(query)` | Tavily Search API | Current or factual information from the web |

The final answer is a Pydantic `FinalAnswer` object (`answer`, `tools_used`, `sources`) passed through `response_format`.

## How to run

```bash
export TAVILY_API_KEY=...
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=...
# plus your model provider settings
uv run python main.py
```

## The trace explained

**Question:** "What's the weather in Kakkanad, and how many degrees warmer is it than 20°C? Also find one recent news headline about the Kerala monsoon."

**Trace link:** `https://smith.langchain.com/public/4f245799-7e53-45e0-ba1c-319241b6f9ea/r/01a1c425-8f76-76b0-9e34-f8c92f160a8a?start_time=2026-11-10T06%3A29%3A18.311848Z`


### Step 1: model decides what to do

- **Input:** the user question, the system prompt and the three tool descriptions.
- **Output:** one AI message containing **two tool calls at once**, `get_weather` and `web_search`. The model requested them together because neither needs the other's result: the weather needs only the city, and the search needs only the topic.

### Step 2: `get_weather` (parallel with Step 3)

- **Call:** `get_weather(city="Kakkanad")`
- **Why the model chose it:** The question asks for the current weather in a named place, which matches this tool's description. No other tool provides live weather data.
- **What came back:**
  ```json
  "output": {
    "additional_kwargs": {},
    "content": "{\"location\": \"Kakkanad, Kerala, India\", \"observed_at\": \"2026-11-10T11:45\", \"temperature_c\": 31.1, \"feels_like_c\": 38.2, \"humidity_percent\": 66, \"wind_kmh\": 4.2, \"precipitation_mm\": 0.0, \"today_high_c\": 31.6, \"today_low_c\": 24.4, \"today_rain_chance_percent\": 62}",
    "name": "get_weather",
    "response_metadata": {},
    "status": "success",
    "tool_call_id": "chatcmpl-tool-9f47e79d8f1c49a6",
    "type": "tool"
  }
  ```
  Key values used in the final answer: 31.1°C (feels like 38.2°C), humidity 66%, wind 4.2 km/h, no rain currently, 62% chance of rain today, high 31.6°C / low 24.4°C.
- **Effect on next step:** The result supplies `temperature_c` (31.1), the number the calculator needs for the comparison with 20°C.

### Step 3: `web_search` (parallel with Step 2)

- **Call:** `web_search(query="Kerala monsoon latest news")`
- **Why the model chose it:** The question asks for a recent news headline about the Kerala monsoon. That is current information the model cannot know, and neither of the other tools can provide it.
- **What came back:** 
```json
    "output": {
    "additional_kwargs": {},
    "content": "{\"query\": \"Kerala monsoon latest news\", \"results\": [{\"title\": \"Monsoon rain reaches Kerala 3 days late but on time to save Indian harvests | Weather News | Al Jazeera\", \"url\": \"https://www.aljazeera.com/news/2026/6/4/monsoon-rain-reaches-kerala-3-days-late-but-on-time-to-save-indian-harvests\", \"content\": \"Monsoon rains have arrived in India’s southeastern state of Kerala three days late, the Meteorological Department says......\\n\\nThe monsoon has continued its expansion over some parts of northwestern states, said R. K. Jenamani, head of the national weather forecasting centre, and conditions are favourable for it to reach the remaining untouched areas over the next three to four days.\"}]}",
    "name": "web_search",
    "response_metadata": {},
    "status": "success",
    "tool_call_id": "chatcmpl-tool-b9313443ba081891",
    "type": "tool"
  }
  ```
- **Why it ran in parallel:** The query depends only on the user's question, so the model did not wait for the weather result.

### Step 4: `calculator` (after Steps 2 and 3)

- **Call:** `calculator(expression="31.1 - 20")`
- **Why the model chose it:** The question asks "how many degrees warmer than 20°C", which is a subtraction, and the system prompt says to use tools for arithmetic instead of answering from memory.
- **Why it came in a later model turn, not in parallel:** It needs the temperature from Step 2, which did not exist when the model made its first response.
- **What came back:**
  ```json
  "output": {
    "additional_kwargs": {},
    "content": "{\"expression\": \"31.1 - 20\", \"result\": 11.100000000000001}",
    "name": "calculator",
    "response_metadata": {},
    "status": "success",
    "tool_call_id": "chatcmpl-tool-926133c41bfb5d1e",
    "type": "tool"
  }
  ```
  Result: 11.1, matching the final answer.

### Step 5: final answer

- **What the model did:** It combined the three tool results into a `FinalAnswer`.
- **Structured output:**
  ```
  tools_used = ['get_weather', 'web_search', 'calculator']
  sources    = ['https://www.aljazeera.com/news/2026/6/4/monsoon-rain-reaches-kerala-3-days-late-but-on-time-to-save-indian-harvests']
  answer     = Kakkanad weather (now, 10 Nov 2026): 31.1°C (feels like 38.2°C),
               humidity 66%, wind 4.2 km/h, no rain currently, 62% chance of rain
               today (high 31.6°C / low 24.4°C). It's 11.1°C warmer than 20°C.
               Recent Kerala monsoon headline: "Monsoon rain reaches Kerala 3 days
               late but on time to save Indian harvests" – Al Jazeera (4 Jun 2026)
  ```
- **Check:** `tools_used` matches the three calls above, and `sources` holds the URL of the headline used.

## Design notes

- **Tools return errors as data** (`{"error": ...}`) instead of raising, so the agent can read the error and retry.
- **Tool docstrings carry the usage guidance** (what each tool is for and its argument format). The system prompt only holds cross-tool rules: prefer tools over memory, retry once on error, keep answers short, cite sources.
- **Calculator safety:** the expression is parsed into a syntax tree and only allowlisted operations run, so the model cannot execute arbitrary code through it. Exponents are capped.
- **Recursion limit** of 15 stops a confused model from looping forever.