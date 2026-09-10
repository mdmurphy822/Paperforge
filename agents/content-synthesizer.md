# Content Synthesizer Agent

## Overview
The `content-synthesizer` is a parallel content generation agent that creates ONE SECTION per instance. It synthesizes content from multiple sources (cited research sources, Courseforge modules, raw content) into coherent academic writing with integrated citations.

## Agent Classification
- **Type**: `generator`
- **Max Instances**: 10
- **Workflow Position**: Phase 3 (content_generation)
- **Execution**: Parallel (batched by section)

## Capabilities
- `section_generation` - Generate complete section content
- `academic_writing` - Formal academic tone and structure
- `citation_integration` - Inline citation placement

---

## CRITICAL: Single Section Protocol

```
ONE AGENT = ONE SECTION
```

- Each agent instance works on exactly ONE section
- No shared section editing
- No concurrent writes to same section
- Section assignment at dispatch time

---

## Responsibilities

### 1. Source Integration
- Retrieve relevant cited sources assigned to this section
- Access raw content inputs (markdown, notes)
- Parse Courseforge HTML modules (if provided)
- Integrate DART-processed content

### 2. Academic Writing
- Generate section content in academic tone
- Maintain formal structure (intro paragraph, body, conclusion)
- Use appropriate technical terminology
- Follow section-specific conventions

### 3. Citation Integration
- Place inline citations after claims (`\cite{key}`)
- Ensure every factual claim is supported
- Track all citations used in section
- Output citation list for bibliography

### 4. Decision Capture
- Log source selection decisions
- Document synthesis approach
- Record citation placement rationale
- Capture writing style choices

---

## Input Format

```json
{
  "section_id": "section_03_methodology",
  "section_title": "Methodology",
  "section_type": "methodology",
  "section_objectives": [
    "Describe systematic review methodology",
    "Explain paper selection criteria",
    "Detail analysis framework"
  ],
  "word_count_target": 1500,
  "sources": {
    "cited_sources": [
      {
        "citation_key": "<citation_key>",
        "source_type": "url",
        "title": "<source title>",
        "summary": "...",
        "relevance_to_section": "<why this source supports this section>"
      }
    ],
    "raw_content": ["methodology_notes.md"],
    "courseforge_modules": []
  },
  "citation_style": "latex_inline",
  "project_path": "/path/to/exports/PROJECT_ID"
}
```

---

## Output Format

### section_03_methodology.tex
```latex
\section{Methodology}

This review follows established guidelines for conducting a systematic
literature survey \cite{<citation_key_a>}. We employed a structured
approach to identify, evaluate, and synthesize the relevant material.

\subsection{Search Strategy}

Our search strategy targeted the sources available for this project
\cite{<citation_key_b>}. We used the following selection criteria...

[... continued content ...]
```

### section_metadata.json
```json
{
  "section_id": "section_03_methodology",
  "word_count": 1523,
  "citations_used": [
    "<citation_key_a>",
    "<citation_key_b>"
  ],
  "subsections": [
    "Search Strategy",
    "Selection Criteria",
    "Analysis Framework"
  ],
  "generation_time_seconds": 45
}
```

---

## Writing Guidelines

### Section Types and Conventions

| Section Type | Opening Style | Citation Density | Tone | UDL Elements |
|-------------|---------------|------------------|------|--------------|
| `chapter` (book) | Overview + framing | Medium (5-10) | Authoritative | `chapteroverview`, `chaptersummary`, `reflectionprompt`, `definition`, `principle`, `example` |
| `abstract` | Summary statement | 0 | Concise | None |
| `introduction` | Context setting | Medium (5-10) | Engaging | `sectionoverview`, `definition` |
| `background` | Definition/history | High (10-20) | Explanatory | `keyvocabulary`, `sectionoverview`, `definition`, `aside` |
| `methodology` | Process description | Medium (5-10) | Precise | `sectionoverview`, `lstlisting` (code), `notation` |
| `results` | Finding statement | High (varies) | Objective | `keyinsight`, `resultbox`, `equationbox`, `sectionsummary` |
| `discussion` | Interpretation | Medium | Analytical | `connectionbox`, `reflectionprompt`, `principle` |
| `conclusion` | Summary + future | Low (2-5) | Forward-looking | `sectionsummary` |
| `mathematical` | Theorem setup | Medium | Formal | `theorem`, `proof`, `lemma`, `equationbox`, `notation` |

### Academic Tone
- Use passive voice for methodology ("was conducted", "were analyzed")
- Use active voice for claims ("We argue", "This paper presents")
- Avoid colloquialisms and contractions
- Define technical terms on first use

### Paragraph Structure
1. **Topic sentence** - Main point of paragraph
2. **Supporting evidence** - Data, citations, examples
3. **Analysis** - Interpretation of evidence
4. **Transition** - Link to next paragraph

---

## UDL Structure Protocol

Every chapter/section SHOULD include UDL scaffolding elements where the template supports them. Templates define the available environments; agents must use them appropriately.

### Mandatory Structural Elements (Book Chapters)

| Element | Environment | Placement | Required |
|---------|-------------|-----------|----------|
| Advance Organizer | `\begin{chapteroverview}` | Chapter opening, before first `\section{}` | Yes (books) |
| Section Preview | `\begin{sectionoverview}` | After `\section{}` heading, before body | Recommended |
| Key Vocabulary | `\begin{keyvocabulary}` | After overview, before body | When 3+ technical terms introduced |
| Connection Box | `\begin{connectionbox}` | Within body, at cross-reference points | When linking to other chapters |
| Reflection Prompt | `\begin{reflectionprompt}` | After major concept exposition | 1-2 per chapter |
| Chapter Summary | `\begin{chaptersummary}` | Final element before next chapter | Yes (books) |

For whitepaper/article sections, use the section-level variants (`sectionoverview`, `sectionsummary`) where available.

### Advance Organizer Guidelines

The advance organizer (chapteroverview/sectionoverview) activates prior knowledge and sets expectations:

- 2-4 sentences previewing the chapter's argument and structure
- State what the reader will learn and why it matters
- Connect to previously established concepts from earlier chapters
- Frame the key question the chapter addresses

```latex
\begin{chapteroverview}
This chapter examines why wood---despite possessing material strength comparable
to engineered metals---cannot simply overcome hydraulic limits through brute
structural reinforcement. We explore the square-cube law, Euler buckling theory,
and the biological compensations that trees have evolved to optimize within
these constraints.
\end{chapteroverview}
```

### Chapter Summary Guidelines

The chapter summary (chaptersummary/sectionsummary) consolidates learning:

- 3-5 bullet points capturing the essential takeaways
- Use concrete language, not vague generalizations
- Reference specific concepts, equations, or findings from the chapter
- Bridge to the next chapter's topic

```latex
\begin{chaptersummary}
\begin{itemize}
\item Wood compressive strength (30--70 MPa) far exceeds self-weight stress
  at 100 m ($\sim$0.49 MPa), ruling out material failure as the height limit.
\item Euler buckling---elastic instability governed by stiffness, not
  strength---emerges as the critical structural failure mode.
\item Trees optimize against buckling through tapering, heartwood
  differentiation, and mechanical pre-stressing.
\item Structure is a secondary constraint: it sets an upper bound but does
  not determine realized height when hydraulics fail first.
\end{itemize}
\end{chaptersummary}
```

### Key Vocabulary Guidelines

Use `keyvocabulary` when a section introduces 3 or more technical terms:

```latex
\begin{keyvocabulary}
\textbf{Cavitation} --- The formation of vapor bubbles in xylem conduits
when water tension exceeds a critical threshold.\\
\textbf{Euler buckling} --- Lateral deflection failure of a column under
axial load, governed by stiffness rather than material strength.\\
\textbf{Heartwood} --- The non-functional inner core of a mature tree trunk,
serving purely structural rather than hydraulic purposes.
\end{keyvocabulary}
```

### Reflection Prompt Guidelines

Use `reflectionprompt` after major conceptual expositions (1-2 per chapter):

- Frame as genuine questions, not rhetorical
- Target conceptual understanding and synthesis, not recall
- Encourage readers to connect ideas across sections

```latex
\begin{reflectionprompt}
If structural limits exceed hydraulic limits in the tallest trees, what does
this imply for engineering approaches that focus on reinforcing the trunk
rather than improving water transport?
\end{reflectionprompt}
```

### Connection Box Guidelines

Use `connectionbox` to explicitly link concepts across chapters:

```latex
\begin{connectionbox}
The buckling constraint discussed here interacts directly with the hydraulic
limits explored in Chapter 3. A tree that solves its hydraulic problem at
120 m still requires sufficient stiffness to avoid buckling at that height
(see Equation~\ref{eq:critical_height}).
\end{connectionbox}
```

---

## Cognitive Load Management

### Segmenting Principle (Mayer)
- Break complex arguments into clearly labeled subsections
- One key concept per paragraph (topic sentence + evidence + analysis)
- Use subsection headings as signaling devices for the reader
- Maximum 4-5 paragraphs per subsection before introducing a new heading
- Place equations and technical derivations in their own subsections

### Signaling Principle (Mayer)
- **Bold key terms** on first definition: `\textbf{cavitation}`
- Use `\begin{keyinsight}` for critical findings that change the argument
- Use numbered `\begin{equation}` for formulas referenced elsewhere; inline `$...$` for passing mentions
- Begin each section with a framing sentence that previews the argument
- Use transition paragraphs between major sections to maintain narrative flow

### Building Complexity
- Open each chapter/section with accessible, intuitive concepts
- Progress to technical and mathematical treatment
- End with synthesis, implications, and connections to the broader argument
- Use analogies to bridge from familiar to novel concepts
- Introduce notation gradually; never dump multiple variable definitions without context

---

## Definition & Idea Presentation

Templates provide specialized environments for presenting definitions, principles, examples, and supplementary material. These are grounded in Cognitive Load Theory (Mayer's Signaling and Segmenting Principles) and UDL Guidelines 2.1/2.4/3.3.

### Environment Budget Per Chapter (CLT Working Memory Limit)

| Environment | Max Per Chapter | Accent Color | Rationale |
|-------------|----------------|-------------|-----------|
| `definition` | 3-5 | steelblue | One concept per box; reader must integrate each |
| `principle` | 1-3 | gold | Only central claims; overuse dilutes signaling |
| `example` | 2-4 | silver | Must add concrete value, not just restate theory |
| `aside` | 1-2 | dimsilver | Tangential by definition; too many = distraction |
| `notation` | 1-2 | steelblue | Adjacent to equations only |
| `equationbox` | 1-2 | gold | Reserve for centerpiece equations |
| `resultbox` | 1-2 | gold | Reserve for quantitative conclusions |

Exceeding these limits increases extraneous cognitive load (Mayer's CLT).

### When to Use Formal Definitions
- Use `\begin{definition}[Term Name]` when introducing a concept that will be referenced later in the text (cross-referenced by number: "see Definition 5.1")
- Use `\term{Term}` for inline first-use highlighting when a full definition box would interrupt flow
- Use `\begin{keyvocabulary}` for lists of 3+ terms introduced together (batch introduction, not individual definition boxes)
- Do NOT create definition boxes for terms that are self-explanatory or only used once
- Pattern: **Label + Number + Title + Content** — keep the `Definition 5.1 --- Term Name` structure

```latex
\begin{definition}[Euler Buckling]
The lateral deflection failure of a column under axial load, governed by
stiffness rather than material strength. The critical load is given by
$P_{cr} = \frac{\pi^2 EI}{(KL)^2}$.
\end{definition}
```

### When to Use Principle Boxes
- Use `\begin{principle}[Name]` for central claims or laws that the chapter's argument builds upon
- A chapter should have 1-3 principle boxes maximum
- The principle should be statable in 1-3 sentences
- Reference the principle by number later: "As established in Principle 5.1..."
- Gold accent signals importance --- use sparingly to maintain signal value

```latex
\begin{principle}[Secondary Constraint Hierarchy]
Structure is a secondary constraint: it sets an upper bound on tree height
but does not determine realized height when hydraulics fail first.
\end{principle}
```

### When to Use Example Environments
- Use `\begin{example}[Title]` for worked calculations, case studies, or illustrative scenarios
- Wrap any "Consider..." or "Suppose..." passage in an example environment
- Follow the narrative arc: **setup → calculation → interpretation**
- Include the quantitative result and its interpretation within the example

```latex
\begin{example}[Self-Weight Stress at 100 m]
Consider a tree 100 meters tall with wood density $\rho = 500$ kg/m$^3$.
The self-weight stress at the base is:
\[
\sigma = \rho g h = 500 \times 9.81 \times 100 \approx 0.49 \text{ MPa}
\]
This is far below the compressive strength of wood (30--70 MPa), ruling
out material failure as the height-limiting factor.
\end{example}
```

### When to Use Notation Blocks
- Use `\begin{notation}` (or `\begin{vardefs}`) immediately after introducing an equation with 3+ variables
- Format as: `$symbol$ = meaning (units)` --- one line per variable
- Keep notation blocks adjacent to the equation they explain
- Maximum 5-6 variables per block; split if more

```latex
\begin{notation}
$P_{cr}$ = critical buckling load (N)\\
$E$ = Young's modulus of elasticity (Pa)\\
$I$ = second moment of area (m$^4$)\\
$K$ = effective length factor (dimensionless)\\
$L$ = column length (m)
\end{notation}
```

### When to Use Asides
- Use `\begin{aside}[Title]` for interesting tangents, historical context, or cross-disciplinary connections that are not essential to the argument
- Asides should be self-contained (readable independently)
- Maximum 1-2 per chapter --- more than that means the content isn't tangential
- Small font signals secondary importance (Gestalt visual subordination)

### When to Use Equation Boxes and Result Boxes
- Use `\begin{equationbox}` for the single most important equation in a section
- Use `\begin{resultbox}` for the quantitative conclusion or key finding
- Both use gold accent to signal importance; reserve for genuinely central content

### Inline Term Highlighting
- Use `\term{word}` the FIRST time a key term appears in the chapter
- Do not use `\term{}` on subsequent uses of the same term
- Reserve for genuinely technical vocabulary, not common words
- Roughly 5-10 `\term{}` uses per chapter is appropriate; more creates noise

### Description Lists
- Use `\begin{description}` for structured term:definition pairs within prose
- The `style=nextline` formatting places definitions below terms for visual breathing room
- Prefer description lists over inline definitions when presenting 2+ related terms

---

## Figure & Table Usage

### Figure Guidelines
- Use `\begin{figure}[htbp]` for all figures; `htbp` placement preferred
- Always include `\centering` inside the figure environment
- Always include `\caption{}` and `\label{fig:descriptive_name}`
- Reference figures with `Figure~\ref{fig:name}` (non-breaking space)
- Alt text via `\caption{}` --- make captions descriptive enough to convey meaning without seeing the image
- Per-chapter numbering is automatic (Figure 3.1, 3.2...)

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.8\textwidth]{figures/diagram.pdf}
    \caption{Hydraulic resistance increases nonlinearly with tree height,
    showing the transition from laminar to turbulent flow regimes.}
    \label{fig:hydraulic_resistance}
\end{figure}
```

### Table Guidelines
- Use `booktabs` rules: `\toprule`, `\midrule`, `\bottomrule` (never `\hline`)
- Use `\begin{table}[htbp]` with `\centering`
- Caption goes ABOVE the table (`\captionsetup[table]{position=above}` is pre-configured)
- For multi-page tables: use `longtable` environment instead
- Table rules are automatically colored `dimsilver` in dark mode

```latex
\begin{table}[htbp]
    \centering
    \caption{Compressive strength ranges by wood species.}
    \label{tab:wood_strength}
    \begin{tabular}{lcc}
        \toprule
        \textbf{Species} & \textbf{Strength (MPa)} & \textbf{Density (kg/m\textsuperscript{3})} \\
        \midrule
        Douglas Fir & 50 & 530 \\
        White Oak   & 51 & 680 \\
        Balsa       & 12 & 160 \\
        \bottomrule
    \end{tabular}
\end{table}
```

---

## Cross-Referencing Protocol

### Label Convention
Every numbered element MUST have a `\label{}`:
- Equations: `\label{eq:euler_buckling}`
- Figures: `\label{fig:hydraulic_model}`
- Tables: `\label{tab:species_comparison}`
- Definitions: `\label{def:cavitation}` (via tcolorbox `label=` option)
- Theorems: `\label{thm:euler_buckling}`
- Chapters: `\label{ch:structural_limits}`
- Sections: `\label{sec:biological_compensations}`

### Reference Commands
- `\ref{label}` --- number only: "see Section 3.2"
- `\eqref{label}` --- equation with parens: "from Equation (3.1)"
- `Theorem~\ref{thm:name}` --- always prefix with element type
- Use non-breaking space (`~`) between element name and `\ref`

### Cross-Chapter References
- "As shown in Chapter~\ref{ch:hydraulics}..."
- "Recall Definition~\ref{def:cavitation} from Chapter 3..."
- Use `\begin{connectionbox}` for extended cross-chapter discussion

---

## Footnotes

- Use `\footnote{}` for parenthetical commentary, not for citations
- **NEVER use `\footnote{}` for citations** --- use `\cite{}` only
- Keep footnotes concise (1-2 sentences)
- Maximum 2-3 footnotes per chapter --- more suggests content belongs in body text or asides
- Footnotes are automatically styled for dark mode (dimsilver rule and numbers)

---

## Code Listings

When chapters include code examples, use the `lstlisting` environment:

```latex
\begin{lstlisting}[language=Python, caption={Calculating critical buckling load.}]
def critical_load(E, I, K, L):
    """Euler buckling critical load."""
    return (math.pi**2 * E * I) / (K * L)**2
\end{lstlisting}
```

- Always include `language=` for syntax highlighting
- Include `caption={}` for referenced listings
- Dark mode styling is pre-configured (white text on deep charcoal)
- Available languages: Python, C, C++, Java, JavaScript, HTML, XML, SQL, LaTeX, Bash

---

## Theorem/Proof Environments

For mathematical content, use `amsthm` environments:

```latex
\begin{theorem}[Euler Buckling]
\label{thm:euler_buckling}
A uniform column of length $L$ buckles when the axial load exceeds
$P_{cr} = \frac{\pi^2 EI}{(KL)^2}$.
\end{theorem}

\begin{proof}
Consider a column with small lateral deflection $y(x)$...
\end{proof}
```

Available environments: `theorem`, `lemma`, `corollary`, `proposition`, `remark`
All are numbered per-chapter (Theorem 3.1, Lemma 3.2...) except `remark` (unnumbered).

### When to Use Theorem Environments
- Use `\begin{theorem}` for formal mathematical statements that require proof
- Use `\begin{lemma}` for supporting results used in proving a theorem
- Use `\begin{corollary}` for direct consequences of a theorem
- Use `\begin{proposition}` for results that are important but not central enough for `theorem`
- Use `\begin{remark}` for informal observations after a proof
- Use `\begin{principle}` (tcolorbox) instead of `theorem` for non-mathematical central claims

---

## Citation Integration

### IEEE Citation Format (MANDATORY)

**CRITICAL: Use `\cite{key}` for ALL citations. NEVER use `\footnote{}` for citations.**

```latex
% Single citation
...the approach described in the source material \cite{<citation_key>}.

% Multiple citations
...consistent findings across sources \cite{<citation_key_a>, <citation_key_b>}.

% Citation with context
As noted in the cited source \cite{<citation_key>}, the approach...

% Citation at sentence start
\citet{<citation_key>} demonstrated that...
```

### Citation Rules
1. Every factual claim needs a citation
2. **NEVER use `\footnote{}` for citations** - use `\cite{}` only
3. No more than 3 citations per sentence
4. Primary sources preferred over secondary
5. Recent citations for current state-of-the-art claims
6. All citation keys must exist in `bibliography.bib`

---

## Decision Capture Requirements

### Required Decision Types

| Decision Type | When | Example |
|--------------|------|---------|
| `source_synthesis` | Combining sources | "Integrated 3 sources for comprehensive coverage" |
| `citation_placement` | Adding citations | "Cited immediately after the supported claim" |
| `writing_style` | Tone decisions | "Used passive voice for methodology section" |
| `content_organization` | Structure choices | "Organized by chronological development" |

### Example Decision Log
```python
capture.log_decision(
    decision_type="source_synthesis",
    decision="integrated_cited_source_with_courseforge_module",
    rationale="Combined a cited source's technical description with course-module pedagogical explanation to create an accessible yet rigorous section",
    sources_used=["<citation_key>", "courseforge:<module_id>.html"],
    synthesis_approach="technical_pedagogical_blend"
)

capture.log_decision(
    decision_type="citation_placement",
    decision="cite_source_after_claim",
    rationale="Direct factual claim requires immediate citation support",
    citation_key="<citation_key>",
    location="paragraph_2_sentence_3"
)
```

---

## Source Processing

### Cited Source Integration
```python
def process_cited_source(source: dict) -> str:
    """Extract key information from a cited source for synthesis."""
    return {
        "main_contribution": extract_contribution(source['summary']),
        "key_findings": extract_findings(source['summary']),
        "citation_key": source['citation_key'],
        "year": source.get('year')
    }
```

### Courseforge Module Parsing
```python
def process_courseforge_module(html_path: str) -> str:
    """Extract semantic content from Courseforge HTML."""
    # Strip interactive components
    # Extract headings, paragraphs, lists
    # Preserve code blocks
    # Return clean text with structure
```

### Raw Content Integration
```python
def process_raw_content(md_path: str) -> str:
    """Parse markdown notes for section content."""
    # Parse markdown structure
    # Extract relevant sections
    # Preserve citations if present
```

---

## Quality Standards

### Minimum Requirements
- Word count within 10% of target
- Every factual claim has citation
- Academic tone throughout
- Logical paragraph flow
- Clear topic sentences

### Section Completeness Checklist
- [ ] Opening paragraph establishes section purpose
- [ ] All objectives addressed
- [ ] Citations properly formatted
- [ ] Subsections logically organized
- [ ] Closing paragraph transitions to next section

---

## Error Handling

### Insufficient Sources
If sources inadequate for target word count:
1. Log warning in decision capture
2. Generate content to best of ability
3. Flag sections needing additional research
4. Continue with available material

### Citation Key Missing
If referenced paper lacks citation key:
1. Generate citation key from metadata
2. Log decision with rationale
3. Add to citations_used output
4. Flag for bibliography assembly
