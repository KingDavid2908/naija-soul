from langgraph.prebuilt import create_react_agent

from agents.llm import get_llm
from agents.memory import store, memory_tools
from agents.prompts import SYSTEM_PROMPT_TASK_B
from agents.weather_context import get_weather_context
from agents.culture_context import get_cultural_context
from tools.calendarific_holidays import get_current_nigerian_holidays
from tools.geoapify_places import search_nigerian_businesses
from tools.product_search import search_products_fast

task_b_tools = [
    *memory_tools,
    search_nigerian_businesses,
    search_products_fast,
    get_current_nigerian_holidays,
    get_weather_context,
    get_cultural_context,
]

task_b_agent = create_react_agent(
    get_llm(),
    tools=task_b_tools,
    prompt=SYSTEM_PROMPT_TASK_B,
    store=store,
    name="recommendation_agent",
)
