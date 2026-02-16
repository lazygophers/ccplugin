"""
错误解决方案模块补充测试
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


class TestFindErrorSolutionExtra:
    """测试 find_error_solution 函数补充"""
    
    @pytest.mark.asyncio
    async def test_find_with_invalid_regex(self, db):
        from memory import record_error_solution, find_error_solution
        
        await record_error_solution(
            error_pattern="[invalid(regex",
            solution="无效正则表达式测试",
        )
        
        solution = await find_error_solution("test [invalid(regex pattern")
        
        assert solution is not None
    
    @pytest.mark.asyncio
    async def test_find_case_insensitive(self, db):
        from memory import record_error_solution, find_error_solution
        
        await record_error_solution(
            error_pattern="TESTERROR",
            solution="测试解决方案",
        )
        
        solution = await find_error_solution("this is a testerror message")
        
        assert solution is not None


class TestMarkSolutionSuccessExtra:
    """测试 mark_solution_success 函数补充"""
    
    @pytest.mark.asyncio
    async def test_mark_nonexistent_solution(self, db):
        from memory import mark_solution_success
        
        await mark_solution_success(99999, success=True)
