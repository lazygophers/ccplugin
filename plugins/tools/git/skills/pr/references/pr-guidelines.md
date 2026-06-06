# Pull Request Guidelines

## Title Format

Use Conventional Commits style:

```text
<type>(<scope>): <subject>
```

Examples:

- `feat(api): add user auth endpoint`
- `fix(db): prevent connection leak`
- `docs(readme): update install guide`

## Creation Flow

1. Ensure code is committed to a feature branch.
2. Ensure branch is based on the latest target branch when required.
3. Push branch to remote.
4. Create PR with complete description, test plan, and linked issue.
5. Respond to review comments promptly.
6. Ensure CI passes before merge.

## Review Checklist

- [ ] PR has one clear purpose.
- [ ] Change list matches title and summary.
- [ ] Tests or manual validation are documented.
- [ ] Docs are updated when behavior changes.
- [ ] Security or performance risks are called out.
- [ ] No unrelated files are included.

## Avoid

- Oversized PRs when safe split is possible.
- Vague titles such as `update code` or `fix stuff`.
- Missing test plan.
- Hidden breaking changes.
- Unrelated cleanup mixed with feature or bug fix.
