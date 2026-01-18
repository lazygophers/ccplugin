#!/usr/bin/env python3
"""
Notify 插件主脚本测试

测试notify.py的各种运行模式
"""

import sys
import json
import subprocess
from pathlib import Path

# 获取项目根目录
script_path = Path(__file__).resolve().parent
plugin_path = script_path.parent
project_root = plugin_path.parent.parent


def run_notify_command(args: list) -> int:
    """
    运行notify脚本并返回退出码

    Args:
        args: 命令行参数列表

    Returns:
        int: 脚本的退出码
    """
    cmd = ["uv", "run", str(script_path / "notify.py")] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"✗ 命令超时: {' '.join(args)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ 执行错误: {e}", file=sys.stderr)
        return 1


def test_help() -> bool:
    """测试帮助信息"""
    print("测试帮助信息...")
    exit_code = run_notify_command(["-h"])
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} 帮助信息: {exit_code}")
    return success


def test_no_args() -> bool:
    """测试不带参数运行"""
    print("测试不带参数运行...")
    exit_code = run_notify_command([])
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} 不带参数: {exit_code}")
    return success


def test_notify_basic() -> bool:
    """测试基础通知功能"""
    print("测试基础通知功能...")
    exit_code = run_notify_command(["测试消息"])
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} 基础通知: {exit_code}")
    return success


def test_notify_with_title() -> bool:
    """测试带标题的通知"""
    print("测试带标题的通知...")
    exit_code = run_notify_command(["测试消息", "测试标题"])
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} 带标题通知: {exit_code}")
    return success


def test_notify_with_timeout() -> bool:
    """测试带超时时间的通知"""
    print("测试带超时时间的通知...")
    exit_code = run_notify_command(["测试消息", "标题", "3000"])
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} 带超时通知: {exit_code}")
    return success


def test_init_mode() -> bool:
    """测试初始化模式"""
    print("测试初始化模式...")
    exit_code = run_notify_command(["--mode", "init"])
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} 初始化模式: {exit_code}")
    return success


def test_hook_mode() -> bool:
    """测试hook模式"""
    print("测试hook模式...")
    hook_input = {
        "session_id": "test-session",
        "hook_event_name": "Stop",
        "transcript_path": "/tmp/test.jsonl",
        "permission_mode": "default",
        "stop_hook_active": False
    }

    cmd = ["uv", "run", str(script_path / "notify.py"), "--mode", "hook", "--hook-event", "Stop"]
    try:
        result = subprocess.run(
            cmd,
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            timeout=10
        )
        success = result.returncode in (0, 1)  # Hook可以返回0或1
        print(f"  {'✓' if success else '✗'} Hook模式: {result.returncode}")
        return success
    except Exception as e:
        print(f"  ✗ Hook模式异常: {e}", file=sys.stderr)
        return False


def main():
    """运行所有测试"""
    print("=" * 50)
    print("Notify 插件测试套件")
    print("=" * 50)
    print()

    test_cases = [
        ("帮助信息", test_help),
        ("不带参数", test_no_args),
        ("基础通知", test_notify_basic),
        ("带标题通知", test_notify_with_title),
        ("带超时通知", test_notify_with_timeout),
        ("初始化模式", test_init_mode),
        ("Hook模式", test_hook_mode),
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
