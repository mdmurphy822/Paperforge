"""
Citationforge configuration — paths and source types.

Citationforge is a Paperforge subsystem that stores the source text behind
every citation, locally, so citations can be verified and re-verified
against the actual source text. It makes no network calls of any kind.

Paths are resolved relative to this file so the package is importable
standalone, but can be overridden to match a host project's own path
conventions via the env vars below.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CITATIONFORGE_DIR = Path(__file__).resolve().parent
PAPERFORGE_DIR = CITATIONFORGE_DIR.parent
PROJECT_ROOT = PAPERFORGE_DIR.parent

DB_PATH = Path(os.environ.get("CITATIONFORGE_DB", CITATIONFORGE_DIR / "citations.db"))

# ---------------------------------------------------------------------------
# Source types
# ---------------------------------------------------------------------------
SOURCE_URL = "url"      # direct link to a PDF or other binary document
SOURCE_PDF = "pdf"      # alias for url that is known to be a PDF
SOURCE_DOI = "doi"      # DOI (e.g. 10.1038/s41586-020-2649-2)
SOURCE_HTML = "html"    # web page snapshotted to local text

SOURCE_TYPES = {SOURCE_URL, SOURCE_PDF, SOURCE_DOI, SOURCE_HTML}
