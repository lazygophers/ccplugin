# PRD — wrapper 用 stream-json + rich 实时渲染

## 需求

所有 bash 调 claude 用 stream-json 模式, 实时解析输出, 人机友好展示。

## 现状

上轮 wrapper 简化为:
```bash
exec claude --settings X --print -p "/cortex-<name>"
```
`--print` 是一次性输出 markdown, 不实时, 不美化工具调用过程。

## 目标

每个 wrapper:
- `--output-format stream-json --verbose` 启 NDJSON 流
- 走 `cortex_stream_runner` (rich UI) 实时渲染:
  · 工具调用 (tool_use) → 浅色 panel
  · 思考 (thinking) → 灰色折叠
  · 文本 (text) → 直显
  · 结果 (result) → 绿色 panel
- 退出: NDJSON stdout 走 `cx_filter_stream` 仅留 final result.text

## 设计

### 1. install_wrappers.sh emit_slash 模板改

```bash
source "$LIB_PATH"   # stream_progress.sh
export CORTEX_JOB_LABEL="cortex-<name>"
cortex_stream_runner claude --settings "$SETTINGS" -p "/cortex-<name>" \
  | cx_filter_stream
rc=${PIPESTATUS[0]}
[ $rc -eq 0 ] && ok "<name> done" || err "<name> failed code=$rc" "$rc"
```

`cortex_stream_runner` 已自动注 `--output-format stream-json --verbose`, 但需验证它支持非 `--bare` 模式。如不支持: 改成直接调 claude + 显式 flag, 然后 pipe 进 cortex_stream.py。

### 2. cron/run.sh 同样

恢复 cortex_stream_runner 调用 (上轮简化掉的):
```bash
source "$DIR/../lib/stream_progress.sh"
export CORTEX_JOB_LABEL="cortex-$JOB"
cortex_stream_runner "${CMD[@]}" 2>>"$ERR_FILE" >"$TMP_NDJSON"
```

CMD 内不含 `--print` (用 stream-json 替代)。保 jq 取 result 行逻辑。

### 3. cortex_stream.py 兼容非 --bare 模式

cortex_stream.py 现解析 NDJSON 假设 claude --bare 输出。非 --bare 输出格式相同? 应该是 (都是 Claude Code stream-json), 验证后调整。

### 4. 真测

`bash ~/.cortex/scripts/dashboard.sh` 应:
- 实时显示工具调用 panel
- 思考折叠灰色
- 文本流式打印
- 末尾绿色 result panel
- EXIT=0

## 实施

### Step 1: install_wrappers.sh emit_slash 加 stream + cx_filter
### Step 2: cron/run.sh 恢复 cortex_stream_runner
### Step 3: 真测 dashboard
### Step 4: marketplace 同步

## 验收
- [ ] 所有 wrapper 用 stream-json 输出 (源 grep `--print` → 0 或仅过滤场景)
- [ ] wrapper 走 cortex_stream_runner
- [ ] **真测 dashboard.sh** 实时 rich UI + EXIT=0
- [ ] 286 tests PASS
- [ ] marketplace 同步
