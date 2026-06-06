---
description: "Creates and reviews GitHub Pull Request content with standard templates, change descriptions, test plans, and review checklists."
when_to_use: |
  Use when the user needs to create a PR, draft a pull request description, prepare a merge request, summarize changes for review, or build a PR checklist.
  Trigger on: pull request, PR, merge request, code review, review checklist, create PR, draft PR, 提交 PR, 创建 PR, 合并请求, 代码审查.
user-invocable: true
context: fork
model: haiku
memory: project
---

# Pull Request 规范

Draft focused Pull Requests with clear scope, test evidence, and review-ready structure.

## Workflow

1. Confirm branch state and committed changes.
2. Compare current branch against target branch.
3. Summarize purpose, implementation approach, and user-visible impact.
4. Select change type and scope using `references/pr-guidelines.md`.
5. Fill PR body using `references/pr-template.md`.
6. Include test plan and known risks.
7. Keep PR atomic; split broad or unrelated work.

## Required Checks

- Keep one PR focused on one purpose.
- Avoid large PRs when changes can be split safely.
- Include test plan even when tests are not run; state reason.
- Link related issue when available.
- Ensure title follows `<type>(<scope>): <subject>`.

## Additional Resources

### Reference Files

- `references/pr-template.md` — full PR body template.
- `references/pr-guidelines.md` — naming, flow, review checklist, and pitfalls.

### Example Files

- `examples/pr-titles.md` — valid PR title examples.
