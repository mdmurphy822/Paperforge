# Citation Manager Agent

## Overview
The `citation-manager` agent collects citations from all generated sections, creates BibTeX entries from source metadata, formats the bibliography, and ensures citation consistency. It is a general-purpose bibliography tool — it has no built-in knowledge of any particular paper, source, or research domain; it only formats whatever metadata it's given.

## Agent Classification
- **Type**: `specialized`
- **Max Instances**: 1
- **Workflow Position**: Phase 4 (citation_assembly)
- **Execution**: Sequential (after content generation)

## Capabilities
- `bibtex_generation` - Create BibTeX entries from metadata
- `citation_formatting` - Format citations in specified style
- `reference_deduplication` - Remove duplicate references

---

## Responsibilities

### 1. Citation Collection
- Scan all generated section .tex files
- Extract `\cite{}` and `\citet{}` commands
- Build master list of required citations
- Identify missing citation keys

### 2. BibTeX Generation
- Assemble metadata for each citation (from the outliner/synthesizer's source list, or manually supplied)
- Generate BibTeX entries for each citation
- Handle citations with incomplete metadata (manual entries)
- Validate BibTeX syntax

### 3. Bibliography Formatting
- Apply citation style (APA, IEEE, ACM, Chicago)
- Format author names consistently
- Handle special characters and Unicode
- Sort entries according to style

### 4. Deduplication
- Identify duplicate citation keys
- Merge duplicate entries
- Update section references if needed
- Log deduplication decisions

---

## Input Format

```json
{
  "project_path": "/path/to/exports/PROJECT_ID",
  "sections_path": "03_content_development",
  "citation_style": "ieee",
  "source_metadata": "01_planning/source_plan.json"
}
```

A source metadata entry has this shape (values are illustrative placeholders, not a real source):

```json
{
  "citation_key": "<lastname><year><word>",
  "title": "<title of the source>",
  "authors": "<Last, First and Last, First ...>",
  "year": "<YYYY>",
  "container": "<journal/venue/publisher, if any>",
  "url": "<link, if any>",
  "identifier": "<DOI or other resolvable id, if any>"
}
```

---

## Output Format

### bibliography.bib
```bibtex
@article{<citation_key>,
    title = {<Title Of The Source>},
    author = {<Last, First and Last, First>},
    journal = {<Journal Or Venue Name>},
    year = {<YYYY>},
    url = {<source url, if any>}
}
```

### citation_index.json
```json
{
  "total_citations": 0,
  "unique_sources": 0,
  "duplicates_merged": 0,
  "citations_by_section": {
    "section_01_introduction": 0
  },
  "citation_keys": [],
  "missing_citations": [],
  "manual_entries": []
}
```

---

## BibTeX Entry Generation

### From Source Metadata
```python
def generate_bibtex_entry(source: dict) -> str:
    """Generate BibTeX from a cited source's metadata."""
    authors = format_authors_bibtex(source['authors'])

    return f"""@article{{{source['citation_key']},
    title = {{{source['title']}}},
    author = {{{authors}}},
    journal = {{{source.get('container', '')}}},
    year = {{{source['year']}}},
    url = {{{source.get('url', '')}}}
}}"""
```

### Author Name Formatting
```python
def format_authors_bibtex(authors_string: str) -> str:
    """Format author names for BibTeX (Last, First and ...)."""
    authors = parse_author_names(authors_string)
    formatted = []
    for author in authors:
        # "First Last" -> "Last, First"
        parts = author.strip().split()
        if len(parts) >= 2:
            formatted.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
        else:
            formatted.append(author)
    return " and ".join(formatted)
```

---

## Citation Styles

Apply whichever style the project requests. The formatting rules (not tied to any specific source):

### IEEE Style
```
[N] <Initials>. <Last> et al., "<title, lowercase except proper nouns>," <venue>, <year>.
```

### APA Style
```
<Last>, <F>. I., <Last2>, <F2>. I. (<year>). <Title, sentence case>.
    <Venue, italicized>.
```

### ACM Style
```
<First> <Last>, <First2> <Last2>, and <First3> <Last3>. <year>.
    <title, lowercase except proper nouns>. In <Venue>.
```

---

## Citation Extraction

### LaTeX Citation Commands
```python
CITATION_PATTERNS = [
    r'\\cite\{([^}]+)\}',           # \cite{key} or \cite{key1,key2}
    r'\\citet\{([^}]+)\}',          # \citet{key}
    r'\\citep\{([^}]+)\}',          # \citep{key}
    r'\\citeauthor\{([^}]+)\}',     # \citeauthor{key}
    r'\\citeyear\{([^}]+)\}',       # \citeyear{key}
]

def extract_citations(tex_content: str) -> List[str]:
    """Extract all citation keys from LaTeX content."""
    citations = set()
    for pattern in CITATION_PATTERNS:
        matches = re.findall(pattern, tex_content)
        for match in matches:
            # Handle multiple keys: \cite{key1,key2,key3}
            keys = [k.strip() for k in match.split(',')]
            citations.update(keys)
    return sorted(citations)
```

---

## Deduplication Strategy

### Detection
```python
def find_duplicates(sources: List[dict]) -> List[Tuple]:
    """Find sources that may be duplicates."""
    duplicates = []

    for i, source1 in enumerate(sources):
        for source2 in sources[i+1:]:
            # Same identifier (DOI, URL, etc.)
            if source1.get('identifier') and source1['identifier'] == source2.get('identifier'):
                duplicates.append((source1, source2, 'same_identifier'))
            # Similar titles (fuzzy match)
            elif title_similarity(source1['title'], source2['title']) > 0.9:
                duplicates.append((source1, source2, 'similar_title'))

    return duplicates
```

### Resolution
```python
def resolve_duplicate(source1: dict, source2: dict) -> dict:
    """Merge duplicate entries, keeping more complete metadata."""
    merged = source1.copy()

    # Keep the more recently updated identifier
    if source2.get('updated_date', '') > source1.get('updated_date', ''):
        merged['identifier'] = source2['identifier']

    # Merge any category/tag fields present
    tags = set((source1.get('categories') or '').split(', '))
    tags.update((source2.get('categories') or '').split(', '))
    merged['categories'] = ', '.join(sorted(t for t in tags if t))

    return merged
```

---

## Decision Capture Requirements

### Required Decision Types

| Decision Type | When | Example |
|--------------|------|---------|
| `bibtex_formatting` | Creating entries | "Used conference-proceedings format for journal field" |
| `deduplication` | Merging entries | "Merged two entries sharing the same DOI" |
| `style_application` | Formatting | "Applied IEEE numeric citation style" |
| `missing_citation` | Handling gaps | "Created manual entry for source with incomplete metadata" |

### Example Decision Log
```python
capture.log_decision(
    decision_type="deduplication",
    decision="merged_duplicate_entries",
    rationale="Two bibliography entries shared the same DOI with slightly different metadata; kept the more complete version",
    original_keys=["<key_a>", "<key_b>"],
    merged_key="<key_a>"
)
```

---

## Validation

### BibTeX Syntax Check
```python
def validate_bibtex(entry: str) -> Tuple[bool, List[str]]:
    """Validate BibTeX entry syntax."""
    errors = []

    # Check required fields
    required = ['title', 'author', 'year']
    for field in required:
        if f'{field} =' not in entry.lower():
            errors.append(f"Missing required field: {field}")

    # Check balanced braces
    if entry.count('{') != entry.count('}'):
        errors.append("Unbalanced braces in entry")

    # Check special characters
    special_chars = ['&', '%', '#', '_']
    for char in special_chars:
        if char in entry and f'\\{char}' not in entry:
            errors.append(f"Unescaped special character: {char}")

    return len(errors) == 0, errors
```

### Citation Coverage
```python
def check_citation_coverage(sections: List[str], bibliography: str) -> dict:
    """Verify all cited sources are in the bibliography."""
    cited = set()
    for section in sections:
        cited.update(extract_citations(section))

    available = set(extract_bibtex_keys(bibliography))

    return {
        "total_cited": len(cited),
        "total_available": len(available),
        "missing": list(cited - available),
        "unused": list(available - cited),
        "coverage": len(cited & available) / len(cited) if cited else 1.0
    }
```

---

## Quality Standards

- All cited sources must have BibTeX entries
- BibTeX syntax must be valid (parseable)
- Author names formatted consistently
- No duplicate citation keys
- Citation coverage >= 1.0 (all citations resolved)
