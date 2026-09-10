# Paperforge

Academic paper, whitepaper, and literature review generation from multiple sources, with a local-only citation store for tracking and verifying claims against source text.

> This is the standalone framework: agent specs, generation scripts, LaTeX/Markdown templates, and the Citationforge citation-tracking subsystem — meant to be driven by an LLM (via an MCP server or any other agent dispatcher) that supplies the research, writes the sections, and fetches nothing on this framework's behalf. It was extracted from a larger private orchestrator, so a few things you'll need to bring yourself: an MCP server (or any driver) that dispatches the agents below, and the [Tectonic](https://tectonic-typesetting.github.io/) binary for LaTeX compilation.

---

## Quick Start

```bash
# Via MCP
create_paper_project(
    title="<paper title>",
    paper_type="lit_review",
    author="<author or team name>",
    citation_style="ieee"
)
```

---

## Document Types

| Type | Description | Template |
|------|-------------|----------|
| `academic` | Research papers with methodology, findings | IEEE, arXiv-style preprint |
| `whitepaper` | Technical/business whitepapers | Technical, business |
| `lit_review` | Literature reviews and surveys | Systematic, narrative |
| `book` | Multi-chapter books with series support | Dark charcoal book |

---

## Series Management

Books can be organized into multi-volume series:

```
Paperforge/series/{series_id}/
└── series.json          # Series manifest with volume tracking
```

Series manifest tracks volumes, templates, and publication status. Create book projects via:
```python
create_book_project(
    title="Book Title",
    series_id="series_name",
    volume=1,
    subtitle="Subtitle",
    template="book/dark_charcoal_book"
)
```

---

## Workflow Pipeline

### paper_generation Workflow

```
1. planning (paper-outliner)
   └── Analyze inputs, determine paper type, create section structure, identify needed sources

2. content_generation (content-synthesizer, parallel max 10)
   └── Generate sections (ONE AGENT = ONE SECTION), citing sources as claims are made

3. citation_assembly (citation-manager + citation-loader, parallel max 4)
   └── Compile BibTeX, format bibliography, attach source text to the citation store (Citationforge)

4. validation (quality-validator + citation-verifier, parallel max 2)
   └── Academic rigor, citation completeness, claim-vs-source verification

5. compilation (latex-compiler + markdown-exporter, parallel)
   └── LaTeX → PDF, Markdown export
```

### book_generation Workflow

```
1. source_processing (book-assembler)
   └── Stage source material (essays, notes, research), format appendices

2. content_generation (content-synthesizer, parallel max 10)
   └── Convert essays to chapters (ONE AGENT = ONE CHAPTER)

3. assembly (book-assembler)
   └── Assemble book.tex from template, parts, chapters, appendices

4. compilation (latex-compiler + markdown-exporter, parallel)
   └── Tectonic → PDF, Markdown export
```

---

## Available Agents

| Agent | Purpose | Max Instances |
|-------|---------|---------------|
| `paper-outliner` | Create paper structure and section plan | 1 |
| `content-synthesizer` | Generate ONE section per instance | 10 |
| `citation-manager` | BibTeX generation, formatting | 1 |
| `citation-loader` | Attach source text to citations (Citationforge, no network) | 4 |
| `citation-verifier` | Verify claims against stored source text | 2 |
| `latex-compiler` | LaTeX → PDF compilation | 1 |
| `book-assembler` | Book assembly, chapter formatting, series management | 1 |
| `markdown-exporter` | Portable Markdown export | 1 |
| `quality-validator` | Academic rigor validation | 2 |

---

## Input Sources

### 1. Raw Content
```
inputs/raw_content/
├── notes.md           # Markdown notes
├── outline.json       # Structured outline
└── data.json          # Data/figures
```

### 2. Courseforge IMSCC
```
inputs/courseforge_packages/
└── course.imscc       # Extract modules → paper sections
```

### 3. DART-Processed Content
```
inputs/dart_processed/
└── converted_*.html   # DART-converted accessible HTML
```

### 4. Whatever research the driving LLM already has
Paperforge doesn't ship a research/retrieval tool of its own. The agent
dispatching `paper-outliner`/`content-synthesizer` is expected to supply
source material and citation candidates itself (its own knowledge, a
database you wire in, documents the user provides, etc.) — Paperforge's
job is turning that into a structured, cited document.

---

## Citationforge (local citation store & verification)

Citationforge is a Paperforge subsystem that stores the **source text behind
every citation**, locally, so citations can be verified — and re-verified —
against the actual source instead of trusting metadata alone.

**Citationforge performs no network access of any kind.** It never fetches or
mirrors anything — you (or the LLM driving Paperforge) supply the source text
directly, and Citationforge stores and matches against it.

### Why
Knowing a source exists doesn't tell you the source *supports the claim you
attached to it*. Citationforge lets you check a quote or paraphrase against
the actual text you attached.

### Location
```
Paperforge/citationforge/
└── citations.db    # SQLite: citations + source text + verification log
```

### Source types (`source_type`)
`url`, `pdf`, `doi`, `html` — these just classify where a citation nominally
points; Citationforge never dereferences them itself. You attach the actual
text with `paperforge_citation_download` (the name is legacy — it stores text
you provide, it does not fetch).

### Verification
`paperforge_citation_verify(key, claim)` runs:
1. **Exact** whitespace-/case-insensitive match (handles PDF line breaks) → score 1.0
2. **Fuzzy** fallback: longest-common-substring coverage + token recall →
   `found` when score ≥ threshold (default 0.85)

Every check is logged to the citation's verification history.

### Typical flow inside `paper_generation`
```
citation_assembly:  ingest bibliography.bib (metadata only) → attach text for each entry
validation:         for each \cite{}-backed claim → verify against stored text
```

### CLI
```bash
PYTHONPATH=Paperforge python3 -m citationforge add-text <citation_key> --file <source_text>.txt --source-type url
PYTHONPATH=Paperforge python3 -m citationforge verify <citation_key> \
    "<claim text to check against the source>"
PYTHONPATH=Paperforge python3 -m citationforge ingest bibliography.bib
```

---

## Output Formats

### LaTeX/PDF
```
exports/{PROJECT_ID}/06_final_output/
├── {Title_Slug}.tex   # Complete LaTeX source (named from paper title)
├── {Title_Slug}.pdf   # Compiled PDF (named from paper title)
└── bibliography.bib   # BibTeX references
```

### Markdown
```
exports/{PROJECT_ID}/06_final_output/
└── {Title_Slug}.md    # Portable Markdown (named from paper title)
```

> **Filename convention:** Output files are named from the paper title in `project_metadata.json` (spaces replaced with underscores, e.g. a paper titled "Example Title" exports as `Example_Title.pdf`). Falls back to `paper.pdf` if no metadata exists. Legacy projects with `paper.tex` are still supported.

---

## Critical Execution Protocols

### ONE AGENT = ONE SECTION
Each `content-synthesizer` instance works on exactly ONE section:
- No shared section editing
- No concurrent writes to same section
- Agent receives section assignment at dispatch

### Citation Requirements
- **Every factual claim must have a citation**
- Use `\cite{key}` for LaTeX inline citations
- All citations must exist in bibliography.bib
- **Default citation style: IEEE** (numeric [1], [2], [3])

### IEEE Citation Format (Default)

Paperforge uses IEEE-style numeric citations by default:

```latex
% Single citation
Research shows significant results \cite{<citation_key>}.

% Multiple citations
Studies confirm these findings \cite{<citation_key_a>, <citation_key_b>, <citation_key_c>}.

% Citation with author mention
As shown in the cited source \cite{<citation_key>}, the approach works.
```

**Critical Rules:**
- Use `\cite{key}` for ALL citations
- **NEVER use `\footnote{}` for citations**
- All citation keys must exist in `bibliography.bib`
- BibTeX style: `\bibliographystyle{IEEEtran}`

### Quality Standards
- Minimum word count per section (configurable)
- Academic tone and formal language
- Logical paragraph progression
- Clear topic sentences

---

## Project Structure

```
Paperforge/
├── CLAUDE.md                    # This file
├── agents/                      # Agent specifications
│   ├── CLAUDE.md               # Coordination protocols
│   ├── paper-outliner.md
│   ├── content-synthesizer.md
│   ├── citation-manager.md
│   ├── citation-loader.md
│   ├── citation-verifier.md
│   ├── latex-compiler.md
│   ├── book-assembler.md
│   ├── markdown-exporter.md
│   └── quality-validator.md
├── citationforge/               # Local citation store & verification subsystem (no network)
│   ├── __init__.py             # Facade: add / add_text / verify / ingest_bibtex
│   ├── config.py                # Paths, source types
│   ├── store.py                 # SQLite store (citations / documents / verifications)
│   ├── verifier.py               # Exact + fuzzy claim matching
│   ├── cli.py                    # `python -m citationforge ...`
│   └── citations.db              # Local citation store (created on first use, not shipped)
├── templates/
│   ├── latex/
│   │   ├── academic/           # IEEE, arXiv-style preprint
│   │   ├── whitepaper/         # Technical, business
│   │   ├── lit_review/         # Systematic, narrative
│   │   ├── federal/            # Federal proposal / unsolicited-proposal formatting
│   │   └── book/               # Dark charcoal book template
│   └── components/
│       └── diagrams/
├── scripts/
│   ├── html_converter/         # Paper → WCAG-compliant HTML
│   └── latex_compiler/         # Compilation engine
├── inputs/                      # Input sources (create as needed, not shipped)
├── exports/                     # Timestamped outputs (create as needed, not shipped)
├── series/                      # Multi-volume book series manifests (create as needed, not shipped)
└── runtime/                     # Temporary workspaces (create as needed, not shipped)
```

---

## Export Structure

Each paper project creates a timestamped export:

```
exports/YYYYMMDD_HHMMSS_paper_title/
├── 01_planning/
│   ├── paper_outline.md
│   └── source_plan.json
├── 03_content_development/
│   ├── section_01_introduction.tex
│   ├── section_02_literature_review.tex
│   └── ...
├── 04_citations/
│   ├── bibliography.bib
│   └── citation_index.json
├── 05_validation/
│   ├── quality_report.json
│   └── citation_coverage.json
├── 06_final_output/
│   ├── {Title_Slug}.tex   # Named from paper title
│   ├── {Title_Slug}.pdf   # Named from paper title
│   ├── {Title_Slug}.md    # Named from paper title
│   └── bibliography.bib
└── project_log.md
```

---

## Decision Capture

All agents log decisions to:
```
training-captures/paperforge/{PAPER_ID}/
├── phase_planning/
├── phase_content_generation/
├── phase_citation_assembly/
├── phase_validation/
└── phase_compilation/
```

### Required Decision Types

| Phase | Decision Types |
|-------|---------------|
| Planning | `paper_type_selection`, `section_structure`, `citation_strategy` |
| Content Gen | `source_synthesis`, `citation_placement`, `writing_style` |
| Citation | `bibtex_formatting`, `deduplication`, `style_application` |
| Validation | `quality_assessment`, `revision_needed` |
| Compilation | `template_selection`, `error_resolution` |

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `create_paper_project` | Initialize new paper project |
| `create_book_project` | Initialize new book project with series support |
| `generate_citations` | Format citations from metadata |
| `generate_bibtex` | Create BibTeX entries from metadata |
| `compile_latex` | LaTeX → PDF compilation |
| `export_markdown` | Export as Markdown |
| `parse_courseforge_for_paper` | Extract IMSCC content |
| `validate_paper_quality` | Quality validation |
| `get_paperforge_status` | Status tracking |
| `paperforge_citation_add` | Register a citation (metadata only, no text) |
| `paperforge_citation_download` | Attach source text to a citation (legacy name — no network) |
| `paperforge_citation_verify` | Verify a quote/claim against the stored source text |
| `paperforge_citation_get` | Citation record + verification history |
| `paperforge_citation_list` | List citations (by project/status) |
| `paperforge_citation_ingest_bibtex` | Bulk-register a .bib (metadata only, auto-classify source_type) |
| `paperforge_citation_search` | Full-text search across stored documents |
| `paperforge_citation_status` | Citationforge store statistics |

---

## LaTeX Compilation

Paperforge uses **Tectonic**, a self-contained LaTeX engine that requires NO system package installation. Download a binary for your platform from the [Tectonic releases page](https://github.com/tectonic-typesetting/tectonic/releases) and place it at `bin/tectonic` (not included in this repo — see Fallback below if you'd rather skip it).

### Tectonic Binary (Primary)
```
Paperforge/bin/tectonic
```

### Compilation Command
```bash
cd exports/{PROJECT}/06_final_output
../../../bin/tectonic paper.tex
```

Tectonic automatically handles:
- Multiple compilation passes
- Bibliography processing
- Font and package downloads (cached after first use)

### Fallback (Optional)
If Tectonic is unavailable, system pdflatex can be used:
```bash
sudo apt-get install texlive-latex-base texlive-latex-extra \
                     texlive-fonts-recommended texlive-bibtex-extra
```
