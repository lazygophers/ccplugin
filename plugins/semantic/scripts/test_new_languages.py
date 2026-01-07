#!/usr/bin/env python3
"""
测试新语言解析器

验证 C, C++, Ruby, PHP 的 AST 解析功能。
"""

from pathlib import Path
import sys

# 添加 lib 目录到路径
lib_dir = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_dir))

from parsers import create_parser


def test_language(language: str, file_path: str) -> dict:
    """测试单个语言"""
    print(f"\n{'='*60}")
    print(f"测试 {language.upper()}")
    print(f"{'='*60}")

    try:
        parser = create_parser(language)
        results = parser.parse_file(Path(file_path))

        print(f"✓ 解析成功")
        print(f"  文件: {file_path}")
        print(f"  提取定义数: {len(results)}")

        if results:
            print(f"\n  提取的定义:")
            for i, result in enumerate(results, 1):
                print(f"    {i}. {result['type']}: {result['name']} " +
                      f"(行 {result['start_line']}-{result['end_line']})")
        else:
            print(f"  ⚠️  警告: 未提取到任何定义")

        return {
            "language": language,
            "success": True,
            "count": len(results),
            "definitions": results
        }

    except Exception as e:
        print(f"✗ 解析失败: {e}")
        return {
            "language": language,
            "success": False,
            "error": str(e)
        }


def main():
    """主测试函数"""
    print("="*60)
    print("新语言解析器验证测试")
    print("="*60)

    test_dir = Path(__file__).parent / "test_samples"

    tests = [
        ("c", test_dir / "test.c"),
        ("cpp", test_dir / "test.cpp"),
        ("ruby", test_dir / "test.rb"),
        ("php", test_dir / "test.php"),
    ]

    results = []
    for lang, file_path in tests:
        if file_path.exists():
            result = test_language(lang, file_path)
            results.append(result)
        else:
            print(f"\n✗ 测试文件不存在: {file_path}")
            results.append({
                "language": lang,
                "success": False,
                "error": "测试文件不存在"
            })

    # 汇总结果
    print(f"\n\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")

    success_count = sum(1 for r in results if r["success"])
    total_definitions = sum(r.get("count", 0) for r in results)

    print(f"\n总语言数: {len(results)}")
    print(f"成功: {success_count}")
    print(f"失败: {len(results) - success_count}")
    print(f"总定义数: {total_definitions}")

    print(f"\n详细结果:")
    for result in results:
        status = "✓" if result["success"] else "✗"
        count = result.get("count", 0)
        print(f"  {status} {result['language'].upper():10} - " +
              f"{count} 个定义")

    if success_count == len(results):
        print(f"\n✓ 所有新语言解析器工作正常！")
        return 0
    else:
        print(f"\n✗ 部分语言解析器存在问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())
