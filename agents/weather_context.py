from datetime import date, datetime
import httpx
from langchain.tools import tool

from app.core.logging import logger
from tools.geoapify_places import geocode_city

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEOUT = 15.0


@tool
def get_weather_context(city: str = "Lagos", date_str: str | None = None) -> str:
    """Get weather conditions for a Nigerian city on a specific date.

    Supports past, present, and future dates. No API key needed.
    Uses Open-Meteo Forecast API (current/future) or Historical Archive API (past).

    Args:
        city: Any Nigerian city, state, or event center name.
        date_str: ISO date string (YYYY-MM-DD). Omit for current weather.
    """
    lon, lat = geocode_city(city)
    today = date.today()

    if date_str is None:
        return _get_current_weather(lat, lon, city)

    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return f"Invalid date '{date_str}'. Use YYYY-MM-DD format."

    if target == today:
        return _get_current_weather(lat, lon, city)
    elif target < today:
        return _get_historical_weather(lat, lon, city, date_str)
    else:
        return _get_forecast_weather(lat, lon, city, date_str)


def _get_current_weather(lat: float, lon: float, city: str) -> str:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,precipitation,wind_speed_10m",
        "timezone": "Africa/Lagos",
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    c = data.get("current", {})
    temp = c.get("temperature_2m", "N/A")
    humidity = c.get("relative_humidity_2m", "N/A")
    code = c.get("weather_code", -1)
    precip = c.get("precipitation", 0)
    wind = c.get("wind_speed_10m", "N/A")

    return (
        f"Current weather in {city}: {temp}°C, humidity {humidity}%, "
        f"precipitation {precip}mm, wind {wind}km/h. "
        f"Conditions: {_wmo_description(code)}."
    )


def _get_historical_weather(lat: float, lon: float, city: str, date_str: str) -> str:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_str,
        "end_date": date_str,
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum,wind_speed_10m_max",
        "timezone": "Africa/Lagos",
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(ARCHIVE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    d = data.get("daily", {})
    temp_max = d.get("temperature_2m_max", ["N/A"])[0]
    temp_min = d.get("temperature_2m_min", ["N/A"])[0]
    code = d.get("weather_code", [-1])[0]
    precip = d.get("precipitation_sum", [0])[0]
    wind = d.get("wind_speed_10m_max", ["N/A"])[0]

    return (
        f"Weather in {city} on {date_str}: high {temp_max}°C, low {temp_min}°C, "
        f"precipitation {precip}mm, max wind {wind}km/h. "
        f"Conditions: {_wmo_description(code)}."
    )


def _get_forecast_weather(lat: float, lon: float, city: str, date_str: str) -> str:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_str,
        "end_date": date_str,
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum,wind_speed_10m_max",
        "timezone": "Africa/Lagos",
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    d = data.get("daily", {})
    temp_max = d.get("temperature_2m_max", ["N/A"])[0]
    temp_min = d.get("temperature_2m_min", ["N/A"])[0]
    code = d.get("weather_code", [-1])[0]
    precip = d.get("precipitation_sum", [0])[0]
    wind = d.get("wind_speed_10m_max", ["N/A"])[0]

    return (
        f"Forecast for {city} on {date_str}: high {temp_max}°C, low {temp_min}°C, "
        f"precipitation {precip}mm, max wind {wind}km/h. "
        f"Conditions: {_wmo_description(code)}."
    )


def _wmo_description(code: int) -> str:
    mapping = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return mapping.get(code, f"Unknown ({code})")
