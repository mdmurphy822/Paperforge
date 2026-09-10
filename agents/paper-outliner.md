# Paper Outliner Agent

## Overview
The `paper-outliner` agent analyzes input sources and creates a structured paper outline with sections, citation strategy, and a plan for what source material each section will need.

## Agent Classification
- **Type**: `specialized`
- **Max Instances**: 1
- **Workflow Position**: Phase 1 (planning)
- **Execution**: Sequential

## Capabilities
- `paper_structure` - Determine paper type and section structure
- `section_planning` - Plan individual sections with objectives
- `citation_strategy` - Define citation requirements per section

---

## Responsibilities

### 1. Input Analysis
- Analyze raw content, Courseforge modules, or a topic description
- Determine appropriate paper type (academic, whitepaper, lit_review)
- Identify key themes and topics

### 2. Paper Structure Creation
- Create section outline based on paper type
- Define section objectives and word count targets
- Establish section dependencies

### 3. Source Planning
- For each section, identify what kind of source would support its claims
- Note where source material is still needed vs. already available
- Define an approximate source count per section

### 4. Citation Strategy
- Determine citation density per section
- Identify sections requiring heavy citation support
- Select citation style (APA, IEEE, ACM)

---

## Input Format

```json
{
  "title": "<paper title>",
  "paper_type": "lit_review",
  "author": "<author or team name>",
  "input_sources": {
    "raw_content": ["notes.md", "outline_draft.json"],
    "courseforge": null,
    "topic_description": "<one-paragraph description of scope>"
  },
  "citation_style": "ieee",
  "target_length": "8000-10000 words"
}
```

---

## Output Format

### paper_outline.md
```markdown
# Paper Outline: <Title>

## Paper Type: Literature Review (Systematic)

## Sections

### 1. Abstract (150-250 words)
- Objective: Summarize scope and findings
- Citations: 0

### 2. Introduction (800-1000 words)
- Objective: Establish context, state purpose
- Citations: 5-8
- Topics: <topic A>, <topic B>

### 3. Background (1000-1200 words)
- Objective: Technical foundations
- Citations: 10-15
- Topics: <topic C>, <topic D>

[... additional sections ...]
```

### source_plan.json
```json
{
  "needs": [
    {
      "topic": "<topic label>",
      "keywords": ["<search term>", "<search term>"],
      "target_source_count": 5,
      "assigned_sections": ["introduction", "background"]
    }
  ],
  "total_target_sources": 30,
  "citation_style": "ieee"
}
```

---

## Decision Capture Requirements

### Required Decision Types

| Decision Type | When | Example |
|--------------|------|---------|
| `paper_type_selection` | Determining document type | "Selected lit_review based on survey scope" |
| `section_structure` | Creating outline | "8-section IMRAD variant for systematic review" |
| `citation_strategy` | Planning citations | "Heavy citation in background, moderate elsewhere" |
| `source_focus` | Defining source needs | "Prioritize foundational sources over recent commentary" |

### Example Decision Log
```python
capture.log_decision(
    decision_type="paper_type_selection",
    decision="literature_review_systematic",
    rationale="Input describes a multi-year survey scope; systematic review format allows comprehensive coverage with methodological rigor",
    alternatives_considered=[
        {"option": "narrative_review", "rejected_because": "Less rigorous for a technical audience"},
        {"option": "academic_research", "rejected_because": "No original experiments presented"}
    ]
)
```

---

## Paper Type Templates

### Academic Research Paper
```
Abstract → Introduction → Related Work → Methodology →
Results → Discussion → Conclusion → References
```

### Whitepaper (Technical)
```
Executive Summary → Problem Statement → Technical Background →
Proposed Solution → Implementation → Case Studies → Conclusion
```

### Literature Review (Systematic)
```
Abstract → Introduction → Methods → Results (Thematic Sections) →
Discussion → Limitations → Conclusion → References
```

---

## Quality Standards

- All sections must have defined objectives
- Word count targets must sum to overall target (±10%)
- Citation targets must be realistic given available source material
- The source plan must cover every major topic in the outline
