"""
路径关联模块测试
"""

import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture
async def db_with_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
            from memory.database import init_db, close_db
            from memory import create_memory
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            memory = await create_memory(uri="test://path", content="路径测试")
            
            yield memory.id
            
            await close_db()
            db_module._db_initialized = False


class TestAddMemoryPath:
    """测试 add_memory_path 函数"""
    
    @pytest.mark.asyncio
    async def test_add_path(self, db_with_path):
        memory_id = db_with_path
        from memory import add_memory_path
        
        path = await add_memory_path(memory_id, "/test/file.py")
        
        assert path.memory_id == memory_id
        assert path.path == "/test/file.py"
    
    @pytest.mark.asyncio
    async def test_add_duplicate_path(self, db_with_path):
        memory_id = db_with_path
        from memory import add_memory_path
        
        await add_memory_path(memory_id, "/test/duplicate.py")
        path = await add_memory_path(memory_id, "/test/duplicate.py")
        
        assert path.path == "/test/duplicate.py"


class TestGetMemoryPaths:
    """测试 get_memory_paths 函数"""
    
    @pytest.mark.asyncio
    async def test_get_paths(self, db_with_path):
        memory_id = db_with_path
        from memory import add_memory_path, get_memory_paths
        
        await add_memory_path(memory_id, "/test/path1.py")
        await add_memory_path(memory_id, "/test/path2.py")
        
        paths = await get_memory_paths(memory_id)
        
        assert len(paths) >= 2
    
    @pytest.mark.asyncio
    async def test_get_paths_empty(self, db_with_path):
        memory_id = db_with_path
        from memory import get_memory_paths
        
        paths = await get_memory_paths(memory_id + 9999)
        
        assert len(paths) == 0


class TestFindMemoriesByPath:
    """测试 find_memories_by_path 函数"""
    
    @pytest.mark.asyncio
    async def test_find_by_path(self, db_with_path):
        memory_id = db_with_path
        from memory import add_memory_path, find_memories_by_path
        
        await add_memory_path(memory_id, "/project/src/main.py")
        
        memories = await find_memories_by_path("main.py")
        
        assert len(memories) >= 1
    
    @pytest.mark.asyncio
    async def test_find_no_match(self, db_with_path):
        from memory import find_memories_by_path
        
        memories = await find_memories_by_path("nonexistent_file_xyz.py")
        
        assert len(memories) == 0
