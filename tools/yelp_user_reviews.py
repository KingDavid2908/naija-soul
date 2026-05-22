import json
import logging
from pathlib import Path
from typing import Any

from langchain.tools import tool

logger = logging.getLogger("naija-soul")

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "yelp"
_REVIEWS_BY_USER: dict[str, list[dict[str, Any]]] | None = None
_USER_NAMES: dict[str, str] | None = None


def _load_data() -> None:
    global _REVIEWS_BY_USER, _USER_NAMES
    if _REVIEWS_BY_USER is not None:
        return
    _REVIEWS_BY_USER = {}
    _USER_NAMES = {}
    review_path = DATA_DIR / "review.json"
    user_path = DATA_DIR / "user.json"
    if review_path.exists():
        with open(review_path, "r") as f:
            for line in f:
                r = json.loads(line)
                uid = r.get("user_id", "")
                if uid:
                    _REVIEWS_BY_USER.setdefault(uid, []).append(r)
    if user_path.exists():
        with open(user_path, "r") as f:
            for line in f:
                u = json.loads(line)
                uid = u.get("user_id", "")
                name = u.get("name", "")
                if uid and name:
                    _USER_NAMES[uid] = name
    logger.info(
        "Loaded %d Yelp users and %d reviews",
        len(_USER_NAMES),
        sum(len(v) for v in _REVIEWS_BY_USER.values()),
    )


@tool
def get_yelp_user_reviews(user_id: str, max_reviews: int = 5) -> str:
    """Fetch past reviews for a Yelp user from the local dataset.

    Returns the user's name and recent reviews to understand their
    writing style, tone, and preferences.
    """
    _load_data()
    name = _USER_NAMES.get(user_id, "Unknown")
    reviews = _REVIEWS_BY_USER.get(user_id, [])
    if not reviews:
        return f"No Yelp reviews found for user_id: {user_id}"
    reviews.sort(key=lambda r: r.get("date", ""), reverse=True)
    result = [f"User: {name} ({user_id}) — {len(reviews)} total reviews"]
    for r in reviews[:max_reviews]:
        text = r.get("text", "")[:300]
        stars = r.get("stars", 0)
        date = r.get("date", "")[:10]
        result.append(f"- [{date}] ★{stars}: {text}")
    return "\n".join(result)
