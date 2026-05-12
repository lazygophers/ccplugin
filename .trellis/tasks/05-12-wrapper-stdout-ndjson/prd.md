# PRD — wrapper stdout NDJSON 过滤

## 问题

用户跑 `~/.cortex/scripts/<wrapper>.sh` 看到大量 raw stream-json NDJSON 漏到终端:
```
{"type":"system","subtype":"init",...}
{"type":"assistant","message":{...thinking...tool_use...}}
{"type":"user","message":{...tool_result...}}
```

根因:
- `cortex_stream_runner` 设计上 stdout 是 NDJSON passthrough (供下游 jq 解析 result line), stderr 是 rich UI
- cron `run.sh` 用 `> /dev/null` 静默 stdout, 但 user-facing wrapper 不重定向 → stdout 直显终端
- cortex_stream.py 不处理某些 type (`system.init` / `user.tool_result`) — 这部分 stdout 不是它的责任 (它写 stderr UI), 但 stdout 是 raw 是设计预期

## 目标

user-facing wrapper stdout 仅显示 **最终 result.text**, 不显示 raw NDJSON。stderr 保 rich UI (实时可见)。

### 范围
- 6 已美化 wrapper: doctor / lint / ingest / search / save / refactor
- 5 新 wrapper: init / memory / recall / promote / consolidate
- 共 11 个调用 cortex_stream_runner 的 wrapper

### 不范围
- cron wrapper (`scripts/cron/*.sh`) 已用 `> /dev/null` (OK)
- cortex_stream.py / stream_progress.sh 设计 (passthrough 契约不变)

## 设计

### 1. wrapper 加 stdout 过滤

每个 wrapper 调用 cortex_stream_runner 后改:

旧:
```bash
cortex_stream_runner claude --bare -p ... "$@"
```

新:
```bash
cortex_stream_runner claude --bare -p ... "$@" \
  | (command -v jq >/dev/null && jq -r 'select(.type=="result" and .subtype=="success") | .result // empty' \
     || cat)
rc=${PIPESTATUS[0]}
```

或更稳: 用 python3 一行解析 (兼容无 jq):
```bash
cortex_stream_runner claude --bare -p ... "$@" \
  | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        if d.get('type') == 'result' and d.get('subtype') == 'success':
            print(d.get('result', ''))
    except: pass
"
rc=${PIPESTATUS[0]}
```

### 2. 处理 jq 缺失

wrapper 已有 jq 检测 (init.sh 等 require jq for config 解析)。但其他不强 require, 退化用 python3 (cortex 已装 python3)。

实施: 加 helper 到 PRELUDE:
```bash
# stdout NDJSON → result.text only
cx_filter_stream() {
  python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try:
        d = json.loads(line)
        if d.get('type') == 'result' and d.get('subtype') == 'success':
            r = d.get('result', '')
            if r: print(r)
    except json.JSONDecodeError:
        pass
"
}
```

wrapper 用:
```bash
cortex_stream_runner claude --bare -p ... "$@" | cx_filter_stream
rc=${PIPESTATUS[0]}
```

### 3. 错误情况处理

若 `result.subtype == "error"`, 显示错误消息 (stderr 红):
```bash
cx_filter_stream() {
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        t = d.get('type')
        if t == 'result':
            sub = d.get('subtype')
            if sub == 'success':
                r = d.get('result', '')
                if r: print(r)
            elif sub == 'error':
                msg = d.get('result') or d.get('error') or '(unknown)'
                print(f'\033[1;31m✗ {msg}\033[0m', file=sys.stderr)
                sys.exit(1)
    except json.JSONDecodeError:
        pass
"
}
```

## 实施

单 agent 串行:
1. `install_wrappers.sh` PRELUDE 加 `cx_filter_stream` 函数
2. 11 个 wrapper (6 已美化 + 5 新) 的 `cortex_stream_runner ...` 调用末尾加 `| cx_filter_stream`
3. 处理 PIPESTATUS 取真实 rc
4. 测试: 跑 memory.sh / init.sh 看 stdout 只 final result, stderr 仍 rich UI

## 验收

- [ ] 11 wrapper 全含 `| cx_filter_stream` 管道
- [ ] PRELUDE 含 cx_filter_stream 函数
- [ ] 实跑 wrapper (mock vault) stdout 仅最终 result.text, 无 NDJSON raw
- [ ] stderr 仍 rich UI (tty)
- [ ] 错误时 stdout 空, stderr 红色 ✗
- [ ] 240 + 测试不回归
- [ ] PIPESTATUS rc 正确传递

## 风险

| 风险 | 缓解 |
|------|------|
| python3 不可用 | cortex 强依赖 python3 (MCP + lint); install.sh 已检测 |
| jq 缺失但 fallback python3 OK | fallback 已设计 |
| 管道破坏 rc | 用 PIPESTATUS[0] |
| 大输出截断 (result 含 newline) | print 全 result 内容 |

## 子任务

单 agent 串行 (install_wrappers.sh 单文件 + 测试)。
