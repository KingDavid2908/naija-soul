import math
from typing import Any

from langchain.tools import tool

from tools.product_store import store as product_store


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


@tool
def search_products_fast(
    query: str = "",
    category: str | None = None,
    limit: int = 5,
) -> str:
    """Search products across Yelp (food), Amazon (video games), Goodreads (books).

    Uses SQLite FTS5 BM25 ranking for fast, exact keyword matching.
    Supports category filtering and multi-word queries.

    Args:
        query: Free-text search.
        category: Optional filter — "food", "book", or None for all.
        limit: Number of results to return (default 5).
    """
    candidates: list[dict[str, Any]] = product_store.search(query, limit=limit * 4)
    if category:
        cat_lower = category.lower()
        candidates = [
            c for c in candidates
            if cat_lower in c.get("category", "").lower()
            or cat_lower in c.get("subcategory", "").lower()
        ]

    if not candidates:
        return f"No products found for query='{query}' category={category}."

    results: list[str] = []
    for c in candidates[:limit]:
        source = c.get("source", "?")
        name = c.get("name", "Unknown")
        cat = c.get("category", "")
        sub = c.get("subcategory", "")
        desc = c.get("description", "")
        results.append(
            f"  [{source}] {name} — {cat}/{sub}\n"
            f"     {desc[:150]}..."
        )

    return "Products found:\n" + "\n".join(results)
