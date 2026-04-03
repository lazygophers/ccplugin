#!/usr/bin/env bash
set -euo pipefail

# Task 插件输出校验脚本
# 用于 SubagentStop hooks，校验 agent 是否已将结果写入 metadata.json
#
# 输入: stdin JSON (hook input)
# 环境变量: VALIDATE_TYPE (planner|verifier|adjuster|finalizer|auto)
# 退出码: 0=合法, 2=校验失败(stderr反馈给Claude)

# 检查依赖命令
command -v jq >/dev/null 2>&1 || { echo "错误: jq 命令未安装" >&2; exit 1; }

input=$(cat)

# 查找当前任务的 metadata.json
# 扫描 .claude/tasks/*/metadata.json，找到 phase 非终态的文件
metadata_file=""
for f in .claude/tasks/*/metadata.json; do
  [ -f "$f" ] || continue
  phase=$(jq -r '.phase // ""' "$f" 2>/dev/null)
  case "$phase" in
    completed|failed) continue ;;
    *) metadata_file="$f"; break ;;
  esac
done

# 无活跃任务则跳过校验
if [ -z "$metadata_file" ]; then
  exit 0
fi

# 读取 metadata.json 的 result 字段
result=$(jq '.result // null' "$metadata_file" 2>/dev/null)

# result 为 null 说明 agent 未写入结果
if [ "$result" = "null" ] || [ -z "$result" ]; then
  validate_type="${VALIDATE_TYPE:-auto}"
  echo "{\"systemMessage\": \"[Hook·校验] ${validate_type} 未将结果写入 metadata.json 的 result 字段。请更新 metadata.json 后再结束。\"}" >&2
  exit 2
fi

validate_type="${VALIDATE_TYPE:-auto}"

# 校验函数：验证 result 字段中的关键值
validate_planner() {
  local status
  status=$(jq -r '.result.status // ""' "$metadata_file")
  if [ -z "$status" ]; then
    echo '{"systemMessage": "[Hook·校验] metadata.json result 缺少 status 字段"}' >&2
    exit 2
  fi
  case "$status" in
    confirmed|rejected|no_tasks|cancelled) ;;
    *)
      echo "{\"systemMessage\": \"[Hook·校验] planner result.status 值非法: '$status'，合法值: confirmed/rejected/no_tasks/cancelled\"}" >&2
      exit 2
      ;;
  esac
}

validate_verifier() {
  local status
  status=$(jq -r '.result.status // ""' "$metadata_file")
  if [ -z "$status" ]; then
    echo '{"systemMessage": "[Hook·校验] metadata.json result 缺少 status 字段"}' >&2
    exit 2
  fi
  case "$status" in
    passed|failed) ;;
    *)
      echo "{\"systemMessage\": \"[Hook·校验] verifier result.status 值非法: '$status'，合法值: passed/failed\"}" >&2
      exit 2
      ;;
  esac
}

validate_adjuster() {
  local strategy
  strategy=$(jq -r '.result.strategy // ""' "$metadata_file")
  if [ -z "$strategy" ]; then
    echo '{"systemMessage": "[Hook·校验] metadata.json result 缺少 strategy 字段"}' >&2
    exit 2
  fi
  case "$strategy" in
    retry|debug|replan|ask_user) ;;
    *)
      echo "{\"systemMessage\": \"[Hook·校验] adjuster result.strategy 值非法: '$strategy'，合法值: retry/debug/replan/ask_user\"}" >&2
      exit 2
      ;;
  esac
}

validate_finalizer() {
  local status
  status=$(jq -r '.result.status // ""' "$metadata_file")
  if [ -z "$status" ]; then
    echo '{"systemMessage": "[Hook·校验] metadata.json result 缺少 status 字段"}' >&2
    exit 2
  fi
  case "$status" in
    completed|partially_completed|failed) ;;
    *)
      echo "{\"systemMessage\": \"[Hook·校验] finalizer result.status 值非法: '$status'，合法值: completed/partially_completed/failed\"}" >&2
      exit 2
      ;;
  esac
}

# 路由校验
case "$validate_type" in
  planner)   validate_planner ;;
  verifier)  validate_verifier ;;
  adjuster)  validate_adjuster ;;
  finalizer) validate_finalizer ;;
  *)         ;; # 未知类型跳过
esac

exit 0
