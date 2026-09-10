"""
Citationforge — a Paperforge subsystem that stores the source text behind
every citation, locally, so claims can be verified and re-verified against
the real source instead of trusting metadata alone.

This package performs NO network access of any kind. You (or the LLM
driving Paperforge) supply the source text — pasted from wherever you
already have it — and Citationforge stores and matches against it.

Public facade
-------------
    init()                          create the store
    add(...)                        register a citation (metadata only)
    add_text(citation_key, text)    attach the source text for a citation
    verify(citation_key, claim)     check a quote/claim against the stored text
    get(citation_key)               citation record + verification history
    citations(project_id, status)   list citations
    ingest_bibtex(text_or_path)     bulk-register from a .bib file (metadata only)
    search(query)                   FTS phrase search across stored documents
    stats()                         store summary
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from . import config, store, verifier as _verify

__all__ = [
    "init", "add", "add_text", "verify", "get", "citations",
    "ingest_bibtex", "search", "stats", "config",
]

def init(db_path: Optional[Path] = None) -> None:
    store.init_db(db_path)


def add(citation_key: str, source_type: str, identifier: Optional[str] = None,
        url: Optional[str] = None, project_id: Optional[str] = None,
        title: Optional[str] = None, authors: Optional[str] = None,
        year: Optional[str] = None, bibtex: Optional[str] = None,
        notes: Optional[str] = None, db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Register a citation without fetching anything."""
    if source_type not in config.SOURCE_TYPES:
        return {"status": "error",
                "error": f"invalid source_type '{source_type}'; "
                         f"expected one of {sorted(config.SOURCE_TYPES)}"}
    init(db_path)
    store.add_citation(citation_key, source_type, db_path, identifier=identifier,
                       url=url, project_id=project_id, title=title, authors=authors,
                       year=year, bibtex=bibtex, notes=notes, status="pending")
    return store.get_citation(citation_key, db_path)


def add_text(citation_key: str, text: str, source_type: Optional[str] = None,
             identifier: Optional[str] = None, url: Optional[str] = None,
             project_id: Optional[str] = None, title: Optional[str] = None,
             authors: Optional[str] = None, year: Optional[str] = None,
             page_count: Optional[int] = None, db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Attach source text to a citation so it can be verified against.

    Registers the citation if it doesn't exist yet (requires source_type).
    You supply the text yourself — Citationforge never fetches it.
    """
    init(db_path)
    cit = store.get_citation(citation_key, db_path)
    if cit is None:
        if not source_type:
            return {"status": "error",
                    "error": "unknown citation_key — provide source_type to "
                             "register it first"}
        store.add_citation(citation_key, source_type, db_path, identifier=identifier,
                           url=url, project_id=project_id, title=title, authors=authors,
                           year=year, status="pending")
        cit = store.get_citation(citation_key, db_path)

    store.set_document_text(cit["id"], text, page_count, db_path)
    store.update_citation(citation_key, db_path, status="ready")
    out = store.get_citation(citation_key, db_path)
    out["has_text"] = True
    return out


def verify(citation_key: str, claim: str, threshold: float = 0.85,
           db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Check whether ``claim`` appears in the stored text for this citation."""
    init(db_path)
    cit = store.get_citation(citation_key, db_path)
    if cit is None:
        return {"status": "error", "error": f"unknown citation_key '{citation_key}'"}
    text = store.get_document_text(cit["id"], db_path)
    if not text:
        return {"status": "error", "citation_key": citation_key,
                "error": "citation has no source text yet; call add_text() first"}
    result = _verify.verify_text(text or "", claim, threshold=threshold)
    if result.get("error"):
        result["status"] = "error"
    else:
        store.record_verification(
            cit["id"], claim, result["found"], method=result["method"],
            match_score=result["score"], snippet=result["snippet"], db_path=db_path,
        )
        result["status"] = "ok"
    result["citation_key"] = citation_key
    result["title"] = cit.get("title")
    result["local_path"] = cit.get("local_path")
    return result


def get(citation_key: str, db_path: Optional[Path] = None) -> Dict[str, Any]:
    init(db_path)
    cit = store.get_citation(citation_key, db_path)
    if cit is None:
        return {"status": "error", "error": f"unknown citation_key '{citation_key}'"}
    cit["verifications"] = store.get_verifications(cit["id"], db_path)
    cit["has_text"] = store.get_document_text(cit["id"], db_path) is not None
    return cit


def citations(project_id: Optional[str] = None, status: Optional[str] = None,
              db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    init(db_path)
    return store.list_citations(project_id=project_id, status=status, db_path=db_path)


def search(query: str, limit: int = 20, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    init(db_path)
    return store.search_documents(query, db_path=db_path, limit=limit)


def stats(db_path: Optional[Path] = None) -> Dict[str, Any]:
    init(db_path)
    return store.stats(db_path)


# ---------------------------------------------------------------------------
# BibTeX ingest (minimal brace-aware parser — no external dependency)
# ---------------------------------------------------------------------------
_TYPE_RE = re.compile(r"\w+")
_FIELD_RE = re.compile(r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|[^,\n]+)", re.DOTALL)


def _clean(v: str) -> str:
    v = v.strip().rstrip(",").strip()
    if v and v[0] in "{\"" and v[-1] in "}\"":
        v = v[1:-1]
    return re.sub(r"\s+", " ", v).strip()


def parse_bibtex(text: str) -> List[Dict[str, str]]:
    """Parse @type{key, field=value, ...} entries by balancing braces.

    Tolerant of single-line and multi-line entries, nested braces, and the
    leading @comment/@string noise that regex parsers choke on.
    """
    entries: List[Dict[str, str]] = []
    n = len(text)
    i = 0
    while True:
        at = text.find("@", i)
        if at < 0:
            break
        m = _TYPE_RE.match(text, at + 1)
        if not m:
            i = at + 1
            continue
        etype = m.group(0)
        j = m.end()
        while j < n and text[j].isspace():
            j += 1
        if j >= n or text[j] != "{":
            i = at + 1
            continue
        depth, k = 0, j
        while k < n:
            if text[k] == "{":
                depth += 1
            elif text[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        if depth != 0:
            break  # unterminated entry
        body = text[j + 1:k]
        i = k + 1
        if etype.lower() in ("comment", "string", "preamble"):
            continue
        comma = body.find(",")
        key = (body[:comma] if comma >= 0 else body).strip()
        field_str = body[comma + 1:] if comma >= 0 else ""
        if not key:
            continue
        fields = {fk.lower(): _clean(fv) for fk, fv in _FIELD_RE.findall(field_str)}
        fields["_type"] = etype.lower()
        fields["_key"] = key
        entries.append(fields)
    return entries


def _classify(entry: Dict[str, str]) -> Dict[str, Optional[str]]:
    """Pick a source_type + identifier/url for a bib entry."""
    doi = entry.get("doi")
    url = entry.get("url")
    if doi:
        return {"source_type": config.SOURCE_DOI, "identifier": doi, "url": None}
    if url:
        st = config.SOURCE_PDF if url.lower().split("?")[0].endswith(".pdf") else config.SOURCE_URL
        return {"source_type": st, "identifier": url, "url": url}
    return {"source_type": config.SOURCE_URL, "identifier": None, "url": None}


def ingest_bibtex(text_or_path: Union[str, Path], project_id: Optional[str] = None,
                  db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Register every entry in a .bib file/string (metadata only — no text)."""
    init(db_path)
    raw = text_or_path
    p = Path(str(text_or_path))
    try:
        if len(str(text_or_path)) < 4096 and p.exists():
            raw = p.read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        raw = text_or_path

    entries = parse_bibtex(raw)
    added = []
    for e in entries:
        cls = _classify(e)
        store.add_citation(
            e["_key"], cls["source_type"], db_path,
            identifier=cls["identifier"], url=cls["url"], project_id=project_id,
            title=e.get("title"), authors=e.get("author"), year=e.get("year"),
            container=e.get("journal") or e.get("booktitle") or e.get("publisher"),
            status="pending",
        )
        added.append(e["_key"])

    return {"status": "ok", "parsed": len(entries), "added": added}
