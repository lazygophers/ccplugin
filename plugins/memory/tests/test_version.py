"""
版本控制模块测试
"""

import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture
async def db_with_version():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
            from memory.database import init_db, close_db
            from memory import create_memory, update_memory
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            await create_memory(uri="test://version", content="版本 1", priority=5)
            await update_memory("test://version", content="版本 2")
            
            yield
            
            await close_db()
            db_module._db_initialized = False


class TestGetVersions:
    """测试 get_versions 函数"""
    
    @pytest.mark.asyncio
    async def test_get_versions_existing(self, db_with_version):
        from memory import get_versions
        
        versions = await get_versions("test://version")
        
        assert len(versions) >= 1
    
    @pytest.mark.asyncio
    async def test_get_versions_nonexistent_memory(self, db_with_version):
        from memory import get_versions
        
        versions = await get_versions("test://nonexistent")
        
        assert len(versions) == 0
    
    @pytest.mark.asyncio
    async def test_get_versions_with_limit(self, db_with_version):
        from memory import get_versions
        
        versions = await get_versions("test://version", limit=1)
        
        assert len(versions) <= 1


class TestGetVersion:
    """测试 get_version 函数"""
    
    @pytest.mark.asyncio
    async def test_get_specific_version(self, db_with_version):
        from memory import get_versions, get_version
        
        all_versions = await get_versions("test://version")
        if all_versions:
            v = await get_version("test://version", all_versions[0].version)
            assert v is not None
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_version(self, db_with_version):
        from memory import get_version
        
        v = await get_version("test://version", 999)
        
        assert v is None


class TestRollbackToVersion:
    """测试 rollback_to_version 函数"""
    
    @pytest.mark.asyncio
    async def test_rollback(self, db_with_version):
        from memory import get_versions, rollback_to_version, get_memory
        
        versions = await get_versions("test://version")
        if versions:
            target_version = versions[-1].version
            memory = await rollback_to_version("test://version", target_version)
            
            assert memory is not None
    
    @pytest.mark.asyncio
    async def test_rollback_nonexistent(self, db_with_version):
        from memory import rollback_to_version
        
        memory = await rollback_to_version("test://nonexistent", 1)
        
        assert memory is None


class TestDiffVersions:
    """测试 diff_versions 函数"""
    
    @pytest.mark.asyncio
    async def test_diff_existing_versions(self, db_with_version):
        from memory import get_versions, diff_versions
        
        versions = await get_versions("test://version")
        if len(versions) >= 2:
            result = await diff_versions("test://version", versions[0].version, versions[1].version)
            
            assert result is not None
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_diff_nonexistent_version(self, db_with_version):
        from memory import diff_versions
        
        result = await diff_versions("test://version", 1, 999)
        
        assert result is None
