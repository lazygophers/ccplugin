---
description: "Creates and manages GitHub Issues with bug report, feature request, label, priority, and lifecycle guidance."
when_to_use: |
  Use when the user needs to create an issue, report a bug, write a feature request, triage issue labels, draft reproduction steps, or manage issue lifecycle.
  Trigger on: issue, GitHub issue, bug report, feature request, reproduce, labels, milestone, 创建 issue, 报告 bug, 提交需求, 功能请求, 复现步骤.
user-invocable: true
context: fork
model: haiku
memory: project
---

# GitHub Issue 规范

Create clear, actionable GitHub Issues for bugs, feature requests, documentation gaps, questions, and discussions.

## Workflow

1. Search existing issues to avoid duplicates.
2. Choose issue type using `references/issue-guidelines.md`.
3. Fill the relevant template from `references/issue-templates.md`.
4. Add priority, type, and status labels when known.
5. Add milestone and assignee only when explicitly available.
6. Link related PR after implementation.
7. Update status and close with a reason.

## Required Checks

- Use concise title format: `[<type>] <subject>`.
- Include reproducible steps for bug reports.
- Include problem background and proposed solution for feature requests.
- Provide environment info and screenshots when relevant.
- Avoid duplicate issues.

## Additional Resources

### Reference Files

- `references/issue-templates.md` — bug report and feature request templates.
- `references/issue-guidelines.md` — title, labels, flow, and checklists.

### Example Files

- `examples/issue-titles.md` — valid issue title examples.
