#!/usr/bin/env python3
"""为所有插件的 mcp 和 hooks 配置添加 PLUGIN_NAME 环境变量"""

import json
import os
import re
from pathlib import Path


def extract_plugin_name(file_path: str) -> str:
    """从文件路径中提取插件名称"""
    # 提取插件目录名（如 task, notify, version 等）
    path_parts = Path(file_path).parts
    plugins_idx = path_parts.index('plugins')
    # path_parts: [..., 'plugins', 'task', '.mcp.json'] 或 [..., 'plugins', 'code', 'semantic', ...]
    if path_parts[plugins_idx + 1] == 'code':
        # code/semantic, code/python 等
        return path_parts[plugins_idx + 2]
    else:
        # task, notify, version 等
        return path_parts[plugins_idx + 1]


def update_mcp_json(file_path: str) -> None:
    """更新 .mcp.json 文件，添加 PLUGIN_NAME 环境变量"""
    plugin_name = extract_plugin_name(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 为每个 mcpServer 添加 PLUGIN_NAME 环境变量
    for server_name, server_config in data.get('mcpServers', {}).items():
        if 'env' not in server_config:
            server_config['env'] = {}
        server_config['env']['PLUGIN_NAME'] = plugin_name

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')  # 添加末尾换行

    print(f"✓ 更新 {file_path} (PLUGIN_NAME={plugin_name})")


def update_hooks_json(file_path: str) -> None:
    """更新 hooks.json 文件，在命令中添加 PLUGIN_NAME 环境变量"""
    plugin_name = extract_plugin_name(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 为所有 hook 命令添加环境变量前缀
    for hook_type, hook_list in data.get('hooks', {}).items():
        for hook_group in hook_list:
            for hook in hook_group.get('hooks', []):
                if 'command' in hook:
                    command = hook['command']
                    # 检查是否已经有 PLUGIN_NAME
                    if 'PLUGIN_NAME' not in command:
                        # 在命令前添加环境变量
                        hook['command'] = f"PLUGIN_NAME={plugin_name} {command}"

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print(f"✓ 更新 {file_path} (PLUGIN_NAME={plugin_name})")


def main():
    """主函数"""
    # 查找所有需要更新的文件
    plugin_dir = Path(__file__).parent.parent / 'plugins'

    mcp_files = list(plugin_dir.rglob('.mcp.json'))
    # 排除 .venv 目录
    mcp_files = [f for f in mcp_files if '.venv' not in str(f)]

    hooks_files = list(plugin_dir.rglob('hooks.json'))
    # 排除 .venv 目录
    hooks_files = [f for f in hooks_files if '.venv' not in str(f)]

    print(f"找到 {len(mcp_files)} 个 .mcp.json 文件")
    print(f"找到 {len(hooks_files)} 个 hooks.json 文件")
    print()

    # 更新 .mcp.json 文件
    print("=== 更新 .mcp.json 文件 ===")
    for mcp_file in mcp_files:
        update_mcp_json(str(mcp_file))

    print()

    # 更新 hooks.json 文件
    print("=== 更新 hooks.json 文件 ===")
    for hooks_file in hooks_files:
        update_hooks_json(str(hooks_file))

    print()
    print("✅ 所有配置文件已更新完成！")


if __name__ == '__main__':
    main()
