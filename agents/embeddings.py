from functools import cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import GOOGLE_API_KEY


@cache
def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2",
        google_api_key=GOOGLE_API_KEY,
    )
