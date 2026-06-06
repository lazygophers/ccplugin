# Conventional Commits Reference

## Template

```text
<type>(<scope>): <subject>

<body>
<footer>
```

## Fields

- `type`: Required. Use `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `revert`, `build`, `ci`, `wip`, `workflow`, `types`, `release`, or `other`.
- `scope`: Optional. Use affected module, package, plugin, directory, or feature name, such as `git`, `commit`, `api`, `docs`, or `build`.
- `subject`: Required. Keep under 50 characters when possible. Use imperative mood, lowercase first letter, and no trailing period.
- `body`: Optional. Explain reason, impact, and tradeoffs. Keep lines near 80 characters.
- `footer`: Optional. Include breaking changes or issue closing metadata, such as `BREAKING CHANGE: ...` or `close #123`.

## Checklist

- [ ] Format matches `<type>(<scope>): <subject>`.
- [ ] `type` matches change kind.
- [ ] `scope` identifies affected area.
- [ ] `subject` describes change clearly.
- [ ] Mixed change types are split into separate commits.
- [ ] Breaking change or issue footer is present when needed.

## Forbidden Messages

Avoid vague subjects such as `update`, `fix bug`, `changes`, or `misc`.
