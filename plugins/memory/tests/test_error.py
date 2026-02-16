"""
错误解决方案模块测试
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


class TestRecordErrorSolution:
    """测试 record_error_solution 函数"""
    
    @pytest.mark.asyncio
    async def test_record_new_solution(self, db):
        from memory import record_error_solution
        
        solution = await record_error_solution(
            error_pattern="ModuleNotFoundError",
            solution="安装缺失的模块",
            error_type="ImportError",
        )
        
        assert solution.error_pattern == "ModuleNotFoundError"
        assert solution.solution == "安装缺失的模块"
        assert solution.error_type == "ImportError"
    
    @pytest.mark.asyncio
    async def test_update_existing_solution(self, db):
        from memory import record_error_solution
        
        await record_error_solution(
            error_pattern="TestError",
            solution="原始解决方案",
        )
        
        solution = await record_error_solution(
            error_pattern="TestError",
            solution="更新后的解决方案",
        )
        
        assert solution.solution == "更新后的解决方案"
    
    @pytest.mark.asyncio
    async def test_record_with_source(self, db):
        from memory import record_error_solution
        
        solution = await record_error_solution(
            error_pattern="CustomError",
            solution="手动解决方案",
            source="manual",
        )
        
        assert solution.source == "manual"


class TestFindErrorSolution:
    """测试 find_error_solution 函数"""
    
    @pytest.mark.asyncio
    async def test_find_matching_solution(self, db):
        from memory import record_error_solution, find_error_solution
        
        await record_error_solution(
            error_pattern="ModuleNotFoundError: No module named 'test'",
            solution="pip install test",
        )
        
        solution = await find_error_solution("ModuleNotFoundError: No module named 'test'")
        
        assert solution is not None
        assert "pip install" in solution.solution
    
    @pytest.mark.asyncio
    async def test_find_no_match(self, db):
        from memory import find_error_solution
        
        solution = await find_error_solution("完全未知的错误信息 xyz123")
        
        assert solution is None
    
    @pytest.mark.asyncio
    async def test_find_with_regex_pattern(self, db):
        from memory import record_error_solution, find_error_solution
        
        await record_error_solution(
            error_pattern=r"Error \d+: .*",
            solution="通用错误处理",
        )
        
        solution = await find_error_solution("Error 404: Not found")
        
        assert solution is not None


class TestMarkSolutionSuccess:
    """测试 mark_solution_success 函数"""
    
    @pytest.mark.asyncio
    async def test_mark_success(self, db):
        from memory import record_error_solution, mark_solution_success
        
        solution = await record_error_solution(
            error_pattern="TestSuccess",
            solution="测试成功",
        )
        initial_count = solution.success_count
        
        await mark_solution_success(solution.id, success=True)
        
        from memory.models import ErrorSolution
        updated = await ErrorSolution.first(where="id = ?", params=(solution.id,))
        assert updated.success_count == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_mark_failure(self, db):
        from memory import record_error_solution, mark_solution_success
        
        solution = await record_error_solution(
            error_pattern="TestFailure",
            solution="测试失败",
        )
        initial_count = solution.failure_count
        
        await mark_solution_success(solution.id, success=False)
        
        from memory.models import ErrorSolution
        updated = await ErrorSolution.first(where="id = ?", params=(solution.id,))
        assert updated.failure_count == initial_count + 1
