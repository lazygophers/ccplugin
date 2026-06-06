# Commit Workflow

## Before Commit

1. Run `git status`.
2. Confirm changed files match requested scope.
3. Check for secrets, credentials, logs, backups, temporary files, generated artifacts, archives, and unrelated changes.
4. Run relevant tests or lint when available.
5. Stage only intended files with explicit paths.
6. Run `git diff --cached`.

## Commit

Use a single-line message for simple changes:

```bash
git commit -m "fix(api): handle empty user response"
```

Use heredoc for multiline messages:

```bash
git commit -m "$(cat <<'EOF'
feat(auth): add login flow

Explain reason and impact here.
EOF
)"
```

## After Commit

- Run `git log -1 --oneline` to confirm commit message.
- Run `git status` to confirm remaining worktree state.
- Report any intentionally uncommitted changes separately.
