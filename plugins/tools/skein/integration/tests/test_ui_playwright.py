"""浏览器级 UI 集成测试 (Playwright chromium headless) — 真前端 dist + 真后端。

Playwright 未装时整文件跳过 (run.sh 安装失败不影响 API/WS 层结果)。
"""
from __future__ import annotations

import uuid

import httpx
import pytest

pw = pytest.importorskip("playwright.sync_api", reason="playwright 未安装")
from playwright.sync_api import sync_playwright  # noqa: E402

BASE = "http://127.0.0.1:8841"


def _tid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _create(api: httpx.Client, tid: str) -> None:
    r = api.post("/__skein__/task/create", json={"id": tid, "name": "UI测试", "desc": "浏览器层"})
    assert r.json().get("ok") is True


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
        page = context.new_page()
        yield page
        browser.close()


def test_board_renders(page) -> None:
    page.goto(f"{BASE}/board/")
    # 侧边导航 + 看板骨架渲染 (来自 dist 静态产物)
    page.wait_for_selector("text=看板", timeout=15_000)
    assert page.locator("nav, aside").first.is_visible()


def test_detail_prd_cards_always_present(api: httpx.Client, page) -> None:
    """PRD 三段固定渲染: 空 task 也亮目标/边界/验收标准卡 + 详细设计卡 (需求: 空也要展示)。"""
    tid = _tid("ui-empty")
    _create(api, tid)
    page.goto(f"{BASE}/task/detail/?id={tid}")
    page.wait_for_selector("h3:has-text('目标')", timeout=15_000)  # React fetch 完成后才渲染内容区
    for title in ("目标", "边界", "验收标准", "详细设计"):
        assert page.locator(f"h3:has-text('{title}')").first.is_visible(), title


@pytest.mark.xfail(reason="已知断裂: TaskSpec 重构移除了 serve /task/prd 端点与 exec_policy prd 白名单, "
                          "前端 PrdSectionCard 的 api.prd 调用 404 — 待前端适配 TaskSpec 后恢复",
                   strict=True)
def test_prd_section_edit_and_save(api: httpx.Client, page) -> None:
    """目标卡: 编辑 → 填一条 → 保存 → 落盘回显 (走 /task/prd → prd write 整章重建)。"""
    tid = _tid("ui-edit")
    _create(api, tid)
    page.goto(f"{BASE}/task/detail/?id={tid}")

    # 卡片容器 class 定位 (外层布局 div 会嵌套命中, 用 Card 本体的 rounded-lg 圈住)
    card = page.locator("div.rounded-lg", has=page.locator("h3", has_text="目标")).first
    card.get_by_role("button", name="编辑").click()
    card.locator("textarea").fill("浏览器编辑的目标条目")
    card.get_by_role("button", name="保存", exact=True).click()
    page.wait_for_selector("text=浏览器编辑的目标条目", timeout=15_000)
    # 落盘确认: task/get 回读
    docs = api.post("/__skein__/task/get", json={"id": tid}).json()
    prd_text = (docs.get("prd") if isinstance(docs.get("prd"), str) else "") or ""
    assert "浏览器编辑的目标条目" in prd_text or "浏览器编辑的目标条目" in str(docs)


def test_sid_click_copies_tid_and_sid(api: httpx.Client, page) -> None:
    """点击 sid → 剪贴板含 "tid sid" 空格分隔 (需求: 同时复制 tid+sid)。"""
    tid = _tid("ui-copy")
    _create(api, tid)
    r = api.post("/__skein__/subtask/add",
                 json={"id": tid, "sid": "st9", "name": "复制靶", "desc": "锚定接缝", "estimate": "1"})
    assert r.json().get("ok") is True

    page.goto(f"{BASE}/task/detail/?id={tid}")
    sid_span = page.locator(f"text={tid} st9").first  # tooltip/文本不显示 tid; 定位 sid span
    sid_span = page.locator("span[title*='复制']").filter(has_text="st9").first
    sid_span.click()
    clipboard = page.evaluate("navigator.clipboard.readText()")
    assert clipboard.strip() == f"{tid} st9"
