"""
错误解决方案模块

提供错误模式匹配和解决方案管理功能。
"""

import re
from datetime import datetime
from typing import Optional

from .models import ErrorSolution


async def record_error_solution(
    error_pattern: str,
    solution: str,
    error_type: Optional[str] = None,
    source: str = "learned",
) -> ErrorSolution:
    """
    记录错误解决方案
    
    保存错误模式及其解决方案，用于错误自动匹配和学习。
    如果错误模式已存在，则更新解决方案。
    
    Args:
        error_pattern: 错误模式，支持正则表达式
        solution: 解决方案描述
        error_type: 错误类型分类
        source: 来源标识 (learned/manual/imported)
        
    Returns:
        ErrorSolution: 创建或更新的解决方案记录
    """
    existing = await ErrorSolution.first(where="error_pattern = ?", params=(error_pattern,))
    
    if existing:
        existing.solution = solution
        existing.error_type = error_type or existing.error_type
        existing.updated_at = datetime.now()
        await existing.save()
        return existing
    
    return await ErrorSolution.create(
        error_pattern=error_pattern,
        error_type=error_type,
        solution=solution,
        source=source,
        success_count=0,
        failure_count=0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


async def find_error_solution(error_message: str) -> Optional[ErrorSolution]:
    """
    查找错误解决方案
    
    根据错误信息匹配已记录的解决方案。
    优先返回成功次数最多的匹配方案。
    
    Args:
        error_message: 错误信息文本
        
    Returns:
        Optional[ErrorSolution]: 匹配的解决方案，无匹配则返回 None
    """
    solutions = await ErrorSolution.find(order_by="success_count DESC")
    
    for solution in solutions:
        try:
            if re.search(solution.error_pattern, error_message, re.IGNORECASE):
                return solution
        except re.error:
            if solution.error_pattern.lower() in error_message.lower():
                return solution
    
    return None


async def mark_solution_success(solution_id: int, success: bool) -> None:
    """
    标记解决方案的成功或失败
    
    更新解决方案的成功/失败计数，用于评估方案有效性。
    
    Args:
        solution_id: 解决方案 ID
        success: True 表示成功，False 表示失败
    """
    solution = await ErrorSolution.first(where="id = ?", params=(solution_id,))
    if solution:
        if success:
            solution.success_count += 1
        else:
            solution.failure_count += 1
        solution.updated_at = datetime.now()
        await solution.save()
