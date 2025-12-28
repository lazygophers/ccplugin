"""Knowledge Plugin 集成模块。

提供任务与知识库的集成功能：
- 添加任务文档到知识库
- 搜索相关任务知识
- 关联任务与知识文章
"""

from typing import Any


class KnowledgeIntegration:
    """Knowledge Plugin 集成辅助类。"""

    def __init__(self) -> None:
        """初始化 Knowledge 集成。"""
        self.plugin_name = "knowledge"

    async def add_task_documentation(
        self,
        task_id: str,
        content: str,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """添加任务文档到知识库。

        Args:
            task_id: 任务 ID
            content: 文档内容
            source: 文档来源
            metadata: 额外元数据

        Returns:
            dict[str, Any]: 添加结果

        Example:
            >>> integration = KnowledgeIntegration()
            >>> await integration.add_task_documentation(
            ...     task_id="tk-123",
            ...     content="登录功能实现文档...",
            ...     source="技术设计文档"
            ... )
        """
        # 构建完整元数据
        full_metadata = {
            "task_id": task_id,
            "type": "task_documentation",
            **(metadata or {}),
        }

        # 使用任务 ID 作为来源的一部分
        full_source = f"Task {task_id}" + (f" - {source}" if source else "")

        # TODO: 调用 Knowledge Plugin 的 knowledge_add 工具
        return {
            "content": content,
            "source": full_source,
            "metadata": full_metadata,
            "status": "pending",
        }

    async def add_task_solution(
        self,
        task_id: str,
        title: str,
        description: str,
        solution: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """添加任务解决方案到知识库。

        Args:
            task_id: 任务 ID
            title: 方案标题
            description: 问题描述
            solution: 解决方案
            tags: 标签列表

        Returns:
            dict[str, Any]: 添加结果
        """
        content = f"""# {title}

## 问题描述

{description}

## 解决方案

{solution}

---
**任务 ID**: {task_id}
**标签**: {', '.join(tags or [])}
"""

        return await self.add_task_documentation(
            task_id=task_id,
            content=content,
            source="解决方案文档",
            metadata={"type": "solution", "tags": tags or [], "title": title},
        )

    async def search_task_knowledge(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """搜索任务相关的知识。

        Args:
            query: 搜索查询
            limit: 返回数量限制

        Returns:
            list[dict[str, Any]]: 知识列表

        Example:
            >>> integration = KnowledgeIntegration()
            >>> results = await integration.search_task_knowledge(
            ...     query="身份验证实现"
            ... )
        """
        # TODO: 调用 Knowledge Plugin 的 knowledge_search 工具
        return []

    async def search_similar_tasks(
        self,
        description: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """搜索类似任务的知识。

        Args:
            description: 任务描述
            limit: 返回数量限制

        Returns:
            list[dict[str, Any]]: 类似任务知识列表
        """
        # 搜索任务文档类型的知识
        results = await self.search_task_knowledge(description, limit)

        # 过滤出任务文档
        return [r for r in results if r.get("metadata", {}).get("type") == "task_documentation"]

    async def add_task_lessons_learned(
        self,
        task_id: str,
        lessons: list[str],
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """添加任务的经验教训到知识库。

        Args:
            task_id: 任务 ID
            lessons: 经验教训列表
            tags: 标签列表

        Returns:
            dict[str, Any]: 添加结果
        """
        content = f"""# 任务 {task_id} 经验教训

"""
        for i, lesson in enumerate(lessons, 1):
            content += f"{i}. {lesson}\n"

        return await self.add_task_documentation(
            task_id=task_id,
            content=content,
            source="经验总结",
            metadata={"type": "lessons_learned", "tags": tags or []},
        )

    async def get_task_references(
        self,
        task_id: str,
    ) -> str:
        """获取任务的参考文档。

        Args:
            task_id: 任务 ID

        Returns:
            str: 格式化的参考文档列表
        """
        # 搜索该任务ID相关的知识
        query = f"task {task_id}"
        results = await self.search_task_knowledge(query)

        if not results:
            return f"任务 {task_id} 暂无参考文档"

        lines = [f"## 任务 {task_id} 参考文档\n"]
        for i, doc in enumerate(results, 1):
            source = doc.get("source", "未知来源")
            content_preview = doc.get("content", "")[:100] + "..."
            lines.append(f"### {i}. {source}")
            lines.append(f"{content_preview}\n")

        return "\n".join(lines)


# 全局实例
_knowledge_integration: KnowledgeIntegration | None = None


def get_knowledge_integration() -> KnowledgeIntegration:
    """获取 Knowledge 集成单例。

    Returns:
        KnowledgeIntegration: Knowledge 集成实例
    """
    global _knowledge_integration
    if _knowledge_integration is None:
        _knowledge_integration = KnowledgeIntegration()
    return _knowledge_integration
