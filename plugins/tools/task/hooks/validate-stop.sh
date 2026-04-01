#!/usr/bin/env bash
set -euo pipefail

# Stop hook 校验脚本
# 用于 loop skill 的 Stop hook，防止在 Finalization 完成前提前终止
#
# 输入: stdin JSON (hook input, 包含 reason 字段)
# 退出码: 0=允许停止, 2=阻止停止(stderr反馈给Claude)

command -v jq >/dev/null 2>&1 || { echo "错误: jq 命令未安装" >&2; exit 1; }

input=$(cat)

reason=$(echo "$input" | jq -r '.reason // ""')

# 空 reason 时跳过校验
if [ -z "$reason" ]; then
  exit 0
fi

# 检查是否包含 Finalization 完成的标志
# MindFlow loop 在 Finalization 完成后会包含这些关键词
if echo "$reason" | grep -qiE "finali[sz](ation|er).*完成|finalizer.*执行完|任务完成|✓.*完成|completed.*cleanup|cleanup.*completed"; then
  exit 0
fi

# 检查是否包含用户取消的标志（用户主动取消应允许停止）
if echo "$reason" | grep -qiE "用户取消|cancelled|user.*cancel"; then
  exit 0
fi

# 检查是否包含明确的阶段完成标志
if echo "$reason" | grep -qiE "\[MindFlow.*Finalization.*完成\]|\[MindFlow.*完成清理.*完成\]"; then
  exit 0
fi

# 未检测到 Finalization 完成标志，阻止停止
echo '{"decision":"block","reason":"[MindFlow·Stop校验] Finalization 阶段未完成，禁止提前终止。请确保 finalizer 清理完成后再停止。","systemMessage":"[Hook·Stop校验] 检测到提前终止尝试。MindFlow loop 铁律要求必须完成 Finalization 阶段才能停止。请继续执行直到 finalizer 清理完成。"}' >&2
exit 2
