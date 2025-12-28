"""Context Plugin 集成模块。

提供任务与会话上下文的集成功能：
- 保存任务讨论到上下文
- 恢复任务相关的历史上下文
- 关联任务 ID 与会话 ID
"""

from typing import Any


class ContextIntegration:
    """Context Plugin 集成辅助类。"""

    def __init__(self) -> None:
        """初始化 Context 集成。"""
        self.plugin_name = "context"

    async def save_task_context(
        self,
        task_id: str,
        content: str,
        role: str = "assistant",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """保存任务相关的上下文。

        Args:
            task_id: 任务 ID
            content: 上下文内容
            role: 角色 ("user" | "assistant")
            metadata: 额外元数据

        Returns:
            dict[str, Any]: 保存结果

        Example:
            >>> integration = ContextIntegration()
            >>> await integration.save_task_context(
            ...     task_id="tk-123",
            ...     content="讨论了登录功能的实现方案",
            ...     role="assistant"
            ... )
        """
        # 使用任务 ID 作为 session_id 的一部分
        session_id = f"task-{task_id}"

        # 构建完整的元数据
        full_metadata = {
            "task_id": task_id,
            "type": "task_context",
            **(metadata or {}),
        }

        # TODO: 调用 Context Plugin 的 context_save 工具
        # 在实际实现中，需要通过 MCP 协议调用其他插件
        return {
            "session_id": session_id,
            "content": content,
            "role": role,
            "metadata": full_metadata,
            "status": "pending",  # 等待实际实现
        }

    async def retrieve_task_context(
        self,
        task_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """检索任务相关的历史上下文。

        Args:
            task_id: 任务 ID
            limit: 返回数量限制

        Returns:
            list[dict[str, Any]]: 上下文记录列表

        Example:
            >>> integration = ContextIntegration()
            >>> contexts = await integration.retrieve_task_context("tk-123")
            >>> for ctx in contexts:
            ...     print(f"{ctx['role']}: {ctx['content']}")
        """
        session_id = f"task-{task_id}"

        # TODO: 调用 Context Plugin 的 context_retrieve 工具
        return []

    async def save_task_comment(
        self,
        task_id: str,
        comment: str,
        author: str = "user",
    ) -> dict[str, Any]:
        """保存任务评论到上下文。

        Args:
            task_id: 任务 ID
            comment: 评论内容
            author: 评论作者

        Returns:
            dict[str, Any]: 保存结果
        """
        return await self.save_task_context(
            task_id=task_id,
            content=comment,
            role="user",
            metadata={"author": author, "type": "comment"},
        )

    async def get_task_discussion(
        self,
        task_id: str,
    ) -> str:
        """获取任务的完整讨论历史。

        Args:
            task_id: 任务 ID

        Returns:
            str: 格式化的讨论历史
        """
        contexts = await self.retrieve_task_context(task_id)

        if not contexts:
            return f"任务 {task_id} 暂无讨论记录"

        lines = [f"## 任务 {task_id} 讨论历史\n"]
        for ctx in contexts:
            role = "👤" if ctx.get("role") == "user" else "🤖"
            content = ctx.get("content", "")
            lines.append(f"{role} {content}\n")

        return "\n".join(lines)


# 全局实例
_context_integration: ContextIntegration | None = None


def get_context_integration() -> ContextIntegration:
    """获取 Context 集成单例。

    Returns:
        ContextIntegration: Context 集成实例
    """
    global _context_integration
    if _context_integration is None:
        _context_integration = ContextIntegration()
    return _context_integration
