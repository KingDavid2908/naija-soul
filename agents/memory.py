import json
import logging
import os
import threading
from pathlib import Path

from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool

from agents.embeddings import get_embeddings

logger = logging.getLogger("naija-soul")

EMBED_DIMS = 3072
PERSIST_FILE = Path(os.getenv("NAIJA_SOUL_MEMORY_FILE", "/tmp/naija_soul_memory.json"))
_lock = threading.Lock()


def _load_persisted() -> dict:
    if PERSIST_FILE.exists():
        try:
            with open(PERSIST_FILE, "r") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("Failed to load persisted memory: %s", exc)
    return {}


def _save_persisted(data: dict) -> None:
    try:
        PERSIST_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PERSIST_FILE, "w") as f:
            json.dump(data, f)
    except Exception as exc:
        logger.warning("Failed to persist memory: %s", exc)


def _replay_into_store(store: InMemoryStore, data: dict) -> None:
    for namespace_str, items in data.items():
        ns = tuple(namespace_str.split("/"))
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                mem_id = item.get("id") or item.get("key", "")
                content = item.get("content") or item.get("value", {})
                if mem_id and content:
                    try:
                        store.put(ns, mem_id, content)
                    except Exception:
                        pass


class PersistedInMemoryStore(InMemoryStore):
    def put(self, namespace, key, value):
        super().put(namespace, key, value)
        _save_persisted(self._dump_all())

    def _dump_all(self) -> dict:
        result = {}
        try:
            for namespace, items in self._data.items():
                ns_key = "/".join(namespace)
                result[ns_key] = [
                    {"key": k, "content": v}
                    for k, v in items.items()
                ]
        except AttributeError:
            pass
        return result


def _create_store() -> PersistedInMemoryStore:
    try:
        embed = get_embeddings()
        store = PersistedInMemoryStore(index={"embed": embed, "dims": EMBED_DIMS})
        logger.info("InMemoryStore with Google Gemini embeddings (semantic search)")
    except Exception as exc:
        logger.warning("Gemini embeddings failed (%s); falling back to no-index store", exc)
        store = PersistedInMemoryStore()

    persisted = _load_persisted()
    if persisted:
        _replay_into_store(store, persisted)
        logger.info("Loaded %d namespaces from persisted memory", len(persisted))

    return store


store = _create_store()

memory_tools = [
    create_manage_memory_tool(namespace=("user_profiles",), store=store, schema=dict),
    create_search_memory_tool(namespace=("user_profiles",), store=store),
]
