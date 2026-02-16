"""
数据库模块测试
"""

import hashlib
import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestComputeHash:
    """测试 compute_hash 函数"""
    
    def test_compute_hash_basic(self):
        from memory.database import compute_hash
        
        result = compute_hash("test content")
        expected = hashlib.sha256("test content".encode('utf-8')).hexdigest()
        
        assert result == expected
        assert len(result) == 64
    
    def test_compute_hash_empty(self):
        from memory.database import compute_hash
        
        result = compute_hash("")
        expected = hashlib.sha256("".encode('utf-8')).hexdigest()
        
        assert result == expected
    
    def test_compute_hash_unicode(self):
        from memory.database import compute_hash
        
        result = compute_hash("中文测试")
        expected = hashlib.sha256("中文测试".encode('utf-8')).hexdigest()
        
        assert result == expected
    
    def test_compute_hash_consistency(self):
        from memory.database import compute_hash
        
        content = "consistent content"
        result1 = compute_hash(content)
        result2 = compute_hash(content)
        
        assert result1 == result2


class TestGetDbPath:
    """测试 get_db_path 函数"""
    
    def test_get_db_path_returns_string(self):
        from memory.database import get_db_path
        
        result = get_db_path()
        
        assert isinstance(result, str)
        assert "memory.db" in result
    
    def test_get_db_path_contains_lazygophers(self):
        from memory.database import get_db_path
        
        result = get_db_path()
        
        assert ".lazygophers" in result or "lazygophers" in result


class TestInitDb:
    """测试 init_db 函数"""
    
    @pytest.mark.asyncio
    async def test_init_db_creates_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                from memory.database import init_db, close_db
                import memory.database as db_module
                db_module._db_initialized = False
                
                await init_db()
                
                assert db_module._db_initialized is True
                
                await close_db()
                db_module._db_initialized = False
    
    @pytest.mark.asyncio
    async def test_init_db_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                from memory.database import init_db, close_db
                import memory.database as db_module
                db_module._db_initialized = False
                
                await init_db()
                await init_db()
                
                assert db_module._db_initialized is True
                
                await close_db()
                db_module._db_initialized = False


class TestCloseDb:
    """测试 close_db 函数"""
    
    @pytest.mark.asyncio
    async def test_close_db_resets_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                from memory.database import init_db, close_db
                import memory.database as db_module
                db_module._db_initialized = False
                
                await init_db()
                assert db_module._db_initialized is True
                
                await close_db()
                assert db_module._db_initialized is False
    
    @pytest.mark.asyncio
    async def test_close_db_without_init(self):
        from memory.database import close_db
        import memory.database as db_module
        db_module._db_initialized = False
        
        await close_db()
        
        assert db_module._db_initialized is False
