"""
会话管理模块

提供会话记录管理功能。
"""

from datetime import datetime
from typing import Optional

from .models import Session


async def create_session(
    session_id: str,
    project_dir: Optional[str] = None,
    project_name: Optional[str] = None,
) -> Session:
    """
    创建会话记录
    
    创建新的会话记录，用于追踪会话级别的记忆操作。
    
    Args:
        session_id: 会话唯一标识
        project_dir: 项目目录路径
        project_name: 项目名称
        
    Returns:
        Session: 创建的会话记录
    """
    return await Session.create(
        session_id=session_id,
        project_dir=project_dir,
        project_name=project_name,
        started_at=datetime.now(),
        memories_created=0,
        memories_accessed=0,
        operations_count=0,
    )


async def end_session(session_id: str, summary: Optional[str] = None) -> Optional[Session]:
    """
    结束会话记录
    
    结束指定会话，记录结束时间和摘要。
    
    Args:
        session_id: 会话唯一标识
        summary: 会话摘要描述
        
    Returns:
        Optional[Session]: 更新后的会话记录，不存在则返回 None
    """
    session = await Session.first(where="session_id = ?", params=(session_id,))
    if not session:
        return None
    
    session.ended_at = datetime.now()
    session.summary = summary
    await session.save()
    
    return session
