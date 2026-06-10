#!/usr/bin/env bash
# SessionStart hook (command type)
# stdin: JSON {session_id, transcript_path, cwd, hook_event_name, ...}
# stdout: 注入到 main context (空 = 不注入)
# 副作用:
#   - CLAUDE_ENV_FILE 持久化环境变量
#   - 未装 trellis CLI 时后台异步 npm install (静默, 不注入提示)
# 退出码 0 永远 (禁返 stop)
#
# 本插件只注入 trellisx 自己的提示词 (prompts/session-route.md);
# trellis CLI 安装 / init 状态不归本插件注入, 仅做静默副作用。

set -u

# 提示词目录 (与本脚本同级 prompts/)
PROMPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/prompts"

emit() { [ -f "$PROMPTS_DIR/$1" ] && cat "$PROMPTS_DIR/$1"; }

INPUT=$(cat 2>/dev/null || true)

# 1. 设环境变量 (启用 agent-teams 实验功能)
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1' >> "$CLAUDE_ENV_FILE"
fi

# 2. trellis CLI 未装 → 后台异步安装 (静默副作用, 不注入提示)
if ! command -v trellis >/dev/null 2>&1; then
  (
    nohup npm install -g @mindfoldhq/trellis \
      >/tmp/trellisx-install.log 2>&1 < /dev/null &
  ) >/dev/null 2>&1
fi

# 3. 提取 cwd
CWD=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print(json.loads(sys.stdin.read()).get('cwd', ''))
except Exception:
    pass
" 2>/dev/null)
[ -z "$CWD" ] && CWD="${CLAUDE_PROJECT_DIR:-${PWD:-$(pwd)}}"

# 4. trellis 项目 → 注入 trellisx 编排路由; 否则静默
if [ -d "$CWD/.trellis" ]; then
  emit session-route.md
fi

exit 0
