"""
Citationforge SQLite store.

Holds one row per cited document plus the extracted full text (for quote-level
verification) and a log of every verification check that has been run.

Tables
------
citations      one row per citation key; metadata + local mirror location + status
documents      extracted plain text of the mirrored document (1:1 with citations)
documents_fts  FTS5 index over documents.text for cross-document phrase search
verifications  append-only log of claim/quote checks against a citation
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection(db_path: Optional[Path] = None, timeout: float = 30.0):
    path = Path(db_path or config.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=timeout)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Optional[Path] = None) -> None:
    """Create tables if they do not exist. Idempotent."""
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS citations (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                citation_key  TEXT UNIQUE NOT NULL,
                project_id    TEXT,
                source_type   TEXT NOT NULL,
                identifier    TEXT,
                title         TEXT,
                authors       TEXT,
                year          TEXT,
                container     TEXT,
                url           TEXT,
                local_path    TEXT,
                content_hash  TEXT,
                mime_type     TEXT,
                file_size     INTEGER,
                http_status   INTEGER,
                status        TEXT NOT NULL DEFAULT 'pending',
                error         TEXT,
                bibtex        TEXT,
                notes         TEXT,
                fetched_at    TEXT,
                created_at    TEXT NOT NULL,
                updated_at    TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_citations_project ON citations(project_id);
            CREATE INDEX IF NOT EXISTS idx_citations_status  ON citations(status);
            CREATE INDEX IF NOT EXISTS idx_citations_hash    ON citations(content_hash);

            CREATE TABLE IF NOT EXISTS documents (
                citation_id   INTEGER PRIMARY KEY,
                text          TEXT,
                char_count    INTEGER,
                page_count    INTEGER,
                extracted_at  TEXT,
                FOREIGN KEY (citation_id) REFERENCES citations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS verifications (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                citation_id   INTEGER NOT NULL,
                claim         TEXT NOT NULL,
                method        TEXT,
                found         INTEGER NOT NULL,
                match_score   REAL,
                snippet       TEXT,
                page          INTEGER,
                checked_at    TEXT NOT NULL,
                FOREIGN KEY (citation_id) REFERENCES citations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_verif_citation ON verifications(citation_id);
            """
        )
        # FTS5 is optional; degrade gracefully if the SQLite build lacks it.
        try:
            conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts "
                "USING fts5(citation_id UNINDEXED, text)"
            )
        except sqlite3.OperationalError:
            pass


def _has_fts(conn) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='documents_fts'"
    ).fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# Citations
# ---------------------------------------------------------------------------
_CITATION_FIELDS = {
    "project_id", "source_type", "identifier", "title", "authors", "year",
    "container", "url", "local_path", "content_hash", "mime_type", "file_size",
    "http_status", "status", "error", "bibtex", "notes", "fetched_at",
}


def add_citation(citation_key: str, source_type: str, db_path: Optional[Path] = None,
                 **fields) -> int:
    """Insert (or update if the key exists) a citation. Returns its row id."""
    now = _now()
    cols = {k: v for k, v in fields.items() if k in _CITATION_FIELDS}
    cols["source_type"] = source_type
    with get_connection(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM citations WHERE citation_key=?", (citation_key,)
        ).fetchone()
        if existing:
            cid = existing["id"]
            if cols:
                sets = ", ".join(f"{k}=?" for k in cols)
                conn.execute(
                    f"UPDATE citations SET {sets}, updated_at=? WHERE id=?",
                    (*cols.values(), now, cid),
                )
            return cid
        cols.setdefault("status", "pending")
        keys = ["citation_key", *cols.keys(), "created_at", "updated_at"]
        vals = [citation_key, *cols.values(), now, now]
        placeholders = ", ".join("?" * len(keys))
        cur = conn.execute(
            f"INSERT INTO citations ({', '.join(keys)}) VALUES ({placeholders})", vals
        )
        return cur.lastrowid


def update_citation(citation_key: str, db_path: Optional[Path] = None, **fields) -> bool:
    cols = {k: v for k, v in fields.items() if k in _CITATION_FIELDS}
    if not cols:
        return False
    with get_connection(db_path) as conn:
        sets = ", ".join(f"{k}=?" for k in cols)
        cur = conn.execute(
            f"UPDATE citations SET {sets}, updated_at=? WHERE citation_key=?",
            (*cols.values(), _now(), citation_key),
        )
        return cur.rowcount > 0


def get_citation(citation_key: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM citations WHERE citation_key=?", (citation_key,)
        ).fetchone()
        return dict(row) if row else None


def get_citation_by_id(citation_id: int, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM citations WHERE id=?", (citation_id,)).fetchone()
        return dict(row) if row else None


def list_citations(project_id: Optional[str] = None, status: Optional[str] = None,
                   db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    clauses, params = [], []
    if project_id:
        clauses.append("project_id=?")
        params.append(project_id)
    if status:
        clauses.append("status=?")
        params.append(status)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM citations {where} ORDER BY created_at DESC", params
        ).fetchall()
        return [dict(r) for r in rows]


def delete_citation(citation_key: str, db_path: Optional[Path] = None) -> bool:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM citations WHERE citation_key=?", (citation_key,)
        ).fetchone()
        if not row:
            return False
        cid = row["id"]
        if _has_fts(conn):
            conn.execute("DELETE FROM documents_fts WHERE citation_id=?", (cid,))
        conn.execute("DELETE FROM citations WHERE id=?", (cid,))
        return True


# ---------------------------------------------------------------------------
# Document text
# ---------------------------------------------------------------------------
def set_document_text(citation_id: int, text: str, page_count: Optional[int] = None,
                      db_path: Optional[Path] = None) -> None:
    now = _now()
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO documents (citation_id, text, char_count, page_count, extracted_at) "
            "VALUES (?,?,?,?,?) "
            "ON CONFLICT(citation_id) DO UPDATE SET "
            "text=excluded.text, char_count=excluded.char_count, "
            "page_count=excluded.page_count, extracted_at=excluded.extracted_at",
            (citation_id, text, len(text or ""), page_count, now),
        )
        if _has_fts(conn):
            conn.execute("DELETE FROM documents_fts WHERE citation_id=?", (citation_id,))
            if text:
                conn.execute(
                    "INSERT INTO documents_fts (citation_id, text) VALUES (?,?)",
                    (citation_id, text),
                )


def get_document_text(citation_id: int, db_path: Optional[Path] = None) -> Optional[str]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT text FROM documents WHERE citation_id=?", (citation_id,)
        ).fetchone()
        return row["text"] if row else None


def search_documents(query: str, db_path: Optional[Path] = None,
                     limit: int = 20) -> List[Dict[str, Any]]:
    """FTS phrase search across all mirrored documents."""
    with get_connection(db_path) as conn:
        if not _has_fts(conn):
            return []
        rows = conn.execute(
            "SELECT f.citation_id, c.citation_key, c.title, "
            "snippet(documents_fts, 1, '[', ']', ' ... ', 12) AS snippet "
            "FROM documents_fts f JOIN citations c ON c.id = f.citation_id "
            "WHERE documents_fts MATCH ? LIMIT ?",
            (query, limit),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Verifications
# ---------------------------------------------------------------------------
def record_verification(citation_id: int, claim: str, found: bool,
                        method: str = "exact", match_score: Optional[float] = None,
                        snippet: Optional[str] = None, page: Optional[int] = None,
                        db_path: Optional[Path] = None) -> int:
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO verifications "
            "(citation_id, claim, method, found, match_score, snippet, page, checked_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (citation_id, claim, method, 1 if found else 0, match_score, snippet, page, _now()),
        )
        return cur.lastrowid


def get_verifications(citation_id: int, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM verifications WHERE citation_id=? ORDER BY checked_at DESC",
            (citation_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------
def stats(db_path: Optional[Path] = None) -> Dict[str, Any]:
    with get_connection(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) FROM citations").fetchone()[0]
        by_status = {
            r["status"]: r["n"]
            for r in conn.execute(
                "SELECT status, COUNT(*) n FROM citations GROUP BY status"
            ).fetchall()
        }
        by_source = {
            r["source_type"]: r["n"]
            for r in conn.execute(
                "SELECT source_type, COUNT(*) n FROM citations GROUP BY source_type"
            ).fetchall()
        }
        docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        verifs = conn.execute("SELECT COUNT(*) FROM verifications").fetchone()[0]
        return {
            "total_citations": total,
            "by_status": by_status,
            "by_source": by_source,
            "documents_with_text": docs,
            "verifications_run": verifs,
        }
