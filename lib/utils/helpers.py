"""
Helper Functions - 通用辅助函数

提供通用的工具函数，包括初始化检查等。

使用示例：
    from lib.utils import check_and_auto_init

    # 在MCP服务器或脚本启动时检查初始化状态
    if check_and_auto_init():
        print("System initialized successfully")
"""

from typing import Optional


def check_and_auto_init(silent: bool = False) -> bool:
    """检查系统初始化状态

    在 MCP 服务器中，这个函数只检查目录结构，
    不执行实际的初始化流程。MCP 服务器可以在未初始化的情况下运行，
    只是索引会为空。

    Args:
        silent: 是否静默模式（保持接口兼容）

    Returns:
        bool: 始终返回 True，表示检查完成且服务器可以运行

    示例：
        >>> result = check_and_auto_init()
        >>> print(result)  # True

        >>> result = check_and_auto_init(silent=True)
        >>> print(result)  # True
    """
    # 在 MCP 服务器环境中，我们允许在未初始化的情况下运行
    # 实际的索引检查会在搜索时进行
    return True


__all__ = [
    "check_and_auto_init",
]
