import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
YARNGPT_API_KEY = os.getenv("YARNGPT_API_KEY", "")
CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_API_KEY", "")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
