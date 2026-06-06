---
description: "Generates Conventional Commits Git commit messages."
when_to_use: |
  Use when the user needs to commit code changes, stage or unstage Git changes, amend a commit, draft or review a commit message, or format a message using Conventional Commits.
  Trigger on: commit, git commit, staged changes, stage, unstage, amend, commit message, Conventional Commits, save changes, 提交, 暂存, 提交信息, 生成提交, 生成提交信息, 改提交, 帮我提交.
user-invocable: true
context: fork
model: haiku
memory: project
---

# Git Commit 规范

Generate atomic Git commits with Conventional Commits messages.

## Workflow

1. Run `git status` to inspect changed and staged files.
2. Confirm change scope and exclude secrets, temporary files, logs, backups, binaries, archives, and unrelated files.
3. Run relevant tests or lint; explain risk if user explicitly skips them.
4. Stage only files needed for current commit with `git add <file...>`.
5. Run `git diff --cached` to inspect staged changes.
6. Draft commit message using `references/conventional-commits.md`.
7. Commit with `git commit`; use heredoc for multiline messages.
8. Verify result with `git log -1 --oneline` or `git status`.

## Required Checks

- Keep each commit atomic and independently revertible.
- Split mixed change types into separate commits.
- Keep `subject` short, imperative, lowercase, and without trailing period.
- Never skip hooks unless user explicitly requests it.

## Additional Resources

### Reference Files

- `references/conventional-commits.md` — message format, fields, types, and checklist.
- `references/commit-workflow.md` — staging, verification, and safety workflow.

### Example Files

- `examples/messages.md` — valid commit message examples.
