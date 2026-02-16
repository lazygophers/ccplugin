"""
版本控制模块补充测试
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
            from memory import create_memory, update_memory
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            await create_memory(uri="test://version-extra", content="版本 1")
            await update_memory("test://version-extra", content="版本 2")
            
            yield
            
            await close_db()
            db_module._db_initialized = False


class TestGetVersionExtra:
    """测试 get_version 函数补充"""
    
    @pytest.mark.asyncio
    async def test_get_version_nonexistent_memory(self, db):
        from memory import get_version
        
        result = await get_version("nonexistent://test", 1)
        
        assert result is None


class TestRollbackExtra:
    """测试 rollback_to_version 函数补充"""
    
    @pytest.mark.asyncio
    async def test_rollback_to_nonexistent_version(self, db):
        from memory import rollback_to_version
        
        result = await rollback_to_version("test://version-extra", 999)
        
        assert result is None


class TestDiffVersionsExtra:
    """测试 diff_versions 函数补充"""
    
    @pytest.mark.asyncio
    async def test_diff_with_nonexistent_version(self, db):
        from memory import diff_versions
        
        result = await diff_versions("test://version-extra", 1, 999)
        
        assert result is None
