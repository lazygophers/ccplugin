"""Memory Plugin 集成模块。

提供任务与记忆管理的集成功能：
- 存储任务决策到记忆图谱
- 搜索任务相关的记忆
- 关联任务与知识点
"""

from typing import Any


class MemoryIntegration:
    """Memory Plugin 集成辅助类。"""

    def __init__(self) -> None:
        """初始化 Memory 集成。"""
        self.plugin_name = "memory"

    async def store_task_decision(
        self,
        task_id: str,
        decision: str,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """存储任务相关的决策到记忆。

        Args:
            task_id: 任务 ID
            decision: 决策内容
            tags: 标签列表
            metadata: 额外元数据

        Returns:
            dict[str, Any]: 存储结果

        Example:
            >>> integration = MemoryIntegration()
            >>> await integration.store_task_decision(
            ...     task_id="tk-123",
            ...     decision="决定使用 JWT 进行身份验证",
            ...     tags=["authentication", "security"]
            ... )
        """
        # 构建标签列表（包含任务 ID）
        full_tags = [f"task:{task_id}", "decision", *(tags or [])]

        # 构建完整元数据
        full_metadata = {
            "task_id": task_id,
            "type": "decision",
            **(metadata or {}),
        }

        # TODO: 调用 Memory Plugin 的 memory_store 工具
        return {
            "content": decision,
            "tags": full_tags,
            "metadata": full_metadata,
            "status": "pending",
        }

    async def store_task_learning(
        self,
        task_id: str,
        learning: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """存储任务中的学习收获。

        Args:
            task_id: 任务 ID
            learning: 学习内容
            tags: 标签列表

        Returns:
            dict[str, Any]: 存储结果
        """
        full_tags = [f"task:{task_id}", "learning", *(tags or [])]

        return await self.store_task_decision(
            task_id=task_id,
            decision=learning,
            tags=full_tags,
            metadata={"type": "learning"},
        )

    async def search_task_memories(
        self,
        task_id: str,
        query: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """搜索任务相关的记忆。

        Args:
            task_id: 任务 ID
            query: 搜索关键词（可选）
            limit: 返回数量限制

        Returns:
            list[dict[str, Any]]: 记忆列表

        Example:
            >>> integration = MemoryIntegration()
            >>> memories = await integration.search_task_memories(
            ...     task_id="tk-123",
            ...     query="身份验证"
            ... )
        """
        # 使用任务标签过滤
        tags = [f"task:{task_id}"]

        # TODO: 调用 Memory Plugin 的 memory_search 工具
        return []

    async def store_task_solution(
        self,
        task_id: str,
        problem: str,
        solution: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """存储任务的问题解决方案。

        Args:
            task_id: 任务 ID
            problem: 问题描述
            solution: 解决方案
            tags: 标签列表

        Returns:
            dict[str, Any]: 存储结果
        """
        content = f"问题: {problem}\n\n解决方案: {solution}"
        full_tags = [f"task:{task_id}", "solution", "problem-solving", *(tags or [])]

        return await self.store_task_decision(
            task_id=task_id,
            decision=content,
            tags=full_tags,
            metadata={"type": "solution", "problem": problem, "solution": solution},
        )

    async def get_task_knowledge(
        self,
        task_id: str,
    ) -> str:
        """获取任务相关的所有知识点。

        Args:
            task_id: 任务 ID

        Returns:
            str: 格式化的知识点列表
        """
        memories = await self.search_task_memories(task_id)

        if not memories:
            return f"任务 {task_id} 暂无相关知识记录"

        lines = [f"## 任务 {task_id} 相关知识\n"]
        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            tags = ", ".join(memory.get("tags", []))
            lines.append(f"### {i}. {content}")
            if tags:
                lines.append(f"**标签**: {tags}\n")

        return "\n".join(lines)

    async def search_similar_solutions(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """搜索类似问题的解决方案。

        Args:
            query: 问题描述
            limit: 返回数量限制

        Returns:
            list[dict[str, Any]]: 类似解决方案列表
        """
        # 搜索带有 solution 标签的记忆
        # TODO: 调用 Memory Plugin 的 memory_search 工具
        return []


# 全局实例
_memory_integration: MemoryIntegration | None = None


def get_memory_integration() -> MemoryIntegration:
    """获取 Memory 集成单例。

    Returns:
        MemoryIntegration: Memory 集成实例
    """
    global _memory_integration
    if _memory_integration is None:
        _memory_integration = MemoryIntegration()
    return _memory_integration
