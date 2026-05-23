# Task A: Review Simulator Agent
#
# End-to-end: Given a product + user persona (or Yelp user_id) →
# generates an authentic Nigerian English/Pidgin review with star
# rating, confidence score, and voice-matched audio narration.
#
# AGENT DECISION LOOP:
# 1. Check memory for this user's existing profile via search_memory.
#    If found, load their ethnicity, voice, and language preferences.
#    If not found, infer from name + location (cold start).
# 2. Optionally call search_products to fetch product descriptions
#    and IDs for constructing Amazon/Goodreads/Yelp links.
# 3. Optionally call get_yelp_user_reviews if a raw Yelp user_id
#    was given — mimics that user's writing style from past reviews.
# 4. Optionally call get_current_nigerian_holidays to inject timely
#    cultural references (e.g. "During Sallah, this suya spot...").
# 5. Optionally call get_weather_context so tone matches Lagos
#    weather (harmattan, rainy season, etc.).
# 6. Choose an appropriate voice based on inferred ethnicity and
#    compose the final Pidgin/English review JSON.
# 7. Save the generated profile + review to memory via manage_memory
#    so the next request continues the conversation.
#
# The agent short-circuits — it only calls tools it actually needs.

from langgraph.prebuilt import create_react_agent

from agents.llm import get_llm
from agents.memory import store, memory_tools
from agents.prompts import SYSTEM_PROMPT_TASK_A

# AGENT: Weather context tool. The agent checks the date and location
# (e.g. "Lagos in October") to ground the review in real conditions.
# Example: "This amala hit different on a harmattan evening!"
from agents.weather_context import get_weather_context

# AGENT: Holiday/festival lookup. The agent calls this to mention
# current Nigerian celebrations in the review — makes the output
# feel culturally aware and timely.
from tools.calendarific_holidays import get_current_nigerian_holidays

# AGENT: Product search tool. The agent calls this to retrieve
# product descriptions, categories, and product_ids (Amazon ASINs /
# Goodreads titles) so it can construct proper links in the response.
from tools.product_search import search_products_fast

# AGENT: Yelp user review lookup. If the request includes a raw
# Yelp user_id (22-char alphanumeric), the agent fetches that user's
# past reviews from our local 20K-review dataset and mimics their
# writing style, vocabulary, and star-rating distribution.
from tools.yelp_user_reviews import get_yelp_user_reviews

# AGENT: The toolset the review simulator can invoke during its
# reasoning loop. Typical call order:
#   search_memory → search_products → get_holidays → get_weather
#   → yelp_lookup → manage_memory
# Each tool returns structured data the agent synthesizes into
# the final review JSON.
task_a_tools = [
    *memory_tools,
    get_current_nigerian_holidays,
    get_weather_context,
    search_products_fast,
    get_yelp_user_reviews,
]

# AGENT: LangGraph's create_react_agent wraps the LLM (Mistral →
# Gemini → Groq fallback chain, see agents/llm.py) in a structured
# reasoning loop. It receives SYSTEM_PROMPT_TASK_A (behavioral rules:
# authentic Pidgin, max 2 paragraphs, 4 sentences each), decides
# which tools to call and in what order, processes each tool's output,
# and keeps looping until it has enough context to produce the final
# JSON with review_text, rating, confidence, voice_used, etc.
task_a_agent = create_react_agent(
    get_llm(),
    tools=task_a_tools,
    prompt=SYSTEM_PROMPT_TASK_A,
    store=store,
    name="review_simulator",
)
