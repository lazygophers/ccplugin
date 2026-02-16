"""
导入导出模块补充测试
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


class TestImportMemoriesExtra:
    """测试 import_memories 函数补充"""
    
    @pytest.mark.asyncio
    async def test_import_with_error(self, db):
        from memory import import_memories
        
        data = {
            "memories": [
                {
                    "uri": "import://error",
                    "content": None,
                }
            ]
        }
        
        stats = await import_memories(data)
        
        assert stats["errors"] >= 1
