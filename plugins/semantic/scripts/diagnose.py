#!/usr/bin/env python3
"""
诊断 Semantic 搜索问题
"""

from pathlib import Path
import sys

# 添加 lib 目录到路径
lib_dir = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_dir))

def get_data_path():
    """获取数据路径"""
    # 优先使用项目本地路径
    local_path = Path.cwd() / ".lazygophers" / "ccplugin" / "semantic"
    if local_path.exists():
        return local_path

    # 其次使用用户主目录
    home_path = Path.home() / ".lazygophers" / "ccplugin" / "semantic"
    if home_path.exists():
        return home_path

    return None

def check_index_status():
    """检查索引状态"""
    print("="*70)
    print("Semantic 诊断工具")
    print("="*70)
    print()

    # 1. 检查数据路径
    data_path = get_data_path()
    print("1. 数据路径检查")
    print("-"*70)
    if data_path:
        print(f"✓ 找到数据路径: {data_path}")
    else:
        print("✗ 未找到数据路径")
        print("  提示: 请先运行初始化命令")
        return

    # 2. 检查索引文件
    print("\n2. 索引文件检查")
    print("-"*70)

    lancedb_path = data_path / "lancedb" / "code_index"
    symbols_db = data_path / "symbols.db"

    if lancedb_path.exists():
        print(f"✓ LanceDB 索引存在: {lancedb_path}")
    else:
        print(f"✗ LanceDB 索引不存在: {lancedb_path}")

    if symbols_db.exists():
        print(f"✓ 符号索引存在: {symbols_db}")
    else:
        print(f"✗ 符号索引不存在: {symbols_db}")

    # 3. 检查配置文件
    print("\n3. 配置文件检查")
    print("-"*70)

    import yaml

    config_file = data_path / "config.yaml"
    if config_file.exists():
        print(f"✓ 配置文件存在: {config_file}")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            threshold = config.get('similarity_threshold', 0.7)
            strategy = config.get('search_strategy', 'fast')

            print(f"  - 相似度阈值: {threshold}")
            print(f"  - 搜索策略: {strategy}")
        except Exception as e:
            print(f"✗ 读取配置文件失败: {e}")
    else:
        print(f"✗ 配置文件不存在: {config_file}")

    # 4. 统计索引数据
    print("\n4. 索引数据统计")
    print("-"*70)

    try:
        from lib.storage import LanceDBStorage

        storage = LanceDBStorage(data_path)
        stats = storage.get_stats()

        total_chunks = stats.get('total_chunks', 0)
        languages = stats.get('languages', {})

        print(f"总代码块数: {total_chunks}")

        if languages:
            print(f"语言分布:")
            for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {lang}: {count} 个代码块")
        else:
            print("  未找到语言分布数据")

        storage.close()

    except Exception as e:
        print(f"✗ 读取索引统计失败: {e}")

    # 5. 建议
    print("\n5. 诊断建议")
    print("-"*70)

    if not lancedb_path.exists():
        print("✗ 索引未建立，请运行:")
        print("  /semantic init    # 初始化")
        print("  /semantic-index   # 建立索引")

    elif total_chunks == 0:
        print("✗ 索引为空，请运行:")
        print("  /semantic-index   # 重建索引")

    else:
        print("✓ 索引状态良好")
        print()
        print("搜索建议:")
        print("  1. 尝试降低相似度阈值:")
        print("     /semantic-search '用户登录' --threshold 0.5")
        print()
        print("  2. 尝试不同的关键词:")
        print("     /semantic-search 'login'")
        print("     /semantic-search 'authenticate'")
        print("     /semantic-search 'user'")
        print()
        print("  3. 查看索引的内容:")
        print(f"     总代码块: {total_chunks}")

    print()
    print("="*70)


if __name__ == "__main__":
    check_index_status()
