#!/usr/bin/env bash
# SessionStart hook (command type)
# stdin: JSON {session_id, transcript_path, cwd, hook_event_name, ...}
# stdout: 注入到 main context (空 = 不注入)
# 副作用:
#   - CLAUDE_ENV_FILE 持久化环境变量
#   - 未装 trellis CLI 时后台异步 npm install (不阻塞 hook)
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

# 3. trellis CLI 检测 + 后台安装
if ! command -v trellis >/dev/null 2>&1; then
  # 后台异步安装, 完全 detach, 不阻塞 hook
  (
    nohup npm install -g @mindfoldhq/trellis \
      >/tmp/trellisx-install.log 2>&1 < /dev/null &
  ) >/dev/null 2>&1
  cat <<'EOF'

trellisx: 未检测到 trellis CLI, 已在后台启动 `npm install -g @mindfoldhq/trellis` (日志 `/tmp/trellisx-install.log`)。下次会话生效, 本次会话 trellis 命令暂不可用。
EOF
  exit 0
fi

# 4. trellis 已装 → 按 cwd 注入路由
if [ -d "$CWD/.trellis" ]; then
  cat <<'EOF'

trellisx 路由 (本项目含 .trellis/):

⚠️ 强制任务门禁 (本会话每次实施动作前自检, 不可绕过):
- 动手写代码 / 改文件 / 系统搜索后准备改动前, 必须先判断任务复杂度
- 多步骤 / 多文件 / 多独立目标 / 需调度 (subtask ≥ 2) → 禁直接动手, 必须先建 trellis task 走 planning (加载 `trellisx-orchestrate` skill)
- 仅单步单文件且无独立子目标 (subtask ≤ 1) → 可 main 直做
- 判定靠不准倾向建 task。"任务看起来不复杂"不是绕过理由 — 按是否拆得出 ≥ 2 个独立可验收 subtask 判定
- 一个 prompt 内含 ≥ 2 个独立问题 / 目标 = 必建 task (可拆 parent + child)
- 已绕过 task 开始实施后才发现复杂 → 立即停, 补建 task 重走 planning

路由:
- 任务编排 (subtask 拆分 / 选执行层 / dispatch prompt / 进度通讯 / 生命周期 / 失败回退 / 状态更新) 走 `trellisx-orchestrate` skill
- spec 演化 (init / optimize / sediment) 走 `trellisx-spec` skill
- task.py start 即创 worktree, 结束合并 + 移除确保环境干净
- 非 trellis 编排场景按 CLAUDE.md 通用规则
EOF
else
  cat <<'EOF'

trellisx: trellis CLI 已装, 当前项目无 .trellis/。如需在本项目启用 trellis 工作流, 运行: `trellis init --claude --yes -s`
EOF
fi

exit 0
