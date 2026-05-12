# PRD — cortex_stream.py 渲染 system/hook 事件 + 未适配静默

## 痛点

bash 调 claude 输出仍有原始 JSON:
- `{"type":"system","subtype":"init",...}` — claude 启动
- `{"type":"system","subtype":"hook_started",...}` — hook 触发
- `{"type":"system","subtype":"hook_response",...}` — hook 完成

cortex_stream.py 不识别这些 system type → fallback 原 JSON 显终端。

## User 约束

"只有未处理的未适配的才允许展示原始的json"  
→ 适配的 rich 渲, 未适配 **silent skip**, 默认绝不显原 JSON (除显式 debug)。

## 参考

[Claude Code headless 文档](https://code.claude.com/docs/zh-CN/headless) 列 system event:
- `system.init` — session 启动 (model/tools/mcp_servers/plugins/agents/skills)
- `system.api_retry` — API 重试 (attempt/max_retries/retry_delay_ms/error)
- `system.plugin_install` — 插件安装 (status/name/error)
- `stream_event` — 增量 (text_delta 等)

ccplugin 实测见:
- `system.hook_started` / `system.hook_response`
- `system.task_started` / `system.task_notification`

## 目标

cortex_stream.py 加 type handler + 未适配静默:

| type/subtype | 渲染 |
|--------------|------|
| system.init | 紧凑 "▸ claude 启动 (model=X, tools=N, mcp=M)" |
| system.hook_started | 灰 "  ▸ hook <name> 触发" |
| system.hook_response | 灰 "  ✓ hook <name> 完成 (exit=N)" / 失败红 ✗ |
| system.task_started | "  ▸ 后台任务 <desc>" |
| system.task_notification | "  ✓ 任务 <desc> 完成" |
| assistant.thinking | 灰色折叠 (已有) |
| assistant.text | 直显 (已有) |
| assistant.tool_use | panel (已有) |
| user.tool_result | 摘要 (已有? 否则加) |
| result | 绿色 panel (已有) |
| 其他未知 | **silent skip** (不显) — 仅 CORTEX_STREAM_DEBUG=1 时显 1 行调试 |

## 设计

### 1. cortex_stream.py 加 handler

`mcp/cortex_stream.py` 内 `_render_event` 函数 (现 dispatcher) 加:

```python
def _render_event(event, ...):
    etype = event.get("type")
    subtype = event.get("subtype")
    
    if etype == "system":
        if subtype == "init":
            return _render_init(event)
        elif subtype == "hook_started":
            return _render_hook_started(event)
        elif subtype == "hook_response":
            return _render_hook_response(event)
        elif subtype == "task_started":
            return _render_task_started(event)
        elif subtype == "task_notification":
            return _render_task_notification(event)
        else:
            # 未适配 system event silent
            return None
    
    elif etype == "assistant":
        # 现有
        ...
    elif etype == "user":
        # 加 user.tool_result 渲染
        ...
    elif etype == "result":
        # 现有
        ...
    else:
        # 完全未知 type, silent
        if os.environ.get("CORTEX_STREAM_DEBUG"):
            return f"[debug] unknown event type={etype}"
        return None
```

### 2. 各 system 渲染

```python
def _render_init(e):
    model = e.get("model", "?")
    tools = len(e.get("tools", []))
    mcp = len([s for s in e.get("mcp_servers", []) if s.get("status") == "connected"])
    return Panel(f"model={model} · tools={tools} · mcp={mcp}", title="▸ claude 启动", border_style="dim")

def _render_hook_started(e):
    name = e.get("hook_name", "?")
    event_name = e.get("hook_event", "")
    return Text(f"  ▸ hook {name} ({event_name})", style="dim")

def _render_hook_response(e):
    name = e.get("hook_name", "?")
    exit_code = e.get("exit_code", 0)
    if exit_code == 0:
        return Text(f"  ✓ hook {name}", style="dim green")
    else:
        return Text(f"  ✗ hook {name} (exit={exit_code})", style="red")
```

### 3. user.tool_result 渲染

```python
def _render_user_tool_result(e):
    msg = e.get("message", {})
    content = msg.get("content", [])
    for item in content:
        if item.get("type") == "tool_result":
            text = item.get("content", "")
            is_error = item.get("is_error", False)
            # 截断长结果 (cap 500 chars)
            preview = str(text)[:500] + ("..." if len(str(text)) > 500 else "")
            style = "red" if is_error else "dim"
            return Panel(preview, title="↩ result", border_style=style)
    return None
```

### 4. 主循环过滤 None

```python
for line in stdin:
    event = json.loads(line)
    rendered = _render_event(event, ...)
    if rendered is None:
        continue  # silent skip
    live.update(rendered)
```

## 实施

### Step 1: cortex_stream.py 加 system handlers
### Step 2: user.tool_result 渲染
### Step 3: 未知 type silent (CORTEX_STREAM_DEBUG opt-in)
### Step 4: 真测 dashboard 看 raw JSON 还有没有
### Step 5: marketplace 同步

## 验收
- [ ] system.init 渲染 panel
- [ ] system.hook_* 渲染灰行
- [ ] user.tool_result 渲染 panel
- [ ] 未知 type silent (无 raw JSON)
- [ ] **真测 dashboard.sh stdout 无任何 raw JSON 漏**
- [ ] CORTEX_STREAM_DEBUG=1 仍可看 debug 行
- [ ] 286 tests PASS
- [ ] marketplace 同步

## 风险

| 风险 | 缓解 |
|------|------|
| 隐藏太多失信号 | CORTEX_STREAM_DEBUG opt-in 保留调试 |
| 长 tool_result 截断丢信息 | cap 500 + 提示 "(truncated)" |
| 未来新 type 出现仍 silent | 由 CORTEX_STREAM_DEBUG 显, 反馈循环 |

## 子任务
单 trellis-implement。
