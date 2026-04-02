#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook 校验脚本
# 用于校验工具调用参数的安全性
#
# 输入: stdin JSON (hook input, 包含 tool_name 和 tool_input)
# 退出码: 0=允许, 2=拒绝(stderr反馈给Claude)

command -v jq >/dev/null 2>&1 || { echo "错误: jq 命令未安装" >&2; exit 1; }

input=$(cat)

tool_name=$(echo "$input" | jq -r '.tool_name // ""')
tool_input=$(echo "$input" | jq -r '.tool_input // "{}"')

# 未识别工具名时跳过
if [ -z "$tool_name" ]; then
  exit 0
fi

# Write 工具校验：检查文件路径
validate_write() {
  local file_path
  file_path=$(echo "$tool_input" | jq -r '.file_path // ""')

  if [ -z "$file_path" ]; then
    exit 0
  fi

  # 允许 .claude/ 下的路径（计划文件、检查点等）
  if echo "$file_path" | grep -qE '\.claude/'; then
    exit 0
  fi

  # 允许项目源代码路径（plugins/tools/task/ 下）
  if echo "$file_path" | grep -qE 'plugins/tools/task/'; then
    exit 0
  fi

  # 拒绝系统路径
  if echo "$file_path" | grep -qE '^/(etc|usr|bin|sbin|var|tmp|root)/'; then
    echo "{\"hookSpecificOutput\":{\"permissionDecision\":\"deny\"},\"systemMessage\":\"[Hook·PreToolUse] Write 被拒绝：系统路径 '$file_path' 不在允许范围内\"}" >&2
    exit 2
  fi

  # 其他路径默认允许
  exit 0
}

# Bash 工具校验：检测危险命令
validate_bash() {
  local command_str
  command_str=$(echo "$tool_input" | jq -r '.command // ""')

  if [ -z "$command_str" ]; then
    exit 0
  fi

  # 检测危险命令模式
  if echo "$command_str" | grep -qE 'rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)?/($|\s)'; then
    echo '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"[Hook·PreToolUse] Bash 被拒绝：检测到危险的 rm 命令（可能删除根目录）"}' >&2
    exit 2
  fi

  if echo "$command_str" | grep -qE 'sudo\s+rm\s+-rf'; then
    echo '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"[Hook·PreToolUse] Bash 被拒绝：检测到 sudo rm -rf 危险命令"}' >&2
    exit 2
  fi

  if echo "$command_str" | grep -qE 'mkfs\.|format\s+[A-Z]:'; then
    echo '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"[Hook·PreToolUse] Bash 被拒绝：检测到格式化命令"}' >&2
    exit 2
  fi

  if echo "$command_str" | grep -qE '>\s*/dev/sd[a-z]|dd\s+.*of=/dev/'; then
    echo '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"[Hook·PreToolUse] Bash 被拒绝：检测到直接写入块设备的命令"}' >&2
    exit 2
  fi

  # 合法命令允许通过
  exit 0
}

# EnterPlanMode/ExitPlanMode 校验：Loop 活跃时禁止使用内置 Plan
validate_plan_mode() {
  local tasks_dir="${PWD}/.claude/tasks"
  if [ -d "$tasks_dir" ]; then
    while IFS= read -r meta_file; do
      phase_content=$(jq -r '.phase // ""' "$meta_file" 2>/dev/null || echo "")
      if [ -n "$phase_content" ] && [ "$phase_content" != "completed" ]; then
        echo "{\"hookSpecificOutput\":{\"permissionDecision\":\"deny\"},\"systemMessage\":\"[Hook·PreToolUse] ${tool_name} 被拒绝：检测到活跃的 Loop 流程，禁止使用内置 Plan 模式。必须使用 Skill(skill=\\\"task:planner\\\") 进行计划设计。\"}" >&2
        exit 2
      fi
    done < <(find "$tasks_dir" -name "metadata.json" -type f 2>/dev/null)
  fi
  exit 0
}

# 路由校验
case "$tool_name" in
  Write)            validate_write ;;
  Bash)             validate_bash ;;
  EnterPlanMode)    validate_plan_mode ;;
  ExitPlanMode)     validate_plan_mode ;;
  *)                exit 0 ;; # 其他工具跳过
esac
