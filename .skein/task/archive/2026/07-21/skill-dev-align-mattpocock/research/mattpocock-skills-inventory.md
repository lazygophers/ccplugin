# Matt Pocock `skills` repo — full skill inventory

Repo: https://github.com/mattpocock/skills (branch `main`). Tree via `gh api repos/mattpocock/skills/git/trees/main?recursive=1` — 269 paths, **41 `SKILL.md`** files. Structure: `skills/<bucket>/<skill>/SKILL.md` + optional siblings. Buckets: `engineering` (promoted), `productivity` (promoted), `misc`, `personal`, `in-progress`, `deprecated`. Every skill dir also carries `agents/openai.yaml` (Codex UI metadata + invocation policy).

Bucket layout & promotion rules: source `CLAUDE.md` L216-240 (identical in `AGENTS.md`). Promoted = `engineering/`+`productivity/`; only promoted get a top-level README entry + `.claude-plugin/plugin.json` skills array + `docs/<bucket>/<skill>.md` page. Invocation spec: `.agents/invocation.md`.

Legend per skill:
- **FM** = frontmatter `name` + `description` (+ optional `disable-model-invocation`, `argument-hint`).
- **Refs** = sibling `.md` reference files (context pointers / disclosed reference).
- **Templates** = report/output templates (inline or sibling file).
- **Deps** = `/skill`-style prose invocations of other skills (per `.agents/invocation.md` L29: dependencies expressed as `/skill` prose, never cross-folder file links).
- **Report template?** = whether skill ships a structured output template.
- **Standalone** = no prose dependency on another skill in this repo.

---

## engineering/ (promoted; 21 skills)

### ask-matt
- Path: `skills/engineering/ask-matt/SKILL.md`
- FM: `name: ask-matt`; `description: Ask which skill or flow fits your situation. A router over the skills in this repo.`; `disable-model-invocation: true`
- Refs: none
- Templates: none
- Deps: references ~all user-invoked skills by `/name` prose (grill-with-docs, grill-me, handoff, prototype, to-spec, to-tickets, implement, tdd, code-review, triage, diagnosing-bugs, wayfinder, improve-codebase-architecture, codebase-design, domain-modeling, research, teach, setup-matt-pocock-skills, compact)
- Report template: no
- Standalone: **router** — its job is to route to others; user-invoked, can only hint at other user-invoked skills

### code-review
- Path: `skills/engineering/code-review/SKILL.md`
- FM: `name: code-review`; `description:` long, two-axis (Standards + Spec), "Use when the user wants to review a branch, a PR, ... or asks to 'review since X'." (model-invoked)
- Refs: none (smell baseline inlined)
- Templates: sub-agent prompt briefs inline (≤400 words each); final report structure (`## Standards` / `## Spec` headings)
- Deps: `/setup-matt-pocock-skills` (for issue tracker); uses `Agent` tool with `general-purpose` subagent
- Report template: yes (inline — two sub-agent report briefs + aggregation format)

### codebase-design
- Path: `skills/engineering/codebase-design/SKILL.md`
- FM: `name: codebase-design`; `description:` "Shared vocabulary for designing deep modules. Use when the user wants to design or improve a module's interface, find deepening opportunities, decide where a seam goes, ... or when another skill needs the deep-module vocabulary." (model-invoked)
- Refs: `DEEPENING.md`, `DESIGN-IT-TWICE.md`
- Templates: ASCII deep/shallow diagrams; glossary inline
- Deps: invoked BY other skills (tdd, improve-codebase-architecture, setup-ts-deep-modules). DESIGN-IT-TWICE.md spawns parallel sub-agents.
- Report template: no (pure reference + vocabulary)

### diagnosing-bugs
- Path: `skills/engineering/diagnosing-bugs/SKILL.md`
- FM: `name: diagnosing-bugs`; `description:` "Diagnosis loop for hard bugs and performance regressions. Use when the user says 'diagnose'/'debug this', or reports something broken/throwing/failing/slow." (model-invoked)
- Refs: `scripts/hitl-loop.template.sh` (HITL feedback-loop template)
- Templates: phase completion criteria checklists (inline `[ ]`); hypothesis falsifiability format
- Deps: hands off to `/improve-codebase-architecture` in Phase 6
- Report template: yes (6-phase loop with checklists)

### domain-modeling
- Path: `skills/engineering/domain-modeling/SKILL.md`
- FM: `name: domain-modeling`; `description:` "Build and sharpen a project's domain model. Use when ... or when another skill needs to maintain the domain model." (model-invoked)
- Refs: `CONTEXT-FORMAT.md`, `ADR-FORMAT.md`
- Templates: file-structure tree; ADR-offer triad (hard-to-reverse / surprising / real trade-off)
- Deps: invoked BY grill-with-docs, triage, improve-codebase-architecture, wayfinder
- Report template: no

### grill-with-docs
- Path: `skills/engineering/grill-with-docs/SKILL.md`
- FM: `name: grill-with-docs`; `description: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.`; `disable-model-invocation: true`
- Refs: none (thin skill)
- Body: 1 line — "Run a `/grilling` session, using the `/domain-modeling` skill."
- Deps: `/grilling`, `/domain-modeling`
- Report template: no
- Standalone: no — orchestrator over grilling + domain-modeling

### implement
- Path: `skills/engineering/implement/SKILL.md`
- FM: `name: implement`; `description: "Implement a piece of work based on a spec or set of tickets."`; `disable-model-invocation: true`
- Refs: none (very thin — 5 lines)
- Deps: `/tdd`, `/code-review`
- Report template: no
- Standalone: no — orchestrator

### improve-codebase-architecture
- Path: `skills/engineering/improve-codebase-architecture/SKILL.md`
- FM: `name: improve-codebase-architecture`; `description: Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick.`; `disable-model-invocation: true`
- Refs: `HTML-REPORT.md` (full HTML scaffold + Tailwind/Mermaid patterns + tone/vocabulary)
- Templates: HTML report card structure; recommendation-strength badges (`Strong`/`Worth exploring`/`Speculative`)
- Deps: `/codebase-design` (vocabulary), `/grilling`, `/domain-modeling`; uses `Agent` tool `subagent_type=Explore`
- Report template: **yes** — sibling `HTML-REPORT.md` is a copy-me scaffold

### prototype
- Path: `skills/engineering/prototype/SKILL.md`
- FM: `name: prototype`; `description: Build a throwaway prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels right, or explore what a UI should look like.` (model-invoked)
- Refs: `LOGIC.md`, `UI.md` (branch-disclosed reference)
- Templates: branch-selection logic
- Deps: none prose; branch-disclosed LOGIC/UI files
- Report template: no

### research
- Path: `skills/engineering/research/SKILL.md`
- FM: `name: research`; `description:` "Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent." (model-invoked)
- Refs: none
- Templates: output is "a single Markdown file, citing each claim's source"
- Deps: spawns a **background agent** to do the reading
- Report template: yes (single cited Markdown file)

### resolving-merge-conflicts
- Path: `skills/engineering/resolving-merge-conflicts/SKILL.md`
- FM: `name: resolving-merge-conflicts`; `description: "Use when you need to resolve an in-progress git merge/rebase conflict."` (model-invoked)
- Refs: none
- Templates: 5-step procedure
- Deps: none
- Report template: no
- Standalone: **yes** (independent)

### setup-matt-pocock-skills
- Path: `skills/engineering/setup-matt-pocock-skills/SKILL.md`
- FM: `name: setup-matt-pocock-skills`; `description: Configure this repo for the engineering skills ... Run once before first use of the other engineering skills.`; `disable-model-invocation: true`
- Refs (seed templates): `domain.md`, `issue-tracker-github.md`, `issue-tracker-gitlab.md`, `issue-tracker-local.md`, `triage-labels.md`
- Templates: `## Agent skills` block template; per-section A/B/C Q&A flow
- Deps: none (precondition for others)
- Report template: yes (inline `## Agent skills` block + seed file templates)

### tdd
- Path: `skills/engineering/tdd/SKILL.md`
- FM: `name: tdd`; `description: Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions 'red-green-refactor', or wants integration tests.` (model-invoked)
- Refs: `tests.md` (examples), `mocking.md` (mocking guidelines)
- Templates: anti-patterns definitions; rules of the loop
- Deps: invoked BY implement; reads `CONTEXT.md` for vocab
- Report template: no

### to-spec
- Path: `skills/engineering/to-spec/SKILL.md`
- FM: `name: to-spec`; `description: Turn the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis of what you've already discussed.`; `disable-model-invocation: true`
- Refs: none
- Templates: **inline `<spec-template>`** (Problem Statement / Solution / User Stories / Implementation Decisions / Testing Decisions / Out of Scope / Further Notes)
- Deps: `/setup-matt-pocock-skills` (issue tracker)
- Report template: yes (inline spec template, published to tracker)

### to-tickets
- Path: `skills/engineering/to-tickets/SKILL.md`
- FM: `name: to-tickets`; `description:` "Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges ..."; `disable-model-invocation: true`
- Refs: none
- Templates: **inline `<local-ticket-template>` + `<issue-template>`**; vertical-slice-rules block
- Deps: `/setup-matt-pocock-skills`, hands off to `/implement`
- Report template: yes (two inline templates — local file + real tracker)

### triage
- Path: `skills/engineering/triage/SKILL.md`
- FM: `name: triage`; `description: Move issues and external PRs through a state machine of triage roles — categorise, verify, grill if needed, and write agent-ready briefs.`; `disable-model-invocation: true`
- Refs: `AGENT-BRIEF.md`, `OUT-OF-SCOPE.md`
- Templates: needs-info template (inline); AI disclaimer prefix `> *This was generated by AI during triage.*`
- Deps: `/setup-matt-pocock-skills`, `/grilling`, `/domain-modeling`
- Report template: yes (needs-info template + agent-brief ref)

### wayfinder
- Path: `skills/engineering/wayfinder/SKILL.md`
- FM: `name: wayfinder`; `description: Plan a huge chunk of work — more than one agent session can hold — as a shared map of decision tickets ...`; `disable-model-invocation: true`
- Refs: none (all inline — longest SKILL.md in repo)
- Templates: map body template (Destination / Notes / Decisions so far / Not yet specified / Out of scope); ticket body template; ticket-type definitions
- Deps: `/setup-matt-pocock-skills`, `/grilling`, `/domain-modeling`, `/research` (subagent), `/prototype`
- Report template: yes (map + ticket templates)

---

## productivity/ (promoted; 5 skills)

### grill-me
- Path: `skills/productivity/grill-me/SKILL.md`
- FM: `name: grill-me`; `description: A relentless interview to sharpen a plan or design.`; `disable-model-invocation: true`
- Refs: none
- Body: 1 line — "Run a `/grilling` session."
- Deps: `/grilling`
- Standalone: no — thin wrapper

### grilling
- Path: `skills/productivity/grilling/SKILL.md`
- FM: `name: grilling`; `description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.` (model-invoked)
- Refs: none
- Templates: none (the reusable loop primitive)
- Deps: none — **the** primitive invoked by grill-me / grill-with-docs / loop-me / batch-grill-me / wayfinder / improve-codebase-architecture / triage / to-questionnaire
- Report template: no

### handoff
- Path: `skills/productivity/handoff/SKILL.md`
- FM: `name: handoff`; `description: Compact the current conversation into a handoff document for another agent to pick up.`; `argument-hint: "What will the next session be used for?"`; `disable-model-invocation: true`
- Refs: none
- Templates: handoff-doc structure ("suggested skills" section)
- Deps: none
- Report template: yes (handoff doc to OS temp dir)

### teach
- Path: `skills/productivity/teach/SKILL.md`
- FM: `name: teach`; `description: Teach the user a new skill or concept, within this workspace.`; `argument-hint: "What would you like to learn about?"`; `disable-model-invocation: true`
- Refs: `GLOSSARY-FORMAT.md`, `LEARNING-RECORD-FORMAT.md`, `MISSION-FORMAT.md`, `RESOURCES-FORMAT.md` (4 format refs)
- Templates: workspace file layout (`MISSION.md`, `./reference/*.html`, `RESOURCES.md`, `./learning-records/*.md`, `./lessons/*.html`, `./assets/*`, `NOTES.md`); lesson philosophy (fluency vs storage strength)
- Deps: none (self-contained)
- Report template: yes (lesson = single HTML file; 4 format specs)

### writing-great-skills
- Path: `skills/productivity/writing-great-skills/SKILL.md`
- FM: `name: writing-great-skills`; `description: Reference for writing and editing skills well — the vocabulary and principles that make a skill predictable.`; `disable-model-invocation: true`
- Refs: `GLOSSARY.md` (the full term dictionary — disclosed reference)
- Templates: information-hierarchy ladder; failure-mode catalogue
- Deps: none — **the meta-skill / authoring reference**
- Report template: no (it IS the reference)

---

## misc/ (4 skills, not promoted)

### git-guardrails-claude-code
- Path: `skills/misc/git-guardrails-claude-code/SKILL.md`
- FM: `name: git-guardrails-claude-code`; `description:` "Set up Claude Code hooks to block dangerous git commands ... Use when user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code." (model-invoked)
- Refs: `scripts/block-dangerous-git.sh`
- Templates: settings.json PreToolUse hook snippet (project + global)
- Deps: none
- Report template: yes (hook JSON config)

### migrate-to-shoehorn
- Path: `skills/misc/migrate-to-shoehorn/SKILL.md`
- FM: `name: migrate-to-shoehorn`; `description: Migrate test files from 'as' type assertions to @total-typescript/shoehorn. Use when user mentions shoehorn, wants to replace 'as' in tests, or needs partial test data.` (model-invoked)
- Refs: none
- Templates: before/after TS code patterns; function-use table; workflow checklist
- Deps: none
- Standalone: yes

### scaffold-exercises
- Path: `skills/misc/scaffold-exercises/SKILL.md`
- FM: `name: scaffold-exercises`; `description: Create exercise directory structures ... Use when user wants to scaffold exercises, create exercise stubs, or set up a new course section.` (model-invoked)
- Refs: none
- Templates: directory-naming; readme stub; lint-rules summary
- Deps: `pnpm ai-hero-cli internal lint` (repo-specific tool)
- Report template: yes (stubbed readme + dir layout)

### setup-pre-commit
- Path: `skills/misc/setup-pre-commit/SKILL.md`
- FM: `name: setup-pre-commit`; `description:` "Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests ... Use when user wants to add pre-commit hooks, set up Husky, configure lint-staged ..." (model-invoked)
- Refs: none
- Templates: `.husky/pre-commit`, `.lintstagedrc`, `.prettierrc` configs; verify checklist
- Deps: none (detects package manager)
- Report template: yes (config files + commit message)

---

## personal/ (2 skills, not promoted)

### edit-article
- Path: `skills/personal/edit-article/SKILL.md`
- FM: `name: edit-article`; `description: Edit and improve articles by restructuring sections ...`; `disable-model-invocation: true`
- Refs: none
- Templates: DAG-of-info sectioning rule; 240-char/paragraph constraint
- Deps: none
- Standalone: yes

### obsidian-vault
- Path: `skills/personal/obsidian-vault/SKILL.md`
- FM: `name: obsidian-vault`; `description: Search, create, and manage notes in the Obsidian vault ...` (model-invoked)
- Refs: none
- Templates: bash find/grep snippets; wikilink conventions
- Deps: none — hardcodes vault path `/mnt/d/Obsidian Vault/AI Research/`
- Standalone: yes (Matt-specific)

---

## in-progress/ (10 skills, drafts)

### batch-grill-me
- FM: `name: batch-grill-me`; `description: A relentless interview that asks every frontier question at once, round by round.`; `disable-model-invocation: true`
- Refs: none; body uses design-tree + frontier vocabulary
- Deps: `/grilling`-style (self-described grilling variant); dispatches sub-agents for facts
- Standalone: mostly (variant of grilling)

### claude-handoff
- FM: `name: claude-handoff`; `description: Hand the current conversation off to a fresh background agent that picks up the work immediately.`; `argument-hint`; `disable-model-invocation: true`
- Refs: none; uses `claude --bg --name`
- Deps: none
- Standalone: yes (variant of handoff launching bg agent)

### loop-me
- FM: `name: loop-me`; `description: Grill me about specs for the workflows I want to build, within this workspace.`; `argument-hint`; `disable-model-invocation: true`
- Refs: none; workspace `workflows/*.md` + `NOTES.md`
- Deps: `/grilling`
- Standalone: no

### setup-ts-deep-modules
- FM: `name: setup-ts-deep-modules`; `description: Wire dependency-cruiser into a TypeScript repo so each package is a deep module ...`; `disable-model-invocation: true`
- Refs: `dependency-cruiser.config.cjs` (copy-me config)
- Templates: 4 rules; example package scaffold; README template
- Deps: `/codebase-design` (vocabulary)
- Standalone: no

### to-questionnaire
- FM: `name: to-questionnaire`; `description: Turn a decision you can't fully answer into a questionnaire for someone else to fill in.`; `disable-model-invocation: true`
- Refs: none
- Templates: **inline `<questionnaire-template>`** + `<question-example>`
- Deps: grilling-style interview about the send
- Standalone: yes

### wizard
- FM: `name: wizard`; `description: Generate an interactive bash wizard ...`; `disable-model-invocation: true`
- Refs: `template.sh` (the bash wizard library — copy-me)
- Templates: stage-authoring helpers (`stage`, `say`/`step`, `open_url`, `ask`/`ask_secret`, `write_env`, `set_secret`/`set_var`, `pause`/`confirm`)
- Deps: none
- Standalone: yes

### writing-beats
- FM: `name: writing-beats`; `description: Writing, exploit — assemble raw material into a journey of beats, grounding each term before a beat leans on it.`; `disable-model-invocation: true`
- Refs: none; uses `<what-to-do>` / `<supporting-info>` custom-tag structure
- Deps: none (writing-exploit phase)
- Standalone: yes (paired with writing-fragments/writing-shape)

### writing-fragments
- FM: `name: writing-fragments`; `description: Writing, explore — mine raw fragments, no structure yet.`; `disable-model-invocation: true`
- Refs: none; file-format template
- Deps: none
- Standalone: yes

### writing-shape
- FM: `name: writing-shape`; `description: Writing, exploit — shape raw material into an article, paragraph by paragraph.`; `disable-model-invocation: true`
- Refs: none; loop + grounding + format-argument templates
- Deps: none
- Standalone: yes

---

## deprecated/ (4 skills)

### design-an-interface
- FM: `name: design-an-interface`; `description: Generate multiple radically different interface designs for a module using parallel sub-agents. Use when ... mentions 'design it twice'.` (model-invoked)
- Refs: none
- Templates: sub-agent prompt template; evaluation criteria; anti-patterns
- Deps: uses Task/Agent tool parallel sub-agents
- **Note:** superseded by `codebase-design/DESIGN-IT-TWICE.md` (design-it-twice absorbed into codebase-design)

### qa
- FM: `name: qa`; `description:` long, "Use when user wants to report bugs, do QA, file issues conversationally, or mentions 'QA session'."
- Refs: none
- Templates: single-issue template + breakdown sub-issue template (inline fenced code)
- Deps: uses `Agent(subagent_type=Explore)`; reads `UBIQUITOUS_LANGUAGE.md`
- Standalone: yes (functionality folded into triage)

### request-refactor-plan
- FM: `name: request-refactor-plan`; `description: Create a detailed refactor plan with tiny commits via user interview ...`
- Refs: none
- Templates: inline `<refactor-plan-template>` (Problem/Solution/Commits/Decision Doc/Testing/Out of Scope)
- Deps: none
- Standalone: yes (superseded by to-spec/to-tickets flow)

### ubiquitous-language
- FM: `name: ubiquitous-language`; `description:` long; `disable-model-invocation: true`
- Refs: none
- Templates: `UBIQUITOUS_LANGUAGE.md` output format (table + relationships + dialogue + flagged ambiguities)
- Deps: none
- Standalone: yes (superseded by domain-modeling/CONTEXT.md)

---

## Cross-cutting observations

- **Every** skill dir has `agents/openai.yaml` (Codex UI: `interface.display_name` + `interface.short_description`; user-invoked adds `policy.allow_implicit_invocation: false`).
- **No skill uses cross-folder file links to other skills' internals.** Dependencies are `/skill` prose invocations (`.agents/invocation.md` L29). Shared reference lives inside the skill that owns it (e.g. `codebase-design` owns the deep-module vocab; `grilling` owns the interview loop).
- **Report templates** ship as either inline `<...-template>` blocks (to-spec, to-tickets, request-refactor-plan, to-questionnaire, qa, ubiquitous-language) or sibling copy-me files (`improve-codebase-architecture/HTML-REPORT.md`, `setup-ts-deep-modules/dependency-cruiser.config.cjs`, `wizard/template.sh`, `git-guardrails-claude-code/scripts/block-dangerous-git.sh`, `diagnosing-bugs/scripts/hitl-loop.template.sh`, `setup-matt-pocock-skills/*.md`).
- **Thin orchestrator skills** (grill-with-docs, implement, grill-me) are 1-5 line wrappers that compose model-invoked primitives.
- **Standalone (zero prose deps)**: resolving-merge-conflicts, grilling, handoff, teach, writing-great-skills, edit-article, obsidian-vault, migrate-to-shoehorn, batch-grill-me, claude-handoff, to-questionnaire, wizard, writing-beats/fragments/shape, and all 4 deprecated.
