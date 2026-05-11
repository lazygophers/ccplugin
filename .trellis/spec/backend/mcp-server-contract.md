# MCP Server Contract (Python)

> **Scope**: Building a Model Context Protocol server inside this monorepo. Covers tool registration, input validation, path containment, secret hygiene, concurrent write safety, and cross-module reuse.
>
> Reference impl: `plugins/tools/cortex/mcp/`.

---

## 1. Scope / Trigger

Apply this contract whenever:

- A new MCP server is added under `plugins/<category>/<name>/mcp/`
- An existing MCP server gains a tool that **writes to disk** or **fetches remote content**
- A tool accepts free-form user/model strings that become **file path segments**

---

## 2. Signatures

### Tool registration

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("<plugin-name>")

TOOL = Tool(
    name="<verb>",                           # snake_case, no plugin prefix
    description="<terse purpose, 1 line>",
    inputSchema={                            # strict JSON Schema
        "type": "object",
        "properties": { ... },
        "required": [...],
    },
)

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [TOOL_A, TOOL_B]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "<verb>":
        return await handle_<verb>(arguments)
    raise ValueError(f"unknown tool: {name}")  # protocol-level error
```

### Tool handler

```python
async def handle_<verb>(args: dict) -> list[TextContent]:
    # 1. Validate required fields (raise ValueError on missing)
    # 2. Sanitize any path-bound segments via _safe_segment()
    # 3. Resolve final path and assert containment via resolve().relative_to(vault)
    # 4. Apply security filters (masking before write, url_security before fetch)
    # 5. Perform IO under lib.lock.file_lock() if writing shared state
    # 6. Return structured JSON in TextContent.text (single element list)
```

---

## 3. Contracts

### Dependency policy (Python MCP)

| Allowed | Forbidden |
|---------|-----------|
| stdlib (`re`, `socket`, `ipaddress`, `urllib`, `fcntl`, `subprocess`, `pathlib`, `hashlib`, `json`, `importlib.util`) | `requests`, `httpx`, `pyyaml`, `pydantic-extra-types` |
| `mcp>=1.0,<2.0` + its bundled `pydantic` | Any GUI / async-io framework beyond `asyncio` |

**Rationale**: MCP servers are distributed via `pipx install <local-path>`. Every extra dep makes install fragile and increases supply-chain surface.

### plugin.json wiring

```jsonc
{
  "mcpServers": {
    "<plugin-name>": {
      "command": "<plugin-name>-mcp",         // pipx console-script
      "args": [],
      "env": {
        "<PLUGIN>_VAULT_PATH": "${<PLUGIN>_VAULT_PATH:-}",
        "<PLUGIN>_PLUGIN_ROOT": "${CLAUDE_PLUGIN_ROOT}"  // critical for cross-module reuse
      }
    }
  }
}
```

`CLAUDE_PLUGIN_ROOT` env is **required** so the pipx-installed binary can locate sibling modules outside its install snapshot (e.g., reuse `hooks/_lib/masking.py`).

### Install script (`install.sh`)

```bash
step_mcp_install() {
  if ! command -v pipx >/dev/null 2>&1; then
    log_warn "pipx missing — MCP server unavailable; skill paths will fall back to CLI."
    return 0   # warn, do not block
  fi
  if pipx list --short 2>/dev/null | grep -q '^<plugin-name>-mcp '; then
    [ "${REINSTALL:-0}" = "1" ] && pipx install --force "${PLUGIN_ROOT}/mcp"
  else
    pipx install "${PLUGIN_ROOT}/mcp" || log_warn "pipx install failed; MCP unavailable"
  fi
}
```

---

## 4. Validation & Error Matrix

| Condition | Behavior |
|-----------|----------|
| Required `inputSchema` field missing | Handler raises `ValueError(f"missing {field}")`; MCP protocol returns structured error |
| Enum-typed field with invalid value | Handler raises `ValueError(f"invalid {field}: expected one of ...")` |
| Path-segment field contains `/` `\` NUL `.` `..` | Handler raises `ValueError(f"unsafe segment: {value}")` |
| Final resolved path outside vault root | Handler raises `ValueError("path escaped vault root")` (defense-in-depth) |
| Write attempt without `file_lock()` on shared file | Code review reject |
| Body containing secrets and no `masking.mask()` call before write | Code review reject |
| Remote URL fetched without `url_security.is_safe()` precheck | Code review reject |
| `fcntl` unavailable (Windows) | `lib/lock.py` falls back to no-op + `stderr` warn (P1 supported macOS/Linux only) |

---

## 5. Good/Base/Bad Cases

- **Good**: Tool that does no IO and returns derived data (read-only search over indexed files). Minimal contract surface.
- **Base**: Tool that writes to a path under a fixed root. Requires `_safe_segment` + final `resolve().relative_to(root)` + `file_lock`.
- **Bad**: Tool that accepts a free-form path arg (`{"target_path": "..."}`) and writes there directly. **Always reject** — tools must construct the path from typed segments.

---

## 6. Tests Required

For every MCP tool that writes or fetches:

| Test | Assertion |
|------|-----------|
| `test_<tool>_missing_required` | Raises `ValueError`, no IO performed |
| `test_<tool>_path_traversal` | At least three vectors (`..`, `/abs/path`, NUL byte); each raises before disk write |
| `test_<tool>_containment_final_guard` | Construct legitimate segments that resolve outside root via symlink/relative parts — final guard catches |
| `test_<tool>_secret_redacted` | Body containing secret pattern is written redacted (calls `masking.mask` in pipeline) |
| `test_<tool>_url_blocked` (fetch tools) | Internal IP / metadata host rejected before any `urllib.urlopen` |
| `test_lock_serializes` | Two concurrent calls on same path serialize (use threads + sentinel file) |
| `test_lock_timeout` | Hold lock externally → caller raises `TimeoutError` within configured window |

Reference: `plugins/tools/cortex/mcp/tests/test_save.py::test_save_rejects_path_traversal`.

---

## 7. Wrong vs Correct

### Wrong — raw path segment

```python
async def handle_save(args):
    path = vault / args["host"] / args["org"] / args["repo"] / f"{args['title']}.md"
    path.write_text(args["body"])  # host="../../etc" escapes root
```

### Correct — segment sanitization + final containment

```python
def _safe_segment(value: str) -> str:
    if any(c in value for c in ("/", "\\", "\x00")) or value in (".", ".."):
        raise ValueError(f"unsafe segment: {value!r}")
    return value

async def handle_save(args):
    parts = [_safe_segment(args[k]) for k in ("host", "org", "repo")]
    title_slug = _safe_segment(slugify(args["title"]))
    path = (vault.joinpath(*parts, f"{title_slug}.md")).resolve()
    path.relative_to(vault.resolve())          # raises if outside; defense in depth
    body, hits = masking.mask(args["body"])    # P0 filter required before write
    with file_lock(path):
        path.write_text(body)
```

---

## Lock File Pattern

> **Warning**: Never `fcntl.flock()` the same fd you are writing to. The lock is released the moment the fd closes, which is exactly when the write commits — defeating the purpose.

```python
# lib/lock.py
@contextmanager
def file_lock(target: Path, timeout: float = 5.0):
    lock_path = target.with_suffix(target.suffix + ".lock")  # sidecar
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"flock timeout: {lock_path}")
                time.sleep(0.05)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
```

---

## Ingest Pipeline Pattern (P4)

When an MCP tool ingests external content (URL, file, etc.) and writes to the vault, it MUST follow this fixed pipeline:

### URL ingest

```
url_security.is_safe(url)         # fail-closed before any network call
    ↓
urllib.request.urlopen(url, t=10) # stdlib only; body capped at 10 MiB
    ↓
Content-Type route               # text/html → extractors.html / application/pdf → extractors.pdf
    ↓
extractor.extract(...)            # → {title, body, meta, warnings}
    ↓
html_sanitize.sanitize(body)      # HTML path only; strips <script>/<iframe>/on*=
    ↓
save._save_internal(             # masking inside, then write under flock
    body=...,
    source_meta={"url": url, "content_type": ct},
)
```

### File ingest

```
Path(arg).expanduser().resolve()  # plus exists / is_file / R_OK check
    ↓
extension route                   # .pdf/.epub/.docx/.md/.txt; unsupported → ValueError
    ↓
extractor.extract(path)
    ↓
save._save_internal(
    body=...,
    source_meta={"file": str(path), "ext": ext},
)
```

### Extractor Contract

All extractors expose:

```python
def extract(source: bytes | str | Path) -> dict:
    """
    Returns:
        {"title": str|None, "body": str, "meta": dict, "warnings": list[str]}
    Raises:
        ValueError    # unsupported/invalid input
        RuntimeError  # parse failure (corrupt, encrypted)
    """
```

Implementation rules:
- Pure function: no logging, no global state mutation, no file IO except reading the path argument.
- Encrypted PDF / corrupt EPUB → `RuntimeError`, never silent empty body.
- Scan-only PDFs (no embedded text) return empty `body` + `warnings=["scan-only pdf"]`.
- EPUB chapter HTML MUST be run through `html_sanitize.sanitize()` inside `extractors/epub.py` (defense in depth — chapters can carry hostile script).

### Body size cap

`urlopen` reads with a hard cap (`_MAX_BYTES = 10 * 1024 * 1024`); responses larger than cap raise `ValueError("response too large")`. This bounds memory and is a partial defense against ZIP bombs (combined with upstream pypdf/ebooklib/python-docx parser limits).

### Fixture generation pattern

Test fixtures for binary formats (PDF/EPUB/DOCX) MUST be generated by a one-shot script committed to `tests/fixture_gen.py`, with the output files committed. Tests never re-run `fixture_gen.py` and never fetch fixtures from the network. The generator MUST embed a known masking-trigger token (e.g., `AKIAIOSFODNN7EXAMPLE` for AWS AKID) so end-to-end masking wiring is testable against every format.

---

## Cross-Module Reuse (importlib pattern)

When the MCP server (installed via pipx in an isolated venv) needs to call into sibling plugin modules (e.g., the P0 masking filter at `hooks/_lib/masking.py`):

```python
# tools/save.py
import importlib.util, os
from pathlib import Path

def _load_masking():
    root = os.environ.get("CORTEX_PLUGIN_ROOT")
    if root:
        candidate = Path(root) / "hooks" / "_lib" / "masking.py"
    else:
        candidate = Path(__file__).resolve().parents[2] / "hooks" / "_lib" / "masking.py"
    spec = importlib.util.spec_from_file_location("cortex_masking", candidate)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

masking = _load_masking()
```

Why: pipx venvs cannot reach `${CLAUDE_PLUGIN_ROOT}` via normal `sys.path`. The `<PLUGIN>_PLUGIN_ROOT` env var injected by `plugin.json` resolves the snapshot mismatch.

---

## References

- `plugins/tools/cortex/mcp/server.py` — minimal stdio MCP server
- `plugins/tools/cortex/mcp/tools/save.py` — write path with all guards (`_safe_segment`, containment, masking, flock)
- `plugins/tools/cortex/mcp/lib/lock.py` — sidecar-file flock pattern
- `plugins/tools/cortex/mcp/tests/test_save.py::test_save_rejects_path_traversal` — required test
- See also: [hooks-contract.md §Security Filter Pipeline](./hooks-contract.md#security-filter-pipeline-p0-hardening)
