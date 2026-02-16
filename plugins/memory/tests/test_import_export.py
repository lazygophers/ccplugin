"""
导入导出模块测试
"""

import json
import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture
async def db_with_export():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
            from memory.database import init_db, close_db
            from memory import create_memory
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            await create_memory(uri="export://test1", content="导出测试1", priority=1)
            await create_memory(uri="export://test2", content="导出测试2", priority=5)
            
            yield
            
            await close_db()
            db_module._db_initialized = False


class TestExportMemories:
    """测试 export_memories 函数"""
    
    @pytest.mark.asyncio
    async def test_export_basic(self, db_with_export):
        from memory import export_memories
        
        data = await export_memories()
        
        assert "exported_at" in data
        assert "version" in data
        assert "memories" in data
        assert len(data["memories"]) >= 2
    
    @pytest.mark.asyncio
    async def test_export_with_uri_prefix(self, db_with_export):
        from memory import export_memories
        
        data = await export_memories(uri_prefix="export://")
        
        assert all(m["uri"].startswith("export://") for m in data["memories"])
    
    @pytest.mark.asyncio
    async def test_export_with_versions(self, db_with_export):
        from memory import export_memories
        
        data = await export_memories(include_versions=True)
        
        for m in data["memories"]:
            assert "versions" in m
    
    @pytest.mark.asyncio
    async def test_export_with_relations(self, db_with_export):
        from memory import export_memories
        
        data = await export_memories(include_relations=True)
        
        for m in data["memories"]:
            assert "relations" in m


class TestImportMemories:
    """测试 import_memories 函数"""
    
    @pytest.mark.asyncio
    async def test_import_new_memories(self, db_with_export):
        from memory import import_memories
        
        data = {
            "memories": [
                {
                    "uri": "import://new1",
                    "content": "新导入的记忆1",
                    "priority": 5,
                    "disclosure": "",
                },
                {
                    "uri": "import://new2",
                    "content": "新导入的记忆2",
                    "priority": 3,
                    "disclosure": "",
                },
            ]
        }
        
        stats = await import_memories(data, strategy="skip")
        
        assert stats["created"] == 2
        assert stats["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_import_skip_existing(self, db_with_export):
        from memory import import_memories
        
        data = {
            "memories": [
                {
                    "uri": "export://test1",
                    "content": "更新的内容",
                    "priority": 5,
                    "disclosure": "",
                },
            ]
        }
        
        stats = await import_memories(data, strategy="skip")
        
        assert stats["skipped"] == 1
    
    @pytest.mark.asyncio
    async def test_import_overwrite_existing(self, db_with_export):
        from memory import import_memories, get_memory
        
        data = {
            "memories": [
                {
                    "uri": "export://test1",
                    "content": "覆盖的内容",
                    "priority": 5,
                    "disclosure": "",
                },
            ]
        }
        
        stats = await import_memories(data, strategy="overwrite")
        
        assert stats["updated"] == 1
        
        memory = await get_memory("export://test1", increment_access=False)
        assert memory.content == "覆盖的内容"
    
    @pytest.mark.asyncio
    async def test_import_merge_existing(self, db_with_export):
        from memory import import_memories, get_memory
        
        data = {
            "memories": [
                {
                    "uri": "export://test1",
                    "content": "追加的内容",
                    "priority": 5,
                    "disclosure": "",
                },
            ]
        }
        
        stats = await import_memories(data, strategy="merge")
        
        assert stats["updated"] == 1
        
        memory = await get_memory("export://test1", increment_access=False)
        assert "导出测试1" in memory.content
        assert "追加的内容" in memory.content
