#!/usr/bin/env bash
# UserPromptSubmit hook (command type)
# stdin: JSON {session_id, transcript_path, cwd, hook_event_name, prompt}
# stdout: 注入到 main context 的提示词 (空 stdout = 不注入)
# 退出码 0 = 透明放行 (永远 0, 禁返 stop)
#
# 行为: trellis 项目内每轮无条件注入任务识别门禁;
#       spec / 编排关键词命中时附专门 skill 路由。

set -u

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
cat <<'EOF'
1. 判定用户输入是新的任务描述还是对已有任务的补充，如果是现有任务的补充，则 扩展 / 修改 / 细化 / 边界调整 → 去补充该 task (更新 PRD / 调度图 / 受影响 subtask 文件)
2. 新任务必须强制 task 走 planning (加载 trellisx-orchestrate skill)
3. 任何任务规划 / PRD / design / implement / subtask 拆分 / 派 sub-agent / 调度图编写 → 加载 trellisx-orchestrate skill 走 planning 全流程
4. 必须新建 worktree 执行任务，且在任务完成后 merge + remove 确保环境干净
EOF

# === 附加: spec 工作路由 ===
if contains "优化 spec" "优化spec" "重写 spec" "重写spec" "spec refactor" "初始化 spec" "初始化spec" "spec 弱" "spec不可执行" "记不住" "老忘" "反复犯错" "又踩坑" "改硬 trellis 规则"; then
  cat <<'EOF'
本轮涉及 spec 工作 → 加载 trellisx-spec skill 按内容选模式 (init / optimize / sediment), 走 4 阶段流程 (诊断 → 提案 → AskUserQuestion 审批 → 执行 + manifest 同步)
EOF
fi

exit 0
