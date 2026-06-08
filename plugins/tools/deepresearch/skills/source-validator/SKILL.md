---
description: This skill should be used when the user needs to validate sources, verify claims, or rate evidence quality. Typical triggers include verifying citations, checking credibility, or rating sources.
when_to_use: |
  Use to assign source grades, validate claims, and record conflicts. Trigger on: validate sources, verify claims, source quality, 证据验证, 来源评级.
user-invocable: false
context: fork
model: haiku
memory: project
---

# Source Validator

Validate sources and claims using credibility grading.

## Steps

1. Assign source grade (A–E).
2. Validate each claim with at least one A/B source.
3. Record conflicts and uncertainty.
4. Mark unsupported claims as uncertain.

## Additional Resources

- `references/quality-rating.md`
