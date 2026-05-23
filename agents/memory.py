# Naija Soul Memory System
#
# This module manages persistent user profiles across sessions using
# LangGraph's InMemoryStore with Gemini semantic embeddings + JSON file
# persistence for crash survival.
#
# AGENT DECISIONS:
# - On startup: loads previously saved profiles from
#   /tmp/naija_soul_memory.json so returning users are recognized
#   across container restarts
# - On manage_memory call: saves the profile dict to both the in-memory
#   semantic index (fast similarity search via Gemini embeddings) and
#   the JSON file (survives crashes)
# - On search_memory call: uses Gemini embeddings to find profiles by
#   name, ethnicity, or location keywords across all stored users
#
# The store is a singleton — both Task A and Task B agents share the
# same memory pool so user history is consistent across features.

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


# AGENT: On every profile save (manage_memory tool call), immediately
# persist to disk. This survives server crashes and Render scale-to-zero
# so the user's conversation history isn't lost between sessions.
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


# AGENT: Try to build a semantic search index with Gemini embeddings
# (3072 dimensions). This lets search_memory find profiles by meaning
# rather than exact keyword match — e.g. "Yoruba guy from Lagos" will
# match profiles tagged "yoruba" + "lagos" even if the wording differs.
# If Gemini is rate-limited, fall back to a no-index store that still
# supports exact-match lookups.
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

# AGENT: Two memory tools available to the agent:
# 1. manage_memory — saves a user profile dict (ethnicity, voice, etc.)
#    after inferring it from the user's name and location.
#    AGENT DECISION: used at the end of every interaction to persist
#    the user's history for future sessions.
# 2. search_memory — looks up existing profiles by semantic similarity.
#    AGENT DECISION: used at the start of every interaction to check
#    if this user has history — avoids generating a fresh profile
#    each time and preserves tone continuity.
memory_tools = [
    create_manage_memory_tool(namespace=("user_profiles",), store=store, schema=dict),
    create_search_memory_tool(namespace=("user_profiles",), store=store),
]
