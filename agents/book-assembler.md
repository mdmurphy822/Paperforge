# Book Assembler Agent

## Overview
The `book-assembler` agent handles book-specific assembly tasks: source material processing, chapter-to-LaTeX conversion, template variable substitution, and final book assembly with series support.

## Agent Classification
- **Type**: `specialized`
- **Max Instances**: 1
- **Workflow Position**: Phase 1 (source_processing) and Phase 3 (assembly)
- **Execution**: Sequential

## Capabilities
- `book_assembly` - Assemble book.tex from template with \input{} calls
- `chapter_formatting` - Convert markdown essays to book-class LaTeX chapters
- `series_management` - Read/update series.json manifests, track volumes
- `dark_mode_compilation` - Handle dark-mode template compilation quirks

---

## Responsibilities

### Phase 1: Source Processing
- Extract content from .docx research files (bring your own .docx extractor; python-docx is the natural fit)
- Stage markdown essays into project inputs
- Format appendix material (e.g., classical texts split into books/sections)
- Validate all source material is present and readable

### Phase 3: Assembly
- Load book template from `templates/latex/book/`
- Substitute template variables: `{{TITLE}}`, `{{SERIES_TITLE}}`, `{{VOLUME}}`, `{{SUBTITLE}}`, `{{AUTHOR}}`, `{{DATE}}`, `{{FRONT_MATTER}}`, `{{PARTS_AND_CHAPTERS}}`, `{{APPENDICES}}`, `{{BIBLIOGRAPHY}}`
- Generate `\input{sections/...}` calls for all parts, chapters, appendices
- Copy all .tex section files to `06_final_output/sections/`
- Write assembled `book.tex` to `06_final_output/`

---

## Markdown-to-LaTeX Conversion Rules

When converting source markdown essays to LaTeX chapters:

1. **Process inline formatting BEFORE escaping** to avoid corrupting LaTeX commands
2. Convert `**bold**` to `\textbf{...}`, `*italic*` to `\textit{...}`
3. Convert markdown headers to `\section*{}`, `\subsection*{}`
4. Convert blockquotes to `\begin{bookquote}...\end{bookquote}`
5. Convert lists to `\begin{itemize}...\end{itemize}`
6. Escape LaTeX special characters: `& % $ # _ { } ~ ^`
7. Replace Unicode characters with LaTeX equivalents (em dashes, curly quotes, etc.)

---

## Template: Dark Charcoal Book

Located at `templates/latex/book/dark_charcoal_book.tex`:

- **Document class**: `book` with `openany` option
- **Fonts**: Palatino (mathpazo) - 8-bit encoding, requires Unicode-to-LaTeX conversion
- **Color palette**: Dark charcoal (#2D2D2D) background, light gray (#E8E8E8) text, silver (#C0C0C0) headers, gold (#D4AF37) accents
- **Custom environments**: `bookquote`, `keyinsight`, `bookepigraph`, `styledforeword`,
  `chapteroverview`, `sectionoverview`, `chaptersummary`, `sectionsummary`,
  `learningobjectives`, `keyvocabulary`, `connectionbox`, `reflectionprompt`,
  `definition`, `principle`, `example`, `aside`, `equationbox`, `notation`/`vardefs`,
  `resultbox`
- **Theorem environments**: `theorem`, `lemma`, `corollary`, `proposition`, `remark`, `proof`
- **Custom commands**: `\term{}`, `\sectionornament`, `\chapterornament`, `\letterspacedtext`
- **Code listings**: `lstlisting` with dark-mode styling pre-configured
- **TOC**: Uses `titletoc` (NOT `tocloft` - incompatible with `titlesec` part formatting)
- **Compilation**: Tectonic (handles multi-pass automatically)

---

## Series Manifest Format

```json
{
  "series_id": "series_name",
  "series_title": "Display Title",
  "template": "book/dark_charcoal_book",
  "theme": "charcoal_silver",
  "volumes": [
    {
      "volume": 1,
      "title": "Volume Title",
      "subtitle": "Volume Subtitle",
      "status": "completed|in_progress|planned",
      "project_id": "YYYYMMDD_HHMMSS_slug"
    }
  ]
}
```

---

## Book Export Structure

```
exports/YYYYMMDD_HHMMSS_book_title/
├── 01_planning/
│   └── book_outline.md
├── 02_source_processing/
│   └── research_extracted/
├── 03_content_development/
│   ├── front_matter.tex
│   ├── part_01.tex ... part_NN.tex
│   ├── chapter_01.tex ... chapter_NN.tex
│   └── back_matter.tex
├── 04_appendices/
│   └── appendix_a_*.tex
├── 05_validation/
│   └── quality_report.json
├── 06_final_output/
│   ├── book.tex
│   ├── book.pdf
│   ├── book.md
│   └── sections/
├── project_metadata.json
└── project_log.md
```

---

## Bibliography Assembly

When the book uses citations (`\cite{}`):
1. Collect all `.bib` entries from `04_citations/bibliography.bib`
2. Copy `bibliography.bib` to `06_final_output/`
3. Set the `{{BIBLIOGRAPHY}}` template variable to:
   ```latex
   \bibliographystyle{IEEEtran}
   \bibliography{bibliography}
   ```
4. If no citations: set `{{BIBLIOGRAPHY}}` to empty string

---

## Index Generation

When makeidx is used:
1. Add `\index{term}` entries during content generation for key terms
2. Tectonic handles `makeindex` automatically during compilation
3. `\printindex` is included in the template after bibliography
4. If no index entries: `\printindex` produces nothing (safe to leave in)

---

## Decision Capture

Log decisions to `training-captures/paperforge/{PROJECT_ID}/`:
- `phase_source_processing/` - Source selection, extraction choices
- `phase_assembly/` - Template selection, variable substitution, structure decisions
