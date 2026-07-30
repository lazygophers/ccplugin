#!/usr/bin/env python3
"""serve 层路由测试 — 经 starlette TestClient 在进程内跑 build_app(DataSource), 不开真实 socket。

证 build_app 把 /__skein__/* 端点接到注入的 DataSource (而非硬编码 Skein):
  - test_routes_real: 真实 Skein 喂种子仓 → 各端点返回视图数据 (路由接线正确)。
  - test_seam_datasource_injected: 假 DataSource 覆写 _snapshot() → 端点全改吃假数据 (两 adapter = 真 seam)。
  - test_uvicorn_app_string_resolves: uvicorn 按字符串 import 的 app 路径必须真能解析 (搬家易失效)。

复用 test_views_char 的种子逻辑 (_seed/_load/TNOW), 冻结 now() → 确定输出。
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

import conftest  # noqa: F401  先 import 它: 模块体把 scripts/ 塞进 sys.path (standalone 直跑时 pytest 不在)
from skeinlib.serve import build_app  # noqa: E402
from test_views_char import TNOW, _load, _seed  # noqa: E402


def _client(app: Any) -> Any:
    from fastapi.testclient import TestClient
    return TestClient(app)


def _built(m: ModuleType, sk: Any) -> Any:
    proj_id = str(sk.dir.resolve())
    return build_app(sk, proj_id, quiet=True, on_ready=None), proj_id


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
    """假 DataSource 覆写 `_snapshot()` → 数据端点全部改吃假数据, 证端点确实走注入源。

    接缝从「每视图一个方法」收窄成一个 `_snapshot()` 之后, 覆写点就是它 —— 换掉一个方法,
    六个视图端点同时换源, 这本身就是接缝收窄的证据 (从前得逐个覆写 `_dashboard`/`_queue`/…)。
    """
    m = _load()
    cwd0 = os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _seed(d)
        os.chdir(d)
        try:
            sk = _seeded_skein(m, d)
            real = sk._snapshot()
            # 假快照: 除 proj 换成哨兵值外全等真快照 (Snapshot 是 dataclass 式容器, 直接改字段)
            fake_snap = sk._snapshot()
            fake_snap.proj = "FAKE-PROJ"

            class FakeDS:
                def __init__(self, inner: Any) -> None:
                    self._inner = inner

                def __getattr__(self, k: str) -> Any:  # 其余成员透传真 Skein
                    return getattr(self._inner, k)

                def _snapshot(self) -> Any:
                    return fake_snap

            app = build_app(FakeDS(sk), str(sk.dir.resolve()), quiet=True)
            with _client(app) as c:
                # 同一次覆写, 两个不同端点都改了源 → 证明它们共用注入的 _snapshot()
                assert c.get("/__skein__/dashboard").json()["proj"] == "FAKE-PROJ"
                assert c.get("/__skein__/data").json()["proj"] == "FAKE-PROJ"
                assert real.proj != "FAKE-PROJ", "前置条件: 真快照的 proj 不该等于哨兵"
                # 数据仍是真种子仓的 (只换了 proj, 不是整个换成空壳)
                assert any(card["id"] == "alpha" for card in c.get("/__skein__/data").json()["cards"])
        finally:
            os.chdir(cwd0)


def test_uvicorn_app_string_resolves() -> None:
    """`uvicorn.run("<mod>:<attr>")` 里那个字符串必须真能 import 到。

    uvicorn 是在 reload 子进程里按字符串 import 的, 所以函数一旦搬家而字符串没跟着改, 单测全绿、
    端点测试也全绿 —— 只有真起 serve 时才炸 "Attribute not found in module"。这条把那个字符串
    从 skein.py 里抠出来当场 import 一次, 把失效点从「运行时」提前到「测试时」。
    """
    import importlib
    import re

    scripts = Path(__file__).resolve().parent.parent
    found = []
    for f in [scripts / "skein.py", *sorted((scripts / "skeinlib").glob("*.py"))]:
        for m in re.finditer(r'uvicorn\.run\(\s*"([^"]+)"', f.read_text()):
            found.append((f.name, m.group(1)))
    assert found, "全仓没找到 uvicorn.run(\"<mod>:<attr>\") 形式的 app 字符串"
    for fname, ref in found:
        mod_name, _, attr = ref.partition(":")
        assert attr, f"{fname}: app 字符串缺 :<attr> 部分 — {ref}"
        mod = importlib.import_module(mod_name)
        assert hasattr(mod, attr), \
            f"{fname}: {mod_name} 里没有 {attr} — uvicorn 起服务时会 Attribute not found"


if __name__ == "__main__":
    test_routes_real()
    test_seam_datasource_injected()
    test_uvicorn_app_string_resolves()
    print("ok")
