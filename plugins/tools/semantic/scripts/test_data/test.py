#!/usr/bin/env python3
"""
Python 测试文件 - 包含函数、类、装饰器、异步函数
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class User:
    """用户数据类"""
    id: int
    name: str
    email: str


def authenticate_user(username: str, password: str) -> Optional[User]:
    """验证用户凭据

    Args:
        username: 用户名
        password: 密码

    Returns:
        用户对象或 None
    """
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user
    return None


async def fetch_user_data(user_id: int) -> dict:
    """异步获取用户数据

    Args:
        user_id: 用户 ID

    Returns:
        用户数据字典
    """
    return await User.fetch(user_id)


class UserSession:
    """用户会话管理类"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.created_at = datetime.now()

    def is_valid(self) -> bool:
        """检查会话是否有效"""
        return datetime.now() - self.created_at < timedelta(hours=24)


def get_user(username: str) -> Optional[User]:
    """获取用户（示例）"""
    # 这里应该是实际的数据库查询
    return User(id=1, name=username, email=f"{username}@example.com")


def create_session(username: str) -> UserSession:
    """创建用户会话"""
    user = get_user(username)
    session = UserSession(user.id)
    session.save()
    return session
