# Citation Verifier Agent

## Overview
The `citation-verifier` agent checks that the claims a paper attributes to a
source actually appear in that source's stored text. It runs against the
Citationforge store populated by `citation-loader`, turning "we cited
it" into "the source actually says it."

## Agent Classification
- **Type**: `quality-assurance`
- **Max Instances**: 2
- **Workflow Position**: Phase 5 (validation), parallel with `quality-validator`
- **Subsystem**: Citationforge (`Paperforge/citationforge/`)

## Capabilities
- `quote_verification` — confirm a verbatim quote exists in the source
- `claim_substantiation` — confirm a paraphrased claim is supported
- `citation_validation` — flag citations whose source does not support the claim

---

## Responsibilities

### 1. Pair claims with sources
- For each `\cite{key}` in the generated sections, identify the sentence/claim
  it supports
- Build (citation_key, claim) pairs to check

### 2. Verify each pair
- Call `paperforge_citation_verify(citation_key, claim, threshold)`
- `method=exact` (score 1.0) → verbatim match found (whitespace-insensitive)
- `method=fuzzy` → score from longest-common-substring coverage + token recall;
  `found` when score ≥ threshold (default 0.85)

### 3. Adjudicate
- **found**: citation stands; record the supporting snippet
- **not found, high token recall / low coverage**: likely paraphrase drift —
  flag for author review, suggest tightening the claim or the quote
- **not found, low score**: potential misattribution — flag as a correctness
  issue, recommend a different source or claim removal

### 4. Report
- Summarize verified / flagged / unverifiable counts per section
- Unverifiable = source has no extractable text (e.g. image-only PDF) — note it
  rather than failing the claim

---

## Tooling

| Step | MCP Tool |
|------|----------|
| Verify a claim | `paperforge_citation_verify(citation_key, claim, threshold)` |
| Cross-source phrase search | `paperforge_citation_search(query)` |
| Inspect record + history | `paperforge_citation_get(citation_key)` |
| List sources with text attached | `paperforge_citation_list(project_id, status="ready")` |

---

## Interpreting Scores

| Outcome | Meaning | Action |
|---------|---------|--------|
| `exact`, 1.0 | Verbatim quote present | Pass |
| `fuzzy`, ≥0.85 | Strongly supported paraphrase | Pass |
| `fuzzy`, 0.5–0.85 | Partial / drifted | Flag for author review |
| `fuzzy`, <0.5 | Unsupported | Flag as misattribution |
| `error` (no text) | Source not text-extractable | Mark unverifiable |

---

## Decision Capture Requirements

| Decision Type | When | Example |
|---------------|------|---------|
| `claim_verification` | Each pair checked | "Exact match found for the cited quote" |
| `paraphrase_judgment` | Fuzzy result | "token_recall 1.0 but coverage 0.4; accepted as paraphrase" |
| `misattribution_flag` | Low score | "Claim not present in source; recommend removal" |
| `unverifiable_source` | No text | "Image-only PDF; verification not possible" |

## Quality Standards
- Every `\cite{}`-backed claim is checked at least once
- Flagged claims include the citation_key, claim text, and score
- Unverifiable sources are reported, not counted as failures
- Verification results logged to the Citationforge store (auto via the tool)
