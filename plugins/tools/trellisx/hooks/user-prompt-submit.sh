#!/usr/bin/env bash
# UserPromptSubmit hook (command type)
# stdin: JSON {session_id, transcript_path, cwd, hook_event_name, prompt}
# stdout: 注入到 main context 的提示词 (空 stdout = 不注入)
# 退出码 0 = 透明放行 (永远 0, 禁返 stop)
#
# 行为: trellis 项目内每轮无条件注入任务识别门禁 (prompts/task-gate.md);
#       spec 关键词命中时附 spec 路由 (prompts/spec-route.md)。
# 提示词内容全部外置到 prompts/*.md, 本脚本仅做逻辑路由 + 注入。

set -u

# 提示词目录 (与本脚本同级 prompts/)
PROMPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/prompts"

emit() { [ -f "$PROMPTS_DIR/$1" ] && cat "$PROMPTS_DIR/$1"; }

INPUT=$(cat 2>/dev/null || true)

PROMPT=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print(json.loads(sys.stdin.read()).get('prompt', ''))
except Exception:
    pass
" 2>/dev/null)

CWD=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print(json.loads(sys.stdin.read()).get('cwd', ''))
except Exception:
    pass
" 2>/dev/null)
[ -z "$CWD" ] && CWD="${CLAUDE_PROJECT_DIR:-${PWD:-$(pwd)}}"

[ -z "$PROMPT" ] && exit 0

# 非 trellis 项目 → 静默放行 (无 task 概念)
[ -d "$CWD/.trellis" ] || exit 0

# 关键词命中检测
contains() {
  for kw in "$@"; do
    [[ "$PROMPT" == *"$kw"* ]] && return 0
  done
  return 1
}

# === 基础任务门禁 (trellis 项目每轮无条件注入) ===
emit task-gate.md

# === 附加: spec 工作路由 ===
if contains "优化 spec" "优化spec" "重写 spec" "重写spec" "spec refactor" "初始化 spec" "初始化spec" "spec 弱" "spec不可执行" "记不住" "老忘" "反复犯错" "又踩坑" "改硬 trellis 规则"; then
  emit spec-route.md
fi

exit 0
