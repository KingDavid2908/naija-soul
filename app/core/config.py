import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
YARNGPT_API_KEY = os.getenv("YARNGPT_API_KEY", "")
CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_API_KEY", "")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def _key_list(name: str, max_count: int = 3) -> list[str]:
    keys: list[str] = []
    primary = os.getenv(name, "")
    if primary:
        keys.append(primary)
    for i in range(2, max_count + 1):
        val = os.getenv(f"{name}_{i}", "")
        if val and val != primary:
            keys.append(val)
    return keys


MISTRAL_API_KEYS = _key_list("MISTRAL_API_KEY")
GOOGLE_API_KEYS = _key_list("GOOGLE_API_KEY")
GROQ_API_KEYS = _key_list("GROQ_API_KEY")
