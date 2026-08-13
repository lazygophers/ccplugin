---
description: This skill should be used when the user asks to "research X", "deep dive into X", "compare A vs B", "evaluate this project", or requests evidence-backed technical research, architecture review, or technology selection.

user-invocable: true
context: fork
model: haiku
memory: project
---

# Deep Research Workflow

Orchestrate evidence-backed technical research with explicit sources and confidence.

## Core Workflow

1. Identify scope, constraints, and target audience.
2. Draft a research plan using `references/workflow.md`.
3. Route tasks by type using `references/task-routing.md`.
4. Retrieve sources and track provenance.
5. Validate sources and claims using `references/source-quality.md`.
6. Synthesize evidence into a decision-ready report.
7. Output in a structured format from `references/output-formats.md`.

## Quality Standards

- Cite all key claims.
- Flag conflicts and uncertainty.
- Separate facts from recommendations.
- Provide limitations and next checks.

## Additional Resources

### Reference Files

- `references/workflow.md` — end-to-end workflow and gates.
- `references/task-routing.md` — task-to-agent/skill routing rules.
- `references/source-quality.md` — source rating and validation rules.
- `references/output-formats.md` — report formats and required sections.

### Example Files

- `examples/technology-selection.md` — framework comparison example.
- `examples/architecture-review.md` — architecture assessment example.
- `examples/project-assessment.md` — project evaluation example.
