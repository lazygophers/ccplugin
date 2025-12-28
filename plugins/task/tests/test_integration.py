"""插件集成测试。

测试 Task Plugin 与其他插件的集成功能。
"""

import pytest

from task.integration.context import ContextIntegration, get_context_integration
from task.integration.knowledge import KnowledgeIntegration, get_knowledge_integration
from task.integration.memory import MemoryIntegration, get_memory_integration


class TestContextIntegration:
    """Context Plugin 集成测试。"""

    def test_singleton(self) -> None:
        """测试单例模式。"""
        ctx1 = get_context_integration()
        ctx2 = get_context_integration()
        assert ctx1 is ctx2

    @pytest.mark.asyncio
    async def test_save_task_context(self) -> None:
        """测试保存任务上下文。"""
        ctx = ContextIntegration()

        result = await ctx.save_task_context(
            task_id="tk-001",
            content="测试讨论内容",
            role="assistant",
            metadata={"author": "test"},
        )

        assert result["session_id"] == "task-tk-001"
        assert result["content"] == "测试讨论内容"
        assert result["role"] == "assistant"
        assert result["metadata"]["task_id"] == "tk-001"
        assert result["metadata"]["type"] == "task_context"
        assert result["metadata"]["author"] == "test"

    @pytest.mark.asyncio
    async def test_save_task_comment(self) -> None:
        """测试保存任务评论。"""
        ctx = ContextIntegration()

        result = await ctx.save_task_comment(
            task_id="tk-002", comment="这是一条评论", author="张三"
        )

        assert result["session_id"] == "task-tk-002"
        assert result["content"] == "这是一条评论"
        assert result["role"] == "user"
        assert result["metadata"]["author"] == "张三"
        assert result["metadata"]["type"] == "comment"

    @pytest.mark.asyncio
    async def test_retrieve_task_context(self) -> None:
        """测试检索任务上下文。"""
        ctx = ContextIntegration()

        # 当前返回空列表（等待实际实现）
        contexts = await ctx.retrieve_task_context("tk-001")
        assert isinstance(contexts, list)

    @pytest.mark.asyncio
    async def test_get_task_discussion(self) -> None:
        """测试获取任务讨论历史。"""
        ctx = ContextIntegration()

        discussion = await ctx.get_task_discussion("tk-001")
        assert "tk-001" in discussion
        # 当无上下文时返回"暂无讨论记录"
        assert "暂无讨论记录" in discussion or "讨论历史" in discussion


class TestMemoryIntegration:
    """Memory Plugin 集成测试。"""

    def test_singleton(self) -> None:
        """测试单例模式。"""
        mem1 = get_memory_integration()
        mem2 = get_memory_integration()
        assert mem1 is mem2

    @pytest.mark.asyncio
    async def test_store_task_decision(self) -> None:
        """测试存储任务决策。"""
        mem = MemoryIntegration()

        result = await mem.store_task_decision(
            task_id="tk-001",
            decision="使用 JWT 进行身份验证",
            tags=["authentication", "security"],
            metadata={"author": "tech-lead"},
        )

        assert result["content"] == "使用 JWT 进行身份验证"
        assert "task:tk-001" in result["tags"]
        assert "decision" in result["tags"]
        assert "authentication" in result["tags"]
        assert result["metadata"]["task_id"] == "tk-001"
        assert result["metadata"]["type"] == "decision"

    @pytest.mark.asyncio
    async def test_store_task_learning(self) -> None:
        """测试存储任务学习。"""
        mem = MemoryIntegration()

        result = await mem.store_task_learning(
            task_id="tk-002", learning="学到了新知识", tags=["learning"]
        )

        assert result["content"] == "学到了新知识"
        assert "task:tk-002" in result["tags"]
        assert "learning" in result["tags"]
        assert result["metadata"]["type"] == "learning"

    @pytest.mark.asyncio
    async def test_store_task_solution(self) -> None:
        """测试存储任务解决方案。"""
        mem = MemoryIntegration()

        result = await mem.store_task_solution(
            task_id="tk-003",
            problem="数据库连接失败",
            solution="增加连接池大小",
            tags=["database"],
        )

        assert "问题: 数据库连接失败" in result["content"]
        assert "解决方案: 增加连接池大小" in result["content"]
        assert "task:tk-003" in result["tags"]
        assert "solution" in result["tags"]
        assert result["metadata"]["type"] == "solution"

    @pytest.mark.asyncio
    async def test_search_task_memories(self) -> None:
        """测试搜索任务记忆。"""
        mem = MemoryIntegration()

        # 当前返回空列表（等待实际实现）
        memories = await mem.search_task_memories("tk-001")
        assert isinstance(memories, list)

    @pytest.mark.asyncio
    async def test_get_task_knowledge(self) -> None:
        """测试获取任务知识。"""
        mem = MemoryIntegration()

        knowledge = await mem.get_task_knowledge("tk-001")
        assert "tk-001" in knowledge
        assert "知识" in knowledge

    @pytest.mark.asyncio
    async def test_search_similar_solutions(self) -> None:
        """测试搜索类似解决方案。"""
        mem = MemoryIntegration()

        solutions = await mem.search_similar_solutions("数据库问题")
        assert isinstance(solutions, list)


class TestKnowledgeIntegration:
    """Knowledge Plugin 集成测试。"""

    def test_singleton(self) -> None:
        """测试单例模式。"""
        kb1 = get_knowledge_integration()
        kb2 = get_knowledge_integration()
        assert kb1 is kb2

    @pytest.mark.asyncio
    async def test_add_task_documentation(self) -> None:
        """测试添加任务文档。"""
        kb = KnowledgeIntegration()

        result = await kb.add_task_documentation(
            task_id="tk-001",
            content="任务文档内容",
            source="技术文档",
            metadata={"author": "tech-writer"},
        )

        assert result["content"] == "任务文档内容"
        assert result["source"] == "Task tk-001 - 技术文档"
        assert result["metadata"]["task_id"] == "tk-001"
        assert result["metadata"]["type"] == "task_documentation"

    @pytest.mark.asyncio
    async def test_add_task_solution(self) -> None:
        """测试添加任务解决方案。"""
        kb = KnowledgeIntegration()

        result = await kb.add_task_solution(
            task_id="tk-002",
            title="登录功能实现",
            description="实现用户登录功能",
            solution="使用 JWT 进行身份验证",
            tags=["authentication", "jwt"],
        )

        assert "登录功能实现" in result["content"]
        assert "实现用户登录功能" in result["content"]
        assert "使用 JWT 进行身份验证" in result["content"]
        assert "tk-002" in result["content"]
        assert result["metadata"]["type"] == "solution"

    @pytest.mark.asyncio
    async def test_search_task_knowledge(self) -> None:
        """测试搜索任务知识。"""
        kb = KnowledgeIntegration()

        # 当前返回空列表（等待实际实现）
        results = await kb.search_task_knowledge("JWT")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_similar_tasks(self) -> None:
        """测试搜索类似任务。"""
        kb = KnowledgeIntegration()

        similar = await kb.search_similar_tasks("登录功能")
        assert isinstance(similar, list)

    @pytest.mark.asyncio
    async def test_add_task_lessons_learned(self) -> None:
        """测试添加经验教训。"""
        kb = KnowledgeIntegration()

        result = await kb.add_task_lessons_learned(
            task_id="tk-003",
            lessons=["经验1", "经验2", "经验3"],
            tags=["best-practice"],
        )

        assert "tk-003" in result["content"]
        assert "经验1" in result["content"]
        assert "经验2" in result["content"]
        assert result["metadata"]["type"] == "lessons_learned"

    @pytest.mark.asyncio
    async def test_get_task_references(self) -> None:
        """测试获取任务参考文档。"""
        kb = KnowledgeIntegration()

        references = await kb.get_task_references("tk-001")
        assert "tk-001" in references
        assert "参考文档" in references


class TestIntegrationWorkflow:
    """集成工作流测试。"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self) -> None:
        """测试完整工作流。"""
        task_id = "tk-workflow-001"

        # 1. Context: 保存讨论
        ctx = get_context_integration()
        ctx_result = await ctx.save_task_context(
            task_id=task_id, content="开始实现功能", role="assistant"
        )
        assert ctx_result["session_id"] == f"task-{task_id}"

        # 2. Memory: 存储决策
        mem = get_memory_integration()
        mem_result = await mem.store_task_decision(
            task_id=task_id, decision="使用 SQLAlchemy ORM", tags=["database"]
        )
        assert mem_result["metadata"]["task_id"] == task_id

        # 3. Knowledge: 添加文档
        kb = get_knowledge_integration()
        kb_result = await kb.add_task_documentation(
            task_id=task_id, content="实现文档", source="开发文档"
        )
        assert kb_result["metadata"]["task_id"] == task_id

        # 4. Memory: 存储解决方案
        sol_result = await mem.store_task_solution(
            task_id=task_id, problem="测试问题", solution="测试解决方案"
        )
        assert "测试问题" in sol_result["content"]

        # 5. Knowledge: 添加经验教训
        lesson_result = await kb.add_task_lessons_learned(
            task_id=task_id, lessons=["教训1", "教训2"]
        )
        assert "教训1" in lesson_result["content"]

    @pytest.mark.asyncio
    async def test_error_handling(self) -> None:
        """测试错误处理。"""
        # 即使插件不可用，集成函数也应该返回合理的默认值
        ctx = get_context_integration()

        # 检索不存在的任务应该返回空列表
        contexts = await ctx.retrieve_task_context("tk-nonexistent")
        assert contexts == []

        # 获取不存在的讨论应该返回友好消息
        discussion = await ctx.get_task_discussion("tk-nonexistent")
        assert "暂无讨论记录" in discussion
