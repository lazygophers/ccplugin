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

trellisx 任务门禁 (本轮先识别任务归属, 闲聊 / 纯咨询可忽略本提示):
1. 识别本轮是否为一个开发 / 实施任务。
2. 若是任务, 判定归属:
   - 现有任务的补充: 输入是对当前 trellis active task 的扩展 / 修改 / 细化 / 边界调整 → 去补充该 task (更新 PRD / 调度图 / 受影响 subtask 文件), 禁新建。
   - 新任务: 与当前 active task 无关, 或无 active task → 新建 trellis task (`task.py create`)。
3. 强制 task: 任务拆解后 ≥ 2 个独立可验收 subtask (多步 / 多文件 / 多目标, 或一个 prompt 含 ≥ 2 个独立问题) → 必须建 task 走 planning (加载 trellisx-orchestrate skill); 仅当拆解后只有 1 个 subtask 才可 main 直做。
4. 判定靠不准倾向建 task。task.py start 即创 worktree, 结束合并 + 移除确保环境干净。
EOF

# === 附加: spec 工作路由 ===
if contains "优化 spec" "优化spec" "重写 spec" "重写spec" "spec refactor" "初始化 spec" "初始化spec" "spec 弱" "spec不可执行" "记不住" "老忘" "反复犯错" "又踩坑" "改硬 trellis 规则"; then
  cat <<'EOF'

trellisx: 本轮涉及 spec 工作 → 加载 trellisx-spec skill 按内容选模式 (init / optimize / sediment), 走 4 阶段流程 (诊断 → 提案 → AskUserQuestion 审批 → 执行 + manifest 同步)。
EOF
fi

# === 附加: 任务规划路由 ===
if contains "写 PRD" "写PRD" "改 PRD" "改PRD" "完善 implement" "完善implement" "完善 design" "拆任务" "拆 subtask" "拆subtask" "派 sub-agent" "派sub-agent" "派 agent" "调度图" "任务规划" "规划任务" "跨包重构" "跨包迁移" "仓库审计" "全量迁移" "全量重构" "全部改造"; then
  cat <<'EOF'

trellisx: 本轮涉及任务规划 → 加载 trellisx-orchestrate skill 走 planning 全流程 (PRD/design/implement/subtask + mermaid 调度图)。
EOF
fi

exit 0
