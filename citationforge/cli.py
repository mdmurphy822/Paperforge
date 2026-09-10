#!/usr/bin/env python3
"""
Citationforge CLI — store citation source text locally, verify claims against it.

Usage:
    python -m citationforge init
    python -m citationforge add KEY SOURCE_TYPE [--id ID] [--url URL] [--project P] [--title T]
    python -m citationforge add-text KEY --file TEXT_FILE [--source-type T] [--id ID] [--url URL] [--project P] [--title T]
    python -m citationforge verify KEY "quoted claim text" [--threshold 0.85]
    python -m citationforge get KEY
    python -m citationforge list [--project P] [--status ready|pending]
    python -m citationforge ingest path/to/bibliography.bib [--project P]
    python -m citationforge search "phrase"
    python -m citationforge stats

SOURCE_TYPE is one of: url, pdf, doi, html. Citationforge never fetches
anything itself — you supply the source text (e.g. --file a .txt you already
extracted) and it stores/matches against it locally.
"""

import argparse
import json
import sys


def _emit(obj):
    print(json.dumps(obj, indent=2, default=str))


def main(argv=None):
    # Allow running as a script (python cli.py) or module (python -m citationforge).
    if __package__:
        from . import add, add_text, citations, get, ingest_bibtex, init, search, stats, verify
    else:  # pragma: no cover - direct script execution
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from citationforge import (add, add_text, citations, get, ingest_bibtex,
                                    init, search, stats, verify)

    p = argparse.ArgumentParser(prog="citationforge", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")

    s = sub.add_parser("add")
    s.add_argument("key"); s.add_argument("source_type")
    s.add_argument("--id"); s.add_argument("--url")
    s.add_argument("--project"); s.add_argument("--title")

    s = sub.add_parser("add-text")
    s.add_argument("key")
    s.add_argument("--file", required=True, help="path to a text file with the source content")
    s.add_argument("--source-type", dest="source_type")
    s.add_argument("--id"); s.add_argument("--url")
    s.add_argument("--project"); s.add_argument("--title")

    s = sub.add_parser("verify")
    s.add_argument("key"); s.add_argument("claim")
    s.add_argument("--threshold", type=float, default=0.85)

    s = sub.add_parser("get"); s.add_argument("key")

    s = sub.add_parser("list")
    s.add_argument("--project"); s.add_argument("--status")

    s = sub.add_parser("ingest")
    s.add_argument("bibfile")
    s.add_argument("--project")

    s = sub.add_parser("search"); s.add_argument("query")

    sub.add_parser("stats")

    args = p.parse_args(argv)

    if args.cmd == "init":
        init(); _emit({"status": "ok", "message": "store initialized"})
    elif args.cmd == "add":
        _emit(add(args.key, args.source_type, identifier=args.id, url=args.url,
                  project_id=args.project, title=args.title))
    elif args.cmd == "add-text":
        from pathlib import Path
        text = Path(args.file).read_text(encoding="utf-8", errors="replace")
        _emit(add_text(args.key, text, source_type=args.source_type, identifier=args.id,
                       url=args.url, project_id=args.project, title=args.title))
    elif args.cmd == "verify":
        _emit(verify(args.key, args.claim, threshold=args.threshold))
    elif args.cmd == "get":
        _emit(get(args.key))
    elif args.cmd == "list":
        _emit(citations(project_id=args.project, status=args.status))
    elif args.cmd == "ingest":
        _emit(ingest_bibtex(args.bibfile, project_id=args.project))
    elif args.cmd == "search":
        _emit(search(args.query))
    elif args.cmd == "stats":
        _emit(stats())


if __name__ == "__main__":
    main()
