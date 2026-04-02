#!/usr/bin/env bash
set -euo pipefail

# Task 插件输出校验脚本
# 用于 SubagentStop / PostToolUse hooks，校验 agent/skill 输出格式
#
# 输入: stdin JSON (hook input)
# 环境变量: VALIDATE_TYPE (planner|verifier|adjuster|finalizer|auto)
# 退出码: 0=合法, 2=校验失败(stderr反馈给Claude)

# 检查依赖命令
command -v jq >/dev/null 2>&1 || { echo "错误: jq 命令未安装" >&2; exit 1; }

input=$(cat)

# 从 hook input 中提取输出内容
# SubagentStop: reason 字段包含 agent 输出
# PostToolUse: tool_result 字段包含 skill 输出
hook_event=$(echo "$input" | jq -r '.hook_event_name // "unknown"')

if [ "$hook_event" = "SubagentStop" ]; then
  output=$(echo "$input" | jq -r '.reason // ""')
elif [ "$hook_event" = "PostToolUse" ]; then
  output=$(echo "$input" | jq -r '.tool_result // ""')
else
  output=$(echo "$input" | jq -r '.reason // .tool_result // ""')
fi

# 空输出直接通过（某些场景输出可能为空）
if [ -z "$output" ]; then
  exit 0
fi

# 尝试从输出中提取 JSON 块（输出可能包含非 JSON 前缀文本）
json_block=""
if echo "$output" | jq -e '.' >/dev/null 2>&1; then
  json_block="$output"
else
  # 尝试提取 ```json ... ``` 代码块中的 JSON
  extracted=$(echo "$output" | sed -n '/^```json/,/^```$/p' | sed '1d;$d')
  if [ -n "$extracted" ] && echo "$extracted" | jq -e '.' >/dev/null 2>&1; then
    json_block="$extracted"
  fi
fi

# 无法提取 JSON 则跳过校验（非结构化输出不校验）
if [ -z "$json_block" ]; then
  exit 0
fi

# 自动检测类型（基于 JSON 字段特征）
detect_type() {
  local json="$1"
  if echo "$json" | jq -e '.tasks' >/dev/null 2>&1 && echo "$json" | jq -e '.plan_md_path // .status' >/dev/null 2>&1; then
    echo "planner"
  elif echo "$json" | jq -e '.strategy' >/dev/null 2>&1; then
    echo "adjuster"
  elif echo "$json" | jq -e '.cleanup_summary' >/dev/null 2>&1; then
    echo "finalizer"
  elif echo "$json" | jq -e '.quality_score' >/dev/null 2>&1 || echo "$json" | jq -e '.stage1' >/dev/null 2>&1; then
    echo "verifier"
  else
    echo "unknown"
  fi
}

validate_type="${VALIDATE_TYPE:-auto}"
if [ "$validate_type" = "auto" ]; then
  validate_type=$(detect_type "$json_block")
fi

# 校验函数
validate_planner() {
  local json="$1"
  local status
  status=$(echo "$json" | jq -r '.status // ""')
  if [ -z "$status" ]; then
    echo '{"systemMessage": "[Hook·校验] planner 输出缺少 status 字段"}' >&2
    exit 2
  fi
  case "$status" in
    confirmed|rejected|no_tasks|cancelled) ;;
    *)
      echo "{\"systemMessage\": \"[Hook·校验] planner status 值非法: '$status'，合法值: confirmed/rejected/no_tasks/cancelled\"}" >&2
      exit 2
      ;;
  esac
}

validate_verifier() {
  local json="$1"
  local status
  status=$(echo "$json" | jq -r '.status // ""')
  if [ -z "$status" ]; then
    echo '{"systemMessage": "[Hook·校验] verifier 输出缺少 status 字段"}' >&2
    exit 2
  fi
  case "$status" in
    passed|failed) ;;
    *)
      echo "{\"systemMessage\": \"[Hook·校验] verifier status 值非法: '$status'，合法值: passed/failed\"}" >&2
      exit 2
      ;;
  esac
}

validate_adjuster() {
  local json="$1"
  local strategy
  strategy=$(echo "$json" | jq -r '.strategy // ""')
  if [ -z "$strategy" ]; then
    echo '{"systemMessage": "[Hook·校验] adjuster 输出缺少 strategy 字段"}' >&2
    exit 2
  fi
  case "$strategy" in
    retry|debug|replan|ask_user) ;;
    *)
      echo "{\"systemMessage\": \"[Hook·校验] adjuster strategy 值非法: '$strategy'，合法值: retry/debug/replan/ask_user\"}" >&2
      exit 2
      ;;
  esac
}

validate_finalizer() {
  local json="$1"
  local status
  status=$(echo "$json" | jq -r '.status // ""')
  if [ -z "$status" ]; then
    echo '{"systemMessage": "[Hook·校验] finalizer 输出缺少 status 字段"}' >&2
    exit 2
  fi
  case "$status" in
    completed|partially_completed|failed) ;;
    *)
      echo "{\"systemMessage\": \"[Hook·校验] finalizer status 值非法: '$status'，合法值: completed/partially_completed/failed\"}" >&2
      exit 2
      ;;
  esac
}

# 路由校验
case "$validate_type" in
  planner)   validate_planner "$json_block" ;;
  verifier)  validate_verifier "$json_block" ;;
  adjuster)  validate_adjuster "$json_block" ;;
  finalizer) validate_finalizer "$json_block" ;;
  unknown)   ;; # 未知类型跳过
  *)         ;; # 其他类型跳过
esac

exit 0
