from langchain.tools import tool

YORUBA_FIRST: set[str] = {
    "ade", "adeola", "adekunle", "ayodele", "ayodeji", "bisola", "bisi",
    "bolanle", "bukola", "damola", "dayo", "eke", "femi", "folake",
    "funke", "gbenga", "ife", "jide", "kayode", "kehinde", "kemi",
    "kunle", "lami", "lola", "modupe", "moyo", "nike", "ola", "olamide",
    "olayinka", "remi", "segun", "seun", "simi", "taiwo",
    "tayo", "tola", "tunde", "wale", "yemi", "yetunde",
}

HAUSA_FIRST: set[str] = {
    "abba", "adamu", "ahmad", "amina", "audu", "bala", "bashir",
    "bello", "bilkisu", "danjuma", "fatima", "habib", "halima",
    "ibrahim", "jibril", "kabiru", "lawan", "mamman", "maryam",
    "musa", "nasir", "rafiu", "sadiq", "salisu", "sani", "suleiman",
    "umar", "yusuf", "zainab", "zara",
}

IGBO_FIRST: set[str] = {
    "achi", "adanna", "akunna", "amara", "arusi", "chekwube",
    "chidi", "chinonso", "chinwe", "chioma", "chisom", "ebuka", "ekene",
    "emeka", "eze", "ifeanyi", "ijendu", "ikechukwu", "kamjido", "kene",
    "kosi", "ndidi", "ngozi", "nkechi", "nkemdilim", "obianuju", "obinna",
    "ogochukwu", "okechukwu", "olisa", "oluchi", "onyeka", "sochika", "uche",
    "udoka", "uzo",
}

LOCATION_INFO: dict[str, tuple[str, str]] = {
    "lagos": ("southwest", "yoruba"),
    "ibadan": ("southwest", "yoruba"),
    "abeokuta": ("southwest", "yoruba"),
    "akure": ("southwest", "yoruba"),
    "osogbo": ("southwest", "yoruba"),
    "ile-ife": ("southwest", "yoruba"),
    "enugu": ("southeast", "igbo"),
    "onitsha": ("southeast", "igbo"),
    "owerri": ("southeast", "igbo"),
    "awka": ("southeast", "igbo"),
    "aba": ("southeast", "igbo"),
    "umahia": ("southeast", "igbo"),
    "kano": ("northwest", "hausa"),
    "kaduna": ("northwest", "hausa"),
    "katsina": ("northwest", "hausa"),
    "sokoto": ("northwest", "hausa"),
    "zaria": ("northwest", "hausa"),
    "jos": ("northeast", "hausa"),
    "maiduguri": ("northeast", "hausa"),
    "bauchi": ("northeast", "hausa"),
    "yola": ("northeast", "hausa"),
    "gombe": ("northeast", "hausa"),
    "benin": ("south-south", "pidgin"),
    "calabar": ("south-south", "pidgin"),
    "port harcourt": ("south-south", "pidgin"),
    "uyo": ("south-south", "pidgin"),
    "warri": ("south-south", "pidgin"),
    "asaba": ("south-south", "pidgin"),
    "abuja": ("northcentral", "english"),
    "ilorin": ("northcentral", "english"),
    "minna": ("northcentral", "english"),
    "lokoja": ("northcentral", "english"),
}

ETHNIC_PREFERENCES: dict[str, dict] = {
    "yoruba": {
        "food": ["swallow", "spicy_stew", "nigerian"],
        "movies": ["comedy", "nollywood_drama"],
        "books": ["fiction", "african_literature"],
        "price_range": "mid",
        "ambience": ["lively", "music"],
    },
    "igbo": {
        "food": ["nigerian", "spicy", "soup_based"],
        "movies": ["epic", "nollywood"],
        "books": ["fiction", "history", "biography"],
        "price_range": "mid",
        "ambience": ["quiet", "family_style"],
    },
    "hausa": {
        "food": ["northern_nigerian", "halal", "grilled"],
        "movies": ["drama", "epic", "cultural"],
        "books": ["religious", "history", "poetry"],
        "price_range": "budget",
        "ambience": ["quiet", "traditional"],
    },
    "english": {
        "food": ["international", "fast_food"],
        "movies": ["action", "comedy"],
        "books": ["fiction", "non_fiction"],
        "price_range": "mid",
        "ambience": ["modern", "casual"],
    },
}

ETHNIC_VOICES: dict[str, str] = {
    "yoruba": "Tayo",
    "igbo": "Chinenye",
    "hausa": "Zainab",
    "english": "Idera",
}


def _first_name(name: str) -> str:
    return name.strip().split()[0].lower() if name.strip() else ""


def infer_ethnicity(name: str) -> tuple[str, float]:
    first = _first_name(name)
    if not first:
        return "english", 0.0
    if first in YORUBA_FIRST:
        return "yoruba", 0.9
    if first in IGBO_FIRST:
        return "igbo", 0.9
    if first in HAUSA_FIRST:
        return "hausa", 0.9
    return "english", 0.3


def infer_profile(name: str, location: str | None = None) -> dict:
    ethnicity, confidence = infer_ethnicity(name)
    region = "unknown"
    preferred_language = "english"
    lang_hint = ""
    region_lang = ""

    if location:
        loc_key = location.strip().lower()
        match = LOCATION_INFO.get(loc_key)
        if not match:
            for key, val in LOCATION_INFO.items():
                if key in loc_key or loc_key in key:
                    match = val
                    break
        if match:
            region = match[0]
            region_lang = match[1]

    pidgin_density = 0.0
    if region in ("south-south",) and ethnicity in ("igbo", "english"):
        pidgin_density = 0.7
        preferred_language = "pidgin"
        lang_hint = "Nigerian Pidgin"
    elif region in ("southwest",) and ethnicity == "yoruba":
        pidgin_density = 0.5
        lang_hint = "Yoruba-infused English"
    elif region in ("northwest", "northeast") and ethnicity == "hausa":
        pidgin_density = 0.2
        lang_hint = "Hausa-infused English"
    else:
        pidgin_density = 0.65
        lang_hint = "Nigerian English"

    prefs = ETHNIC_PREFERENCES.get(ethnicity, ETHNIC_PREFERENCES["english"])

    return {
        "name": name,
        "inferred_ethnicity": ethnicity,
        "ethnicity_confidence": round(confidence, 2),
        "inferred_location": location or "unknown",
        "inferred_region": region,
        "voice_assigned": ETHNIC_VOICES.get(ethnicity, "Idera"),
        "preferred_language": preferred_language,
        "language_hint": lang_hint,
        "pidgin_density": round(pidgin_density, 2),
        "review_history": [],
        "preferences": dict(prefs),
        "conversation_count": 0,
    }


@tool
def infer_user_profile(name: str, location: str | None = None) -> str:
    """Infer a user profile from name and optional location.

    Uses name keyword matching for ethnicity (Yoruba/Hausa/Igbo/English)
    and location mapping for region/language preferences.
    No LLM or API calls needed.

    Args:
        name: The user's full name.
        location: Optional city or town name in Nigeria.
    """
    import json
    profile = infer_profile(name, location)
    return json.dumps(profile, ensure_ascii=False)
