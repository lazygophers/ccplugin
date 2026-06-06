# Commit Message Examples

```bash
git commit -m "feat(auth): add login flow"
git commit -m "fix(api): handle empty user response"
git commit -m "docs(readme): update install guide"
git commit -m "refactor(git): merge commit command into skill"
git commit -m "test(core): add parser edge cases"
git commit -m "chore(deps): update lockfile"
```

## Multiline Example

```bash
git commit -m "$(cat <<'EOF'
feat(config): add workspace defaults

Add default settings so new workspaces start with shared conventions.

close #123
EOF
)"
```
