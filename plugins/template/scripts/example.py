#!/usr/bin/env python3
"""
示例 Python 脚本

用于复杂逻辑、数据处理、API 调用等场景。
"""

import sys
import json
import os
from pathlib import Path


def main():
    """主函数"""
    # 获取插件根目录
    plugin_root = Path(os.environ.get('CLAUDE_PLUGIN_ROOT', '.'))

    # 示例：处理输入数据
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        print(f"Processing: {input_file}")

        # 读取文件
        if input_file == '-':
            data = sys.stdin.read()
        else:
            with open(input_file) as f:
                data = f.read()

        # 处理数据（示例：JSON 解析）
        try:
            obj = json.loads(data)
            result = process_data(obj)
            print(json.dumps(result, indent=2))
        except json.JSONDecodeError:
            result = process_text(data)
            print(result)
    else:
        # 无参数时显示帮助
        print("Usage: example.py [input-file|-]")
        print("  input-file: 处理指定文件")
        print("  -: 从 stdin 读取")
        sys.exit(1)


def process_data(data):
    """处理 JSON 数据"""
    # 在这里添加你的处理逻辑
    if isinstance(data, dict):
        return {**data, "processed": True}
    elif isinstance(data, list):
        return [process_data(item) for item in data]
    else:
        return data


def process_text(text):
    """处理文本数据"""
    # 在这里添加你的文本处理逻辑
    lines = text.strip().split('\n')
    return '\n'.join(f"[{i+1}] {line}" for i, line in enumerate(lines))


if __name__ == "__main__":
    main()
