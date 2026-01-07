#!/usr/bin/env python3
"""
测试配置文件加载和相似度阈值功能
"""

from pathlib import Path
import sys
import yaml

# 添加 lib 目录到路径
lib_dir = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_dir))


def test_config_loading():
    """测试配置加载"""
    print("="*60)
    print("测试配置文件加载")
    print("="*60)

    # 查找配置文件
    config_paths = [
        Path.home() / ".lazygophers" / "ccplugin" / "semantic" / "config.yaml",
        Path(__file__).parent.parent / ".lazygophers" / "ccplugin" / "semantic" / "config.yaml",
    ]

    config_path = None
    for path in config_paths:
        if path.exists():
            config_path = path
            break

    if not config_path:
        print("❌ 未找到配置文件")
        print(f"   查找路径:")
        for path in config_paths:
            print(f"   - {path}")
        return False

    print(f"✓ 找到配置文件: {config_path}\n")

    # 加载配置
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        print("配置文件内容（部分）:")
        print(f"  backend: {config_data.get('backend')}")
        print(f"  embedding_model: {config_data.get('embedding_model')}")
        print(f"  chunk_size: {config_data.get('chunk_size')}")
        print()

    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        return False

    # 测试相似度阈值
    print("测试相似度阈值配置:")
    print("-" * 60)

    threshold = config_data.get("similarity_threshold")

    if threshold is None:
        print("❌ 未找到 similarity_threshold 配置项")
        print("   提示: 请在配置文件中添加 'similarity_threshold: 0.7'")
        return False

    print(f"✓ similarity_threshold = {threshold}")
    print()

    # 验证阈值范围
    if not (0.0 <= threshold <= 1.0):
        print(f"❌ 相似度阈值超出有效范围: {threshold}")
        print("   有效范围: 0.0 - 1.0")
        return False

    print(f"✓ 阈值在有效范围内: 0.0 - 1.0")
    print()

    # 显示不同阈值的效果
    print("不同阈值的过滤效果:")
    print("-" * 60)

    test_similarities = [0.95, 0.85, 0.75, 0.68, 0.55, 0.42]

    filtered = [s for s in test_similarities if s >= threshold]
    filtered_out = [s for s in test_similarities if s < threshold]

    print(f"测试相似度值: {test_similarities}")
    print(f"阈值 {threshold}:")
    print(f"  ✓ 保留 ({len(filtered)} 个): {filtered}")
    print(f"  ✗ 过滤 ({len(filtered_out)} 个): {filtered_out}")
    print()

    # 推荐配置
    print("推荐配置:")
    print("-" * 60)
    recommendations = {
        0.5: "较宽松，会返回更多结果但可能包含不相关内容",
        0.6: "初次探索/广泛搜索",
        0.7: "日常使用（默认），平衡准确度和召回率",
        0.8: "精确查找，只返回高度相关的结果",
        0.9: "非常严格，可能错过部分相关结果",
    }

    current_rec = recommendations.get(threshold, "自定义值")
    print(f"当前阈值 {threshold}: {current_rec}")
    print()

    print("其他推荐配置:")
    for val, desc in recommendations.items():
        if val != threshold:
            print(f"  {val}: {desc}")
    print()

    # 测试结果
    print("="*60)
    print("✅ 配置加载测试通过！")
    print()
    print("总结:")
    print(f"  - 配置文件路径: {config_path}")
    print(f"  - 相似度阈值: {threshold}")
    print(f"  - 推荐用途: {current_rec}")
    print("="*60)

    return True


def test_command_line_override():
    """测试命令行参数覆盖"""
    print("\n" + "="*60)
    print("命令行参数覆盖说明")
    print("="*60)
    print()
    print("即使配置文件中设置了 similarity_threshold，")
    print("您仍然可以通过命令行参数覆盖它：")
    print()
    print("  示例:")
    print("    /semantic search '查询' --threshold 0.8")
    print("    /semantic search '查询' -t 0.6")
    print()
    print("  这样会临时使用指定的阈值，不影响配置文件。")
    print("="*60)


if __name__ == "__main__":
    success = test_config_loading()

    if success:
        test_command_line_override()
        sys.exit(0)
    else:
        sys.exit(1)
