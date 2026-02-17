"""
Hooks 模块测试
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestRunAsync:
    """测试 run_async 函数"""
    
    def test_run_async_basic(self):
        from hooks import run_async
        
        async def simple_coro():
            return "test result"
        
        result = run_async(simple_coro())
        
        assert result == "test result"


class TestHandleHook:
    """测试 handle_hook 函数"""
    
    def test_handle_hook_unknown_event(self):
        from hooks import handle_hook
        
        with patch("hooks.load_hooks", return_value={"hook_event_name": "UnknownEvent"}):
            with patch("lib.logging.debug") as mock_debug:
                handle_hook()
                mock_debug.assert_called()
    
    def test_handle_hook_session_start(self):
        from hooks import handle_hook
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("hooks.load_hooks", return_value={"hook_event_name": "SessionStart"}):
                with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                    handle_hook()
    
    def test_handle_hook_session_end(self):
        from hooks import handle_hook
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("hooks.load_hooks", return_value={
                "hook_event_name": "SessionEnd",
                "message": "测试消息"
            }):
                with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                    import memory.database as db_module
                    db_module._db_initialized = False
                    handle_hook()


class TestHandleSessionStart:
    """测试 handle_session_start 函数"""
    
    def test_handle_session_start_basic(self):
        from hooks import handle_session_start
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_session_start({})


class TestHandleSessionEnd:
    """测试 handle_session_end 函数"""
    
    def test_handle_session_end_with_message(self):
        from hooks import handle_session_end
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                import memory.database as db_module
                db_module._db_initialized = False
                handle_session_end({"message": "测试结束消息"})
    
    def test_handle_session_end_without_message(self):
        from hooks import handle_session_end
        
        handle_session_end({})


class TestHandlePreToolUse:
    """测试 handle_pre_tool_use 函数"""
    
    def test_handle_pre_tool_use_read(self):
        from hooks import handle_pre_tool_use
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_pre_tool_use({
                    "tool_name": "Read",
                    "tool_input": {"file_path": "/test/file.py"}
                })
    
    def test_handle_pre_tool_use_other_tool(self):
        from hooks import handle_pre_tool_use
        
        handle_pre_tool_use({
            "tool_name": "OtherTool",
            "tool_input": {}
        })


class TestHandlePostToolUse:
    """测试 handle_post_tool_use 函数"""
    
    def test_handle_post_tool_use_edit(self):
        from hooks import handle_post_tool_use
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_post_tool_use({
                    "tool_name": "Edit",
                    "tool_input": {"file_path": "/test/file.py"},
                    "tool_result": "success"
                })
    
    def test_handle_post_tool_use_other_tool(self):
        from hooks import handle_post_tool_use
        
        handle_post_tool_use({
            "tool_name": "OtherTool",
            "tool_input": {},
            "tool_result": ""
        })


class TestHandlePostToolUseFailure:
    """测试 handle_post_tool_use_failure 函数"""
    
    def test_handle_post_tool_use_failure(self):
        from hooks import handle_post_tool_use_failure
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_post_tool_use_failure({
                    "tool_name": "Edit",
                    "tool_input": {"file_path": "/test/file.py"},
                    "error": "Test error"
                })


class TestHandleStop:
    """测试 handle_stop 函数"""
    
    def test_handle_stop(self):
        from hooks import handle_stop
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_stop({"reason": "test_reason"})


class TestHandlePreCompact:
    """测试 handle_pre_compact 函数"""
    
    def test_handle_pre_compact(self):
        from hooks import handle_pre_compact
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_pre_compact({
                    "transcript_path": "/test/transcript.json",
                    "session_id": "test_session"
                })


class TestHandleUserPromptSubmit:
    """测试 handle_user_prompt_submit 函数"""
    
    def test_handle_user_prompt_submit_with_prompt(self):
        from hooks import handle_user_prompt_submit
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_user_prompt_submit({
                    "prompt": "请帮我配置项目文件",
                    "session_id": "test_session"
                })
    
    def test_handle_user_prompt_submit_without_prompt(self):
        from hooks import handle_user_prompt_submit
        
        handle_user_prompt_submit({
            "prompt": "",
            "session_id": "test_session"
        })


class TestHandlePermissionRequest:
    """测试 handle_permission_request 函数"""
    
    def test_handle_permission_request_allow(self):
        from hooks import handle_permission_request
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_permission_request({
                    "tool_name": "Bash",
                    "permission_type": "execute",
                    "decision": "allow"
                })
    
    def test_handle_permission_request_deny(self):
        from hooks import handle_permission_request
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_permission_request({
                    "tool_name": "Bash",
                    "permission_type": "execute",
                    "decision": "deny"
                })


class TestHandleNotification:
    """测试 handle_notification 函数"""
    
    def test_handle_notification_error(self):
        from hooks import handle_notification
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_notification({
                    "notification_type": "error",
                    "message": "发生错误",
                    "title": "错误通知"
                })
    
    def test_handle_notification_warning(self):
        from hooks import handle_notification
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_notification({
                    "notification_type": "warning",
                    "message": "警告信息",
                    "title": "警告"
                })
    
    def test_handle_notification_without_message(self):
        from hooks import handle_notification
        
        handle_notification({
            "notification_type": "info",
            "message": "",
            "title": ""
        })


class TestHandleSubagentStart:
    """测试 handle_subagent_start 函数"""
    
    def test_handle_subagent_start(self):
        from hooks import handle_subagent_start
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_subagent_start({
                    "subagent_id": "sub_123",
                    "parent_session_id": "session_456",
                    "task": "执行测试任务"
                })


class TestHandleSubagentStop:
    """测试 handle_subagent_stop 函数"""
    
    def test_handle_subagent_stop_success(self):
        from hooks import handle_subagent_stop
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_subagent_stop({
                    "subagent_id": "sub_123",
                    "result": "任务完成",
                    "success": True
                })
    
    def test_handle_subagent_stop_failure(self):
        from hooks import handle_subagent_stop
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                handle_subagent_stop({
                    "subagent_id": "sub_123",
                    "result": "任务失败",
                    "success": False
                })
