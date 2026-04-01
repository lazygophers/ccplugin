#!/usr/bin/env bash
set -euo pipefail

# Stop hook 校验脚本
# 基于状态文件判断是否允许停止，替代脆弱的文本匹配
#
# 输入: stdin JSON (hook input, 包含 reason 字段)
# 退出码: 0=允许停止, 2=阻止停止(stderr反馈给Claude)

command -v jq >/dev/null 2>&1 || { echo "错误: jq 命令未安装" >&2; exit 1; }

input=$(cat)
reason=$(echo "$input" | jq -r '.reason // ""')

# === 第一优先级：状态文件检查 ===
# 查找所有活跃的 loop-phase 文件
tasks_dir="${PWD}/.claude/tasks"
if [ -d "$tasks_dir" ]; then
  has_active=false
  while IFS= read -r phase_file; do
    phase_content=$(cat "$phase_file" 2>/dev/null | tr -d '[:space:]' || echo "")
    if [ "$phase_content" = "completed" ]; then
      continue  # 已完成的 loop，不阻止
    elif [ -n "$phase_content" ]; then
      has_active=true  # 发现活跃的 loop
      break
    fi
  done < <(find "$tasks_dir" -name "loop-phase" -type f 2>/dev/null)

  if [ "$has_active" = true ]; then
    # 用户取消仍然允许停止
    if echo "$reason" | grep -qiE "用户取消|cancelled|user.*cancel"; then
      exit 0
    fi
    echo '{"decision":"block","reason":"[MindFlow·Stop校验] 检测到活跃的 Loop 流程（状态文件非 completed），禁止提前终止。","systemMessage":"[Hook·Stop校验] Loop 流程尚未完成 Finalization。请继续执行直到 finalizer 清理完成并写入 completed 状态。"}' >&2
    exit 2
  fi
fi

# === 第二优先级：无状态文件时的文本匹配兜底 ===
# 用户取消
if echo "$reason" | grep -qiE "用户取消|cancelled|user.*cancel"; then
  exit 0
fi

# 收紧的 Finalization 完成标志（必须有 [MindFlow 前缀或明确的 finalizer 关键词）
if echo "$reason" | grep -qiE "\[MindFlow.*[Ff]inali[sz](ation|er).*完成\]|\[MindFlow.*✓.*完成\]|finalizer.*执行完成|finalizer.*清理完成|completed.*cleanup.*successfully"; then
  exit 0
fi

# 无状态文件且无完成标志 → 允许停止（可能不是 loop 场景）
exit 0
