from langgraph.prebuilt import create_react_agent

from agents.llm import get_llm
from agents.memory import store, memory_tools
from agents.prompts import SYSTEM_PROMPT_TASK_A
from agents.weather_context import get_weather_context
from tools.calendarific_holidays import get_current_nigerian_holidays
from tools.product_search import search_products_fast

task_a_tools = [
    *memory_tools,
    get_current_nigerian_holidays,
    get_weather_context,
    search_products_fast,
]

task_a_agent = create_react_agent(
    get_llm(),
    tools=task_a_tools,
    prompt=SYSTEM_PROMPT_TASK_A,
    store=store,
    name="review_simulator",
)
