"""
API 错误路径测试
"""

import os
import sys
import tempfile
from unittest.mock import patch

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


class TestAPIErrorPaths:
    """测试 API 错误路径"""
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_memory(self, app_client):
        response = await app_client.put(
            "/api/memories/nonexistent://test",
            json={"content": "test"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_memory(self, app_client):
        response = await app_client.delete("/api/memories/nonexistent://test")
        
        assert response.status_code == 404
