# LaTeX Compiler Agent

## Overview
The `latex-compiler` agent assembles the complete LaTeX document from generated sections, applies templates, and compiles to PDF with bibliography processing.

## Agent Classification
- **Type**: `specialized`
- **Max Instances**: 1
- **Workflow Position**: Phase 6 (compilation)
- **Execution**: Parallel with markdown-exporter

## Capabilities
- `latex_compilation` - Multi-pass LaTeX compilation
- `pdf_generation` - Produce final PDF output
- `error_handling` - Parse and recover from LaTeX errors

---

## Responsibilities

### 1. Document Assembly
- Load appropriate LaTeX template
- Insert title page, abstract, sections
- Include bibliography file
- Add packages and preamble

### 2. Template Processing
- Substitute template variables
- Configure document class options
- Set page geometry and margins
- Apply style customizations

### 3. Compilation
- Execute multi-pass compilation sequence
- Process bibliography with bibtex/biber
- Resolve cross-references
- Generate table of contents

### 4. Error Recovery
- Parse LaTeX error logs
- Identify common error patterns
- Attempt automatic fixes
- Log unrecoverable errors

---

## Input Format

```json
{
  "project_path": "/path/to/exports/PROJECT_ID",
  "sections_path": "03_content_development",
  "bibliography_path": "04_citations/bibliography.bib",
  "template": "academic/ieee_conference",
  "metadata": {
    "title": "<paper title>",
    "author": "Research Team",
    "institution": "Research Institute",
    "date": "2026",
    "keywords": ["<keyword one>", "<keyword two>", "<keyword three>"]
  },
  "options": {
    "bibliography_style": "IEEEtran",
    "paper_size": "letter",
    "font_size": "10pt"
  }
}
```

---

## Output Format

### paper.tex (assembled document)
```latex
\documentclass[conference]{IEEEtran}

% Packages
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{hyperref}

\begin{document}

\title{<Paper Title>}

\author{
    \IEEEauthorblockN{Research Team}
    \IEEEauthorblockA{Research Institute}
}

\maketitle

\begin{abstract}
% Content from section_00_abstract.tex
\input{sections/section_00_abstract}
\end{abstract}

\begin{IEEEkeywords}
<keyword one, keyword two>
\end{IEEEkeywords}

% Main sections
\input{sections/section_01_introduction}
\input{sections/section_02_background}
\input{sections/section_03_methodology}
\input{sections/section_04_results}
\input{sections/section_05_discussion}
\input{sections/section_06_conclusion}

\bibliographystyle{IEEEtran}
\bibliography{bibliography}

\end{document}
```

### Compilation Output
```json
{
  "status": "success",
  "pdf_path": "/path/to/exports/PROJECT_ID/06_final_output/paper.pdf",
  "tex_path": "/path/to/exports/PROJECT_ID/06_final_output/paper.tex",
  "compilation_log": "compilation.log",
  "passes": 4,
  "warnings": 3,
  "errors": 0,
  "page_count": 12
}
```

---

## Compilation Sequence

### Tectonic Compilation (Recommended)
```bash
# Single command handles everything
Paperforge/bin/tectonic paper.tex
```

Tectonic automatically performs multiple passes and bibliography processing.

### Fallback: pdflatex Compilation (4-pass)
```bash
# Pass 1: Initial compilation (generates .aux)
pdflatex -interaction=nonstopmode paper.tex

# Pass 2: Process bibliography
bibtex paper

# Pass 3: Resolve citations
pdflatex -interaction=nonstopmode paper.tex

# Pass 4: Finalize cross-references
pdflatex -interaction=nonstopmode paper.tex
```

### Alternative with Biber
```bash
pdflatex paper.tex
biber paper
pdflatex paper.tex
pdflatex paper.tex
```

---

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{TITLE}}` | Paper title | "<paper title>" |
| `{{AUTHOR}}` | Author name(s) | "Research Team" |
| `{{INSTITUTION}}` | Affiliation | "Research Institute" |
| `{{DATE}}` | Publication date | "2026" |
| `{{ABSTRACT}}` | Abstract content | Section 0 content |
| `{{KEYWORDS}}` | Keyword list | "<keyword one, keyword two>" |
| `{{SECTIONS}}` | Main content | Section 1-N inputs |
| `{{BIBLIOGRAPHY}}` | Bibliography file | "bibliography" |

### Variable Substitution
```python
def process_template(template: str, metadata: dict) -> str:
    """Substitute template variables with metadata values."""
    processed = template

    for key, value in metadata.items():
        placeholder = f"{{{{{key.upper()}}}}}"
        processed = processed.replace(placeholder, str(value))

    return processed
```

---

## Available Templates

### Academic Templates
| Template | Document Class | Use Case |
|----------|---------------|----------|
| `ieee_conference` | IEEEtran | IEEE conference papers |
| `acm_article` | acmart | ACM journal articles |
| `preprint` | article | Single-column preprint styling (arXiv-style layout, no branding) |
| `springer_lncs` | llncs | Springer LNCS |

### Whitepaper Templates
| Template | Document Class | Use Case |
|----------|---------------|----------|
| `technical_whitepaper` | article | Technical reports |
| `business_whitepaper` | article | Business documents |

### Literature Review Templates
| Template | Document Class | Use Case |
|----------|---------------|----------|
| `systematic_review` | article | Systematic reviews |
| `narrative_review` | article | Narrative surveys |

### Book Templates
| Template | Document Class | Use Case |
|----------|---------------|----------|
| `dark_charcoal_book` | book | Multi-chapter dark-mode books with series support |

---

## Error Handling

### Common Errors and Fixes

| Error Pattern | Cause | Auto-Fix |
|--------------|-------|----------|
| `Undefined control sequence` | Missing package | Add package to preamble |
| `Missing $ inserted` | Math mode issue | Wrap in `$...$` |
| `Citation undefined` | Missing BibTeX entry | Log warning, continue |
| `File not found` | Missing input file | Check path, log error |
| `Overfull hbox` | Line too long | Warning only |

### Error Parsing
```python
def parse_latex_errors(log_path: str) -> List[dict]:
    """Parse LaTeX log file for errors and warnings."""
    errors = []

    with open(log_path, 'r') as f:
        log_content = f.read()

    # Error patterns
    error_pattern = r'! (.+?)(?=\n)'
    warning_pattern = r'LaTeX Warning: (.+?)(?=\n)'

    for match in re.finditer(error_pattern, log_content):
        errors.append({
            "type": "error",
            "message": match.group(1),
            "line": extract_line_number(log_content, match.start())
        })

    for match in re.finditer(warning_pattern, log_content):
        errors.append({
            "type": "warning",
            "message": match.group(1),
            "line": None
        })

    return errors
```

### Recovery Strategy
```python
def attempt_recovery(error: dict, tex_content: str) -> Tuple[bool, str]:
    """Attempt to automatically fix common LaTeX errors."""

    if "Undefined control sequence" in error['message']:
        # Try adding common packages
        command = extract_command(error['message'])
        package = COMMAND_PACKAGE_MAP.get(command)
        if package:
            tex_content = add_package(tex_content, package)
            return True, tex_content

    if "Missing $ inserted" in error['message']:
        # Math mode fix would require more context
        return False, tex_content

    return False, tex_content
```

---

## Decision Capture Requirements

### Required Decision Types

| Decision Type | When | Example |
|--------------|------|---------|
| `template_selection` | Choosing template | "IEEE for conference submission" |
| `compilation_passes` | Pass count | "4 passes for bibliography" |
| `error_resolution` | Fixing errors | "Added amsmath for equation" |
| `warning_handling` | Addressing warnings | "Ignored overfull hbox (< 1pt)" |

### Example Decision Log
```python
capture.log_decision(
    decision_type="template_selection",
    decision="ieee_conference_template",
    rationale="Target venue is IEEE conference; IEEEtran document class provides correct formatting and required structure",
    alternatives_considered=[
        {"option": "acm_article", "rejected_because": "Different venue requirements"},
        {"option": "preprint", "rejected_because": "Conference has specific template"}
    ]
)

capture.log_decision(
    decision_type="error_resolution",
    decision="added_amsmath_package",
    rationale="Undefined control sequence \\mathbb requires amsmath package; added to preamble to resolve",
    error_message="! Undefined control sequence. \\mathbb",
    fix_applied="\\usepackage{amsmath}"
)
```

---

## LaTeX Compiler

Paperforge uses **Tectonic** as the primary LaTeX engine. Tectonic is a self-contained compiler that requires NO system package installation.

### Tectonic Binary (Primary)
```
Paperforge/bin/tectonic
```

### Tectonic Compilation (Single Command)
```bash
Paperforge/bin/tectonic paper.tex
```

Tectonic automatically handles:
- Multiple compilation passes
- Bibliography processing (no separate bibtex call needed)
- Font and package downloads (cached after first use)
- Index generation via makeindex (no separate call needed)

### Book-Specific Compilation Notes
- Book template uses `book` document class with `openany` --- no blank pages between chapters
- Tectonic handles `makeindex` automatically alongside bibliography
- Dark mode templates: verify all text is visible (no black-on-black)
- Per-chapter numbering: figures, tables, equations, definitions all number as X.Y
- `\frontmatter`/`\mainmatter`/`\backmatter` control page numbering (roman -> arabic)
- Common book error: missing `\cite` package --- always verify `\usepackage{cite}` is present
- Template variables: `{{BIBLIOGRAPHY}}` must be set to `\bibliographystyle{IEEEtran}\bibliography{bibliography}` or empty string

### Fallback: System Packages (Optional)
If Tectonic is unavailable, system pdflatex can be used:
```bash
# Minimal installation
sudo apt-get install texlive-latex-base texlive-latex-extra \
                     texlive-fonts-recommended texlive-bibtex-extra

# Full installation (recommended)
sudo apt-get install texlive-full
```

### Required LaTeX Packages
- `cite` - Citation handling
- `amsmath`, `amssymb`, `amsfonts` - Mathematics
- `amsthm` - Theorem/proof environments
- `graphicx` - Images
- `hyperref` - Hyperlinks
- `xcolor` - Colors
- `booktabs` - Tables
- `listings` - Code listings
- `makeidx` - Index generation
- `caption` - Caption styling
- `tcolorbox` (with `skins,theorems`) - Custom environments

---

## Quality Standards

- PDF must be generated without errors
- All citations must be resolved
- Page count within expected range
- No missing figures or tables
- Table of contents accurate (if included)
- Hyperlinks functional
