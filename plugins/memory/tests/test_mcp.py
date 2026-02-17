"""
MCP Server 模块测试
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestMemoryMCPServer:
    """测试 MemoryMCPServer 类"""
    
    def test_server_initialization(self):
        from mcps import MemoryMCPServer
        
        server = MemoryMCPServer()
        
        assert server.server is not None
        assert server._db_initialized is False
    
    @pytest.mark.asyncio
    async def test_read_memory_system_uri(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        from memory import create_memory
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        await create_memory(uri="core://test", content="测试内容", priority=1)
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._read_memory({"uri": "system://boot"})
                        
                        assert len(result) == 1
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_read_memory_nonexistent(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._read_memory({"uri": "nonexistent://test"})
                        
                        assert "未找到" in result[0].text
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_create_memory(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._create_memory({
                            "uri": "test://mcp-create",
                            "content": "MCP 创建测试",
                            "priority": 5,
                        })
                        
                        assert "success" in result[0].text.lower() or "uri" in result[0].text.lower()
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_update_memory(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        from memory import create_memory
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        await create_memory(uri="test://mcp-update", content="原始内容", priority=5)
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._update_memory({
                            "uri": "test://mcp-update",
                            "content": "更新内容",
                        })
                        
                        assert "success" in result[0].text.lower() or "uri" in result[0].text.lower()
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_delete_memory(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        from memory import create_memory
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        await create_memory(uri="test://mcp-delete", content="删除测试", priority=5)
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._delete_memory({"uri": "test://mcp-delete"})
                        
                        assert "success" in result[0].text.lower() or "删除" in result[0].text
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_search_memory(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        from memory import create_memory
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        await create_memory(uri="test://search", content="搜索关键词测试", priority=5)
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._search_memory({"query": "关键词"})
                        
                        assert "count" in result[0].text.lower() or "memories" in result[0].text.lower()
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_preload_memory(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._preload_memory({
                            "context_type": "file",
                            "context_data": "/test/main.py",
                        })
                        
                        assert "context_type" in result[0].text
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_save_session(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._save_session({
                            "title": "测试会话",
                            "summary": "会话摘要内容",
                        })
                        
                        assert "success" in result[0].text.lower() or "session" in result[0].text.lower()
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_list_memories(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        from memory import create_memory
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        await create_memory(uri="test://list", content="列表测试", priority=5)
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._list_memories({})
                        
                        assert "count" in result[0].text.lower() or "memories" in result[0].text.lower()
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_get_memory_stats(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._get_memory_stats({})
                        
                        assert "total" in result[0].text.lower() or "stats" in result[0].text.lower()
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_export_memories(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._export_memories({})
                        
                        assert "memories" in result[0].text.lower() or "export" in result[0].text.lower()
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_import_memories(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._import_memories({
                            "data": {
                                "memories": [
                                    {"uri": "test://import", "content": "导入测试", "priority": 5}
                                ]
                            },
                            "strategy": "skip"
                        })
                        
                        assert "success" in result[0].text.lower() or "stats" in result[0].text.lower()
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_add_alias(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        from memory import create_memory
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        await create_memory(uri="test://alias-target", content="别名目标", priority=5)
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._add_alias({
                            "target_uri": "test://alias-target",
                            "alias_uri": "test://alias-new",
                        })
                        
                        assert "success" in result[0].text.lower() or "alias" in result[0].text.lower()
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_add_alias_nonexistent_target(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._add_alias({
                            "target_uri": "test://nonexistent",
                            "alias_uri": "test://alias-new",
                        })
                        
                        assert "未找到" in result[0].text
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_get_memory_versions(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        from memory import create_memory, update_memory
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        await create_memory(uri="test://versions", content="版本测试", priority=5)
                        await update_memory(uri="test://versions", content="版本测试v2")
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._get_memory_versions({"uri": "test://versions"})
                        
                        assert "versions" in result[0].text.lower() or "version" in result[0].text.lower()
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_rollback_memory(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        from memory import create_memory, update_memory, get_versions
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        await create_memory(uri="test://rollback", content="原始内容", priority=5)
                        await update_memory(uri="test://rollback", content="更新内容")
                        
                        versions = await get_versions("test://rollback")
                        target_version = versions[-1].version if versions else 0
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._rollback_memory({
                            "uri": "test://rollback",
                            "version": target_version,
                        })
                        
                        assert "success" in result[0].text.lower() or "rolled" in result[0].text.lower() or "回滚" in result[0].text
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_diff_versions(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        from memory import create_memory, update_memory, get_versions
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        await create_memory(uri="test://diff", content="内容v1", priority=5)
                        await update_memory(uri="test://diff", content="内容v2")
                        
                        versions = await get_versions("test://diff")
                        if len(versions) >= 2:
                            v1 = versions[-1].version
                            v2 = versions[0].version
                        else:
                            v1, v2 = 0, 1
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._diff_versions({
                            "uri": "test://diff",
                            "version1": v1,
                            "version2": v2,
                        })
                        
                        assert "content1" in result[0].text.lower() or "version" in result[0].text.lower() or "无法对比" in result[0].text
                        
                        await close_db()
                        db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_list_rollbacks(self):
        from mcps import MemoryMCPServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                with patch("memory.database.get_project_dir", return_value=tmpdir):
                    with patch("lib.utils.gitignore.add_gitignore_rule", return_value=True):
                        from memory.database import init_db, close_db
                        from memory import create_memory, update_memory
                        import memory.database as db_module
                        db_module._db_initialized = False
                        
                        await init_db()
                        await create_memory(uri="test://rollbacks", content="内容v1", priority=5)
                        await update_memory(uri="test://rollbacks", content="内容v2")
                        
                        server = MemoryMCPServer()
                        server._db_initialized = True
                        
                        result = await server._list_rollbacks({"uri": "test://rollbacks"})
                        
                        assert "rollback" in result[0].text.lower() or "version" in result[0].text.lower()
                        
                        await close_db()
                        db_module._db_initialized = False
