import httpx
from datetime import datetime
from langchain.tools import tool

from app.core.config import CALENDARIFIC_API_KEY
from app.core.logging import logger

API_URL = "https://calendarific.com/api/v2/holidays"
TIMEOUT = 15.0


@tool
def get_current_nigerian_holidays(month: int | None = None, year: int | None = None) -> str:
    """Get Nigerian public holidays, cultural festivals, and observances.

    Covers national holidays, local/regional festivals (New Yam Festival, Eyo
    Festival, Argungu Fishing Festival, Lagos Carnival, etc.), and observances.

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
        "type": "national,local,observance",
    }

    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    holidays = data.get("response", {}).get("holidays", [])
    if not holidays:
        return f"No holidays found for {month}/{year}."

    lines = [f"Nigerian holidays and observances — {month}/{year}:"]
    for h in holidays:
        name = h.get("name", "Unknown")
        desc = h.get("description", "")
        types = ", ".join(h.get("type", []))
        date_iso = h.get("date", {}).get("iso", "")
        date_str = f" ({date_iso})" if date_iso else ""
        desc_str = f" — {desc}" if desc else ""
        lines.append(f"  {name}{date_str} [{types}]{desc_str}")

    return "\n".join(lines)
