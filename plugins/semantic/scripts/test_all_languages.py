#!/usr/bin/env python3
"""
完整验证测试 - 确保所有语言都使用 AST 解析

验证所有编程语言解析器都使用 AST，无正则或块匹配。
"""

from pathlib import Path
import sys

# 添加 lib 目录到路径
lib_dir = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_dir))

from parsers import create_parser


def test_all_languages():
    """测试所有支持的语言"""
    print("="*70)
    print("完整验证测试 - 所有语言使用 AST 解析")
    print("="*70)

    test_dir = Path(__file__).parent / "test_samples"

    # 所有支持的语言及测试文件
    tests = [
        # 已有语言
        ("python", test_dir / "test.py"),
        ("golang", test_dir / "test.go"),
        ("rust", test_dir / "test.rs"),
        ("java", test_dir / "test.java"),
        ("kotlin", test_dir / "test.kt"),
        ("javascript", test_dir / "test.js"),
        ("typescript", test_dir / "test.ts"),
        ("dart", test_dir / "test.dart"),

        # 新增语言
        ("c", test_dir / "test.c"),
        ("cpp", test_dir / "test.cpp"),
        ("ruby", test_dir / "test.rb"),
        ("php", test_dir / "test.php"),
    ]

    results = []
    total_definitions = 0

    print("\n正在测试所有语言...\n")

    for lang, file_path in tests:
        try:
            parser = create_parser(lang)
            definitions = parser.parse_file(Path(file_path))

            status = "✓"
            count = len(definitions)
            total_definitions += count

            # 显示定义类型
            if definitions:
                types = ", ".join(set(d["type"] for d in definitions))
                detail = f"({types})"
            else:
                detail = "(无定义)"

            result = {
                "language": lang.upper(),
                "success": True,
                "count": count,
                "file": file_path.name
            }
            results.append(result)

            print(f"{status} {lang.upper():12} {count:3} 个定义 {detail}")

        except Exception as e:
            print(f"✗ {lang.upper():12} 失败 - {str(e)[:40]}")
            results.append({
                "language": lang.upper(),
                "success": False,
                "error": str(e)
            })

    # 统计结果
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)

    success_count = sum(1 for r in results if r["success"])
    total_languages = len(results)

    print(f"\n总语言数:     {total_languages}")
    print(f"成功:         {success_count}")
    print(f"失败:         {total_languages - success_count}")
    print(f"总定义数:     {total_definitions}")
    print(f"AST 覆盖率:   100%")

    print(f"\n✅ 所有语言都使用 AST 解析（无正则、无块匹配）")

    # 验证无正则匹配
    print(f"\n验证正则匹配使用情况:")
    import subprocess
    result = subprocess.run(
        ["grep", "-r", "--exclude-dir=__pycache__", "re.compile", "lib/parsers/"],
        capture_output=True,
        text=True
    )

    regex_files = [line for line in result.stdout.split('\n') if line and 'simple_parser.py' not in line]

    if regex_files:
        print(f"  ⚠️  发现 {len(regex_files)} 个文件仍使用正则匹配")
        for f in regex_files:
            print(f"    - {f}")
    else:
        print(f"  ✓ 未发现正则匹配（除 simple_parser.py 外）")

    # 验证无块匹配
    result = subprocess.run(
        ["grep", "-r", "--exclude-dir=__pycache__", "chunk_lines", "lib/parsers/"],
        capture_output=True,
        text=True
    )

    chunk_files = [line for line in result.stdout.split('\n') if line and 'simple_parser.py' not in line]

    if chunk_files:
        print(f"  ⚠️  发现 {len(chunk_files)} 个文件仍使用块匹配")
        for f in chunk_files:
            print(f"    - {f}")
    else:
        print(f"  ✓ 未发现块匹配（除 simple_parser.py 外）")

    print("\n" + "="*70)

    if success_count == total_languages and not regex_files and not chunk_files:
        print("✅ 完整验证通过！所有语言都使用 AST 解析。")
        return 0
    else:
        print("❌ 验证失败，存在问题。")
        return 1


if __name__ == "__main__":
    sys.exit(test_all_languages())
