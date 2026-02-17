"""
REST API 模块

提供 FastAPI 应用和 API 端点。
"""

import json
import os
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
    handle_system_uri,
    is_system_uri,
    rollback_to_version,
    diff_versions,
    clean_memories,
)

from .template import get_template_path


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


def create_app() -> FastAPI:
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
        template_path = os.path.join(get_template_path(), "index.html")
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    
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
                "created_at": m.created_at,
                "updated_at": m.updated_at,
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
            "last_accessed_at": memory.last_accessed_at,
            "created_at": memory.created_at,
            "updated_at": memory.updated_at,
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
                "changed_at": v.changed_at,
                "change_reason": v.change_reason,
                "changed_by": v.changed_by,
            }
            for v in versions
        ]
    
    @app.get("/api/relations/{uri:path}")
    async def api_get_relations(uri: str, direction: str = "both"):
        relations = await get_relations(uri, direction=direction)
        return relations
    
    @app.get("/api/system/{path:path}")
    async def api_system_uri(path: str, limit: int = Query(20, le=100)):
        uri = f"system://{path}"
        result = await handle_system_uri(uri, limit=limit)
        if not result:
            raise HTTPException(status_code=404, detail="未知的系统 URI")
        return result
    
    @app.post("/api/rollback/{uri:path}")
    async def api_rollback(uri: str, version: int):
        memory = await rollback_to_version(uri, version)
        if not memory:
            raise HTTPException(status_code=400, detail="回滚失败")
        return {"success": True, "uri": memory.uri}
    
    @app.get("/api/diff/{uri:path}")
    async def api_diff(uri: str, version1: int, version2: int):
        result = await diff_versions(uri, version1, version2)
        if not result:
            raise HTTPException(status_code=400, detail="无法获取版本差异")
        return {
            "version1": version1,
            "version2": version2,
            "content1": result[0],
            "content2": result[1],
        }
    
    @app.post("/api/cleanup")
    async def api_cleanup(
        unused_days: Optional[int] = None,
        deprecated_days: Optional[int] = None,
        dry_run: bool = True,
    ):
        stats = await clean_memories(unused_days, deprecated_days, dry_run)
        return stats
    
    return app
