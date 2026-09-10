# Markdown Exporter Agent

## Overview
The `markdown-exporter` agent converts the LaTeX document to portable Markdown format with embedded citations, suitable for sharing, web publishing, or further editing.

## Agent Classification
- **Type**: `specialized`
- **Max Instances**: 1
- **Workflow Position**: Phase 6 (compilation)
- **Execution**: Parallel with latex-compiler

## Capabilities
- `markdown_generation` - Convert LaTeX to Markdown
- `citation_embedding` - Format citations for Markdown

---

## Responsibilities

### 1. LaTeX to Markdown Conversion
- Parse LaTeX section files
- Convert LaTeX commands to Markdown equivalents
- Handle math equations
- Process figures and tables

### 2. Citation Embedding
- Convert `\cite{}` commands to readable format
- Generate references section
- Support multiple citation styles

### 3. Structure Preservation
- Maintain heading hierarchy
- Preserve lists and formatting
- Handle code blocks
- Process special environments

---

## Input Format

```json
{
  "project_path": "/path/to/exports/PROJECT_ID",
  "sections_path": "03_content_development",
  "bibliography_path": "04_citations/bibliography.bib",
  "citation_style": "inline",
  "metadata": {
    "title": "<paper title>",
    "author": "<author or team name>",
    "date": "2026"
  },
  "options": {
    "include_toc": true,
    "math_format": "latex",
    "citation_format": "author_year"
  }
}
```

---

## Output Format

### paper.md
```markdown
# <Paper Title>

**Author:** <author or team name>
**Date:** 2026

## Table of Contents
- [Abstract](#abstract)
- [Introduction](#introduction)
- [Background](#background)
...

## Abstract

<Summary of scope and findings.>

## Introduction

<Context-setting paragraph with an inline citation \cite{<citation_key>}.>

## Background

### <Subsection Title>

<Body text, with an equation where relevant.>

$$
<equation>
$$

...

## References

1. <Last, F. (Year). Title. Venue.>

2. <Last, F. (Year). Title. Venue.>

...
```

---

## Conversion Rules

### LaTeX to Markdown Mappings

| LaTeX | Markdown |
|-------|----------|
| `\section{Title}` | `## Title` |
| `\subsection{Title}` | `### Title` |
| `\subsubsection{Title}` | `#### Title` |
| `\textbf{text}` | `**text**` |
| `\textit{text}` | `*text*` |
| `\texttt{code}` | `` `code` `` |
| `\begin{itemize}` | `- item` list |
| `\begin{enumerate}` | `1. item` list |
| `\cite{key}` | `(Author, Year)` |
| `$equation$` | `$equation$` (preserved) |
| `\begin{equation}` | `$$...$$` block |

### Section Command Conversion
```python
def convert_sections(tex_content: str) -> str:
    """Convert LaTeX section commands to Markdown headers."""
    conversions = [
        (r'\\section\{([^}]+)\}', r'## \1'),
        (r'\\subsection\{([^}]+)\}', r'### \1'),
        (r'\\subsubsection\{([^}]+)\}', r'#### \1'),
        (r'\\paragraph\{([^}]+)\}', r'##### \1'),
    ]

    result = tex_content
    for pattern, replacement in conversions:
        result = re.sub(pattern, replacement, result)

    return result
```

### Text Formatting Conversion
```python
def convert_formatting(tex_content: str) -> str:
    """Convert LaTeX text formatting to Markdown."""
    conversions = [
        (r'\\textbf\{([^}]+)\}', r'**\1**'),
        (r'\\textit\{([^}]+)\}', r'*\1*'),
        (r'\\emph\{([^}]+)\}', r'*\1*'),
        (r'\\texttt\{([^}]+)\}', r'`\1`'),
        (r'\\underline\{([^}]+)\}', r'<u>\1</u>'),
    ]

    result = tex_content
    for pattern, replacement in conversions:
        result = re.sub(pattern, replacement, result)

    return result
```

---

## Citation Formats

### Inline Author-Year (Default)
```markdown
...as shown in the cited source (<Author>, <Year>). This approach...
```

### Numeric References
```markdown
...as shown in [1]. This approach...

## References
[1] <Last, F. (Year). Title. Venue.>
```

### Footnote Style
```markdown
...as shown in the cited source.[^1] This approach...

[^1]: <Last, F. (Year). Title. Venue.>
```

### Citation Conversion
```python
def convert_citations(tex_content: str, bibliography: dict, style: str) -> str:
    """Convert LaTeX citations to Markdown format."""

    def replace_cite(match):
        keys = [k.strip() for k in match.group(1).split(',')]
        citations = []

        for key in keys:
            if key in bibliography:
                paper = bibliography[key]
                if style == "author_year":
                    author = paper['author'].split(',')[0].split()[-1]
                    year = paper['year']
                    citations.append(f"{author} et al., {year}")
                elif style == "numeric":
                    idx = list(bibliography.keys()).index(key) + 1
                    citations.append(f"[{idx}]")

        return "(" + "; ".join(citations) + ")"

    result = re.sub(r'\\cite\{([^}]+)\}', replace_cite, tex_content)
    return result
```

---

## Math Handling

### Inline Math
```python
# LaTeX: $E = mc^2$
# Markdown: $E = mc^2$ (preserved for MathJax/KaTeX)
```

### Display Math
```python
def convert_display_math(tex_content: str) -> str:
    """Convert LaTeX display math to Markdown."""
    # \begin{equation} ... \end{equation} -> $$ ... $$
    result = re.sub(
        r'\\begin\{equation\}(.*?)\\end\{equation\}',
        r'\n$$\1$$\n',
        tex_content,
        flags=re.DOTALL
    )

    # \[ ... \] -> $$ ... $$
    result = re.sub(r'\\\[(.*?)\\\]', r'\n$$\1$$\n', result, flags=re.DOTALL)

    return result
```

---

## List Conversion

### Itemize (Bullet Lists)
```python
def convert_itemize(tex_content: str) -> str:
    """Convert LaTeX itemize to Markdown bullet list."""
    # Remove begin/end tags
    result = re.sub(r'\\begin\{itemize\}', '', tex_content)
    result = re.sub(r'\\end\{itemize\}', '', result)

    # Convert items
    result = re.sub(r'\\item\s*', '- ', result)

    return result
```

### Enumerate (Numbered Lists)
```python
def convert_enumerate(tex_content: str) -> str:
    """Convert LaTeX enumerate to Markdown numbered list."""
    result = re.sub(r'\\begin\{enumerate\}', '', tex_content)
    result = re.sub(r'\\end\{enumerate\}', '', result)

    # Convert items with numbering
    counter = [0]  # Mutable counter for closure

    def replace_item(match):
        counter[0] += 1
        return f"{counter[0]}. "

    result = re.sub(r'\\item\s*', replace_item, result)

    return result
```

---

## Table Conversion

### LaTeX Table to Markdown
```python
def convert_table(tex_content: str) -> str:
    """Convert LaTeX tabular to Markdown table."""
    # Extract table content
    table_match = re.search(
        r'\\begin\{tabular\}\{[^}]+\}(.*?)\\end\{tabular\}',
        tex_content,
        flags=re.DOTALL
    )

    if not table_match:
        return tex_content

    table_content = table_match.group(1)

    # Parse rows
    rows = table_content.split('\\\\')
    md_rows = []

    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.split('&')]
        md_row = '| ' + ' | '.join(cells) + ' |'
        md_rows.append(md_row)

        # Add header separator after first row
        if i == 0:
            separator = '|' + '|'.join(['---'] * len(cells)) + '|'
            md_rows.append(separator)

    return '\n'.join(md_rows)
```

---

## Decision Capture Requirements

### Required Decision Types

| Decision Type | When | Example |
|--------------|------|---------|
| `format_conversion` | Converting LaTeX | "Preserved math as LaTeX for MathJax" |
| `citation_style` | Choosing style | "Used author-year for readability" |
| `structure_handling` | Complex elements | "Converted figure to image link" |

### Example Decision Log
```python
capture.log_decision(
    decision_type="citation_style",
    decision="author_year_inline",
    rationale="Author-year format provides better readability in Markdown context; maintains academic credibility without requiring footnote support",
    alternatives_considered=[
        {"option": "numeric", "rejected_because": "Less informative without hover"},
        {"option": "footnote", "rejected_because": "Platform-dependent support"}
    ]
)
```

---

## Table of Contents Generation

```python
def generate_toc(md_content: str) -> str:
    """Generate table of contents from Markdown headers."""
    toc_lines = ["## Table of Contents\n"]

    headers = re.findall(r'^(#{2,4})\s+(.+)$', md_content, re.MULTILINE)

    for level, title in headers:
        if title == "Table of Contents":
            continue

        indent = "  " * (len(level) - 2)
        anchor = title.lower().replace(' ', '-').replace('.', '')
        anchor = re.sub(r'[^\w-]', '', anchor)

        toc_lines.append(f"{indent}- [{title}](#{anchor})")

    return '\n'.join(toc_lines) + '\n\n'
```

---

## Quality Standards

- All sections converted successfully
- Citations properly formatted
- Math equations preserved and renderable
- Tables properly aligned
- No broken links or references
- Table of contents accurate
- References section complete
