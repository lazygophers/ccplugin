#!/usr/bin/env python3
"""
通知插件 Hook 测试脚本

测试所有支持的 hook 事件：
- SessionStart, SessionEnd
- UserPromptSubmit
- PreToolUse, PostToolUse
- Notification
- Stop
- SubagentStop
- PreCompact
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# 获取项目根目录
script_path = Path(__file__).resolve().parent
plugin_path = script_path.parent
project_root = plugin_path.parent.parent


def run_hook(hook_event: str, hook_input: Optional[Dict[str, Any]] = None) -> int:
    """
    运行 notify.py 的 hook 模式
    
    Args:
        hook_event: Hook 事件名称
        hook_input: Hook 输入的 JSON 数据
    
    Returns:
        int: 返回码（0 表示成功）
    """
    cmd = [
        "uv", "run",
        str(script_path / "notify.py"),
        "--mode", "hook",
        "--hook-event", hook_event
    ]
    
    try:
        # 如果有 hook_input，通过 stdin 传入
        stdin_data = json.dumps(hook_input) if hook_input else None
        
        result = subprocess.run(
            cmd,
            input=stdin_data,
            text=True,
            capture_output=True,
            timeout=10
        )
        
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"✗ {hook_event}: 超时", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ {hook_event}: 执行错误 - {e}", file=sys.stderr)
        return 1


def test_session_start() -> bool:
    """测试 SessionStart hook"""
    print("测试 SessionStart hook...")
    hook_input = {
        "session_id": "test-session-001",
        "hook_event_name": "SessionStart",
        "timestamp": "2026-01-18T10:00:00Z"
    }
    exit_code = run_hook("SessionStart", hook_input)
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} SessionStart: {exit_code}")
    return success


def test_session_end() -> bool:
    """测试 SessionEnd hook"""
    print("测试 SessionEnd hook...")
    hook_input = {
        "session_id": "test-session-001",
        "hook_event_name": "SessionEnd",
        "reason": "normal",
        "timestamp": "2026-01-18T10:05:00Z"
    }
    exit_code = run_hook("SessionEnd", hook_input)
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} SessionEnd: {exit_code}")
    return success


def test_user_prompt_submit() -> bool:
    """测试 UserPromptSubmit hook"""
    print("测试 UserPromptSubmit hook...")
    hook_input = {
        "session_id": "test-session-001",
        "hook_event_name": "UserPromptSubmit",
        "prompt": "测试提示词",
        "timestamp": "2026-01-18T10:01:00Z"
    }
    exit_code = run_hook("UserPromptSubmit", hook_input)
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} UserPromptSubmit: {exit_code}")
    return success


def test_pretool_use() -> bool:
    """测试 PreToolUse hook"""
    print("测试 PreToolUse hook...")
    hook_input = {
        "session_id": "test-session-001",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "timestamp": "2026-01-18T10:02:00Z"
    }
    exit_code = run_hook("PreToolUse", hook_input)
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} PreToolUse: {exit_code}")
    return success


def test_posttool_use() -> bool:
    """测试 PostToolUse hook"""
    print("测试 PostToolUse hook...")
    hook_input = {
        "session_id": "test-session-001",
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "result": "success",
        "timestamp": "2026-01-18T10:02:30Z"
    }
    exit_code = run_hook("PostToolUse", hook_input)
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} PostToolUse: {exit_code}")
    return success


def test_notification() -> bool:
    """测试 Notification hook"""
    print("测试 Notification hook...")
    hook_input = {
        "session_id": "test-session-001",
        "hook_event_name": "Notification",
        "notification_type": "permission_prompt",
        "message": "需要权限批准",
        "timestamp": "2026-01-18T10:03:00Z"
    }
    exit_code = run_hook("Notification", hook_input)
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} Notification: {exit_code}")
    return success


def test_stop() -> bool:
    """测试 Stop hook"""
    print("测试 Stop hook...")
    hook_input = {
        "session_id": "test-session-001",
        "hook_event_name": "Stop",
        "transcript_path": "/tmp/test-transcript.jsonl",
        "permission_mode": "default",
        "stop_hook_active": False,
        "timestamp": "2026-01-18T10:04:00Z"
    }
    exit_code = run_hook("Stop", hook_input)
    success = exit_code in (0, 1)  # Stop hook 可以返回 0 或 1
    print(f"  {'✓' if success else '✗'} Stop: {exit_code}")
    return success


def test_subagent_stop() -> bool:
    """测试 SubagentStop hook"""
    print("测试 SubagentStop hook...")
    hook_input = {
        "session_id": "test-session-001",
        "hook_event_name": "SubagentStop",
        "subagent_id": "subagent-001",
        "stop_hook_active": False,
        "timestamp": "2026-01-18T10:04:30Z"
    }
    exit_code = run_hook("SubagentStop", hook_input)
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} SubagentStop: {exit_code}")
    return success


def test_precompact() -> bool:
    """测试 PreCompact hook"""
    print("测试 PreCompact hook...")
    hook_input = {
        "session_id": "test-session-001",
        "hook_event_name": "PreCompact",
        "compaction_ratio": 0.5,
        "timestamp": "2026-01-18T10:04:45Z"
    }
    exit_code = run_hook("PreCompact", hook_input)
    success = exit_code == 0
    print(f"  {'✓' if success else '✗'} PreCompact: {exit_code}")
    return success


def main():
    """运行所有 hook 测试"""
    print("=" * 50)
    print("通知插件 Hook 测试")
    print("=" * 50)
    print()
    
    # 测试用例列表
    test_cases = [
        ("SessionStart", test_session_start),
        ("SessionEnd", test_session_end),
        ("UserPromptSubmit", test_user_prompt_submit),
        ("PreToolUse", test_pretool_use),
        ("PostToolUse", test_posttool_use),
        ("Notification", test_notification),
        ("Stop", test_stop),
        ("SubagentStop", test_subagent_stop),
        ("PreCompact", test_precompact),
    ]
    
    results = {}
    for name, test_func in test_cases:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"✗ {name}: 测试异常 - {e}", file=sys.stderr)
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
    
    # 返回退出码
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
