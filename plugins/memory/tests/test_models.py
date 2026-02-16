"""
模型模块测试
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestMemoryStatus:
    """测试 MemoryStatus 枚举"""
    
    def test_active_value(self):
        from memory.models import MemoryStatus
        
        assert MemoryStatus.ACTIVE.value == "active"
    
    def test_deprecated_value(self):
        from memory.models import MemoryStatus
        
        assert MemoryStatus.DEPRECATED.value == "deprecated"
    
    def test_archived_value(self):
        from memory.models import MemoryStatus
        
        assert MemoryStatus.ARCHIVED.value == "archived"
    
    def test_deleted_value(self):
        from memory.models import MemoryStatus
        
        assert MemoryStatus.DELETED.value == "deleted"
    
    def test_is_string_enum(self):
        from memory.models import MemoryStatus
        
        assert isinstance(MemoryStatus.ACTIVE, str)
        assert MemoryStatus.ACTIVE == "active"


class TestRelationType:
    """测试 RelationType 枚举"""
    
    def test_relates_to_value(self):
        from memory.models import RelationType
        
        assert RelationType.RELATES_TO.value == "relates_to"
    
    def test_depends_on_value(self):
        from memory.models import RelationType
        
        assert RelationType.DEPENDS_ON.value == "depends_on"
    
    def test_contradicts_value(self):
        from memory.models import RelationType
        
        assert RelationType.CONTRADICTS.value == "contradicts"
    
    def test_evolves_from_value(self):
        from memory.models import RelationType
        
        assert RelationType.EVOLVES_FROM.value == "evolves_from"
    
    def test_is_string_enum(self):
        from memory.models import RelationType
        
        assert isinstance(RelationType.RELATES_TO, str)


class TestMemoryModel:
    """测试 Memory 模型"""
    
    def test_table_name(self):
        from memory.models import Memory
        
        assert Memory.__tablename__ == "memories"
    
    def test_has_required_fields(self):
        from memory.models import Memory
        
        assert hasattr(Memory, 'id')
        assert hasattr(Memory, 'uri')
        assert hasattr(Memory, 'content')
        assert hasattr(Memory, 'priority')
        assert hasattr(Memory, 'status')


class TestMemoryPathModel:
    """测试 MemoryPath 模型"""
    
    def test_table_name(self):
        from memory.models import MemoryPath
        
        assert MemoryPath.__tablename__ == "memory_paths"
    
    def test_has_required_fields(self):
        from memory.models import MemoryPath
        
        assert hasattr(MemoryPath, 'id')
        assert hasattr(MemoryPath, 'memory_id')
        assert hasattr(MemoryPath, 'path')


class TestMemoryVersionModel:
    """测试 MemoryVersion 模型"""
    
    def test_table_name(self):
        from memory.models import MemoryVersion
        
        assert MemoryVersion.__tablename__ == "memory_versions"
    
    def test_has_required_fields(self):
        from memory.models import MemoryVersion
        
        assert hasattr(MemoryVersion, 'id')
        assert hasattr(MemoryVersion, 'memory_id')
        assert hasattr(MemoryVersion, 'version')
        assert hasattr(MemoryVersion, 'content')


class TestMemoryRelationModel:
    """测试 MemoryRelation 模型"""
    
    def test_table_name(self):
        from memory.models import MemoryRelation
        
        assert MemoryRelation.__tablename__ == "memory_relations"
    
    def test_has_required_fields(self):
        from memory.models import MemoryRelation
        
        assert hasattr(MemoryRelation, 'id')
        assert hasattr(MemoryRelation, 'source_memory_id')
        assert hasattr(MemoryRelation, 'target_memory_id')
        assert hasattr(MemoryRelation, 'relation_type')


class TestSessionModel:
    """测试 Session 模型"""
    
    def test_table_name(self):
        from memory.models import Session
        
        assert Session.__tablename__ == "sessions"
    
    def test_has_required_fields(self):
        from memory.models import Session
        
        assert hasattr(Session, 'id')
        assert hasattr(Session, 'session_id')
        assert hasattr(Session, 'started_at')


class TestErrorSolutionModel:
    """测试 ErrorSolution 模型"""
    
    def test_table_name(self):
        from memory.models import ErrorSolution
        
        assert ErrorSolution.__tablename__ == "error_solutions"
    
    def test_has_required_fields(self):
        from memory.models import ErrorSolution
        
        assert hasattr(ErrorSolution, 'id')
        assert hasattr(ErrorSolution, 'error_pattern')
        assert hasattr(ErrorSolution, 'solution')
