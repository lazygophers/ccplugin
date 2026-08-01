"""前端 ETA 数学回归 — 经 node 跑 `assets/webapp/src/new/{model,eta}.js` 的纯函数。

## 为什么这两个模块能被测
它们原本埋在 `app.js` 里, 而 app.js 一被 import 就自启动 (碰 `document`), 于是这套算法在
浏览器外根本跑不起来, 只能靠人眼看看板。抽成 `model.js` (字段/状态规范化) + `eta.js` (ETA 数学)
之后, node 直接 import 就能验。

## 为什么值得测
看板的「预计剩余」是唯一给用户「还要多久」答案的地方, 而它依赖两件容易静默错的事:
① 中文状态映射 —— 没映上就走 `OWN_LEFT` 的兜底系数 0.6, 数字会**悄悄偏**而不会报错;
② 并发折算 —— `max_active` 缺省 2, 累加与墙钟差一倍, 口径搞混就是答非所问。

node 缺失时 skip (纯 stdlib 铁律只约束 Python 侧; 前端资产本就需要浏览器/node 环境)。
"""
from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

import pytest

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from conftest import SCRIPTS  # noqa: E402

WEBAPP = SCRIPTS.parent / "assets" / "webapp" / "src" / "new"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="需要 node 才能跑前端模块")

# 三个 task: b 依赖 a, c 独立。全部 planning (OWN_LEFT=1, 剩余 = 全额估时)。
TASKS = [
    {"id": "a", "status": "待处理", "estimate": 10, "spct": 0, "deps": [], "subtable": []},
    {"id": "b", "status": "待处理", "estimate": 20, "spct": 0, "deps": ["a"], "subtable": []},
    {"id": "c", "status": "待处理", "estimate": 6, "spct": 0, "deps": [], "subtable": []},
    {"id": "d", "status": "已完成", "estimate": 8, "spct": 100, "deps": [], "subtable": []},
]


def _eval(tasks: list[dict[str, Any]], max_active: int) -> dict[str, Any]:
    """跑真 model.normalizeTasks + eta.{overallProgress,aggregateEta}, 返回结果 dict。"""
    script = f"""
      const M = await import({str(WEBAPP / 'model.js')!r});
      const E = await import({str(WEBAPP / 'eta.js')!r});
      const T = M.normalizeTasks({json.dumps(tasks)});
      const a = E.aggregateEta(T, {max_active});
      console.log(JSON.stringify({{
        statuses: T.map(t => t.status),
        overall: E.overallProgress(T),
        hours: a.hours, work: a.work, critical: a.critical, unknown: a.unknown,
      }}));
    """
    r = subprocess.run(["node", "--input-type=module", "-e", script],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"node 跑失败:\n{r.stderr}"
    return dict(json.loads(r.stdout.strip()))


def test_chinese_status_maps_before_eta_math() -> None:
    """中文状态必须先映成 5 状态 —— 没映上不会报错, 只会让 ETA 走兜底系数悄悄偏。"""
    out = _eval(TASKS, 2)
    assert out["statuses"] == ["planning", "planning", "planning", "done"], out["statuses"]


def test_wall_clock_folds_by_concurrency() -> None:
    """墙钟 = max(关键路径, 总工时/并发) —— 并发变了结果必须跟着变。

    a(10) → b(20) 串行 = 30h 关键路径; c(6) 并行。总工时 36h。
    并发 2: max(30, 18) = 30h (关键路径压不动)。并发 1: max(30, 36) = 36h。
    """
    two = _eval(TASKS, 2)
    one = _eval(TASKS, 1)
    assert two["work"] == 36, two
    assert two["critical"] == 30, two
    assert two["hours"] == 30, "并发 2 下应被关键路径卡住"
    assert one["hours"] == 36, "并发 1 下应等于总工时"
    assert one["hours"] > two["hours"], "并发降低, 墙钟必须变长"


def test_done_tasks_excluded() -> None:
    """已完成 task 不进剩余 —— d 估了 8h 但已完成, 不该出现在任何一项里。"""
    out = _eval(TASKS, 2)
    assert out["work"] == 36, f"已完成的 8h 混进了总工时: {out['work']}"


def test_overall_progress_is_estimate_weighted() -> None:
    """整体进度按工时加权 —— 一个 40h 的 task 不该和 1h 的各占一半分母。"""
    heavy_done = [
        {"id": "big", "status": "已完成", "estimate": 40, "spct": 100, "deps": [], "subtable": []},
        {"id": "tiny", "status": "待处理", "estimate": 1, "spct": 0, "deps": [], "subtable": []},
    ]
    out = _eval(heavy_done, 2)
    assert out["overall"] >= 95, f"按工时加权应接近 100%, 等权则只有 50%: {out['overall']}"


def test_empty_and_all_done_are_zero_not_crash() -> None:
    """空库 / 全完成: 返回 0, 不炸也不出 NaN。"""
    assert _eval([], 2)["hours"] == 0
    all_done = [{"id": "x", "status": "已完成", "estimate": 5, "spct": 100, "deps": [], "subtable": []}]
    out = _eval(all_done, 2)
    assert out["hours"] == 0 and out["overall"] == 100, out


def test_unestimated_tasks_are_counted_not_guessed() -> None:
    """没填工时的 task 记进 unknown, 不瞎猜一个数 —— 免得剩余时间看起来很确定其实是编的。"""
    out = _eval([{"id": "n", "status": "待处理", "deps": [], "subtable": []}], 2)
    assert out["unknown"] == 1 and out["hours"] == 0, out


def _eval_summary(tasks: list[dict[str, Any]], max_active: int) -> dict[str, Any]:
    """跑 eta.overallSummary —— 看板页头消费的正是这个函数 (board.js#overallSummary)。"""
    script = f"""
      const M = await import({str(WEBAPP / 'model.js')!r});
      const E = await import({str(WEBAPP / 'eta.js')!r});
      const T = M.normalizeTasks({json.dumps(tasks)});
      console.log(JSON.stringify(E.overallSummary(T, {max_active})));
    """
    r = subprocess.run(["node", "--input-type=module", "-e", script],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"node 跑失败:\n{r.stderr}"
    return dict(json.loads(r.stdout.strip()))


def test_summary_no_tasks_says_no_tasks_not_nan() -> None:
    """无 task: 「暂无任务」而非 NaN / 空白 / 0%。"""
    out = _eval_summary([], 2)
    assert out == {"pct": 0, "remainText": "暂无任务", "remainHint": ""}, out


def test_summary_all_done_says_all_done_not_zero_hours() -> None:
    """全部完成: 「全部完成」而非误导性的 0h。"""
    out = _eval_summary(
        [{"id": "x", "status": "已完成", "estimate": 5, "spct": 100, "deps": [], "subtable": []}], 2)
    assert out["pct"] == 100 and out["remainText"] == "全部完成" and out["remainHint"] == "", out


def test_summary_all_unestimated_is_unknown_not_zero() -> None:
    """全部未估工时: 剩余标「未知」而非 0h —— 0h 会让人以为马上做完, 比不显示更有害。"""
    out = _eval_summary(
        [{"id": "n", "status": "待处理", "deps": [], "subtable": []}], 2)
    assert out["remainText"] == "未知" and "1 个未估工时" in out["remainHint"], out


def test_summary_matches_overall_progress_and_aggregate_eta() -> None:
    """同源同算: overallSummary 的 pct 必须和直接调 overallProgress 一致 (这条钉死看板与概览页
    不会各算各的 —— 两处最终都经 overallProgress/aggregateEta 这两个函数, 不是各写一份)。"""
    out = _eval(TASKS, 2)
    summary = _eval_summary(TASKS, 2)
    assert summary["pct"] == out["overall"], (summary, out)
    assert summary["remainHint"].startswith("总工时"), summary


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("前端 ETA 自检过")
