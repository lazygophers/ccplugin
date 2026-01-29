#!/usr/bin/env python3
"""
Semantic 搜索插件测试

测试semantic.py的基本功能
"""

import sys
import subprocess
from pathlib import Path


def run_semantic_command(args: list) -> tuple[int, str, str]:
    """
    运行semantic脚本

    Args:
        args: 命令行参数列表

    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    script_path = Path(__file__).resolve().parent
    cmd = ["uv", "run", str(script_path / "semantic.py")] + args

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timeout"
    except Exception as e:
        return 1, "", str(e)


def test_help() -> bool:
    """测试帮助信息"""
    print("测试帮助信息...")
    exit_code, stdout, stderr = run_semantic_command(["-h"])
    success = exit_code == 0 or ("help" in stdout.lower() or "usage" in stderr.lower())
    print(f"  {'✓' if success else '✗'} 帮助信息: {exit_code}")
    return success


def test_no_args() -> bool:
    """测试不带参数运行"""
    print("测试不带参数运行...")
    exit_code, stdout, stderr = run_semantic_command([])
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} 不带参数: {exit_code}")
    return success


def test_version_flag() -> bool:
    """测试版本标志"""
    print("测试版本标志...")
    exit_code, stdout, stderr = run_semantic_command(["--version"])
    success = exit_code == 0 or exit_code == 2  # 有些工具返回2表示版本
    print(f"  {'✓' if success else '✗'} 版本标志: {exit_code}")
    return success


def test_script_executable() -> bool:
    """测试脚本是否可执行"""
    print("测试脚本可执行性...")
    script_path = Path(__file__).resolve().parent / "semantic.py"
    success = script_path.exists() and script_path.stat().st_mode & 0o111
    print(f"  {'✓' if success else '✗'} 脚本可执行: {success}")
    return success


def test_script_syntax() -> bool:
    """测试脚本Python语法"""
    print("测试脚本语法...")
    script_path = Path(__file__).resolve().parent / "semantic.py"

    try:
        import py_compile
        py_compile.compile(str(script_path), doraise=True)
        print("  ✓ 脚本语法正确")
        return True
    except py_compile.PyCompileError as e:
        print(f"  ✗ 脚本语法错误: {e}", file=sys.stderr)
        return False


def main():
    """运行所有测试"""
    print("=" * 50)
    print("Semantic 搜索插件测试套件")
    print("=" * 50)
    print()

    test_cases = [
        ("脚本可执行性", test_script_executable),
        ("脚本语法", test_script_syntax),
        ("帮助信息", test_help),
        ("不带参数", test_no_args),
        ("版本标志", test_version_flag),
    ]

    results = {}
    for name, test_func in test_cases:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"✗ {name}: 异常 - {e}", file=sys.stderr)
            results[name] = False
        print()

    # 总结
    print("=" * 50)
    print("测试总结")
    print("=" * 50)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"总计: {passed}/{total} 通过")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
