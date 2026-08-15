"""WS 热重载集成测试 — 真容器里的 watchfiles 监听 → /__skein__/live 增量推送。

链路: 数据落盘 (CLI/exec 端点) → watch_loop 检测 mtime/card sig 变化 → 推 task-changed。
"""
from __future__ import annotations

import asyncio
import json
import uuid

import httpx
import websockets


def _tid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


async def _first_push(url: str, action, timeout: float = 20.0) -> dict | str:
    """连 WS, 执行 action, 返回第一条非自身触发的服务端推送。"""
    async with websockets.connect(url, open_timeout=10) as ws:
        await action()
        msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
    try:
        return json.loads(msg)
    except (TypeError, ValueError):
        return msg  # 兜底旧字符串消息 ("data"/"reload")


def _run(coro):
    return asyncio.run(coro)


def test_task_create_pushes_task_changed(api: httpx.Client, base: str) -> None:
    tid = _tid("ws-create")

    async def action():
        r = api.post("/__skein__/task/create", json={"id": tid, "name": "WS新建", "desc": "推送"})
        assert r.json().get("ok") is True

    msg = _run(_first_push(f"{base.replace('http', 'ws')}/__skein__/live", action))
    # 期望精准 task-changed (含 id), 也接受兜底 "data" 全刷
    if isinstance(msg, dict):
        assert msg.get("type") == "task-changed"
        assert msg.get("id") == tid
    else:
        assert msg == "data"


def test_design_save_pushes_task_changed(api: httpx.Client, base: str) -> None:
    tid = _tid("ws-doc")
    r = api.post("/__skein__/task/create", json={"id": tid, "name": "WS文档", "desc": "文档推送"})
    assert r.json().get("ok") is True
    import time
    time.sleep(1)  # 让创建本身的推送先过去

    async def action():
        r = api.post("/__skein__/task/design-save",
                     json={"id": tid, "content": "# 设计\n\n## 测试接缝 (seam)\n\n- [ ] 接缝A\n"})
        assert r.json().get("ok") is True

    msg = _run(_first_push(f"{base.replace('http', 'ws')}/__skein__/live", action))
    if isinstance(msg, dict):
        assert msg.get("type") == "task-changed"
        assert msg.get("id") == tid
    else:
        assert msg == "data"
