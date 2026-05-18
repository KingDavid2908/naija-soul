import logging

from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool

from agents.embeddings import get_embeddings

logger = logging.getLogger("naija-soul")

EMBED_DIMS = 3072


def _create_store() -> InMemoryStore:
    try:
        embed = get_embeddings()
        store = InMemoryStore(index={"embed": embed, "dims": EMBED_DIMS})
        logger.info("InMemoryStore with Google Gemini embeddings (semantic search)")
    except Exception as exc:
        logger.warning("Gemini embeddings failed (%s); falling back to no-index store", exc)
        store = InMemoryStore()
    return store


store = _create_store()

memory_tools = [
    create_manage_memory_tool(namespace=("user_profiles",), store=store),
    create_search_memory_tool(namespace=("user_profiles",), store=store),
]
