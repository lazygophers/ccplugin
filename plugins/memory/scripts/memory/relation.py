"""
关系管理模块

提供记忆之间的关系管理功能。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import Memory, MemoryRelation, RelationType


async def add_relation(
    source_uri: str,
    target_uri: str,
    relation_type: RelationType,
    strength: float = 0.5,
) -> Optional[MemoryRelation]:
    """
    添加记忆关系
    
    在两条记忆之间建立关系，构建知识图谱。
    如果关系已存在，则更新关系强度。
    
    Args:
        source_uri: 源记忆 URI
        target_uri: 目标记忆 URI
        relation_type: 关系类型，参见 RelationType
        strength: 关系强度 0-1，默认 0.5
        
    Returns:
        Optional[MemoryRelation]: 创建或更新的关系对象，
                                  任一记忆不存在则返回 None
    """
    source = await Memory.first(where="uri = ?", params=(source_uri,))
    target = await Memory.first(where="uri = ?", params=(target_uri,))
    
    if not source or not target:
        return None
    
    existing = await MemoryRelation.first(
        where="source_memory_id = ? AND target_memory_id = ? AND relation_type = ?",
        params=(source.id, target.id, relation_type.value),
    )
    
    if existing:
        existing.strength = strength
        await existing.save()
        return existing
    
    return await MemoryRelation.create(
        source_memory_id=source.id,
        target_memory_id=target.id,
        relation_type=relation_type.value,
        strength=strength,
        created_at=datetime.now(),
    )


async def get_relations(uri: str, direction: str = "both") -> List[Dict[str, Any]]:
    """
    获取记忆的关系列表
    
    返回与指定记忆相关的所有关系，可选择方向。
    
    Args:
        uri: 记忆的唯一标识符
        direction: 关系方向
            - "out": 只返回出向关系（该记忆指向其他记忆）
            - "in": 只返回入向关系（其他记忆指向该记忆）
            - "both": 返回所有关系（默认）
        
    Returns:
        List[Dict[str, Any]]: 关系信息列表
    """
    memory = await Memory.first(where="uri = ?", params=(uri,))
    if not memory:
        return []
    
    results = []
    
    if direction in ("out", "both"):
        outgoing = await MemoryRelation.find(
            where="source_memory_id = ?",
            params=(memory.id,),
        )
        for rel in outgoing:
            target = await Memory.first(where="id = ?", params=(rel.target_memory_id,))
            if target:
                results.append({
                    "relation_type": rel.relation_type,
                    "strength": rel.strength,
                    "target_uri": target.uri,
                    "direction": "out",
                })
    
    if direction in ("in", "both"):
        incoming = await MemoryRelation.find(
            where="target_memory_id = ?",
            params=(memory.id,),
        )
        for rel in incoming:
            source = await Memory.first(where="id = ?", params=(rel.source_memory_id,))
            if source:
                results.append({
                    "relation_type": rel.relation_type,
                    "strength": rel.strength,
                    "source_uri": source.uri,
                    "direction": "in",
                })
    
    return results


async def remove_relation(source_uri: str, target_uri: str, relation_type: Optional[RelationType] = None) -> bool:
    """
    移除记忆关系
    
    删除两条记忆之间的关系。可指定关系类型，或删除所有关系类型。
    
    Args:
        source_uri: 源记忆 URI
        target_uri: 目标记忆 URI
        relation_type: 可选的关系类型，如不指定则删除所有类型的关系
        
    Returns:
        bool: 成功删除返回 True，关系不存在返回 False
    """
    source = await Memory.first(where="uri = ?", params=(source_uri,))
    target = await Memory.first(where="uri = ?", params=(target_uri,))
    
    if not source or not target:
        return False
    
    if relation_type:
        count = await MemoryRelation.delete(
            where="source_memory_id = ? AND target_memory_id = ? AND relation_type = ?",
            params=(source.id, target.id, relation_type.value),
        )
    else:
        count = await MemoryRelation.delete(
            where="source_memory_id = ? AND target_memory_id = ?",
            params=(source.id, target.id),
        )
    
    return count > 0
