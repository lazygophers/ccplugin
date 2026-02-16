"""
REST API 模块

提供 FastAPI 应用和 API 端点。
"""

import json
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from memory import (
    init_db,
    close_db,
    create_memory,
    get_memory,
    update_memory,
    delete_memory,
    search_memories,
    list_memories,
    get_versions,
    get_relations,
    get_stats,
)

from .template import HTML_TEMPLATE


class MemoryCreate(BaseModel):
    """创建记忆请求模型"""
    uri: str
    content: str
    priority: int = 5
    disclosure: str = ""


class MemoryUpdate(BaseModel):
    """更新记忆请求模型"""
    content: Optional[str] = None
    priority: Optional[int] = None
    disclosure: Optional[str] = None


async def create_app() -> FastAPI:
    """
    创建 FastAPI 应用
    
    Returns:
        FastAPI 应用实例
    """
    app = FastAPI(title="Memory Manager", description="智能记忆管理 Web 界面")
    
    @app.on_event("startup")
    async def startup():
        await init_db()
    
    @app.on_event("shutdown")
    async def shutdown():
        await close_db()
    
    @app.get("/", response_class=HTMLResponse)
    async def index():
        return HTML_TEMPLATE
    
    @app.get("/api/memories")
    async def api_list_memories(
        uri_prefix: str = "",
        status: Optional[str] = None,
        priority_min: Optional[int] = None,
        priority_max: Optional[int] = None,
        limit: int = Query(50, le=1000),
        offset: int = 0,
    ):
        memories = await list_memories(
            uri_prefix=uri_prefix,
            status=status,
            priority_min=priority_min,
            priority_max=priority_max,
            limit=limit,
            offset=offset,
        )
        return [
            {
                "uri": m.uri,
                "content": m.content,
                "priority": m.priority,
                "disclosure": m.disclosure,
                "status": m.status,
                "access_count": m.access_count,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            }
            for m in memories
        ]
    
    @app.get("/api/memories/{uri:path}")
    async def api_get_memory(uri: str):
        memory = await get_memory(uri, increment_access=False)
        if not memory:
            raise HTTPException(status_code=404, detail="记忆不存在")
        return {
            "uri": memory.uri,
            "content": memory.content,
            "priority": memory.priority,
            "disclosure": memory.disclosure,
            "status": memory.status,
            "access_count": memory.access_count,
            "last_accessed_at": memory.last_accessed_at.isoformat() if memory.last_accessed_at else None,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
            "metadata": json.loads(memory.metadata or "{}"),
        }
    
    @app.post("/api/memories")
    async def api_create_memory(data: MemoryCreate):
        memory = await create_memory(
            uri=data.uri,
            content=data.content,
            priority=data.priority,
            disclosure=data.disclosure,
        )
        return {"uri": memory.uri, "id": memory.id}
    
    @app.put("/api/memories/{uri:path}")
    async def api_update_memory(uri: str, data: MemoryUpdate):
        memory = await update_memory(
            uri=uri,
            content=data.content,
            priority=data.priority,
            disclosure=data.disclosure,
        )
        if not memory:
            raise HTTPException(status_code=404, detail="记忆不存在")
        return {"uri": memory.uri}
    
    @app.delete("/api/memories/{uri:path}")
    async def api_delete_memory(uri: str):
        success = await delete_memory(uri, soft=True)
        if not success:
            raise HTTPException(status_code=404, detail="记忆不存在")
        return {"success": True}
    
    @app.get("/api/search")
    async def api_search_memories(
        q: str,
        uri_prefix: Optional[str] = None,
        limit: int = Query(20, le=100),
    ):
        memories = await search_memories(
            query=q,
            uri_prefix=uri_prefix,
            limit=limit,
        )
        return [
            {
                "uri": m.uri,
                "content": m.content,
                "priority": m.priority,
                "status": m.status,
            }
            for m in memories
        ]
    
    @app.get("/api/stats")
    async def api_get_stats():
        return await get_stats()
    
    @app.get("/api/versions/{uri:path}")
    async def api_get_versions(uri: str, limit: int = Query(20, le=100)):
        versions = await get_versions(uri, limit=limit)
        return [
            {
                "version": v.version,
                "content": v.content,
                "changed_at": v.changed_at.isoformat() if v.changed_at else None,
                "change_reason": v.change_reason,
                "changed_by": v.changed_by,
            }
            for v in versions
        ]
    
    @app.get("/api/relations/{uri:path}")
    async def api_get_relations(uri: str, direction: str = "both"):
        relations = await get_relations(uri, direction=direction)
        return relations
    
    return app
