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


def handle_pre_compact(hook_data: Dict[str, Any]) -> None:
    """
    对话压缩前提取重要信息
    
    触发时机：Claude Code 准备压缩对话历史时
    操作：分析即将压缩的内容，提取重要信息并保存到记忆系统
    """
    logging.info("handle_pre_compact: 提取重要信息")
    
    transcript_path = hook_data.get("transcript_path", "")
    session_id = hook_data.get("session_id", "")
    
    async def _handle():
        await init_db()
        
        compact_memories = await search_memories("compact", limit=5)
        
        important_keywords = ["决定", "decision", "重要", "important", "关键", "key", "配置", "config"]
        important_memories = []
        
        for keyword in important_keywords:
            memories = await search_memories(keyword, limit=3)
            important_memories.extend(memories)
        
        if important_memories:
            content_lines = ["# 压缩前重要信息提取\n"]
            content_lines.append(f"时间: {datetime.now().isoformat()}\n")
            content_lines.append(f"会话ID: {session_id}\n")
            content_lines.append("\n## 相关记忆:\n")
            
            seen_uris = set()
            for mem in important_memories:
                if mem.uri not in seen_uris:
                    seen_uris.add(mem.uri)
                    content_lines.append(f"- [{mem.uri}] {mem.content[:100]}...\n")
            
            await create_memory(
                uri=f"compact://{datetime.now().strftime('%Y%m%d%H%M%S')}",
                content="".join(content_lines),
                priority=3
            )
            logging.info(f"已保存压缩前信息，包含 {len(seen_uris)} 条相关记忆")
        
        await close_db()
    
    run_async(_handle())


def handle_user_prompt_submit(hook_data: Dict[str, Any]) -> None:
    """
    用户提交提示时分析意图、预加载相关记忆
    
    触发时机：用户提交提示后
    操作：分析用户意图，预加载相关记忆
    """
    prompt = hook_data.get("prompt", "")
    session_id = hook_data.get("session_id", "")
    
    logging.info(f"handle_user_prompt_submit: 分析用户意图")
    
    if not prompt:
        return
    
    async def _handle():
        await init_db()
        
        keywords = []
        
        if "文件" in prompt or "file" in prompt.lower():
            keywords.append("file")
        if "配置" in prompt or "config" in prompt.lower():
            keywords.append("config")
        if "错误" in prompt or "error" in prompt.lower():
            keywords.append("error")
        if "测试" in prompt or "test" in prompt.lower():
            keywords.append("test")
        if "项目" in prompt or "project" in prompt.lower():
            keywords.append("project")
        
        words = prompt.split()
        for word in words:
            if len(word) > 3:
                keywords.append(word)
        
        related_memories = []
        for keyword in keywords[:5]:
            memories = await search_memories(keyword, limit=2)
            related_memories.extend(memories)
        
        if related_memories:
            logging.info(f"预加载 {len(related_memories)} 条相关记忆")
            for mem in related_memories[:5]:
                content_preview = mem.content[:100] if len(mem.content) > 100 else mem.content
                logging.info(f"[预加载:{mem.uri}] {content_preview}...")
        
        await create_memory(
            uri=f"prompt://{datetime.now().strftime('%Y%m%d%H%M%S')}",
            content=f"用户提示: {prompt[:500]}",
            priority=4
        )
        
        await close_db()
    
    run_async(_handle())


def handle_permission_request(hook_data: Dict[str, Any]) -> None:
    """
    权限请求时记录决策、学习偏好
    
    触发时机：Claude Code 请求权限时
    操作：记录权限决策，学习用户偏好
    """
    tool_name = hook_data.get("tool_name", "")
    permission_type = hook_data.get("permission_type", "")
    decision = hook_data.get("decision", "")
    
    logging.info(f"handle_permission_request: tool={tool_name}, type={permission_type}, decision={decision}")
    
    async def _handle():
        await init_db()
        
        await create_memory(
            uri=f"permission://{datetime.now().strftime('%Y%m%d%H%M%S')}",
            content=f"权限请求: {tool_name} - {permission_type} - 决策: {decision}",
            priority=5
        )
        
        if decision == "allow":
            existing = await search_memories(f"权限偏好 {tool_name}", limit=1)
            if not existing:
                await create_memory(
                    uri=f"preference://permission/{tool_name}",
                    content=f"用户偏好: 允许 {tool_name} 的 {permission_type} 权限",
                    priority=2
                )
        
        await close_db()
    
    run_async(_handle())


def handle_notification(hook_data: Dict[str, Any]) -> None:
    """
    发送通知时记录重要通知
    
    触发时机：Claude Code 发送通知时
    操作：记录重要通知内容
    """
    notification_type = hook_data.get("notification_type", "")
    message = hook_data.get("message", "")
    title = hook_data.get("title", "")
    
    logging.info(f"handle_notification: type={notification_type}, title={title}")
    
    if not message:
        return
    
    async def _handle():
        await init_db()
        
        priority = 5
        if "error" in notification_type.lower() or "错误" in message:
            priority = 3
        elif "warning" in notification_type.lower() or "警告" in message:
            priority = 4
        elif "success" in notification_type.lower() or "成功" in message:
            priority = 6
        
        content = f"通知类型: {notification_type}\n"
        if title:
            content += f"标题: {title}\n"
        content += f"内容: {message}"
        
        await create_memory(
            uri=f"notification://{datetime.now().strftime('%Y%m%d%H%M%S')}",
            content=content,
            priority=priority
        )
        
        await close_db()
    
    run_async(_handle())


def handle_subagent_start(hook_data: Dict[str, Any]) -> None:
    """
    Subagent 启动时传递上下文、隔离记忆
    
    触发时机：Subagent 启动时
    操作：传递相关上下文，创建隔离的记忆空间
    """
    subagent_id = hook_data.get("subagent_id", "")
    parent_session_id = hook_data.get("parent_session_id", "")
    task = hook_data.get("task", "")
    
    logging.info(f"handle_subagent_start: subagent={subagent_id}")
    
    async def _handle():
        await init_db()
        
        core_memories = await get_memories_by_priority(max_priority=2)
        
        context_lines = [f"# Subagent 上下文传递\n"]
        context_lines.append(f"Subagent ID: {subagent_id}\n")
        context_lines.append(f"父会话 ID: {parent_session_id}\n")
        context_lines.append(f"任务: {task[:200]}\n")
        context_lines.append("\n## 核心记忆:\n")
        
        for mem in core_memories[:5]:
            context_lines.append(f"- [{mem.uri}] {mem.content[:100]}...\n")
        
        await create_memory(
            uri=f"subagent://{subagent_id}/context",
            content="".join(context_lines),
            priority=2
        )
        
        await create_memory(
            uri=f"subagent://{subagent_id}/start",
            content=f"Subagent 启动: {task[:200]}",
            priority=3
        )
        
        await close_db()
    
    run_async(_handle())


def handle_subagent_stop(hook_data: Dict[str, Any]) -> None:
    """
    Subagent 停止时收集结果、合并记忆
    
    触发时机：Subagent 停止时
    操作：收集执行结果，合并重要记忆到父会话
    """
    subagent_id = hook_data.get("subagent_id", "")
    result = hook_data.get("result", "")
    success = hook_data.get("success", True)
    
    logging.info(f"handle_subagent_stop: subagent={subagent_id}, success={success}")
    
    async def _handle():
        await init_db()
        
        status = "成功" if success else "失败"
        
        await create_memory(
            uri=f"subagent://{subagent_id}/stop",
            content=f"Subagent 停止: {status}\n结果: {result[:500] if result else '无结果'}",
            priority=3
        )
        
        subagent_memories = await search_memories(f"subagent://{subagent_id}", limit=10)
        
        if subagent_memories and success:
            summary_lines = [f"# Subagent {subagent_id} 执行摘要\n"]
            summary_lines.append(f"状态: {status}\n")
            summary_lines.append(f"记忆数量: {len(subagent_memories)}\n")
            summary_lines.append("\n## 关键记忆:\n")
            
            for mem in subagent_memories[:5]:
                summary_lines.append(f"- [{mem.uri}] {mem.content[:100]}...\n")
            
            await create_memory(
                uri=f"subagent://{subagent_id}/summary",
                content="".join(summary_lines),
                priority=3
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
        "PreCompact": handle_pre_compact,
        "UserPromptSubmit": handle_user_prompt_submit,
        "PermissionRequest": handle_permission_request,
        "Notification": handle_notification,
        "SubagentStart": handle_subagent_start,
        "SubagentStop": handle_subagent_stop,
    }
    
    handler = handlers.get(event_name)
    if handler:
        handler(hook_data)
    else:
        logging.debug(f"未处理的事件: {event_name}")
