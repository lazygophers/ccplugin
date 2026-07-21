# Matt Pocock `skills` — abstracted design patterns (copy-me skeleton)

Source: 41 `SKILL.md` files read in full + `README.md`, `CLAUDE.md`/`AGENTS.md`, `.agents/invocation.md`, `.agents/writing-docs.md`, `docs/productivity/writing-great-skills.md`, `GLOSSARY.md`. All citations are file paths within https://github.com/mattpocock/skills/tree/main/.

The whole authoring theory lives in `skills/productivity/writing-great-skills/SKILL.md` + its `GLOSSARY.md`. Everything below is the operating instantiation of that theory across 41 skills.

---

## 1. Directory shape (mandatory)

```
skills/<bucket>/<skill-name>/
  SKILL.md              # always present, always named exactly this
  agents/openai.yaml    # always present — Codex UI + invocation policy
  <REFERENCE>.md        # 0..N disclosed reference files (capitalised, kebab-SCREAMING optional)
  <TEMPLATE>.*          # 0..N copy-me template/config files
  scripts/              # 0..N helper scripts
```

- `SKILL.md` filename is fixed. Reference siblings named for what they hold (`GLOSSARY.md`, `HTML-REPORT.md`, `DEEPENING.md`, `LOGIC.md`, `tests.md`, `mocking.md`).
- Bucket (`engineering`/`productivity`/`misc`/`personal`/`in-progress`/`deprecated`) signals promotion status, not skill behaviour. (`CLAUDE.md` L217-224)
- **No skill ever links into another skill's folder.** Dependencies are `/skill`-style prose invocations. (`.agents/invocation.md` L29)

---

## 2. Frontmatter — the invocation axis

Two fields are near-universal; one optional field flips invocation mode.

```yaml
---
name: <kebab-case-id>            # required, matches dir name
description: <one-liner-or-long> # required; content depends on invocation mode (below)
disable-model-invocation: true   # OPTIONAL — present iff user-invoked
argument-hint: "<hint>"          # OPTIONAL — only when skill takes an arg (handoff, teach, loop-me, claude-handoff)
---
```

### Two invocation modes (`.agents/invocation.md` L13-21, GLOSSARY.md `Model-Invoked`/`User-Invoked`)

| Mode | `disable-model-invocation` | `agents/openai.yaml` | `description` style | Who reaches it |
|---|---|---|---|---|
| **Model-invoked** | omitted | no `policy` block | **model-facing, trigger-rich**: "Use when the user wants…, mentions…, asks for…" | model OR human |
| **User-invoked** | `true` | `policy.allow_implicit_invocation: false` | **human-facing one-liner**, trigger lists stripped | human typing name ONLY |

Test for which mode (`.agents/invocation.md` L19): _could the model usefully reach for this autonomously?_ If yes → model-invoked. Reuse is the reason to extract, NOT the test.

Counts in repo (41 skills):
- User-invoked: ask-matt, grill-with-docs, implement, improve-codebase-architecture, setup-matt-pocock-skills, to-spec, to-tickets, triage, wayfinder, grill-me, handoff, teach, writing-great-skills, edit-article, batch-grill-me, claude-handoff, loop-me, setup-ts-deep-modules, to-questionnaire, wizard, writing-beats, writing-fragments, writing-shape, ubiquitous-language.
- Model-invoked: code-review, codebase-design, diagnosing-bugs, domain-modeling, prototype, research, resolving-merge-conflicts, tdd, grilling, obsidian-vault, git-guardrails-claude-code, migrate-to-shoehorn, scaffold-exercises, setup-pre-commit, design-an-interface, qa, request-refactor-plan.

### `agents/openai.yaml` (always present, tiny)

Model-invoked example (`skills/engineering/tdd/agents/openai.yaml`):
```yaml
interface:
  display_name: "TDD"
  short_description: "Test-driven red-green-refactor"
```
User-invoked example (`skills/engineering/ask-matt/agents/openai.yaml`):
```yaml
interface:
  display_name: "Ask Matt"
  short_description: "Find the right skill or workflow"
policy:
  allow_implicit_invocation: false
```
Sync rule (`.agents/invocation.md` L23): a skill is user-invoked in **both** harnesses or neither.

### Description-writing rules (writing-great-skills SKILL.md L2310-2317 "Writing the description")
1. **Front-load the skill's leading word** — description is where invocation work happens.
2. **One trigger per branch.** Synonyms renaming one branch = duplication; collapse them.
3. **Cut identity already in the body.** Keep description to triggers + any "when another skill needs…" reach clause.
4. Every word costs context load (model-invoked) — prune harder than the body.

---

## 3. SKILL.md body structure — the Information Hierarchy ladder

Per `writing-great-skills` SKILL.md L2318-2332 + GLOSSARY `Information Hierarchy`. Three rungs ranked by immediacy:

1. **In-skill steps** — ordered actions; each ends on a **completion criterion** (checkable + exhaustive). Primary tier.
2. **In-skill reference** — definition/rule/fact consulted on demand. Often a legitimately flat peer-set.
3. **External/disclosed reference** — pushed to a sibling `.md` behind a **context pointer**, loaded only when pointer fires.

Branch test for disclosure (GLOSSARY `Progressive Disclosure`): inline what every branch needs; push behind a pointer what only some branches reach. A pointer's **wording** (not its target) decides when the agent reaches the material — sharpen wording before inlining back.

### Observed section orders (by skill archetype)

**A. Thin orchestrator** (grill-with-docs, implement, grill-me) — 1-5 lines, just "Run a `/primitive` session [using `/other-skill`]." Body is the composition, not the procedure.

**B. Procedure skill with completion criteria** (diagnosing-bugs, setup-matt-pocock-skills, setup-ts-deep-modules, setup-pre-commit, git-guardrails, triage, to-tickets, wayfinder, scaffold-exercises) — numbered phases each ending on `**Done when:**` or a `[ ]` checklist. Example `diagnosing-bugs` "Phase 1 — Build a feedback loop" → "Completion criterion — a tight loop that goes red" with 4 `[ ]` bullets.

**C. Pure reference skill** (codebase-design, writing-great-skills, code-review's smell baseline) — glossary + principles + anti-patterns; no ordered steps. `codebase-design` opens with a `## Glossary` then `## Deep vs shallow`, `## Principles`, `## Designing for testability`, `## Relationships`, `## Rejected framings`, `## Going deeper` (pointers to disclosed refs).

**D. Template-emitter** (to-spec, to-tickets, request-refactor-plan, to-questionnaire, qa, ubiquitous-language) — short process section, then a fenced `<template-name>` block. Example `to-spec` → `<spec-template>` with 7 fixed sections.

**E. Branch-disclosed skill** (prototype) — `## Pick a branch` lists branches, each a pointer to a disclosed file (`LOGIC.md` / `UI.md`).

### Universal body beats (when present, in this order)
1. Optional `# H1 title` (some skip it — `tdd`, `research`, `prototype`, `grilling` open on prose).
2. **One-sentence job statement** ("A prototype is throwaway code that answers a question. The question decides the shape.") — `prototype` L437.
3. Optional `## Process` / numbered steps, each with `**Done when:**` or `[ ]` completion criteria.
4. Inline templates inside `<name>` custom-tag fences OR fenced ``` blocks.
5. Optional `## Failure modes` / anti-patterns (writing-great-skills, design-an-interface).
6. Optional `## Out of scope` (writing-shape, to-spec template).

### Negation rule (GLOSSARY `Negation`, writing-great-skills L2371)
Steer by the **positive** — state target behaviour so the banned one is never spoken. Keep a prohibition only as a hard guardrail you can't phrase positively, paired with what to do instead.

---

## 4. References — split granularity

- **Disclose when**: a branch needs it OR the top would bloat. `codebase-design` discloses `DEEPENING.md` (deepening a cluster) + `DESIGN-IT-TWICE.md` (parallel sub-agent interface exploration) — both reached only on a deeper path. `improve-codebase-architecture` discloses `HTML-REPORT.md` (the full visual scaffold).
- **Co-locate** (GLOSSARY `Co-location`): a concept's definition + rules + caveats under one heading, not scattered. `codebase-design` Glossary puts each term with its `_Avoid_` list inline.
- **Keep the top legible** — push down whatever you can; the ladder decides how far down, co-location decides what sits beside it once there.
- Reference filenames: SCREAMING for single-concept docs (`GLOSSARY.md`, `HTML-REPORT.md`, `DEEPENING.md`, `LOGIC.md`, `UI.md`, `ADR-FORMAT.md`, `CONTEXT-FORMAT.md`, `MISSION-FORMAT.md`, `LEARNING-RECORD-FORMAT.md`, `RESOURCES-FORMAT.md`, `AGENT-BRIEF.md`, `OUT-OF-SCOPE.md`); lowercase for topical (`tests.md`, `mocking.md`, `domain.md`, `triage-labels.md`, `issue-tracker-github.md`).

---

## 5. Report / output templates

Three shipping styles observed:

1. **Inline `<...-template>` custom-tag fences** inside SKILL.md — `to-spec` `<spec-template>`, `to-tickets` `<local-ticket-template>`+`<issue-template>`+`<vertical-slice-rules>`, `request-refactor-plan` `<refactor-plan-template>`, `to-questionnaire` `<questionnaire-template>`+`<question-example>`, `qa` fenced issue templates, `ubiquitous-language` output format. Keeps template next to the step that emits it.
2. **Sibling copy-me file** for large/structural artefacts — `improve-codebase-architecture/HTML-REPORT.md` (full HTML+Tailwind+Mermaid scaffold), `setup-ts-deep-modules/dependency-cruiser.config.cjs`, `wizard/template.sh`, `git-guardrails-claude-code/scripts/block-dangerous-git.sh`, `diagnosing-bugs/scripts/hitl-loop.template.sh`, `setup-matt-pocock-skills/{domain,issue-tracker-*,triage-labels}.md`.
3. **Inline config JSON / bash** for small setup snippets — `git-guardrails` settings.json hooks, `setup-pre-commit` `.husky/pre-commit`+`.lintstagedrc`+`.prettierrc`.

Template-emitter skill = short process + one fenced template block. Template body uses fixed `## Section` headings so output is uniform across runs.

---

## 6. Scoring / verification mechanisms

Repo avoids numeric scoring. Verification is structured as **completion criteria** + **checklists** + **self-checks**:

- **Completion criteria** per step (GLOSSARY `Completion Criterion`): checkable ("can the agent tell done from not-done?") AND exhaustive ("every modified model accounted for", not "produce a change list"). Diagnosing-bugs Phase 1 has a 4-bullet `[ ]` checklist (Red-capable / Deterministic / Fast / Agent-runnable).
- **"Prove the rules bite" pattern** (`setup-ts-deep-modules` step 6, `git-guardrails` step 5): run pass → inject violation → confirm fail → revert → confirm pass. The completion criterion is observing the fail.
- **"It's working if" pattern** (`.agents/writing-docs.md` L87-89, applied to docs pages): observable signals that the skill is firing correctly.
- **Verify checklists** (`setup-pre-commit` step 7, `scaffold-exercises` lint pass) — `[ ]` items the agent ticks before declaring done.
- **No numeric scoring rubric** anywhere. `design-an-interface` (deprecated) compares designs on prose criteria (simplicity / depth / efficiency) — not a score. Recommendation strength in `improve-codebase-architecture` is a 3-value badge (`Strong`/`Worth exploring`/`Speculative`), not a number.
- **Triage disclaimer** (`triage`): every posted comment must start with `> *This was generated by AI during triage.*` — a provenance stamp, not a score.

---

## 7. Anti-patterns / negation handling

- **Yes, anti-patterns are used** — but framed positively where possible. `design-an-interface` has explicit `## Anti-Patterns`. `code-review` inlines a "smell baseline" (Fowler smells) as _labelled heuristics_, each "smell → how to fix". `tdd` lists anti-patterns (Implementation-coupled / Tautological / Horizontal slicing) each with "the tell".
- **Negation as last resort** (GLOSSARY `Negation`): keep prohibitions only as hard guardrails you cannot phrase positively; always pair with the positive target. Example `prototype` rule 4 "Skip the polish. No tests, no error handling…" — the positive frame ("the point is to learn something fast") carries it.
- **"Rejected framings"** section (`codebase-design`) names what NOT to call things and why (e.g. reject "boundary" — overloaded with DDD's bounded context). Glossary entries carry `_Avoid_:` lists naming the synonyms to drop. This is the sanctioned form of negation: name the rejected term + the reason, so the agent knows why.

---

## 8. Skill independence (how the set stays composable)

Per `.agents/invocation.md` L27-33 + README L172 ("Reference" section):

- **User-invoked may invoke model-invoked; never another user-invoked.** A user-invoked skill has no `description`, so nothing but the human can reach it.
- **Dependencies are `/skill` prose**, never `../other-skill/FILE.md` cross-references. Keeps each skill folder self-contained; refactoring one skill's files never breaks another's link.
- **Shared reference lives in the skill that owns it.** `grilling` owns the relentless-interview loop (invoked by grill-me, grill-with-docs, loop-me, batch-grill-me, wayfinder, triage, improve-codebase-architecture, to-questionnaire). `codebase-design` owns the deep-module vocabulary (invoked by tdd, improve-codebase-architecture, setup-ts-deep-modules). `domain-modeling` owns the active glossary discipline (invoked by grill-with-docs, triage, improve-codebase-architecture, wayfinder).
- **Thin orchestrators compose primitives.** `grill-with-docs` = `/grilling` + `/domain-modeling`. `implement` = `/tdd` + `/code-review`. `grill-me` = `/grilling`. Each primitive is independently reusable; each orchestrator is independently swap-able.
- **Router pattern** (`ask-matt`) cures cognitive load when user-invoked skills multiply — one user-invoked skill names the others and when to reach for each. README L172: "A user-invoked skill may invoke model-invoked skills, but never another user-invoked one."
- **Two-load budget** (GLOSSARY `Cognitive Load`/`Context Load`): every model-invoked skill spends context load (its description, always loaded); every user-invoked skill spends cognitive load (the human must remember it). Splitting earns its cut only when it spends less load than it adds.

---

## 9. Copy-me skeleton (minimal new skill)

```markdown
---
name: <kebab-name>
description: <ONE job sentence>. Use when the user <trigger branches, one per branch>.
# disable-model-invocation: true   # uncomment iff user-invoked
# argument-hint: "<hint>"          # uncomment iff takes an arg
---

# <Title>

<One-sentence job statement — the defining constraint that makes this skill
behave differently from the obvious default.>

## Process

### 1. <Step>
<action>

**Done when:** <checkable + exhaustive criterion, or `[ ]` checklist>.

### 2. <Step>
...

<template-name>-template (if the skill emits a fixed-shape artefact):

<template>
## <Fixed section>
...
</template>

## Failure modes   (optional — only if the skill has characteristic misfires)

- **<Named failure>** — <the tell>. → <the fix>.
```

Plus `agents/openai.yaml`:
```yaml
interface:
  display_name: "<Display>"
  short_description: "<one-liner>"
# policy:                      # user-invoked only
#   allow_implicit_invocation: false
```

This skeleton satisfies: fixed dir shape, invocation axis in frontmatter, information-hierarchy ladder (steps → completion criteria → disclosed template), positive framing, `/skill`-prose-only deps, two-load budgeting.
