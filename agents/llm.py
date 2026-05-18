from functools import cache

from langchain_groq import ChatGroq

from app.core.config import GROQ_API_KEY


@cache
def get_llm() -> ChatGroq:
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.7,
        api_key=GROQ_API_KEY,
    )
