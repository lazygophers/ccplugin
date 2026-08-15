"""API 全链路集成测试 — 真 uvicorn 进程 + 真落盘 (容器卷), 覆盖 task 完整生命周期与守门。

通道: /__skein__/* HTTP 端点 (web 前端同款) + 容器内 skein CLI (exec 白名单外命令)。
"""
from __future__ import annotations

import uuid

import httpx


def _tid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _cli_post(api: httpx.Client, path: str, body: dict) -> dict:
    """CLI 类端点: HTTP 200 但 body.ok=false 表示命令失败, 当断言异常抛出。"""
    r = api.post(path, json=body)
    r.raise_for_status()
    d = r.json()
    assert d.get("ok") is True, f"{path} 命令失败: {d.get('stderr') or d.get('stdout')}"
    return d


# ── 基础设施 ──────────────────────────────────────────────────────────────

def test_identity_probe(api: httpx.Client) -> None:
    r = api.get("/__skein__/id")
    assert r.status_code == 200
    assert "/workspace" in r.text  # 项目标识 = .skein 绝对路径


def test_board_empty_then_create(api: httpx.Client) -> None:
    r = api.post("/__skein__/task/list")
    assert r.status_code == 200
    assert "overview" in r.json()
    tid = _tid("probe")
    _cli_post(api, "/__skein__/task/create", {"id": tid, "name": "探针", "desc": "冒烟"})
    card = next(c for c in api.post("/__skein__/task/list").json()["cards"] if c["id"] == tid)
    assert card["status"] == "pending"


# ── task 完整生命周期: create → spec → design → subtask → confirm → check → finishing → finish ──

def test_task_full_lifecycle(api: httpx.Client, skein) -> None:
    tid = _tid("life")
    _cli_post(api, "/__skein__/task/create",
              {"id": tid, "name": "全链路", "desc": "集成测试生命周期", "estimate": "10"})

    # TaskSpec 四要素补齐 (CLI 通道 — serve 端点未覆盖 spec 写)
    skein("task", "spec", tid, "--should", "覆盖生命周期; 落盘可查",
          "--not", "不碰 exec 阶段", "--acceptance", "终态 done; 时间线完整")
    spec = skein("task", "spec", tid).stdout
    assert "验收" in spec or "acceptance" in spec.lower()

    # design.md 测试接缝 (confirm 硬门)
    skein("design", "seam", tid, "--list", "- [ ] API 层接缝\n- [ ] CLI 层接缝")

    # subtask DAG: st1 前置, st2 依赖 st1
    _cli_post(api, "/__skein__/subtask/add",
              {"id": tid, "sid": "st1", "name": "前置", "desc": "定 schema 接缝", "estimate": "2"})
    _cli_post(api, "/__skein__/subtask/add",
              {"id": tid, "sid": "st2", "name": "下游", "desc": "消费 st1 产物", "estimate": "1.5",
               "deps": "st1"})

    # confirm: 齐备后放行 (force = 看板「确认规划」同款通道)
    _cli_post(api, "/__skein__/task/confirm", {"id": tid, "force": True})
    detail = api.post("/__skein__/task/get", json={"id": tid}).json()
    assert detail["task"]["status"] == "active"

    # subtask 全 done (CLI 自跑收尾通道) → board 反映
    skein("subtask", "start", tid, "st1")
    skein("subtask", "done", tid, "st1")
    skein("subtask", "start", tid, "st2")
    skein("subtask", "done", tid, "st2")
    detail = api.post("/__skein__/task/get", json={"id": tid}).json()
    assert all(s["status"] == "done" for s in detail["subtasks"])

    # check → finishing → finish (finish 会合 worktree, 容器内有 git 仓)
    skein("task", "check", tid)
    skein("task", "finishing", tid)
    r = skein("task", "finish", tid, ok=False)
    assert r.returncode == 0, f"finish 失败:\n{r.stdout}\n{r.stderr}"
    detail = api.post("/__skein__/task/get", json={"id": tid}).json()
    assert detail["task"]["status"] == "done"


# ── confirm 硬门 ─────────────────────────────────────────────────────────

def test_confirm_rejected_when_planning_incomplete(api: httpx.Client) -> None:
    tid = _tid("gate")
    _cli_post(api, "/__skein__/task/create", {"id": tid, "name": "占位", "desc": "啥都没填"})
    r = api.post("/__skein__/task/confirm", json={"id": tid, "force": False})
    d = r.json()
    assert d.get("ok") is False
    assert "未就绪" in (d.get("stderr") or ""), d
    # 状态未被推进
    detail = api.post("/__skein__/task/get", json={"id": tid}).json()
    assert detail["task"]["status"] == "pending"


# ── design-save 守门 ─────────────────────────────────────────────────────

def test_design_save_validation(api: httpx.Client, skein) -> None:
    tid = _tid("design")
    _cli_post(api, "/__skein__/task/create", {"id": tid, "name": "设计", "desc": "design-save 守门"})
    _cli_post(api, "/__skein__/task/create", {"id": f"{tid}-2", "name": "邻位", "desc": "路径穿越靶"})

    # 合法写: 全文落盘, task/get 可见
    content = "# 详细设计\n\n## 测试接缝 (seam)\n\n- [ ] API 层\n- [ ] UI 层\n"
    r = api.post("/__skein__/task/design-save", json={"id": tid, "content": content})
    assert r.status_code == 200 and r.json()["ok"] is True
    assert api.post("/__skein__/task/get", json={"id": tid}).json()["docs"]["design"] == content

    # 路径穿越 id 拒绝
    for evil in ("../../etc", "a/b", ".."):
        r = api.post("/__skein__/task/design-save", json={"id": evil, "content": "x"})
        assert r.status_code == 400, evil

    # 不存在的 task
    r = api.post("/__skein__/task/design-save", json={"id": "no-such-task", "content": "x"})
    assert r.status_code == 404


# ── config hooks 拒写 (RCE 守门) ─────────────────────────────────────────

def test_config_hooks_never_persisted(api: httpx.Client) -> None:
    before = api.post("/__skein__/system/config-get").json()
    original_hooks = before.get("hooks")
    api.post("/__skein__/system/config-set",
             json={**before, "hooks": {"SessionStart": "rm -rf /"}})
    after = api.post("/__skein__/system/config-get").json()
    assert after.get("hooks") == original_hooks
    assert "rm -rf" not in str(after.get("hooks"))


# ── 软删 → 回收站 → 清空 ─────────────────────────────────────────────────

def test_trash_flow(api: httpx.Client) -> None:
    tid = _tid("trash")
    _cli_post(api, "/__skein__/task/create", {"id": tid, "name": "待删", "desc": "回收站流转"})
    _cli_post(api, "/__skein__/task/delete", {"id": tid, "force": True})

    trashed = api.post("/__skein__/trash/list").json()["tasks"]
    assert any(t["id"] == tid for t in trashed)

    r = api.post("/__skein__/trash/purge", json={"id": tid})
    assert r.json()["ok"] is True
    trashed = api.post("/__skein__/trash/list").json()["tasks"]
    assert not any(t["id"] == tid for t in trashed)


# ── exec 白名单: 参数非法一律拒 ──────────────────────────────────────────

def test_exec_whitelist_rejects_bad_params(api: httpx.Client) -> None:
    # create 缺 name/desc → 400 (exec_argv 拒绝)
    r = api.post("/__skein__/task/create", json={"id": "bad"})
    assert r.status_code == 400
    # subtask-add 缺 estimate → 400
    r = api.post("/__skein__/subtask/add",
                 json={"id": "x", "sid": "s1", "name": "n", "desc": "d"})
    assert r.status_code == 400
