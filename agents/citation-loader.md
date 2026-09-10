# Citation Loader Agent

## Overview
The `citation-loader` agent attaches source text to each registered citation in
the local Citationforge store so that claims can be verified against the real
source. Citationforge performs **no network access of any kind** — this agent
supplies the text itself (from content already available to the run: inputs
already provided to the project, or text the LLM already has in context from
having read/summarized the source elsewhere) and hands it to Citationforge to
store and index.

## Agent Classification
- **Type**: `research`
- **Max Instances**: 4
- **Workflow Position**: Phase 4 (citation_assembly), parallel with `citation-manager`
- **Subsystem**: Citationforge (`Paperforge/citationforge/`)

## Capabilities
- `text_attachment` — attach source text to a registered citation
- `source_classification` — classify a citation's source_type (doi / url / pdf / html)

---

## Responsibilities

### 1. Ingest the bibliography
- Read `04_citations/bibliography.bib` for the project
- Call `paperforge_citation_ingest_bibtex` to register every entry under the
  project id (metadata only — no fetching)

### 2. Attach source text
- For each registered citation, obtain its source text from whatever the run
  already has available (a document already staged in `inputs/`, text quoted
  earlier in the conversation, or text supplied by the user)
- Call `paperforge_citation_download` — despite the name, this stores text
  you provide; it does not fetch anything over the network
- Extracted full text is indexed automatically for verification

### 3. Report coverage gaps
- Flag entries with no available source text (`missing_text`) so a human can
  supply one manually
- Never fabricate source text to fill a gap — an unverifiable citation should
  stay flagged, not silently marked complete

---

## Tooling

| Step | MCP Tool |
|------|----------|
| Register a .bib | `paperforge_citation_ingest_bibtex(bibtex, project_id)` |
| Register one source | `paperforge_citation_add(citation_key, source_type, identifier/url)` |
| Attach source text | `paperforge_citation_download(citation_key, text, ...)` |
| Inspect a record | `paperforge_citation_get(citation_key)` |
| Status | `paperforge_citation_status()` |

`source_type` is one of: `url`, `pdf`, `doi`, `html`.

---

## No-Network Policy
Citationforge makes **zero** network calls. It never fetches, mirrors, or
transmits anything — it only stores and indexes text you hand it directly.
If you don't have a source's text on hand, leave the citation flagged rather
than inventing content or trying to reach out to the network yourself.

---

## Decision Capture Requirements

| Decision Type | When | Example |
|---------------|------|---------|
| `source_classification` | Choosing source_type | "Entry has a DOI → doi source" |
| `text_source` | Where the text came from | "Attached text from inputs/report.pdf already staged for this project" |
| `coverage_gap` | No text available | "No source text available; flagged for manual supply" |

## Quality Standards
- Every citation with available source text has it attached before validation
- Coverage gaps are recorded with a reason, never silently dropped
- No fabricated or paraphrased-as-original source text — only text that actually came from the source
