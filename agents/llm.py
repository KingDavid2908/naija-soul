from functools import cache

from langchain_core.runnables import Runnable
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from app.core.config import MISTRAL_API_KEYS, GOOGLE_API_KEYS, GROQ_API_KEYS


@cache
def get_llm() -> Runnable:
    mistral_instances = [
        ChatMistralAI(
            model="mistral-large-latest",
            temperature=0.7,
            max_tokens=2048,
            mistral_api_key=key,
            max_retries=30,
        )
        for key in MISTRAL_API_KEYS
    ]
    fallbacks = (
        mistral_instances[1:]
        + [
            ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.7,
                max_retries=5,
                google_api_key=key,
            )
            for key in GOOGLE_API_KEYS
        ]
        + [
            ChatGroq(
                model="openai/gpt-oss-120b",
                temperature=0.7,
                max_retries=5,
                groq_api_key=key,
            )
            for key in GROQ_API_KEYS
        ]
    )
    return mistral_instances[0].with_fallbacks(fallbacks)
