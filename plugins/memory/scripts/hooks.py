import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from lib import logging
from lib.hooks import load_hooks
from lib.utils import get_plugins_path

from memory import (
    init_db,
    close_db,
    create_memory,
    get_memory,
    search_memories,
    delete_memory,
    list_memories,
    add_memory_path,
    get_memory_paths,
    get_memories_by_priority,
    create_session,
    end_session,
    record_error_solution,
    find_error_solution,
    mark_solution_success,
)


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)


def handle_session_start(hook_data: Dict[str, Any]) -> None:
    logging.info("handle_session_start: 加载会话记忆")
    
    async def _handle():
        await init_db()
        
        core_memories = await get_memories_by_priority(max_priority=3)
        
        if core_memories:
            for mem in core_memories:
                content_preview = mem.content[:200] if len(mem.content) > 200 else mem.content
                print(f"[Memory:{mem.uri}] {content_preview}...")
    
    run_async(_handle())


def handle_session_end(hook_data: Dict[str, Any]) -> None:
    logging.info("handle_session_end: 保存会话记忆")
    message = hook_data.get("message", "")
    
    if message:
        async def _handle():
            await init_db()
            await create_memory(
                uri=f"session://{datetime.now().strftime('%Y%m%d%H%M%S')}",
                content=message,
                priority=3
            )
            await close_db()
        
        run_async(_handle())


def handle_pre_tool_use(hook_data: Dict[str, Any]) -> None:
    tool_name = hook_data.get("tool_name", "").lower()
    tool_input = hook_data.get("tool_input", {})
    
    logging.debug(f"handle_pre_tool_use: tool={tool_name}")
    
    if tool_name in ("read", "edit", "write"):
        file_path = tool_input.get("file_path", "")
        if file_path:
            async def _handle():
                await init_db()
                memories = await search_memories(file_path, limit=3)
                for mem in memories:
                    content_preview = mem.content[:100] if len(mem.content) > 100 else mem.content
                    logging.info(f"[相关记忆:{mem.uri}] {content_preview}...")
                await close_db()
            
            run_async(_handle())


def handle_post_tool_use(hook_data: Dict[str, Any]) -> None:
    tool_name = hook_data.get("tool_name", "").lower()
    tool_input = hook_data.get("tool_input", {})
    tool_result = hook_data.get("tool_result", "")
    
    logging.debug(f"handle_post_tool_use: tool={tool_name}")
    
    if tool_name in ("edit", "write"):
        file_path = tool_input.get("file_path", "")
        if file_path and tool_result:
            async def _handle():
                await init_db()
                result_preview = tool_result[:500] if len(tool_result) > 500 else tool_result
                await create_memory(
                    uri=f"file://{file_path}",
                    content=f"文件操作: {tool_name} - {result_preview}",
                    priority=4
                )
                await close_db()
            
            run_async(_handle())


def handle_post_tool_use_failure(hook_data: Dict[str, Any]) -> None:
    tool_name = hook_data.get("tool_name", "").lower()
    tool_input = hook_data.get("tool_input", {})
    error = hook_data.get("error", "未知错误")
    
    logging.warning(f"handle_post_tool_use_failure: tool={tool_name}, error={error}")
    
    async def _handle():
        await init_db()
        await create_memory(
            uri=f"error://{datetime.now().strftime('%Y%m%d%H%M%S')}",
            content=f"工具失败: {tool_name} - {error}",
            priority=7
        )
        await close_db()
    
    run_async(_handle())


def handle_stop(hook_data: Dict[str, Any]) -> None:
    logging.info("handle_stop: 保存会话状态")
    reason = hook_data.get("reason", "unknown")
    
    async def _handle():
        await init_db()
        await create_memory(
            uri=f"stop://{datetime.now().strftime('%Y%m%d%H%M%S')}",
            content=f"会话停止: {reason}",
            priority=2
        )
        await close_db()
    
    run_async(_handle())


def handle_hook() -> None:
    hook_data = load_hooks()
    event_name = hook_data.get("hook_event_name", "")
    
    handlers = {
        "SessionStart": handle_session_start,
        "SessionEnd": handle_session_end,
        "PreToolUse": handle_pre_tool_use,
        "PostToolUse": handle_post_tool_use,
        "PostToolUseFailure": handle_post_tool_use_failure,
        "Stop": handle_stop,
    }
    
    handler = handlers.get(event_name)
    if handler:
        handler(hook_data)
    else:
        logging.debug(f"未处理的事件: {event_name}")
