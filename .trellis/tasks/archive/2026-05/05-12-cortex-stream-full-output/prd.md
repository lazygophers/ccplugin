# PRD — cortex_stream.py 输出完整化 (含输入 prompt)

## 背景

用户实测 lint.sh 见:
```
[tool: Bash] {"command":"python3 ... --json 2>&1", "de  ← 截断
[text] Here's the cortex-lint summary for the vault:    ← 截断 200 字
[OK] done                                                 ← 缺 .result
```

当前 cortex_stream.py 限:
- `text` 截 200 字
- `tool_use.input` 截 120 字
- `thinking` 类型静默丢
- `result` 仅 `[OK] done` (success) / `[FAILED] ...` (error),缺 success 时的 `.result` 内容
- **未打输入 prompt**:用户看不到送给 claude 的 prompt + system prompt 是啥

用户两条新需求 (同会话连发):
1. "thinking 内容、输出的内容,都要打印出来"
2. "输入的提示词也需要"

## 目标

cortex_stream.py 输出扩展 6 项:
1. `thinking` 类型 → 打 `[thinking] ...` (dim italic 样式)
2. `text` 不截或大 cap (2000)
3. `tool_use.input` 不截或大 cap (800)
4. `result.is_error=false` 时打完整 `.result` 内容
5. 启动前打输入 prompt (system + user)
6. **system prompt panel title 含 skill/agent name** (从 frontmatter 提取 `name:` 字段)

## 范围

### 修改

- `plugins/tools/cortex/mcp/cortex_stream.py` — 渲染逻辑 + 启动前 prompt 显示
- `plugins/tools/cortex/mcp/tests/test_cortex_stream.py` — 加 thinking / prompt 提取 / result.result 用例

### 不在范围

- 不动 stream_progress.sh / run.sh / install.sh / hooks / P0-P6

## 详细规范

### 1. thinking 类型处理

`assistant.message.content[].type == "thinking"` → `[thinking] {.thinking}`,样式 `dim italic` (思考过程,降低视觉权重)。

不截断 thinking (cap 4000 防爆)。

```python
elif btype == "thinking":
    th = (blk.get("thinking") or "").strip()
    if th:
        history.append(Text(f"[thinking] {th[:4000]}", style="dim italic"))
```

### 2. text / tool_input cap 放宽

```python
TEXT_CAP = 2000     # 原 200
TOOL_CAP = 800      # 原 120
THINK_CAP = 4000

# text
txt = (blk.get("text") or "").lstrip("\n")[:TEXT_CAP]

# tool_use
inp = json.dumps(blk.get("input", {}), ensure_ascii=False)[:TOOL_CAP]
```

`ensure_ascii=False` 保中文不转 `\uXXXX`。

### 3. result.result 完整打

```python
elif etype == "result":
    if evt.get("is_error", False):
        msg = (evt.get('result') or 'unknown error')[:TEXT_CAP]
        history.append(Text(f"[FAILED] {msg}", style="bold red"))
    else:
        msg = (evt.get('result') or '').strip()
        if msg:
            history.append(Text(f"[OK] {msg[:TEXT_CAP]}", style="bold green"))
        else:
            history.append(Text("[OK] done", style="bold green"))
```

### 4. 输入 prompt 显示

启动前 (step 1/2 之后) 解析 cmd 提取 system + user prompt 打 rich Panel。

```python
def _extract_prompts(cmd: list[str]) -> tuple[str | None, str | None]:
    """Return (system_prompt, user_prompt) from claude CLI args.

    Heuristics:
    - --append-system-prompt VALUE  → system_prompt = VALUE
    - --system-prompt VALUE         → system_prompt = VALUE (alternative)
    - 末尾非 flag 的 positional 参数 → user_prompt
    """
    system_prompt = None
    user_prompt = None
    i = 0
    positionals: list[str] = []
    while i < len(cmd):
        arg = cmd[i]
        if arg in ("--append-system-prompt", "--system-prompt"):
            if i + 1 < len(cmd):
                system_prompt = cmd[i + 1]
                i += 2
                continue
        if arg.startswith("--"):
            # 通用 --flag VALUE 跳过两元素 (假设带 value)
            i += 1
            if i < len(cmd) and not cmd[i].startswith("-"):
                i += 1
            continue
        if arg.startswith("-") and len(arg) > 1:
            # 短 flag (如 -p), 跳一元素
            i += 1
            continue
        # positional
        positionals.append(arg)
        i += 1
    if positionals:
        user_prompt = positionals[-1]
    return system_prompt, user_prompt
```

在 `run()` 入口,step 1/2 print 之后:

```python
sys_p, user_p = _extract_prompts(full_cmd)
if sys_p:
    summary = sys_p.strip().split("\n", 1)[0][:200]
    err_console.print(Panel(
        Text(f"{summary}{'...' if len(sys_p) > 200 else ''}\n[{len(sys_p)} chars]",
             style="cyan"),
        title="system prompt", border_style="cyan", padding=(0, 1)))
if user_p:
    err_console.print(Panel(
        Text(user_p[:TEXT_CAP], style="white"),
        title="prompt", border_style="magenta", padding=(0, 1)))
```

system prompt 通常是 skill 大文本,只摘头行 + 字符数。user prompt 显示完整 (cap TEXT_CAP)。

### 5. system prompt panel title 含 skill/agent name

cortex wrapper 用 `--append-system-prompt "$(cat $SKILL_PATH)"` 注入 SKILL.md 全文,带 YAML frontmatter:

```yaml
---
name: cortex-lint
description: ...
---
```

解析:

```python
import re

_FRONTMATTER_NAME_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL
)

def _extract_skill_name(system_prompt: str) -> str | None:
    """Parse YAML frontmatter from system prompt, return name field."""
    if not system_prompt:
        return None
    m = _FRONTMATTER_NAME_RE.match(system_prompt.lstrip())
    if not m:
        return None
    fm = m.group(1)
    for line in fm.splitlines():
        line = line.strip()
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return None
```

Panel title 改:

```python
if sys_p:
    skill_name = _extract_skill_name(sys_p)
    title = f"system prompt [skill: {skill_name}]" if skill_name else "system prompt"
    summary = sys_p.strip().split("\n", 1)[0][:200]
    err_console.print(Panel(
        Text(f"{summary}{'...' if len(sys_p) > 200 else ''}\n[{len(sys_p)} chars]",
             style="cyan"),
        title=title, border_style="cyan", padding=(0, 1)))
```

效果:`╭───── system prompt [skill: cortex-lint] ─────╮`

## 验收

1. `bash ~/.cortex/scripts/lint.sh` 终端见:
   - step 1/2 + step 2/2
   - Panel "system prompt" (skill 摘头 + char count)
   - Panel "prompt" (user prompt 完整)
   - 流式 history: `[thinking]` (dim italic) + `[tool: ...]` Panel + `[text] ...` (完整不截 200)
   - `[OK] <完整 result 内容>` 或 `[OK] done`
   - spinner 心跳
2. pytest 新加 ≥3 用例:thinking event / _extract_prompts (3 场景) / result.result 完整
3. ruff + py_compile 全绿
4. P0-P6 不回归

## 不变量

- 纯 stdlib + rich
- cap 上限存在防爆 (4000 / 2000 / 800)
- ensure_ascii=False 保中文
- 输入 prompt 显示在 step 之后, 流式 history 之前
- 不破坏 Phase A API (CORTEX_STREAM_TEE_FILE / --label / --timeout / `--`)

## 风险

- **system prompt 大 (>10K)**: 只摘头行 + 字符数,不全打
- **prompt 含敏感信息**: 用户主动跑 lint 是自己 prompt, 信任前提下 OK
- **history 滚动 5 条仍 cap**: thinking + 多 tool 早期会被挤出 visible 区,**但** tee_file 完整保留
