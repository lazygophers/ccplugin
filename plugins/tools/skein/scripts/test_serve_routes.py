#!/usr/bin/env python3
"""serve 层路由测试 — 经 starlette TestClient 在进程内跑 build_app(DataSource), 不开真实 socket。

证 build_app 把 /__skein__/* 端点接到注入的 DataSource (而非硬编码 Skein):
  - test_routes_real: 真实 Skein 喂种子仓 → 各端点返回视图数据 (路由接线正确)。
  - test_seam_datasource_injected: 假 DataSource 覆写 _dashboard 返回哨兵 → 端点回哨兵 (两 adapter = 真 seam)。

复用 test_views_char 的种子逻辑 (_seed/_load/TNOW), 冻结 now() → 确定输出。
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

from test_views_char import TNOW, _load, _seed


def _client(app: Any) -> Any:
    from fastapi.testclient import TestClient
    return TestClient(app)


def _built(m: ModuleType, sk: Any) -> Any:
    proj_id = str(sk.dir.resolve())
    return m.build_app(sk, proj_id, quiet=True, on_ready=None), proj_id


def _seeded_skein(m: ModuleType, d: Path) -> Any:
    saved = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("CLAUDE_PLUGIN_OPTION_")}
    os.environ.update(saved)  # 仅探测键存在与否, 不改行为; 保原样
    m.now = lambda: TNOW  # type: ignore[assignment]
    sk = m.Skein()
    sk.proj = "TESTPROJ"
    return sk


def test_routes_real() -> None:
    m = _load()
    cwd0 = os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _seed(d)
        os.chdir(d)
        try:
            sk = _seeded_skein(m, d)
            app, proj_id = _built(m, sk)
            with _client(app) as c:
                assert c.get("/__skein__/id").text == proj_id
                data = c.get("/__skein__/data").json()
                assert any(card["id"] == "alpha" for card in data["cards"])
                assert c.get("/__skein__/dashboard").json()["proj"] == "TESTPROJ"
                assert "pendingQueue" in c.get("/__skein__/queue").json()
                assert isinstance(c.get("/__skein__/archive").json()["tasks"], list)
                hits = c.get("/__skein__/search", params={"q": "alpha"}).json()["hits"]
                assert any(h["id"] == "alpha" for h in hits)
                assert c.get("/__skein__/task", params={"id": "alpha"}).status_code == 200
                assert c.get("/__skein__/task", params={"id": "ghost1"}).status_code == 404
                assert c.get("/__skein__/task").status_code == 422  # id 必填, 禁 path 参数
                assert c.get("/").status_code == 200
        finally:
            os.chdir(cwd0)


def test_seam_datasource_injected() -> None:
    # 假 DataSource: 全权委托真 Skein, 仅覆写 _dashboard 返哨兵 → 证端点走注入源
    m = _load()
    cwd0 = os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _seed(d)
        os.chdir(d)
        try:
            sk = _seeded_skein(m, d)
            sentinel = {"proj": "FAKE", "taskCount": 999, "_sentinel": True}

            class FakeDS:
                def __init__(self, inner: Any) -> None:
                    self._inner = inner

                def __getattr__(self, k: str) -> Any:  # 其余成员透传真 Skein
                    return getattr(self._inner, k)

                def _dashboard(self) -> dict[str, Any]:
                    return sentinel

            app, _ = m.build_app(FakeDS(sk), str(sk.dir.resolve()), quiet=True), None
            with _client(app) as c:
                assert c.get("/__skein__/dashboard").json() == sentinel
                # 未覆写的端点仍走真 Skein
                assert any(card["id"] == "alpha" for card in c.get("/__skein__/data").json()["cards"])
        finally:
            os.chdir(cwd0)


if __name__ == "__main__":
    test_routes_real()
    test_seam_datasource_injected()
    print("ok")
