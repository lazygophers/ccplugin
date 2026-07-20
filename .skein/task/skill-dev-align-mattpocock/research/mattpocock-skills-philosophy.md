# Matt Pocock `skills` — design philosophy & principles (with original-text citations)

Source documents (all under https://github.com/mattpocock/skills/tree/main/):
- `README.md` — the "Why These Skills Exist" manifesto
- `skills/productivity/writing-great-skills/SKILL.md` — the authoring theory
- `skills/productivity/writing-great-skills/GLOSSARY.md` — the term dictionary
- `docs/productivity/writing-great-skills.md` — human-facing orientation
- `CLAUDE.md` / `AGENTS.md` — repo operating rules
- `.agents/invocation.md` — invocation axis
- `CONTEXT.md` — the repo's own ubiquitous-language glossary (dogfooded)

Blockquotes are verbatim from the cited file. Line numbers are 1-indexed into the fetched raw file.

---

## 1. The root virtue: Predictability, not output-determinism

A skill exists to make a stochastic system behave the same **way** every run — same process, not same tokens.

> "A skill exists to wrangle determinism out of a stochastic system. **Predictability** — the agent taking the same _process_ every run, not producing the same output — is the root virtue; every lever below serves it."
> — `skills/productivity/writing-great-skills/SKILL.md` L2295

> "The degree to which a skill makes the agent behave the same _way_ on every run — the same process, not the same output (a brainstorming skill should _predictably_ diverge; its tokens vary, its behaviour doesn't). The root virtue every other term serves — cost and maintainability are symptoms of it, not rivals."
> — `GLOSSARY.md` `## Predictability` L357

> "A skill's job is to wrangle determinism out of a stochastic system, so the goal is not the same _output_ every run but the same _process_. **Predictability** is the root virtue, and every design choice is judged against it — not against how clever, complete, or exhaustive the skill reads."
> — `docs/productivity/writing-great-skills.md` L317

---

## 2. Why the skills exist — four failure modes of AI coding

`README.md` "Why These Skills Exist" (L70-168) frames the whole repo as fixes for four failure modes. Each is anchored to a quoted authority.

### #1 Misalignment — "The Agent Didn't Do What I Want"
> "The most common failure mode in software development is misalignment... This is just the same in the AI age. There is a communication gap between you and the agent. The fix for this is a **grilling session** - getting the agent to ask you detailed questions about what you're building."
> — `README.md` L80-82

Anchor quote: > "No-one knows exactly what they want" — Thomas & Hunt, _The Pragmatic Programmer_ (`README.md` L77).

### #2 Verbosity / jargon — "The Agent Is Way Too Verbose"
> "Agents are usually dropped into a project and asked to figure out the jargon as they go. So they use 20 words where 1 will do."
> — `README.md` L99

Fix: a **shared language** (`CONTEXT.md`). "It might be the single coolest technique in this repo." (`README.md` L119)
Anchor: Eric Evans, _DDD_ (`README.md` L93) — "With a ubiquitous language, conversations among developers and expressions of the code are all derived from the same domain model."

> [!TIP] in README (L121-127): a shared language also (a) names variables/functions/files consistently, (b) makes the codebase easier for the agent to navigate, (c) **spends fewer tokens on thinking** because it has access to a more concise language.

### #3 No feedback — "The Code Doesn't Work"
> "Without feedback on how the code it produces actually runs, the agent will be flying blind."
> — `README.md` L136

Fix: types + browser + automated tests, with a **red-green-refactor** loop (the `/tdd` skill) and `/diagnosing-bugs` for the hard ones.
Anchor: > "Always take small, deliberate steps. The rate of feedback is your speed limit." — Thomas & Hunt (`README.md` L130).

### #4 Ball of mud — "We Built A Ball Of Mud"
> "Because agents can radically speed up coding, they also accelerate software entropy. Codebases get more complex at an unprecedented rate."
> — `README.md` L156

Fix: **care about the design of the code** — deep modules. `/to-spec` quizzes about modules; `/improve-codebase-architecture` rescues mud (recommend running every few days, L164).
Anchors: Kent Beck _XP_ ("Invest in the design of the system _every day_.", L149) and John Ousterhout _A Philosophy of Software Design_ ("The best modules are deep.", L153).

### Summary (README L166-168)
> "Software engineering fundamentals matter more than ever. These skills are my best effort at condensing these fundamentals into repeatable practices."

---

## 3. Small, adaptable, composable — the positioning vs. GSD/BMAD/Spec-Kit

> "Approaches like GSD, BMAD, and Spec-Kit try to help by owning the process. But while doing so, they take away your control and make bugs in the process hard to resolve."
> "These skills are designed to be **small, easy to adapt, and composable**. They work with any model. They're based on decades of engineering experience. Hack around with them. Make them your own."
> — `README.md` L18-20

Implication for skill authoring: keep each skill small and swappable; the system is a composition of independent primitives, not a monolithic process owner.

---

## 4. The two loads — the core economic model

Every design decision trades **cognitive load** against **context load**. This is the lens the whole authoring reference turns on.

> "Every skill spends one or the other:
> - A **model-invoked** skill keeps a description in the window every turn, so it costs **context load** but fires on its own.
> - A **user-invoked** skill strips that description; it costs zero context load, but now _you_ are the index that has to remember it exists — that's **cognitive load**."
> — `docs/productivity/writing-great-skills.md` L328-330

> "Cognitive load is the pressure the whole system is built to manage: when user-invoked skills multiply past what you can hold in your head, the cure is a **router skill** that names the others and when to reach for each."
> — `docs/productivity/writing-great-skills.md` L332

GLOSSARY refines cognitive load as **not a cost to minimise**:
> "Not a cost to minimise: it is the price of human agency, the reason some skills stay user-invoked. Spend it where human judgement matters; remove it where it does not."
> — `GLOSSARY.md` `### Cognitive Load` L398

Test for model-invocation (`.agents/invocation.md` L19): _"could the model usefully reach for this autonomously?"_ — reuse is the reason to extract a skill, not the test.

---

## 5. The Information Hierarchy — what sits where, and why

> "A skill is built from two content types — **steps** and **reference** — that mix freely... The core decision is which to use and where each sits on the **information hierarchy**, a ladder ranked by how immediately the agent needs the material."
> — `writing-great-skills/SKILL.md` L2320

The three rungs: in-skill step → in-skill reference → disclosed/external reference. **Progressive disclosure** is the move down the ladder so the top stays legible.

> "Push too little down and the top bloats; push too much and you hide material the agent actually needs. That tension is the whole decision."
> — `writing-great-skills/SKILL.md` L2328

Co-location governs the within-file arrangement:
> "Keep a concept's definition, rules, and caveats under one heading rather than scattered, so reading one part brings its neighbours with it."
> — `writing-great-skills/SKILL.md` L2332

---

## 6. Leading words — the cheapest predictability lever

> "A **leading word** is a compact concept already living in the model's pretraining that the agent thinks with while running the skill (e.g. _lesson_, _fog of war_, _tracer bullets_). Repeated throughout the text..., it accumulates a distributed definition and anchors a whole region of behaviour in the fewest tokens, by recruiting priors the model already holds."
> — `writing-great-skills/SKILL.md` L2351

It pays off twice — execution in the body, invocation in the description:
> "In the body it anchors _execution_... In the description it anchors _invocation_: when the same word lives in your prompts, docs, and code, the agent links that shared language to the skill and fires it more reliably."
> — `writing-great-skills/SKILL.md` L2353

Authoring mandate:
> "Assume every skill is carrying restatements that leading words retire — go find them."
> — `writing-great-skills/SKILL.md` L2360

GLOSSARY note on coined words: > "Coining your own works if you define it clearly, but a made-up word recruits no priors — you pay in definition tokens what a pretrained word gives free. Reach for an existing word first." (`GLOSSARY.md` `### Leading Word` L478)

---

## 7. Pruning discipline — against sediment, sprawl, duplication, no-ops

> "Keep each meaning in a **single source of truth**: one authoritative place, so changing the behaviour is a one-place edit."
> — `writing-great-skills/SKILL.md` L2343

> "Then hunt **no-ops** sentence by sentence, not just line by line: run the no-op test on each sentence in isolation, and when one fails, delete the whole sentence rather than trim words from it. Be aggressive — most prose that fails should go, not be rewritten."
> — `writing-great-skills/SKILL.md` L2347

The no-op test (`GLOSSARY.md` `### No-Op` L544): _"does a line change behaviour versus the default?"_ — model-relative, settled by running the skill, not by debate.

Failure modes catalogue (`writing-great-skills/SKILL.md` L2362-2371): **premature completion**, **duplication**, **sediment** ("the default fate of any skill without a pruning discipline"), **sprawl**, **no-op**, **negation**.

---

## 8. Negation — prompt the positive

> "**Negation** — steering by prohibition backfires: _don't think of an elephant_ names the elephant and makes it more available, not less. Prompt the **positive** — state the target behaviour so the banned one is never spoken; keep a prohibition only as a hard guardrail you can't phrase positively, and even then pair it with what to do instead."
> — `writing-great-skills/SKILL.md` L2371

GLOSSARY `### Negation` L510: the prohibition's leading word is the _elephant_; the cure is to describe the target behaviour so the banned one is never spoken.

---

## 9. Completion criteria — checkable + exhaustive

> "Each step ends on a **completion criterion**, the condition that tells the agent the work is done. Make it _checkable_ (can the agent tell done from not-done?) and, where it matters, _exhaustive_ ('every modified model accounted for', not 'produce a change list') — a vague criterion invites **premature completion**."
> — `writing-great-skills/SKILL.md` L2322

GLOSSARY `### Completion Criterion` L486: clarity resists premature completion; demand sets legwork. The strongest criteria are both checkable and exhaustive.

---

## 10. When to split — by invocation or by sequence

> "**Granularity** is how finely you divide skills, and each cut spends one of the two loads, so split only when the cut earns it."
> — `writing-great-skills/SKILL.md` L2336

Two cuts:
- **By invocation** — split off a model-invoked skill when you have a distinct leading word that should trigger it on its own, or another skill must reach it (`L2338`).
- **By sequence** — split a run of steps when the steps still ahead tempt the agent to rush the current one (premature completion) (`L2339`).

---

## 11. Independence via `/skill`-prose dependencies

> "Dependencies are expressed as **`/skill`-style prose invocation** ('Run the `/grilling` skill'), not deep `../other-skill/FILE.md` cross-references. Shared reference docs live inside the skill that owns them; other skills reach that material by invoking the skill, not by linking across folders."
> — `.agents/invocation.md` L29

> "A user-invoked skill may invoke model-invoked skills, but never another user-invoked one."
> — `README.md` L172 (and `.agents/invocation.md` L21)

---

## 12. The dogfooded glossary

The repo itself has a `CONTEXT.md` practicing what `/domain-modeling` preaches — e.g. it records the resolution to stop using "backlog":
> "'backlog' was previously used to mean both the _tool_ hosting issues and the _body of work_ inside it — resolved: the tool is the **Issue tracker**; 'backlog' is no longer used as a domain term."
> — `CONTEXT.md` L297

This is the same format `domain-modeling` writes into project `CONTEXT.md`s — the repo is its own first user.

---

## 13. Scope discipline — YAGNI and out-of-scope as first-class

`improve-codebase-architecture` opens the explore phase with:
> "**Scope before you scan — YAGNI.** Deepening a module pays off by making future changes to it easier, so put extra weight on the parts of the codebase that have recently changed. Decide _where_ to look before you look."
> — `skills/engineering/improve-codebase-architecture/SKILL.md` L375

`wayfinder` makes "out of scope" a section of the map, distinct from "fog of war":
> "The destination fixes the scope, so work beyond it is **out of scope** — it isn't fog, and it doesn't belong in **Not yet specified**."
> — `skills/engineering/wayfinder/SKILL.md` L1068

`triage` writes rejected requests to a `.out-of-scope/` knowledge base so they don't get re-suggested (`triage` SKILL.md L942).

The repo also keeps a top-level `.out-of-scope/` dir for features consciously ruled out (e.g. `mainstream-issue-trackers-only.md`, `question-limits.md`, `setup-skill-verify-mode.md`) — see full tree.

---

## 14. Throwaway-from-day-one (prototypes, wizards)

> "A prototype is **throwaway code that answers a question**. The question decides the shape."
> — `skills/engineering/prototype/SKILL.md` L437

> "**Throwaway from day one, and clearly marked as such.**"
> — `prototype` rule 1, L449

`wizard` similarly: > "A wizard is ephemeral by default — built for one run, saved to a scratch or `scripts/` path, deleted when the job's done." (`skills/in-progress/wizard/SKILL.md` L1344)

Principle: produce the cheapest artefact that answers the question; keep the answer, delete the code.

---

## 15. Docs pages are a distributed router, not skill copies

> "Most of these skills are **user-invoked**: the agent will never fire them for you, so _you_ are the index that has to remember they exist... That memory is **cognitive load**. The job of a docs page is to relieve it — to orient one reader around one skill... The pages are collectively a distributed router; each is a node."
> — `.agents/writing-docs.md` L40

> "Explain the **why**, not the process. The page orients and situates the skill; it never reproduces the `SKILL.md` steps or template dumps."
> — `.agents/writing-docs.md` L103

The non-negotiable for a docs page:
> "The single non-negotiable: **surface the skill's leading word / defining idea** — `tight` feedback loop, `deep module`, throwaway-code-answers-a-question, red-green."
> — `.agents/writing-docs.md` L85

---

## 16. Repo governance rules (from `CLAUDE.md`)

- Promoted buckets (`engineering/`, `productivity/`) only: must appear in top-level `README.md` AND `.claude-plugin/plugin.json` skills array; get a `docs/<bucket>/<skill>.md` page. (`CLAUDE.md` L226)
- Each `SKILL.md` is either user-invoked (`disable-model-invocation: true` + `agents/openai.yaml` `policy.allow_implicit_invocation: false`) or model-invoked — no third state. (`CLAUDE.md` L236)
- `ask-matt` is the router over every user-reachable skill; it must be re-synced whenever a user-reachable skill is added/renamed/removed or its flow-fit changes. (`CLAUDE.md` L238)
- Each bucket has a `README.md`; promoted buckets group by User-invoked vs Model-invoked, non-promoted use a flat list. (`CLAUDE.md` L232)

---

## TL;DR — the philosophy in five lines

1. **Predictability** (same process, not same output) is the root virtue; cost and maintainability are symptoms. (`writing-great-skills/SKILL.md` L2295)
2. Every skill spends **context load** (model-invoked) or **cognitive load** (user-invoked); split only when a cut earns its load. (`docs/productivity/writing-great-skills.md` L328)
3. Arrange content on the **information hierarchy** — steps with checkable+exhaustive completion criteria on top, reference co-located, deep material disclosed behind context pointers. (`writing-great-skills/SKILL.md` L2320)
4. Hunt **leading words** to retire restatements; prune **no-ops/sediment/duplication** sentence by sentence; prompt the **positive**, never the negation. (`writing-great-skills/SKILL.md` L2347, 2360, 2371)
5. Keep skills **independent** via `/skill`-prose deps (never cross-folder file links); shared reference lives in the skill that owns it. (`.agents/invocation.md` L29)
