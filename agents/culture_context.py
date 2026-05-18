import httpx
from datetime import datetime
from langchain.tools import tool

from app.core.config import CALENDARIFIC_API_KEY
from app.core.logging import logger

API_URL = "https://calendarific.com/api/v2/holidays"
TIMEOUT = 15.0

_CULTURAL_TYPES = {"Local holiday", "Observance"}


@tool
def get_cultural_context(month: int | None = None, year: int | None = None) -> str:
    """Get Nigerian cultural festivals and observances for a given month.

    Covers local/regional festivals like New Yam Festival, Eyo Festival,
    Argungu Fishing Festival, Lagos Carnival, etc.

    Args:
        month: Month number (1-12). Defaults to current month if omitted.
        year: Year (e.g. 2026). Defaults to current year if omitted.
    """
    now = datetime.now()
    month = month or now.month
    year = year or now.year

    params = {
        "api_key": CALENDARIFIC_API_KEY,
        "country": "NG",
        "year": year,
        "month": month,
        "type": "local,observance",
    }

    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    holidays = data.get("response", {}).get("holidays", [])
    cultural = [h for h in holidays if _CULTURAL_TYPES & set(h.get("type", []))]

    if not cultural:
        return f"No cultural festivals found for {month}/{year}."

    lines = [f"Nigerian cultural festivals and observances — {month}/{year}:"]
    for h in cultural:
        name = h.get("name", "Unknown")
        desc = h.get("description", "")
        types = ", ".join(h.get("type", []))
        date_iso = h.get("date", {}).get("iso", "")
        date_str = f" ({date_iso})" if date_iso else ""
        desc_str = f" — {desc}" if desc else ""
        lines.append(f"  {name}{date_str} [{types}]{desc_str}")

    return "\n".join(lines)
