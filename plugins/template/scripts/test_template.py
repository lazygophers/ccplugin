#!/usr/bin/env python3
"""
Template 模板插件测试

测试example.py的基本功能
"""

import sys
import subprocess
from pathlib import Path


def run_example_command(args: list) -> tuple[int, str, str]:
    """
    运行example脚本

    Args:
        args: 命令行参数列表

    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    script_path = Path(__file__).resolve().parent
    cmd = ["uv", "run", str(script_path / "example.py")] + args

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timeout"
    except Exception as e:
        return 1, "", str(e)


def test_with_stdin() -> bool:
    """测试从stdin读取"""
    print("测试从stdin读取...")
    cmd = [
        "uv", "run",
        str(Path(__file__).resolve().parent / "example.py"),
        "-"
    ]
    try:
        result = subprocess.run(
            cmd,
            input="test data",
            capture_output=True,
            text=True,
            timeout=10
        )
        success = result.returncode == 0 or "[1]" in result.stdout
        print(f"  {'✓' if success else '✗'} stdin处理: {result.returncode}")
        return success
    except Exception as e:
        print(f"  ✗ stdin处理异常: {e}", file=sys.stderr)
        return False


def test_no_args() -> bool:
    """测试不带参数运行"""
    print("测试不带参数运行...")
    exit_code, stdout, stderr = run_example_command([])
    # example.py不带参数时返回1且显示usage
    success = (exit_code == 1) and ("Usage" in stdout)
    print(f"  {'✓' if success else '✗'} 不带参数: {exit_code}")
    return success


def test_script_executable() -> bool:
    """测试脚本是否可执行"""
    print("测试脚本可执行性...")
    script_path = Path(__file__).resolve().parent / "example.py"
    success = script_path.exists() and script_path.stat().st_mode & 0o111
    print(f"  {'✓' if success else '✗'} 脚本可执行: {success}")
    return success


def test_script_syntax() -> bool:
    """测试脚本Python语法"""
    print("测试脚本语法...")
    script_path = Path(__file__).resolve().parent / "example.py"

    try:
        import py_compile
        py_compile.compile(str(script_path), doraise=True)
        print(f"  ✓ 脚本语法正确")
        return True
    except py_compile.PyCompileError as e:
        print(f"  ✗ 脚本语法错误: {e}", file=sys.stderr)
        return False


def main():
    """运行所有测试"""
    print("=" * 50)
    print("Template 模板插件测试套件")
    print("=" * 50)
    print()

    test_cases = [
        ("脚本可执行性", test_script_executable),
        ("脚本语法", test_script_syntax),
        ("stdin处理", test_with_stdin),
        ("不带参数", test_no_args),
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
