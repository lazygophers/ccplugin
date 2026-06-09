#!/usr/bin/env bash
# SessionStart hook (command type)
# stdin: JSON {session_id, transcript_path, cwd, hook_event_name, ...}
# stdout: 注入到 main context (空 = 不注入)
# 副作用: 通过 CLAUDE_ENV_FILE 持久化环境变量
# 退出码 0 永远 (禁返 stop)

set -u

INPUT=$(cat 2>/dev/null || true)

# 1. 设环境变量 (启用 agent-teams 实验功能)
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1' >> "$CLAUDE_ENV_FILE"
fi

# 2. 提取 cwd
CWD=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print(json.loads(sys.stdin.read()).get('cwd', ''))
except Exception:
    pass
" 2>/dev/null)
[ -z "$CWD" ] && CWD="${CLAUDE_PROJECT_DIR:-${PWD:-$(pwd)}}"

# 3. trellis 项目时注入路由指引
if [ -d "$CWD/.trellis" ]; then
  cat <<'EOF'

trellisx 路由 (本项目含 .trellis/):
- 任务编排 (subtask 拆分 / 选执行层 / dispatch prompt / 进度通讯 / 生命周期 / 失败回退 / 状态更新) 走 `trellisx-orchestrate` skill
- spec 演化 (init / optimize / sediment) 走 `trellisx-spec` skill
- 非 trellis 编排场景按 CLAUDE.md 通用规则
EOF
fi

exit 0
