#!/usr/bin/env bash
# UserPromptSubmit hook (command type)
# stdin: JSON {session_id, transcript_path, cwd, hook_event_name, prompt}
# stdout: 注入到 main context 的提示词 (空 stdout = 不注入)
# 退出码 0 = 透明放行 (永远 0, 禁返 stop)

set -u

INPUT=$(cat 2>/dev/null || true)

PROMPT=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    print(d.get('prompt', ''))
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

# 关键词命中检测
contains() {
  for kw in "$@"; do
    [[ "$PROMPT" == *"$kw"* ]] && return 0
  done
  return 1
}

if contains "优化 spec" "优化spec" "重写 spec" "重写spec" "spec refactor" "初始化 spec" "初始化spec" "spec 弱" "spec不可执行" "记不住" "老忘" "反复犯错" "又踩坑" "改硬 trellis 规则"; then
  cat <<'EOF'

trellisx hook: 本轮涉及 spec 工作, 加载 `trellisx-spec` skill 按内容选模式 (init / optimize / sediment), 走 4 阶段流程 (诊断 → 提案 → AskUserQuestion 审批 → 执行 + manifest 同步)。
EOF
  exit 0
fi

if contains "新任务" "新需求" "新的需求" "另一个事" "换一个" "另起一个"; then
  cat <<'EOF'

trellisx hook: 本轮是新任务 (与当前 active task 无关或用户显式声明)。先 `task.py create` 建新 trellis task, 再加载 `trellisx-orchestrate` skill 走 planning 全流程 (PRD/design/implement/subtask + mermaid 调度图)。
EOF
  exit 0
fi

if contains "写 PRD" "写PRD" "改 PRD" "改PRD" "完善 implement" "完善implement" "完善 design" "拆任务" "拆 subtask" "拆subtask" "派 sub-agent" "派sub-agent" "派 agent" "调度图" "任务规划" "规划任务" "跨包重构" "跨包迁移" "仓库审计" "全量迁移" "全量重构" "全部改造"; then
  cat <<'EOF'

trellisx hook: 本轮涉及任务规划。加载 `trellisx-orchestrate` skill。任务规模 subtask ≥ 2 (多步/多文件/多 deliverable) 强制建 trellis task 走 planning 全流程; subtask ≤ 1 可 main 直做。已有 active task 则补充更新 PRD / 调度图 / 受影响 subtask 文件, 不新建。task.py start 即创 worktree, 结束合并 + 移除确保环境干净。
EOF
  exit 0
fi

# 实施类信号 (仅 trellis 项目): 注入复杂度门禁自检
# 命中实施动词 → 提醒先判复杂度再动手 (复杂任务常不含 "拆任务/写PRD" 关键词)
if [ -d "$CWD/.trellis" ]; then
  if contains "修复" "实现" "重构" "优化" "新增" "加一个" "加个" "处理" "搞定" "做一个" "做个" "开发" "解决" "fix" "implement" "refactor" "重新设计" "调整" "改造" "迁移" "升级" "支持" "对接" "集成" "排查" "两个问题" "几个问题" "多个" "同时"; then
    cat <<'EOF'

trellisx hook: 本轮含实施信号。动手前先判任务复杂度: 拆得出 ≥ 2 个独立可验收 subtask (多步/多文件/多目标), 或一个 prompt 含 ≥ 2 个独立问题 → 禁直接动手, 必须先建 trellis task 走 planning (加载 trellisx-orchestrate skill); 仅单步单文件可 main 直做。判定靠不准倾向建 task。
EOF
    exit 0
  fi
fi

# 无关 → 不输出 = 透明放行
exit 0
