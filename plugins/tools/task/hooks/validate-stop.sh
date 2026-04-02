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
  found_any=false
  while IFS= read -r phase_file; do
    found_any=true
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
    echo '{"decision":"block","reason":"[MindFlow·Stop校验] 检测到活跃的 Loop 流程（状态文件非 completed），禁止提前终止。","systemMessage":"[Hook·Stop校验] Loop 流程尚未完成 Cleanup。请继续执行直到 finalizer 清理完成并写入 completed 状态。"}' >&2
    exit 2
  fi

  # 找到了 loop-phase 文件且全部为 completed → 允许停止
  if [ "$found_any" = true ]; then
    exit 0
  fi
fi

# === 第二优先级：无状态文件时的文本匹配兜底 ===
# 用户取消
if echo "$reason" | grep -qiE "用户取消|cancelled|user.*cancel"; then
  exit 0
fi

# 收紧的 Cleanup 完成标志（必须有 [MindFlow 前缀或明确的 finalizer/cleanup 关键词）
if echo "$reason" | grep -qiE "\[MindFlow.*(Cleanup|[Ff]inali[sz](ation|er)).*完成\]|\[MindFlow.*✓.*完成\]|finalizer.*执行完成|finalizer.*清理完成|cleanup.*完成|completed.*cleanup.*successfully"; then
  exit 0
fi

# 无状态文件且无完成标志 → task:loop hook 场景，默认阻止停止
# 此 hook 仅注册在 task:loop skill 上，触发即代表 Loop 场景
echo '{"decision":"block","reason":"[MindFlow·Stop校验] 未检测到 loop-phase 状态文件或完成标志","systemMessage":"[Hook·Stop校验] Loop 尚未完成 Finalization，禁止停止。根据当前阶段继续执行：\n- Planner 已返回 confirmed → 立即进入 Execution（读取计划文件，调度任务）\n- Execution 已完成 → 立即调用 Skill(task:verifier)\n- Verifier 已返回 passed → 立即调用 Skill(task:finalizer)\n- Finalizer 已完成 → echo completed > .claude/tasks/{task_id}/loop-phase 后可结束"}' >&2
exit 2
