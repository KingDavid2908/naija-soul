import json
import os
from pathlib import Path
from langchain.tools import tool

from app.core.logging import logger

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_jsonl(path: str, limit: int = 0) -> list[dict]:
    if not os.path.isfile(path):
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def search_yelp(query: str, category: str | None, limit: int) -> list[dict]:
    path = DATA_DIR / "yelp" / "business.json"
    records = _load_jsonl(str(path))
    results = []
    for r in records:
        name = r.get("name", "")
        cats = (r.get("categories") or "").lower()
        desc = r.get("description", f"{r.get('city', '')} — {cats}")
        if query and query.lower() not in name.lower() and query.lower() not in desc.lower():
            continue
        if category and category.lower() not in cats and category.lower() != (r.get("category") or "").lower():
            continue
        results.append({
            "source": "yelp",
            "id": r.get("business_id", ""),
            "name": name,
            "category": "food",
            "subcategory": cats.split(",")[0].strip() if cats else "",
            "rating": r.get("stars"),
            "city": r.get("city", ""),
            "description": desc,
        })
        if len(results) >= limit:
            break
    return results


def search_amazon(query: str, category: str | None, limit: int) -> list[dict]:
    path = DATA_DIR / "amazon" / "reviews.json"
    records = _load_jsonl(str(path))
    seen: set[str] = set()
    results = []
    for r in records:
        title = r.get("product_title", "")
        body = r.get("review_body", "")
        cat = (r.get("product_category") or "").lower()
        if query and query.lower() not in title.lower() and query.lower() not in body.lower():
            continue
        if category and category.lower() not in cat:
            continue
        pid = r.get("product_id", "")
        if pid in seen:
            continue
        seen.add(pid)
        results.append({
            "source": "amazon",
            "id": pid,
            "name": title,
            "category": "book",
            "subcategory": cat,
            "rating": r.get("star_rating"),
            "description": body[:200] + "..." if len(body) > 200 else body,
        })
        if len(results) >= limit:
            break
    return results


def search_goodreads(query: str, category: str | None, limit: int) -> list[dict]:
    path = DATA_DIR / "goodreads" / "books.json"
    records = _load_jsonl(str(path))
    results = []
    for r in records:
        name = r.get("Book") or r.get("name") or ""
        summary = r.get("Description") or r.get("summary") or ""
        genres_raw = r.get("Genres") or r.get("genres") or []
        genres_str = ", ".join(genres_raw) if isinstance(genres_raw, list) else str(genres_raw)
        if query and query.lower() not in name.lower() and query.lower() not in summary.lower():
            continue
        if category and category.lower() not in genres_str.lower():
            continue
        rating = r.get("star_rating") or r.get("average_rating")
        try:
            rating = round(float(rating), 2) if rating else None
        except (ValueError, TypeError):
            rating = None
        results.append({
            "source": "goodreads",
            "id": r.get("id", ""),
            "name": name,
            "category": "book",
            "subcategory": genres_str.split(",")[0].strip() if genres_str else "",
            "rating": rating,
            "author": r.get("author", ""),
            "description": (summary[:200] + "..." if summary and len(summary) > 200 else summary) if summary else "",
        })
        if len(results) >= limit:
            break
    return results


@tool
def search_products(
    query: str = "",
    category: str | None = None,
    limit: int = 10,
    dataset: str = "all",
) -> str:
    """Search across Yelp (food), Amazon Reviews (books), and Goodreads (books).

    Args:
        query: Free-text search against product name / title / description.
        category: Filter — "food" (restaurants), "book" (books), or None for all.
        limit: Max results per dataset.
        dataset: Which dataset to search — "yelp", "amazon", "goodreads", or "all".
    """
    results: list[dict] = []

    if dataset in ("all", "yelp"):
        results.extend(search_yelp(query, category, limit))
    if dataset in ("all", "amazon"):
        results.extend(search_amazon(query, category, limit))
    if dataset in ("all", "goodreads"):
        results.extend(search_goodreads(query, category, limit))

    if not results:
        return f"No products found for query='{query}' category={category}."

    lines = [f"Products found ({len(results)}):"]
    for i, r in enumerate(results[:limit * 3], 1):
        name = r.get("name", "Unknown")
        source = r.get("source", "?")
        cat = r.get("category", "")
        sub = r.get("subcategory", "")
        rating = r.get("rating", "")
        author = r.get("author", "")
        city = r.get("city", "")
        desc = r.get("description", "")
        rating_str = f" [{rating}/5]" if rating else ""
        author_str = f" by {author}" if author else ""
        loc_str = f" in {city}" if city else ""
        lines.append(f"  {i}. [{source}] {name}{author_str}{loc_str}{rating_str} — {cat}/{sub}")
        if desc:
            lines.append(f"     {desc[:120]}")

    return "\n".join(lines)
