#!/usr/bin/env python3
"""
诊断脚本：测试 Semantic 索引器的初始化
用法：
  cd /Users/luoxin/persons/lyxamour/ccplugin
  python3 test_semantic_init.py
"""

import sys
from pathlib import Path

# 添加脚本路径
script_path = Path("./plugins/semantic/scripts").resolve()
sys.path.insert(0, str(script_path))

print("=" * 60)
print("Semantic 索引器初始化诊断")
print("=" * 60)
print(f"\n脚本路径: {script_path}")
print(f"路径存在: {script_path.exists()}")

try:
    print("\n[1] 导入模块...")
    from lib.indexer import CodeIndexer
    from lib.config import load_config, get_data_path
    from lib.utils import check_and_auto_init
    print("✓ 所有模块导入成功")

    print("\n[2] 检查初始化状态...")
    result = check_and_auto_init(silent=True)
    print(f"✓ check_and_auto_init 返回: {result}")

    print("\n[3] 加载配置...")
    config = load_config()
    print(f"✓ 配置加载成功")
    print(f"  - 配置键数: {len(config)}")
    print(f"  - 后端: {config.get('backend', 'unknown')}")
    print(f"  - 嵌入模型: {config.get('embedding_model', 'unknown')}")

    print("\n[4] 获取数据路径...")
    data_path = get_data_path()
    print(f"✓ 数据路径: {data_path}")
    print(f"  - 路径存在: {data_path.exists()}")

    print("\n[5] 创建 CodeIndexer...")
    indexer = CodeIndexer(config, data_path)
    print("✓ CodeIndexer 创建成功")

    print("\n[6] 调用 indexer.initialize()...")
    result = indexer.initialize()
    print(f"✓ indexer.initialize() 返回: {result}")

    if result:
        print("\n✅ 所有初始化步骤成功!")
    else:
        print("\n⚠️ indexer.initialize() 返回 False")
        print("  这可能意味着存储或嵌入模型加载失败")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    print("\n错误详情:")
    print(traceback.format_exc())

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
