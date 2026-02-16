"""
Web API 模块测试
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture
async def app_client():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
            from memory.database import init_db, close_db
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            from web.api import create_app
            from httpx import AsyncClient, ASGITransport
            
            app = create_app()
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                yield client
            
            await close_db()
            db_module._db_initialized = False


class TestIndexEndpoint:
    """测试首页端点"""
    
    @pytest.mark.asyncio
    async def test_index_returns_html(self, app_client):
        response = await app_client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestMemoriesEndpoints:
    """测试记忆 API 端点"""
    
    @pytest.mark.asyncio
    async def test_list_memories_empty(self, app_client):
        response = await app_client.get("/api/memories")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_create_memory(self, app_client):
        response = await app_client.post(
            "/api/memories",
            json={
                "uri": "api://test",
                "content": "API 测试内容",
                "priority": 5,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["uri"] == "api://test"
    
    @pytest.mark.asyncio
    async def test_get_memory(self, app_client):
        await app_client.post(
            "/api/memories",
            json={
                "uri": "api://get-test",
                "content": "获取测试",
                "priority": 5,
            }
        )
        
        response = await app_client.get("/api/memories/api://get-test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["uri"] == "api://get-test"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_memory(self, app_client):
        response = await app_client.get("/api/memories/nonexistent://test")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_memory(self, app_client):
        await app_client.post(
            "/api/memories",
            json={
                "uri": "api://update-test",
                "content": "原始内容",
                "priority": 5,
            }
        )
        
        response = await app_client.put(
            "/api/memories/api://update-test",
            json={
                "content": "更新内容",
                "priority": 3,
            }
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, app_client):
        await app_client.post(
            "/api/memories",
            json={
                "uri": "api://delete-test",
                "content": "删除测试",
                "priority": 5,
            }
        )
        
        response = await app_client.delete("/api/memories/api://delete-test")
        
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestSearchEndpoint:
    """测试搜索端点"""
    
    @pytest.mark.asyncio
    async def test_search_memories(self, app_client):
        await app_client.post(
            "/api/memories",
            json={
                "uri": "search://test",
                "content": "搜索测试内容",
                "priority": 5,
            }
        )
        
        response = await app_client.get("/api/search?q=搜索")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestStatsEndpoint:
    """测试统计端点"""
    
    @pytest.mark.asyncio
    async def test_get_stats(self, app_client):
        response = await app_client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "active" in data


class TestVersionsEndpoint:
    """测试版本端点"""
    
    @pytest.mark.asyncio
    async def test_get_versions(self, app_client):
        await app_client.post(
            "/api/memories",
            json={
                "uri": "version://test",
                "content": "版本测试",
                "priority": 5,
            }
        )
        
        response = await app_client.get("/api/versions/version://test")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestRelationsEndpoint:
    """测试关系端点"""
    
    @pytest.mark.asyncio
    async def test_get_relations(self, app_client):
        await app_client.post(
            "/api/memories",
            json={
                "uri": "relation://test",
                "content": "关系测试",
                "priority": 5,
            }
        )
        
        response = await app_client.get("/api/relations/relation://test")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
