from functools import cache

from langchain_mistralai import ChatMistralAI

from app.core.config import MISTRAL_API_KEY


@cache
def get_llm() -> ChatMistralAI:
    return ChatMistralAI(
        model="mistral-large-latest",
        temperature=0.7,
        max_tokens=2048,
        mistral_api_key=MISTRAL_API_KEY,
        max_retries=30,
    )
