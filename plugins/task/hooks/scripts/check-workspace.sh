#!/bin/bash
# Task Plugin - Session Start Hook
# 自动初始化工作空间（如果未初始化）

set -e

# 获取当前工作目录
WORKSPACE_ROOT="${PWD}"
TASK_DATA_DIR="${WORKSPACE_ROOT}/.task_data"

# 检查是否存在 .task_data 目录
if [ ! -d "${TASK_DATA_DIR}" ]; then
    echo "🚀 Task Plugin 自动初始化工作空间..."

    # 调用初始化脚本（静默模式）
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

    # 使用 Python 调用工作空间初始化
    cd "${PLUGIN_ROOT}"
    uv run python -c "
from task.workspace import WorkspaceManager
import os
workspace = WorkspaceManager('${WORKSPACE_ROOT}', auto_init=True)
print('✅ 工作空间初始化完成')
print(f'📁 数据库: {workspace.get_workspace_info()[\"database_path\"]}')
" 2>/dev/null || echo "⚠️ 初始化失败，请手动运行: workspace_init"

    exit 0
fi

# 已初始化，静默通过
exit 0
