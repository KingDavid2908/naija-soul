# Task B: Recommendation Agent
#
# End-to-end: Given a user persona + optional category filter →
# returns 5 personalized recommendations across food, books, movies,
# and local Nigerian businesses, with spoken audio explanation.
#
# AGENT DECISION LOOP:
# 1. Check memory for this user's existing preferences via
#    search_memory. If returning user, reuse their past voice,
#    ethnicity, and preferred categories.
# 2. If cold-start (no memory match), infer ethnicity, region,
#    and voice from the user_id name using built-in Yoruba/Hausa/
#    Igbo name lists (see memory/user_profiles.py).
# 3. For food/business: call search_nigerian_businesses (Geoapify)
#    to find real Nigerian restaurants with addresses and websites.
# 4. For books/products: call search_products (Goodreads + Amazon
#    + Yelp datasets) to find items with product_ids for links.
# 5. Check get_current_nigerian_holidays + get_cultural_context
#    to mention relevant festivals (e.g. "Try this during Ojude Oba"
#    or "Perfect for Eid celebrations").
# 6. Check get_weather_context to make recommendations
#    location-aware (e.g. "Hot day in Kano? Try this chilled drink").
# 7. Optionally call get_yelp_user_reviews if a Yelp user_id was
#    given — analyzes their past reviews for better personalization.
# 8. Rank top 5 by relevance score, construct a link for each
#    (Amazon ASIN URL, Goodreads search, Yelp search, or website).
# 9. Draft spoken explanation text, save profile to memory, and
#    emit final JSON for the router to translate and generate audio.

from langgraph.prebuilt import create_react_agent

from agents.llm import get_llm
from agents.memory import store, memory_tools
from agents.prompts import SYSTEM_PROMPT_TASK_B

# AGENT: Weather context tool. The agent checks the forecast at the
# user's inferred location. AGENT DECISION: recommends warm meals
# on rainy days, chilled items during hot harmattan, etc.
from agents.weather_context import get_weather_context

# AGENT: Cultural context tool. The agent checks upcoming festivals
# and local events from Calendarific. AGENT DECISION: prioritises
# recommendations that align with current celebrations — e.g.
# "This suya spot is great for Sallah gatherings."
from agents.culture_context import get_cultural_context

# AGENT: Holiday lookup tool. Called alongside cultural context to
# get both national and local observances so recommendations feel
# specific to the user's region (Kano gets different holidays
# from Enugu).
from tools.calendarific_holidays import get_current_nigerian_holidays

# AGENT: Nigerian business search via Geoapify API. The agent calls
# this for food/business/recreation categories. AGENT DECISION:
# returns real businesses with addresses, phone numbers, and
# website URLs — these become the "link" field in each
# recommendation response.
from tools.geoapify_places import search_nigerian_businesses

# AGENT: Product search across all datasets (Amazon, Goodreads,
# Yelp). AGENT DECISION: for books and video games, this is the
# primary data source. The tool returns product_ids (ASINs for
# Amazon) that the agent uses to build clickable links.
from tools.product_search import search_products_fast

# AGENT: Yelp user review lookup — if the request contains a
# Yelp user_id, the agent fetches their past review history
# from the local dataset and adapts recommendations to match
# the user's known preferences and critical style.
from tools.yelp_user_reviews import get_yelp_user_reviews

# AGENT: The recommendation agent's toolset. Typical call order:
#   search_memory → infer_profile → search_businesses →
#   search_products → get_holidays → get_cultural_context →
#   get_weather → yelp_lookup → rank_recs → manage_memory
# Each tool call adds data the agent uses to narrow down and
# rank the top 5 personalized recommendations.
task_b_tools = [
    *memory_tools,
    search_nigerian_businesses,
    search_products_fast,
    get_current_nigerian_holidays,
    get_weather_context,
    get_cultural_context,
    get_yelp_user_reviews,
]

# AGENT: LangGraph's create_react_agent wraps the LLM (Mistral →
# Gemini → Groq fallback chain) in a reasoning loop initialized
# with SYSTEM_PROMPT_TASK_B. The agent receives the user's query
# (persona + optional category), calls tools in any order it
# chooses, synthesizes results, and loops until it can produce
# the final JSON with 5 recommendations (each with name, category,
# score, reason, and link) plus a spoken explanation summary.
task_b_agent = create_react_agent(
    get_llm(),
    tools=task_b_tools,
    prompt=SYSTEM_PROMPT_TASK_B,
    store=store,
    name="recommendation_agent",
)
