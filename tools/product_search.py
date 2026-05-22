import math
from typing import Any

from langchain.tools import tool
from google.genai import Client as GenAIClient, types

from app.core.config import GOOGLE_API_KEY
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
    1. SQLite FTS5 BM25 -> top 100 candidates (fast, exact keyword match)
    2. Gemini embeddings -> cosine similarity rerank -> top-k

    Args:
        query: Free-text search.
        category: Optional filter — "food", "book", or None for all.
        limit: Number of results to return (default 5).
    """
    candidates: list[dict[str, Any]] = product_store.search(query, limit=30)
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
        texts = [query] + [
            f"{c['name']} {c['description']}" for c in candidates
        ]
        genai_client = GenAIClient(api_key=GOOGLE_API_KEY)
        contents = [types.Content(parts=[types.Part(text=t)]) for t in texts]
        result = genai_client.models.embed_content(
            model="models/gemini-embedding-2",
            contents=contents,
        )
        vectors = [e.values for e in result.embeddings]
        query_vec = vectors[0]
        candidate_vecs = vectors[1:]

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
        pid = c.get("product_id", "")
        pid_str = f" (id: {pid})" if pid else ""
        results.append(
            f"  [{source}] {name}{pid_str} — {cat}/{sub}\n"
            f"     {desc[:150]}..."
        )

    return "Products found:\n" + "\n".join(results)
