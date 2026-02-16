"""
会话管理模块测试
"""

import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture
async def db():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
            from memory.database import init_db, close_db
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            yield
            
            await close_db()
            db_module._db_initialized = False


class TestCreateSession:
    """测试 create_session 函数"""
    
    @pytest.mark.asyncio
    async def test_create_session(self, db):
        from memory import create_session
        
        session = await create_session(
            session_id="test-session-1",
            project_dir="/test/project",
            project_name="Test Project",
        )
        
        assert session.session_id == "test-session-1"
        assert session.project_dir == "/test/project"
        assert session.project_name == "Test Project"
    
    @pytest.mark.asyncio
    async def test_create_session_minimal(self, db):
        from memory import create_session
        
        session = await create_session(session_id="test-session-2")
        
        assert session.session_id == "test-session-2"
        assert session.memories_created == 0
        assert session.memories_accessed == 0


class TestEndSession:
    """测试 end_session 函数"""
    
    @pytest.mark.asyncio
    async def test_end_session(self, db):
        from memory import create_session, end_session
        
        await create_session(session_id="test-session-3")
        
        session = await end_session("test-session-3", summary="测试摘要")
        
        assert session is not None
        assert session.summary == "测试摘要"
        assert session.ended_at is not None
    
    @pytest.mark.asyncio
    async def test_end_nonexistent_session(self, db):
        from memory import end_session
        
        session = await end_session("nonexistent-session")
        
        assert session is None
