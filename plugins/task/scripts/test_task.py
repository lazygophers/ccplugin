#!/usr/bin/env python3
"""
Task 插件测试脚本

测试init_task_system.py初始化功能
"""

import sys
import subprocess
from pathlib import Path

# 获取项目根目录
script_path = Path(__file__).resolve().parent


def run_task_init() -> int:
    """
    运行task初始化脚本

    Returns:
        int: 脚本的退出码
    """
    cmd = ["uv", "run", str(script_path / "init_task_system.py")]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode
    except subprocess.TimeoutExpired:
        print("✗ 初始化超时", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ 执行错误: {e}", file=sys.stderr)
        return 1


def test_init_creates_directories() -> bool:
    """测试初始化是否创建目录结构"""
    print("测试目录结构创建...")

    # 运行初始化
    exit_code = run_task_init()
    success = exit_code == 0

    # 检查必要的目录是否被创建
    if success:
        # 任务目录在项目根目录中创建
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        task_dir = project_root / ".claude" / "task"
        archive_dir = task_dir / "archive"

        # 验证目录存在
        dirs_exist = task_dir.exists() and archive_dir.exists()
        success = success and dirs_exist

        if not dirs_exist:
            print(f"  ✗ 目录创建失败 (task_dir: {task_dir.exists()}, archive_dir: {archive_dir.exists()})")
        else:
            print("  ✓ 目录结构正确")

    print(f"  {'✓' if success else '✗'} 初始化: {exit_code}")
    return success


def test_init_creates_files() -> bool:
    """测试初始化是否创建文件"""
    print("测试文件创建...")

    # 运行初始化
    exit_code = run_task_init()
    success = exit_code == 0

    if success:
        # 任务目录在项目根目录中创建
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        task_dir = project_root / ".claude" / "task"

        # 检查必需的文件
        required_files = [
            task_dir / "todo.md",
            task_dir / "in-progress.md",
            task_dir / "done.md",
            task_dir / "archive" / "README.md",
        ]
        files_exist = all(f.exists() for f in required_files)
        success = success and files_exist

        if not files_exist:
            missing = [f.name for f in required_files if not f.exists()]
            print(f"  ✗ 文件未创建: {missing}")
        else:
            print("  ✓ 初始文件正确")

    print(f"  {'✓' if success else '✗'} 文件创建: {exit_code}")
    return success


def test_init_idempotent() -> bool:
    """测试初始化是否幂等（多次运行结果一致）"""
    print("测试初始化幂等性...")

    # 运行初始化两次
    exit_code1 = run_task_init()
    exit_code2 = run_task_init()

    success = exit_code1 == 0 and exit_code2 == 0
    print(f"  {'✓' if success else '✗'} 幂等性: {exit_code1}, {exit_code2}")
    return success


def main():
    """运行所有测试"""
    print("=" * 50)
    print("Task 插件测试套件")
    print("=" * 50)
    print()

    test_cases = [
        ("目录创建", test_init_creates_directories),
        ("文件创建", test_init_creates_files),
        ("幂等性", test_init_idempotent),
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
