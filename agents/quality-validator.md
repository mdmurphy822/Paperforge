# Quality Validator Agent

## Overview
The `quality-validator` agent assesses academic rigor, citation completeness, structural coherence, and overall quality of the generated paper before final compilation.

## Agent Classification
- **Type**: `quality-assurance`
- **Max Instances**: 2
- **Workflow Position**: Phase 5 (validation)
- **Execution**: Parallel (structure + citations)

## Capabilities
- `academic_rigor_check` - Assess scholarly quality
- `citation_validation` - Verify citation completeness
- `structure_verification` - Check document structure

---

## Responsibilities

### 1. Structure Validation
- Verify all required sections present
- Check heading hierarchy
- Validate section flow and coherence
- Assess word count targets

### 2. Citation Validation
- Verify every claim has citation
- Check citation format consistency
- Validate bibliography completeness
- Identify orphaned references

### 3. Academic Quality Assessment
- Evaluate writing quality
- Check technical accuracy indicators
- Assess argumentation strength
- Review methodology rigor (if applicable)

### 4. Quality Scoring
- Generate overall quality score
- Identify specific issues
- Prioritize issues by severity
- Recommend revisions

---

## Input Format

```json
{
  "project_path": "/path/to/exports/PROJECT_ID",
  "sections_path": "03_content_development",
  "bibliography_path": "04_citations/bibliography.bib",
  "paper_outline": "01_planning/paper_outline.md",
  "validation_type": "comprehensive",
  "thresholds": {
    "min_quality_score": 0.75,
    "min_citation_coverage": 0.90,
    "max_issues_high_severity": 0
  }
}
```

---

## Output Format

### quality_report.json
```json
{
  "overall_score": 0.87,
  "pass": true,
  "validation_timestamp": "2026-01-10T14:30:00Z",

  "structure_validation": {
    "score": 0.92,
    "sections_expected": 8,
    "sections_found": 8,
    "sections_complete": true,
    "heading_hierarchy_valid": true,
    "word_count": {
      "target": 8000,
      "actual": 8234,
      "variance": 0.029
    }
  },

  "citation_validation": {
    "score": 0.95,
    "claims_total": 87,
    "claims_cited": 83,
    "citation_coverage": 0.954,
    "citations_unique": 28,
    "bibliography_entries": 28,
    "orphaned_references": 0,
    "missing_citations": [
      {
        "section": "section_04_results",
        "paragraph": 3,
        "claim": "Model-X achieves state-of-the-art performance",
        "severity": "medium"
      }
    ]
  },

  "academic_quality": {
    "score": 0.82,
    "tone_consistency": 0.88,
    "technical_depth": 0.85,
    "argumentation_strength": 0.78,
    "methodology_rigor": 0.80
  },

  "issues": [
    {
      "id": "ISS001",
      "type": "missing_citation",
      "severity": "medium",
      "section": "section_04_results",
      "description": "Performance claim without citation",
      "suggestion": "Add citation for Model-X benchmark results"
    },
    {
      "id": "ISS002",
      "type": "weak_transition",
      "severity": "low",
      "section": "section_03_methodology",
      "description": "Abrupt transition between subsections",
      "suggestion": "Add transitional paragraph"
    }
  ],

  "recommendations": [
    "Add 4 citations to Results section for uncited claims",
    "Strengthen methodology justification in section 3.2",
    "Consider adding limitations subsection to Discussion"
  ]
}
```

### citation_coverage.json
```json
{
  "by_section": {
    "section_01_introduction": {
      "claims": 12,
      "citations": 11,
      "coverage": 0.917
    },
    "section_02_background": {
      "claims": 25,
      "citations": 24,
      "coverage": 0.960
    }
  },
  "uncited_claims": [
    {
      "section": "section_04_results",
      "text": "Model-X achieves state-of-the-art performance on...",
      "suggested_citation": "acme2023modeleval"
    }
  ],
  "citation_density": {
    "overall": 3.5,
    "by_section": {
      "introduction": 2.1,
      "background": 5.2,
      "methodology": 1.8,
      "results": 4.1
    }
  }
}
```

---

## Validation Checks

### Structure Checks
```python
def validate_structure(sections: List[str], outline: dict) -> dict:
    """Validate document structure against outline."""
    results = {
        "sections_expected": len(outline['sections']),
        "sections_found": len(sections),
        "missing_sections": [],
        "extra_sections": [],
        "heading_issues": []
    }

    expected_titles = [s['title'] for s in outline['sections']]
    found_titles = [extract_title(s) for s in sections]

    results['missing_sections'] = set(expected_titles) - set(found_titles)
    results['extra_sections'] = set(found_titles) - set(expected_titles)

    # Check heading hierarchy
    for section in sections:
        issues = check_heading_hierarchy(section)
        results['heading_issues'].extend(issues)

    return results
```

### Citation Validation
```python
def validate_citations(sections: List[str], bibliography: dict) -> dict:
    """Validate citation completeness and consistency."""
    results = {
        "claims_total": 0,
        "claims_cited": 0,
        "missing_citations": [],
        "orphaned_references": []
    }

    all_citations = set()

    for section in sections:
        claims = identify_claims(section)
        results['claims_total'] += len(claims)

        for claim in claims:
            if has_citation(claim):
                results['claims_cited'] += 1
                all_citations.update(extract_citation_keys(claim))
            else:
                results['missing_citations'].append({
                    "section": section_name,
                    "claim": claim['text'][:100],
                    "severity": assess_claim_importance(claim)
                })

    # Find orphaned references
    bib_keys = set(bibliography.keys())
    results['orphaned_references'] = list(bib_keys - all_citations)

    return results
```

### Academic Quality Assessment
```python
def assess_academic_quality(content: str) -> dict:
    """Assess academic writing quality."""
    results = {
        "tone_consistency": 0.0,
        "technical_depth": 0.0,
        "argumentation_strength": 0.0
    }

    # Tone consistency: Check for informal language
    informal_patterns = ['gonna', 'wanna', "isn't", "can't", 'stuff', 'things']
    informal_count = sum(content.lower().count(p) for p in informal_patterns)
    word_count = len(content.split())
    results['tone_consistency'] = max(0, 1 - (informal_count / word_count * 100))

    # Technical depth: Check for technical terms and definitions
    technical_indicators = count_technical_terms(content)
    definitions = count_definitions(content)
    results['technical_depth'] = min(1.0, (technical_indicators + definitions) / 50)

    # Argumentation: Check for claim-evidence-analysis structure
    claims = count_claims(content)
    evidence = count_evidence_markers(content)
    analysis = count_analysis_markers(content)
    results['argumentation_strength'] = min(1.0, (claims + evidence + analysis) / 30)

    return results
```

---

## Claim Identification

### Claim Patterns
```python
CLAIM_INDICATORS = [
    r'\b(show|demonstrate|prove|indicate|suggest|reveal)\b',
    r'\b(achieve|outperform|improve|surpass|exceed)\b',
    r'\b(is|are|was|were) (the|a) (first|best|most|only)\b',
    r'\b(significant|substantial|notable|important)\b',
    r'\bstate-of-the-art\b',
    r'\b\d+%\s+(improvement|increase|decrease|accuracy)\b',
]

def identify_claims(text: str) -> List[dict]:
    """Identify sentences that make claims requiring citations."""
    sentences = split_sentences(text)
    claims = []

    for sentence in sentences:
        for pattern in CLAIM_INDICATORS:
            if re.search(pattern, sentence, re.IGNORECASE):
                claims.append({
                    "text": sentence,
                    "pattern_matched": pattern,
                    "has_citation": bool(re.search(r'\\cite\{', sentence))
                })
                break

    return claims
```

---

## Severity Levels

| Severity | Description | Action Required |
|----------|-------------|-----------------|
| `critical` | Paper cannot be published | Must fix before compilation |
| `high` | Significant quality issue | Should fix, blocks pass |
| `medium` | Notable quality concern | Recommended to fix |
| `low` | Minor improvement opportunity | Optional fix |

### Issue Types and Default Severity

| Issue Type | Default Severity |
|------------|-----------------|
| `missing_section` | critical |
| `missing_citation` (factual claim) | high |
| `missing_citation` (general statement) | medium |
| `orphaned_reference` | low |
| `word_count_deviation` (>20%) | medium |
| `heading_hierarchy_error` | medium |
| `weak_transition` | low |
| `informal_language` | medium |

---

## Decision Capture Requirements

### Required Decision Types

| Decision Type | When | Example |
|--------------|------|---------|
| `quality_assessment` | Scoring | "Section 4 needs additional citations" |
| `severity_assignment` | Rating issues | "Missing methodology citation is high severity" |
| `pass_fail_decision` | Final determination | "Pass with 0.87 score, above 0.75 threshold" |
| `revision_recommendation` | Suggesting fixes | "Add 4 citations to address gaps" |

### Example Decision Log
```python
capture.log_decision(
    decision_type="quality_assessment",
    decision="section_04_below_threshold",
    rationale="Results section has 4 uncited performance claims including state-of-the-art assertions; citation coverage 0.78 below 0.90 threshold",
    section="section_04_results",
    score=0.78,
    issues_found=4
)

capture.log_decision(
    decision_type="pass_fail_decision",
    decision="pass",
    rationale="Overall quality score 0.87 exceeds minimum threshold 0.75; no critical issues; 3 medium issues identified but non-blocking",
    overall_score=0.87,
    threshold=0.75,
    critical_issues=0,
    high_issues=0,
    medium_issues=3
)
```

---

## Parallel Execution Strategy

When 2 validators are dispatched:
- **Validator 1**: Structure validation + word count + heading hierarchy
- **Validator 2**: Citation validation + academic quality assessment

Results merged into single `quality_report.json`.

---

## Quality Thresholds

### Default Thresholds
```python
DEFAULT_THRESHOLDS = {
    "min_quality_score": 0.75,
    "min_citation_coverage": 0.90,
    "max_word_count_variance": 0.15,
    "max_issues_critical": 0,
    "max_issues_high": 0,
    "min_section_completeness": 1.0
}
```

### Pass Criteria
```python
def determine_pass(report: dict, thresholds: dict) -> bool:
    """Determine if paper passes validation."""
    checks = [
        report['overall_score'] >= thresholds['min_quality_score'],
        report['citation_validation']['citation_coverage'] >= thresholds['min_citation_coverage'],
        count_issues_by_severity(report, 'critical') <= thresholds['max_issues_critical'],
        count_issues_by_severity(report, 'high') <= thresholds['max_issues_high']
    ]

    return all(checks)
```

---

## Quality Standards

- Overall score must meet threshold (default 0.75)
- Citation coverage must meet threshold (default 0.90)
- No critical severity issues allowed
- No high severity issues allowed (configurable)
- All required sections must be present
- Word count within acceptable variance
