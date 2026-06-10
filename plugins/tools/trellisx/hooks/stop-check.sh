#!/usr/bin/env bash
# Stop hook (command type)
# stdin: JSON {last_assistant_message, stop_hook_active, cwd, ...}
# 职责: 检查 AI 最后回复是否以 `[trellisx` 开头 (前缀标记)。
#       缺前缀 = AI 未被注入 trellisx 规范 → block + 重注入完整提示词。
# 输出: 缺前缀时 {"decision":"block","reason":<重注入提示词>}; 否则空 (放行)。
#
# 防循环: stop_hook_active=true 时放行 (已试过一次); Claude Code 另有
#         8-consecutive-continuation cap 兜底。

set -u

PROMPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/prompts"
REINJECT_FILE="$PROMPTS_DIR/stop-reinject.md"

INPUT=$(cat 2>/dev/null || true)

REINJECT_FILE="$REINJECT_FILE" TRELLISX_INPUT="$INPUT" python3 <<'PYEOF'
import json, os, sys

raw = os.environ.get("TRELLISX_INPUT", "")
try:
    d = json.loads(raw)
except Exception:
    sys.exit(0)  # 解析失败 → 放行

cwd = d.get("cwd") or os.getcwd()
# 非 trellis 项目 → 放行
if not os.path.isdir(os.path.join(cwd, ".trellis")):
    sys.exit(0)

# 已是 stop hook 触发的继续 → 放行 (防循环)
if d.get("stop_hook_active") is True:
    sys.exit(0)

msg = (d.get("last_assistant_message") or "").lstrip()
# 已带 [trellisx 前缀 → 放行
if msg.startswith("[trellisx"):
    sys.exit(0)

# 缺前缀 → block 重注入完整提示词
reinject_path = os.environ.get("REINJECT_FILE", "")
reason = ""
try:
    with open(reinject_path, encoding="utf-8") as f:
        reason = f.read().strip()
except Exception:
    reason = "你的回复未以 [trellisx-{status}-{task name}] (无任务时 [trellisx]) 开头, 说明 trellisx 强制规范未生效。立即加载 trellisx-enforce skill 阅读全部规范并遵守, 之后所有回复必须以 [trellisx...] 前缀开头。"

print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
PYEOF
