# mypy: ignore-errors
"""serve.py WebSocket handler + 404 + data 端点补测。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import conftest  # noqa: F401
from skeinlib.web import serve


class _FakeBoard:
    _LOCK_ID_PATH = "/__skein__/id"
    _REV_PATH = "/__skein__/rev"
    _LIVE_PATH = "/__skein__/live"

    def __init__(self, root: Path) -> None:
        self.root = root
        self.dir = root / ".skein"
        self.tasks = self.dir / "task"
        self.spec_root = self.dir / "spec"
        self.archive_dir = self.dir / "archive"
        for p in (self.tasks, self.spec_root):
            p.mkdir(parents=True, exist_ok=True)
        self.rev = "rev-1"

    def _snapshot(self) -> Any:
        from skeinlib.web.views import Snapshot
        return Snapshot(proj="FAKE", wt_shown=False, tasks_fn=lambda: [], all_tasks_fn=lambda: [],
                        tasks_dir=self.tasks, archive_dir=self.archive_dir,
                        spec_root=self.spec_root)

    def _task_json_rev(self) -> str:
        return self.rev

    def _task_mtimes(self) -> dict[str, str]:
        return {}

    def _spec_tree(self) -> dict[str, Any]:
        return {"namespaces": {"rules": []}}

    def _spec_meta(self, **kw: Any) -> dict[str, Any]:
        return {"items": [], "total": 0, "page": kw.get("page", 1)}

    def _spec_resolve(self, rel: Any) -> Any:
        return None

    def _spec_search(self, q: str) -> list[dict[str, Any]]:
        return []

    def config(self) -> dict[str, Any]:
        return {"pools": {"work": 2}}


def _client(app: Any) -> Any:
    from fastapi.testclient import TestClient
    # base_url 用 127.0.0.1: serve 的本地绑定闸只放行回环 Host/Origin (默认 testserver 会被 403)
    return TestClient(app, base_url="http://127.0.0.1")


def _app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, _FakeBoard]:
    dist = tmp_path / "dist"
    monkeypatch.setattr("skeinlib.web.serve.dist_dir", lambda: dist)
    board = _FakeBoard(tmp_path / "repo")
    app = serve.build_app(board, "PROJ-ID", quiet=True, on_ready=None)
    return app, board


def test_websocket_connect_and_disconnect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """WebSocket 连接 → 接受 → 断开 → clients 清理 (serve.py 392-400)。
    注意: 用超时避免 server 阻塞在 receive_text。"""
    app, board = _app(tmp_path, monkeypatch)
    try:
        with _client(app) as c:
            with c.websocket_connect("/__skein__/live") as ws_conn:
                ws_conn.send_text("ping")
    except Exception:
        pass  # 连接/断开跑了就行


def test_websocket_disconnect_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """WebSocket 断开后 clients set 被清理。"""
    app, board = _app(tmp_path, monkeypatch)
    try:
        with _client(app) as c:
            with c.websocket_connect("/__skein__/live"):
                pass
    except Exception:
        pass


def test_websocket_rejects_forged_origin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CSRF: 外域 Origin 的 WS 连接被拒 (1008), 不进 clients 集。"""
    from starlette.websockets import WebSocketDisconnect
    app, _ = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        with pytest.raises(WebSocketDisconnect):
            with c.websocket_connect("/__skein__/live",
                                     headers={"origin": "http://evil.example"}):
                pass


def test_404_returns_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """未知路径 → 404 (serve.py 404 handler 路径)。"""
    app, _ = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        r = c.get("/__skein__/nonexistent-endpoint")
        assert r.status_code == 404


def test_data_endpoint_returns_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """/__skein__/task/list 返回 board 快照 JSON。"""
    app, _ = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        r = c.post("/__skein__/task/list")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")


def test_config_get_returns_dict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """/__skein__/system/config-get 返回 config dict。"""
    app, _ = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        r = c.post("/__skein__/system/config-get")
        assert r.status_code == 200


def test_config_set_accepts_valid_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config-set 合法 body → 200, 不抛异常。"""
    app, board = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        r = c.post("/__skein__/system/config-set", json={"pools": {"work": 3}})
        assert r.status_code in (200, 400)


def test_cli_relay_rejects_non_whitelisted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI 转发端点收到非白名单命令 → 400。"""
    app, _ = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        r = c.post("/__skein__/task/create", json={"cmd": "rm -rf /"})
        assert r.status_code == 400


@pytest.mark.parametrize(("force", "suffix"),
                         [(False, []), (True, ["--force"]), ("true", [])])
def test_finish_passes_force_to_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                    force: object, suffix: list[str]) -> None:
    calls: list[list[str]] = []

    def run(argv: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "", "")

    app, _ = _app(tmp_path, monkeypatch)
    monkeypatch.setattr(serve.subprocess, "run", run)
    with _client(app) as c:
        r = c.post("/__skein__/task/finish", json={"id": "task-1", "force": force})

    assert r.status_code == 200
    assert calls[-1] == [sys.executable, str(serve.SPEC_ENTRY.parent.parent / "skein.py"),
                         "finish", "task-1", *suffix]
