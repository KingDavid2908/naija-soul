import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger("naija-soul")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _get_name(rec: dict) -> str:
    return (
        rec.get("name")
        or rec.get("Book")
        or rec.get("product_title")
        or rec.get("title", "")
    )


def _get_desc(rec: dict) -> str:
    return (
        rec.get("description")
        or rec.get("Description")
        or rec.get("review_body")
        or rec.get("reviewText", "")
    )


def _get_cat(rec: dict) -> str:
    raw = rec.get("category") or rec.get("categories") or rec.get("product_category") or ""
    if isinstance(raw, list):
        return raw[0] if raw else "unknown"
    return str(raw).split(",")[0].strip() if raw else "unknown"


def _get_subcat(rec: dict) -> str:
    raw = rec.get("subcategory") or rec.get("categories") or rec.get("Genres") or ""
    if isinstance(raw, list):
        return ", ".join(str(x) for x in raw)
    return str(raw)


def _iter_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(DATA_DIR.rglob("*.json")):
        src = path.parent.name
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                name = _get_name(rec) or ""
                desc = _get_desc(rec) or ""
                cat = _get_cat(rec)
                sub = _get_subcat(rec)
                records.append({
                    "name": name[:500],
                    "description": desc[:1000],
                    "category": cat[:100],
                    "subcategory": sub[:200],
                    "source": src,
                })
    return records


class ProductStore:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._build_index()

    def _build_index(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "CREATE VIRTUAL TABLE products USING fts5("
            "  name, description, category, subcategory, source"
            ")"
        )
        records = _iter_records()
        for r in records:
            cur.execute(
                "INSERT INTO products VALUES (?, ?, ?, ?, ?)",
                (r["name"], r["description"], r["category"], r["subcategory"], r["source"]),
            )
        self.conn.commit()
        logger.info("ProductStore built with %d records", len(records))

    def search(self, query: str, limit: int = 100) -> list[dict[str, Any]]:
        fts5_query = self._sanitize_fts5_query(query)
        sql = (
            "SELECT rowid, name, description, category, subcategory, source, rank "
            "FROM products WHERE products MATCH ? ORDER BY rank LIMIT ?"
        )
        cols = ["rowid", "name", "description", "category", "subcategory", "source", "rank"]
        return [
            dict(zip(cols, row))
            for row in self.conn.execute(sql, (fts5_query, limit))
        ]

    @staticmethod
    def _sanitize_fts5_query(query: str) -> str:
        special = set('"\'()*:^~+-,!@#$%&|;<=>?/[]{}')
        escaped = []
        for ch in query:
            if ch in special:
                escaped.append(f'"{ch}"')
            elif ch.isspace():
                escaped.append(" ")
            else:
                escaped.append(ch)
        parts = "".join(escaped).split()
        if not parts:
            return ""
        return " OR ".join(parts) + "*"

    @property
    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]


store = ProductStore()
