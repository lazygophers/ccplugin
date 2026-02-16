"""
关系管理模块测试
"""

import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture
async def db_with_relations():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
            from memory.database import init_db, close_db
            from memory import create_memory
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            await create_memory(uri="test://source", content="源记忆")
            await create_memory(uri="test://target", content="目标记忆")
            
            yield
            
            await close_db()
            db_module._db_initialized = False


class TestAddRelation:
    """测试 add_relation 函数"""
    
    @pytest.mark.asyncio
    async def test_add_relation(self, db_with_relations):
        from memory import add_relation
        from memory.models import RelationType
        
        relation = await add_relation(
            "test://source",
            "test://target",
            RelationType.RELATES_TO,
        )
        
        assert relation is not None
        assert relation.relation_type == "relates_to"
    
    @pytest.mark.asyncio
    async def test_add_relation_with_strength(self, db_with_relations):
        from memory import add_relation
        from memory.models import RelationType
        
        relation = await add_relation(
            "test://source",
            "test://target",
            RelationType.DEPENDS_ON,
            strength=0.8,
        )
        
        assert relation.strength == 0.8
    
    @pytest.mark.asyncio
    async def test_add_relation_nonexistent_memory(self, db_with_relations):
        from memory import add_relation
        from memory.models import RelationType
        
        relation = await add_relation(
            "test://nonexistent",
            "test://target",
            RelationType.RELATES_TO,
        )
        
        assert relation is None
    
    @pytest.mark.asyncio
    async def test_update_existing_relation(self, db_with_relations):
        from memory import add_relation
        from memory.models import RelationType
        
        await add_relation("test://source", "test://target", RelationType.RELATES_TO, strength=0.5)
        
        relation = await add_relation("test://source", "test://target", RelationType.RELATES_TO, strength=0.9)
        
        assert relation.strength == 0.9


class TestGetRelations:
    """测试 get_relations 函数"""
    
    @pytest.mark.asyncio
    async def test_get_outgoing_relations(self, db_with_relations):
        from memory import add_relation, get_relations
        from memory.models import RelationType
        
        await add_relation("test://source", "test://target", RelationType.RELATES_TO)
        
        relations = await get_relations("test://source", direction="out")
        
        assert len(relations) >= 1
        assert all(r["direction"] == "out" for r in relations)
    
    @pytest.mark.asyncio
    async def test_get_incoming_relations(self, db_with_relations):
        from memory import add_relation, get_relations
        from memory.models import RelationType
        
        await add_relation("test://source", "test://target", RelationType.RELATES_TO)
        
        relations = await get_relations("test://target", direction="in")
        
        assert len(relations) >= 1
        assert all(r["direction"] == "in" for r in relations)
    
    @pytest.mark.asyncio
    async def test_get_both_relations(self, db_with_relations):
        from memory import add_relation, get_relations
        from memory.models import RelationType
        
        await add_relation("test://source", "test://target", RelationType.RELATES_TO)
        
        relations = await get_relations("test://source", direction="both")
        
        assert len(relations) >= 1
    
    @pytest.mark.asyncio
    async def test_get_relations_nonexistent(self, db_with_relations):
        from memory import get_relations
        
        relations = await get_relations("test://nonexistent")
        
        assert len(relations) == 0


class TestRemoveRelation:
    """测试 remove_relation 函数"""
    
    @pytest.mark.asyncio
    async def test_remove_relation(self, db_with_relations):
        from memory import add_relation, remove_relation, get_relations
        from memory.models import RelationType
        
        await add_relation("test://source", "test://target", RelationType.RELATES_TO)
        
        result = await remove_relation("test://source", "test://target", RelationType.RELATES_TO)
        
        assert result is True
        
        relations = await get_relations("test://source")
        assert not any(r["target_uri"] == "test://target" for r in relations)
    
    @pytest.mark.asyncio
    async def test_remove_all_relations(self, db_with_relations):
        from memory import add_relation, remove_relation
        from memory.models import RelationType
        
        await add_relation("test://source", "test://target", RelationType.RELATES_TO)
        await add_relation("test://source", "test://target", RelationType.DEPENDS_ON)
        
        result = await remove_relation("test://source", "test://target")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_relation(self, db_with_relations):
        from memory import remove_relation
        from memory.models import RelationType
        
        result = await remove_relation("test://source", "test://target", RelationType.RELATES_TO)
        
        assert result is False
