import logging
from functools import cache

from google.genai import Client as GenAIClient, types

from app.core.config import GOOGLE_API_KEY

logger = logging.getLogger("naija-soul")

LANGUAGES = {"yoruba", "igbo", "hausa"}


@cache
def _get_client() -> GenAIClient:
    return GenAIClient(api_key=GOOGLE_API_KEY)


async def translate(text: str, target_language: str) -> str:
    if target_language not in LANGUAGES:
        return text

    prompt = (
        f"Translate the following English/Pidgin English text to {target_language}. "
        f"Return only the translation, no explanations.\n\n{text}"
    )

    try:
        client = _get_client()
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=types.Content(parts=[types.Part(text=prompt)]),
        )
        translated = response.text.strip()
        if translated:
            return translated
    except Exception as exc:
        logger.warning("Translation to %s failed: %s", target_language, exc)

    return text
