# Paperforge Agent Coordination

## Execution Protocol (this repo's conventions)

- ONE agent instance = ONE file/section at a time — no shared file editing, no concurrent writes to the same section
- Keep parallel batches to a sane size for your dispatcher (10 is a reasonable default) and wait for a batch to finish before starting the next
- Every agent logs its decisions with a rationale (20+ characters) — see Decision Capture below
- Failed tasks: retry up to 3 times (immediate, then 5s, then 30s) before flagging for manual intervention

---

## Agent Coordination Strategy

### Workspace Containment
Each agent operates within a single timestamped project folder:
```
exports/YYYYMMDD_HHMMSS_paper_title/
```

All agent outputs go to designated subdirectories within this folder.

### Parallel Execution Rules

| Phase | Agents | Parallelism | Notes |
|-------|--------|-------------|-------|
| Planning | paper-outliner | Sequential | Creates structure, identifies source material needed |
| Content Gen | content-synthesizer | Max 10 | ONE AGENT = ONE SECTION |
| Citation | citation-manager, citation-loader, citation-verifier | Sequential → parallel | Aggregate citations, attach source text, verify claims |
| Validation | quality-validator | Max 2 | Structure + citations |
| Compilation | latex-compiler, markdown-exporter | Parallel 2 | Independent outputs |

### Batch Size Limitations
```
Maximum 10 simultaneous Task calls per batch
```

Wait for ALL batch completions before proceeding to next phase.

---

## Scratchpad Protocol

Each agent uses a scratchpad within the project folder:
```
exports/{PROJECT}/agent_workspaces/{AGENT_NAME}/
├── scratchpad.md        # Working notes
├── decisions.jsonl      # Decision log
└── outputs/             # Generated artifacts
```

### Scratchpad Rules
1. Each agent has exclusive access to its scratchpad
2. No cross-agent scratchpad access
3. Final outputs copied to phase directories
4. Scratchpad cleared after phase completion

---

## Inter-Agent Communication

Agents communicate through structured files in phase directories:

### Planning → Content Generation
```json
// 01_planning/source_plan.json
{
  "topics": ["<topic A>", "<topic B>"],
  "sources": [
    {
      "citation_key": "<citation_key>",
      "title": "<source title>",
      "source_type": "url",
      "assigned_sections": ["introduction", "<section id>"]
    }
  ]
}
```

### Content Generation → Citation Assembly
```json
// 03_content_development/citations_used.json
{
  "section_01_introduction": ["<citation_key_a>", "<citation_key_b>"],
  "section_02_background": ["<citation_key_c>", "<citation_key_d>"]
}
```

---

## Decision Capture Requirements

Every agent should log its non-obvious decisions — append one JSON object per
decision to `training-captures/paperforge/{PAPER_ID}/phase_{phase}/decisions.jsonl`
(bring your own writer; this is a convention, not a shipped module):

```json
{
  "decision_type": "category",
  "decision": "what was decided",
  "rationale": "why (minimum 20 characters)",
  "alternatives_considered": [
    {"option": "...", "rejected_because": "..."}
  ]
}
```

### Required Fields
- `decision_type`: Category of decision
- `decision`: The actual choice made
- `rationale`: Explanation (20+ characters)
- `alternatives_considered`: Optional list of rejected options

---

## Error Handling

### Retry Protocol
1. First retry: Immediate
2. Second retry: After 5 seconds
3. Third retry: After 30 seconds
4. After 3 failures: Log error, require manual intervention

### Error Logging
Errors logged to:
- `project_log.md` in export folder
- `training-captures/paperforge/{PAPER_ID}/errors.jsonl`

---

## Quality Gates

### Phase Completion Criteria

| Phase | Completion Criteria |
|-------|---------------------|
| Planning | Outline has all required sections, sources identified |
| Content Gen | All sections generated, word count met |
| Citations | All cited papers in bibliography |
| Validation | Quality score >= threshold |
| Compilation | PDF generated without errors |

### Validation Thresholds
- Quality score minimum: 0.75
- Citation coverage minimum: 0.90
- Section completeness: 1.0 (all sections must be present)
