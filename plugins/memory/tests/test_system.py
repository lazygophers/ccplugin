"""
系统 URI 模块测试
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
            from memory import create_memory
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            await create_memory(uri="core://agent", content="核心身份", priority=0)
            await create_memory(uri="core://user", content="用户信息", priority=1)
            await create_memory(uri="project://config", content="项目配置", priority=5)
            
            yield
            
            await close_db()
            db_module._db_initialized = False


class TestIsSystemUri:
    """测试 is_system_uri 函数"""
    
    def test_system_boot(self):
        from memory import is_system_uri
        
        assert is_system_uri("system://boot") is True
    
    def test_system_index(self):
        from memory import is_system_uri
        
        assert is_system_uri("system://index") is True
    
    def test_system_recent(self):
        from memory import is_system_uri
        
        assert is_system_uri("system://recent") is True
    
    def test_non_system_uri(self):
        from memory import is_system_uri
        
        assert is_system_uri("project://test") is False
        assert is_system_uri("user://info") is False
        assert is_system_uri("random") is False


class TestGetSystemUriDescription:
    """测试 get_system_uri_description 函数"""
    
    def test_boot_description(self):
        from memory import get_system_uri_description
        
        desc = get_system_uri_description("system://boot")
        assert desc is not None
        assert "核心" in desc or "priority" in desc.lower()
    
    def test_index_description(self):
        from memory import get_system_uri_description
        
        desc = get_system_uri_description("system://index")
        assert desc is not None
        assert "索引" in desc or "index" in desc.lower()
    
    def test_recent_description(self):
        from memory import get_system_uri_description
        
        desc = get_system_uri_description("system://recent")
        assert desc is not None
        assert "最近" in desc or "recent" in desc.lower()
    
    def test_non_system_uri(self):
        from memory import get_system_uri_description
        
        desc = get_system_uri_description("project://test")
        assert desc is None


class TestHandleSystemUri:
    """测试 handle_system_uri 函数"""
    
    @pytest.mark.asyncio
    async def test_handle_boot(self, db):
        from memory import handle_system_uri
        
        result = await handle_system_uri("system://boot")
        
        assert result is not None
        assert result["uri"] == "system://boot"
        assert "memories" in result
        assert result["loaded_count"] >= 2
    
    @pytest.mark.asyncio
    async def test_handle_index(self, db):
        from memory import handle_system_uri
        
        result = await handle_system_uri("system://index")
        
        assert result is not None
        assert result["uri"] == "system://index"
        assert "domains" in result
        assert "stats" in result
    
    @pytest.mark.asyncio
    async def test_handle_recent(self, db):
        from memory import handle_system_uri
        
        result = await handle_system_uri("system://recent")
        
        assert result is not None
        assert result["uri"] == "system://recent"
        assert "memories" in result
    
    @pytest.mark.asyncio
    async def test_handle_recent_with_limit(self, db):
        from memory import handle_system_uri
        
        result = await handle_system_uri("system://recent", limit=2)
        
        assert result is not None
        assert result["count"] <= 2
    
    @pytest.mark.asyncio
    async def test_handle_non_system_uri(self, db):
        from memory import handle_system_uri
        
        result = await handle_system_uri("project://test")
        
        assert result is None
