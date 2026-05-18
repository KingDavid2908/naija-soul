import httpx
from langchain.tools import tool

from app.core.config import GEOAPIFY_API_KEY
from app.core.logging import logger

GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"
PLACES_URL = "https://api.geoapify.com/v2/places"
TIMEOUT = 15.0


def geocode_city(city_name: str) -> tuple[float, float]:
    params = {
        "text": f"{city_name}, Nigeria",
        "filter": "countrycode:ng",
        "limit": 1,
        "apiKey": GEOAPIFY_API_KEY,
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(GEOCODE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        if not features:
            logger.warning("Geocode returned no results for '%s', falling back to Lagos", city_name)
            return 3.3792, 6.5244
        props = features[0].get("properties", {})
        lon = props.get("lon")
        lat = props.get("lat")
        if lon is None or lat is None:
            coords = features[0].get("geometry", {}).get("coordinates")
            if coords and len(coords) == 2:
                lon, lat = coords
            else:
                logger.warning("No coordinates for '%s', falling back to Lagos", city_name)
                return 3.3792, 6.5244
        logger.info("Geocoded '%s' → (%s, %s)", city_name, lon, lat)
        return lon, lat


@tool
def search_nigerian_businesses(
    category: str = "catering.restaurant",
    location: str = "Lagos",
    limit: int = 5,
) -> str:
    """Search for businesses in Nigeria by category and location.

    Args:
        category: Business category (e.g. catering.restaurant, catering.cafe,
                  catering.fast_food, commercial.supermarket, entertainment.culture,
                  accommodation.hotel, leisure.park).
        location: Any Nigerian city, state, or event center name.
        limit: Max results (1-20).
    """
    try:
        lon, lat = geocode_city(location)
    except Exception as exc:
        logger.warning("Geocoding failed for '%s': %s", location, exc)
        lon, lat = 3.3792, 6.5244

    params = {
        "categories": category,
        "filter": f"circle:{lon},{lat},5000",
        "limit": min(limit, 20),
        "apiKey": GEOAPIFY_API_KEY,
    }

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(PLACES_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("Geoapify Places API error: %s", exc)
        return f"Could not find results for '{category}' in {location}. Try a different category."

    features = data.get("features", [])
    if not features:
        return f"No businesses found for '{category}' in {location}."

    lines = [f"Businesses in {location} ({category}):"]
    for i, f in enumerate(features[:limit], 1):
        p = f.get("properties", {})
        name = p.get("name", "Unknown")
        address = p.get("formatted", p.get("address_line2", ""))
        distance = p.get("distance")
        dist_str = f" — {distance}m away" if distance is not None else ""
        lines.append(f"  {i}. {name}{dist_str} — {address}")

    return "\n".join(lines)
