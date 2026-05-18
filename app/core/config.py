import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
YARNGPT_API_KEY = os.getenv("YARNGPT_API_KEY", "")
CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_API_KEY", "")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "")
