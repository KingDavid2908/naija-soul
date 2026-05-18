import math
from typing import Any

from langchain.tools import tool

from agents.embeddings import get_embeddings
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

    Two-stage hybrid search:
    1. SQLite FTS5 BM25 → top 100 candidates (fast, exact keyword match)
    2. Gemini text-embedding-004 → embed query + candidates → cosine similarity → top-k

    Args:
        query: Free-text search.
        category: Optional filter — "food", "book", or None for all.
        limit: Number of results to return (default 5).
    """
    candidates: list[dict[str, Any]] = product_store.search(query, limit=20)
    if category:
        cat_lower = category.lower()
        candidates = [
            c for c in candidates
            if cat_lower in c.get("category", "").lower()
            or cat_lower in c.get("subcategory", "").lower()
        ]

    if not candidates:
        return f"No products found for query='{query}' category={category}."

    try:
        embed = get_embeddings()
        query_vec = embed.embed_query(query)
        candidate_vecs = [
            embed.embed_query(f"{c['name']} {c['description']}")
            for c in candidates
        ]
        scores = [_cosine_sim(query_vec, cv) for cv in candidate_vecs]
        top_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:limit]
    except Exception:
        top_indices = list(range(min(limit, len(candidates))))

    results: list[str] = []
    for i in top_indices:
        c = candidates[i]
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
