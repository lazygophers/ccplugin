"""
测试配置

提供测试 fixtures 和通用配置。
"""

import asyncio
import os
import tempfile
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def temp_db():
    import os
    from unittest.mock import patch
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        
        with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
            from memory.database import init_db, close_db, _db_initialized
            
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            yield db_path
            
            await close_db()
            db_module._db_initialized = False


@pytest.fixture
async def sample_memory(temp_db):
    from memory import create_memory
    
    memory = await create_memory(
        uri="test://sample",
        content="测试记忆内容",
        priority=5,
        disclosure="测试触发条件",
    )
    return memory
