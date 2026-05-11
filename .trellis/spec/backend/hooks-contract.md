# Hooks Contract

> Claude Code hook events, the JSON I/O protocol, exit codes, and timeout budget — as implemented in this repo.

---

## Scope

Every hook handler in this repo (`.claude/hooks/*.py`, `plugins/*/scripts/hooks.py`) is a short-lived process invoked by Claude Code on specific lifecycle events. This file documents the contract every handler must satisfy.

---

## How Hooks Are Wired

Hooks are declared in two places:

1. **Repo-level** Claude Code config (under `.claude/`) — for cross-cutting concerns like Trellis context injection.
2. **Plugin manifests** — `plugin.json:hooks` map event names to commands. Real example, `plugins/memory/.claude-plugin/plugin.json:22-34`:
   ```json
   "hooks": {
     "SessionStart": [
       {
         "hooks": [
           {
             "type": "command",
             "command": "PLUGIN_NAME=memory uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks",
             "async": true,
             "timeout": 1000
           }
         ]
       }
     ]
   }
   ```

Each entry has:

| Field | Notes |
|-------|-------|
| `type` | `"command"` (only supported value here) |
| `command` | shell command; `${CLAUDE_PLUGIN_ROOT}` resolves to the install dir |
| `async` | `true` lets the hook return immediately while work continues |
| `timeout` | budget in milliseconds; the hook process is killed past this |

---

## Supported Event Names

The events validated by `scripts/check.py:37-60`:

```
SessionStart            UserPromptSubmit         PreToolUse
PermissionRequest       PostToolUse              PostToolUseFailure
Notification            SubagentStart            SubagentStop
Stop                    StopFailure              TeammateIdle
TaskCompleted           InstructionsLoaded       ConfigChange
CwdChanged              FileChanged              WorktreeCreate
WorktreeRemove          PreCompact               PostCompact
Elicitation             ElicitationResult        SessionEnd
```

A plugin / repo hook can register for any subset. Unknown event names are ignored by Claude Code (and rejected by `scripts/check.py`).

---

## Input: stdin JSON

Every hook receives a single JSON object on stdin. Common fields (every event):

```jsonc
{
  "session_id": "string",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default" | "grant" | "deny",
  "hook_event_name": "<one of the names above>"
}
```

Event-specific fields are added on top. Examples (`scripts/check.py:217-249`):

- `InstructionsLoaded` adds `file_path`, `memory_type`, `load_reason`.
- `FileChanged` adds `file_path`, `event` (e.g. `"change"`).
- `PreToolUse` adds `tool_name`, `tool_input`.
- `Notification` adds `notification_type`, `title`, `message`.

Always read stdin defensively. Reference (`.claude/hooks/session-start.py:625-633`):

```python
def main():
    if should_skip_injection():
        sys.exit(0)
    try:
        hook_input = json.loads(sys.stdin.read())
        if not isinstance(hook_input, dict):
            hook_input = {}
    except (json.JSONDecodeError, ValueError):
        hook_input = {}
```

Rules:

- If stdin is empty or invalid JSON, fall back to `{}` and continue (advisory hooks) OR exit `0` (no-op).
- Never raise — always convert to `{}` or an exit code.

---

## Output: stdout JSON / Text

There are two valid stdout shapes depending on the hook's purpose:

1. **Advisory hooks** (the common case): write text that should be injected back into the session. The repo-level Trellis hooks use this — `.claude/hooks/session-start.py` builds a string in `StringIO` and prints it. The memory plugin uses bare `print(...)` for memory previews (`plugins/memory/scripts/hooks.py:43-45`):
   ```python
   for mem in core_memories[:5]:
       content_preview = mem.content[:200] if len(mem.content) > 200 else mem.content
       print(f"[Memory:{mem.uri}] {content_preview}...")
   ```
2. **Validating hooks** (e.g. `PreToolUse` blockers): emit a JSON object on stdout describing the decision; non-zero exit code means "block".

Either way, **stdout is a protocol channel**. Diagnostics MUST go to `lib.logging` (which writes to a log file), never to stdout.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0`  | Success / continue. Advisory hooks should ALWAYS exit `0` even on internal failure so the user is not blocked. |
| non-zero | Halt the action that triggered the hook (only meaningful for blocking hooks like `PreToolUse`). |

Pattern for an advisory hook that wraps everything:

```python
def main():
    try:
        ...do work...
    except Exception as e:
        # Log, but do NOT block the user's session.
        logging.error(f"hook failed: {e}")
        sys.exit(0)
```

Choose non-zero only when you genuinely intend to block the operation.

---

## Timeout Budget

`timeout` (ms) in the manifest is hard. Common budgets in this repo:

| Event | Budget | Why |
|-------|--------|-----|
| `SessionStart` | 1000 ms | runs once per session; small budget keeps startup snappy |
| `PreToolUse` | 500 ms | runs before EVERY tool call; must be fast |
| `PostToolUse` | 1000 ms | runs after every tool call; can do a bit more work |
| `SessionEnd` | 1000 ms | persistence + cleanup |

If you can't finish inside the budget, set `async: true` and do work in the background — but remember: a backgrounded hook can be killed when the session ends. Persist any state explicitly.

---

## Resource Lifecycle in Hooks

Hook processes are short-lived. If you open external resources, you MUST close them, otherwise the hook process hangs at exit and the timeout kills it. Reference (`plugins/memory/scripts/hooks.py:33-49`):

```python
async def _handle():
    await init_db()
    try:
        core_memories = await get_memories_by_priority(max_priority=3)
        if core_memories:
            for mem in core_memories[:5]:
                content_preview = mem.content[:200] if len(mem.content) > 200 else mem.content
                print(f"[Memory:{mem.uri}] {content_preview}...")
    finally:
        await close_db()       # critical — hook process otherwise blocks
```

Always pair `init_db` / `close_db`, file open / close, network connect / close.

---

## Forbidden Patterns

```python
# ❌ Logging to stdout (pollutes the protocol channel)
print(f"DEBUG: tool_name={tool_name}")     # use logging.debug() instead

# ❌ Crashing on bad input
hook_input = json.loads(sys.stdin.read())  # raises if stdin is empty/invalid

# ❌ Exit non-zero on internal failure in an advisory hook
except Exception:
    sys.exit(1)                             # blocks the user's session for no good reason

# ❌ Long-running synchronous work inside a sub-second budget
await fetch_remote_index()                  # set async: true and use a background queue

# ❌ Leaving DB / file handles open
await init_db()
do_work()
# missing close_db() → process hangs, killed by timeout
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Hook silently does nothing | Verify the manifest event name matches exactly (case-sensitive) |
| Hook is killed mid-work | Increase `timeout` OR set `async: true` and persist incrementally |
| Hook output never appears in session | You wrote to stderr or to the log file; advisory hooks must use stdout |
| Hook crashes the agent | Replace bare `raise` with try/except + `sys.exit(0)` for advisory; non-zero only for blockers |
| Wrong subcommand dispatched | Plugins use a single `main.py hooks` entry that switches on `hook_event_name`; ensure your dispatcher covers the event you registered |

---

## Security Filter Pipeline (P0 Hardening)

Hooks/skills that accept external content (URL ingest, transcript persist, free-form note save) **MUST** run three pure-function filters before any disk write or external fetch.

### 1. Scope / Trigger

- Trigger: any path that persists model output or fetches remote content into the vault.
- Reference impl: `plugins/tools/cortex/hooks/_lib/{masking,url_security,html_sanitize}.py`.

### 2. Signatures

```python
# masking.py
def mask(text: str) -> tuple[str, list[str]]: ...
# Returns (redacted_text, hit_rule_names). hit list NEVER contains the original secret.

# url_security.py
def is_safe(url: str) -> tuple[bool, str]: ...
# Returns (allowed, reason). DNS lookup uses 2s timeout, fail-closed on resolution error.

# html_sanitize.py
def sanitize(markdown: str) -> str: ...
# Idempotent. Preserves fenced code blocks (``` and ~~~) verbatim.
```

### 3. Contracts

| Step | Input | Output | Fail Mode |
|------|-------|--------|-----------|
| `url_security.is_safe(url)` | raw URL string | `(bool, reason)` | DNS error → `(False, reason)` (fail-closed) |
| `html_sanitize.sanitize(md)` | post-fetch markdown | sanitized markdown | regex never raises (stdlib `re`) |
| `masking.mask(text)` | sanitized text | `(masked, hits)` | hits list of rule names only |

**Mandatory order**: `url_security → fetch → html_sanitize → masking → write`. Reordering is a regression.

Env keys:

- `CORTEX_SKIP_SANITIZE=1` — test-only bypass for `masking` + `html_sanitize`. **Never** bypasses `url_security` (SSRF must not be skippable).

### 4. Validation & Error Matrix

| Condition | Filter | Result |
|-----------|--------|--------|
| URL scheme `file:` / `gopher:` | url_security | reject `unsupported scheme` |
| URL host resolves to `127.0.0.0/8` / `10.x` / `172.16-31.x` / `192.168.x` / `169.254.x` | url_security | reject `private network` |
| URL host == `localhost` / `metadata` / `metadata.google.internal` | url_security | reject `metadata host` |
| URL port < 1024 and not in {80, 443} | url_security | reject `low port` |
| DNS resolution timeout (>2s) | url_security | reject `dns timeout` (fail-closed) |
| `<script>` / `<iframe>` / `<object>` / `<embed>` outside fenced code | html_sanitize | stripped |
| `on*=` inline event attr | html_sanitize | attr removed |
| `javascript:` / `data:text/html` href | html_sanitize | replaced with `#` |
| Same patterns **inside** ` ``` ` or `~~~` fence | html_sanitize | preserved verbatim |
| `AKIA[0-9A-Z]{16}` | masking | `<REDACTED:aws_akid>` |
| `sk-ant-[A-Za-z0-9_-]{20,}` | masking | `<REDACTED:anthropic_key>` (matched **before** openai_key) |
| `sk-[A-Za-z0-9]{20,}` with word boundary | masking | `<REDACTED:openai_key>` |
| `gh[pousr]_[A-Za-z0-9]{36,}` | masking | `<REDACTED:github_pat>` |
| JWT 3-part / PEM private key / Slack `xox[abprs]-` | masking | `<REDACTED:*>` |

### 5. Good/Base/Bad Cases

- **Good**: `cortex-ingest` flow: `url_security("https://example.com") → WebFetch → html_sanitize(md) → masking(md) → save`.
- **Base**: `cortex-save` flow (model-authored note, no remote fetch): `masking(body) → write`.
- **Bad**: skipping `url_security` because "the URL came from the user" — user input can still be SSRF (open redirect, paste from LLM).

### 6. Tests Required

- `tests/python/test_masking.py` — each of 7 rules has ≥1 hit case + ≥1 plain-text non-hit case; assert hit list contains rule name only (never original).
- `tests/python/test_url_security.py` — 9 private-net IPs + 3 metadata hosts + low-port + non-http scheme each reject; ≥2 public URLs pass; assert `is_safe()` returns `False` on DNS timeout.
- `tests/python/test_html_sanitize.py` — script/iframe/object/embed/on*=/javascript: each stripped; fenced code block with same patterns preserved; markdown tables/wikilinks/callouts untouched.

### 7. Wrong vs Correct

```python
# ❌ Wrong — masking before sanitize: model can embed <script>$KEY</script> inline, sanitize then drops the masking marker too
masked, hits = masking.mask(raw)
clean = html_sanitize.sanitize(masked)  # may strip <REDACTED:*> inside a stripped tag

# ❌ Wrong — bypassing url_security in "trusted" path
md = WebFetch(user_url)  # no SSRF check

# ✅ Correct
ok, reason = url_security.is_safe(user_url)
if not ok:
    raise SecurityError(reason)
md = WebFetch(user_url)
md = html_sanitize.sanitize(md)
md, hits = masking.mask(md)
log.info("masking hits: %s", hits)  # names only
write(md)
```

### Known Gotcha — DNS Rebinding (P1 backlog)

> **Warning**: `url_security.is_safe()` resolves DNS once, but downstream `WebFetch` / `curl` resolves again. An attacker can flip the A record between resolutions to point at `127.0.0.1`.
>
> Mitigation (deferred to P1): `is_safe()` should return `(safe, resolved_ip)`; caller dials the IP directly and sets `Host:` header to the original hostname. Until then, the window is small (2 resolutions within ~ms) but real for high-value internal services.

---

## References

- `scripts/check.py:37-60` — canonical event-name list
- `scripts/check.py:99-291` — example payload schemas per event
- `.claude/hooks/session-start.py:625-680` — repo-level advisory hook (Trellis injection)
- `plugins/memory/scripts/hooks.py` — plugin hook handlers (12 handlers)
- `plugins/memory/.claude-plugin/plugin.json:22-...` — manifest hook registration
- `plugins/tools/cortex/hooks/_lib/masking.py` — secret redaction reference impl
- `plugins/tools/cortex/hooks/_lib/url_security.py` — SSRF guard reference impl
- `plugins/tools/cortex/hooks/_lib/html_sanitize.py` — HTML injection guard reference impl
- See also: [plugin-conventions](./plugin-conventions.md), [logging-guidelines](./logging-guidelines.md)
