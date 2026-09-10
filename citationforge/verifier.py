"""
Citationforge verification — check whether a claim/quote actually appears in a
mirrored document's extracted text.

Pure functions over (text, claim); no I/O. The package facade loads the text
from the store, calls :func:`verify_text`, and records the result.

Strategy:
  1. Exact (whitespace-flexible, case-insensitive) regex match. PDF text
     extraction injects line breaks, so a verbatim quote rarely matches a naive
     substring search; matching across ``\\s+`` fixes that. -> score 1.0.
  2. Fuzzy fallback: longest common substring coverage + token recall, anchored
     to a human-readable snippet. Useful for paraphrase / OCR drift / minor edits.
"""

import re
from difflib import SequenceMatcher
from typing import Any, Dict

_WS = re.compile(r"\s+")
_WORD = re.compile(r"\w+")


def _norm(s: str) -> str:
    return _WS.sub(" ", (s or "").strip().lower())


def _flexible_pattern(claim: str) -> str:
    return r"\s+".join(re.escape(tok) for tok in claim.split())


def _snippet(text: str, start: int, end: int, pad: int = 160) -> str:
    a = max(0, start - pad)
    b = min(len(text), end + pad)
    body = _WS.sub(" ", text[a:b].strip())
    return ("… " if a > 0 else "") + body + (" …" if b < len(text) else "")


def verify_text(text: str, claim: str, threshold: float = 0.85) -> Dict[str, Any]:
    result = {
        "found": False, "method": None, "score": 0.0, "snippet": None,
        "lcs_coverage": 0.0, "token_recall": 0.0, "error": None,
    }
    if not (text or "").strip():
        result["error"] = "no extracted text for this citation"
        return result
    if not (claim or "").strip():
        result["error"] = "empty claim"
        return result

    # 1. Exact, whitespace-flexible, case-insensitive.
    try:
        match = re.search(_flexible_pattern(claim), text, re.IGNORECASE | re.DOTALL)
    except re.error:
        match = None
    if match:
        result.update(found=True, method="exact", score=1.0,
                      lcs_coverage=1.0, token_recall=1.0,
                      snippet=_snippet(text, match.start(), match.end()))
        return result

    # 2. Fuzzy.
    nt, nc = _norm(text), _norm(claim)
    sm = SequenceMatcher(None, nt, nc, autojunk=False)
    lm = sm.find_longest_match(0, len(nt), 0, len(nc))
    lcs_cov = lm.size / len(nc) if nc else 0.0

    claim_toks = _WORD.findall(nc)
    text_toks = set(_WORD.findall(nt))
    token_recall = (
        sum(1 for t in claim_toks if t in text_toks) / len(claim_toks)
        if claim_toks else 0.0
    )
    score = max(lcs_cov, token_recall * 0.9)

    snippet = None
    if claim_toks:
        anchor = max(claim_toks, key=len)
        am = re.search(re.escape(anchor), text, re.IGNORECASE)
        if am:
            snippet = _snippet(text, am.start(), am.end())
    result.update(found=score >= threshold or token_recall >= 0.95,
                  method="fuzzy", score=round(score, 4),
                  lcs_coverage=round(lcs_cov, 4),
                  token_recall=round(token_recall, 4), snippet=snippet)
    return result
