# fix-task-pct-subtasks-done — 详细设计

## 用户确认 (2026-07-20)

- **现象**: task 的 subtask 全部 done, 但 task 进度显 85% (用户报「14 个任务都已完成但总进度 85%」)
- **根因**: `_task_pct` (skein.py:2762) 把 task 状态机阶段 (plan/exec/check/done) 和 subtask 完成度混在一起加权, S_ACTIVE 段天花板钉死在 `10 + 75 = 85`, subs 全 done 也到不了 100

## 进度算法全景 (审计)

### 基础算法
- `_sub_pct(s)` (skein.py:2754): done→100; 有验收→round(done/总×100); 无验收未 done→0
- `_task_pct(t)` (skein.py:2762): done→100; check→85; active→无subs=10 / 有subs=10+75×(均值/100); pending→无subs=5/有subs=10

### 聚合点
- vision.md overall (skein.py:1647): `sum(_task_pct(c)) // len(children)` — supertask 整体进度
- serve board task_pct (skein.py:1690): 纯委托 `_task_pct`, 无跨 task 聚合

## 缺陷

| # | 位置 | 缺陷 |
|---|---|---|
| 1 | `_task_pct` S_ACTIVE | subs 全 done → 10+75×1.0 = 85, 与 S_CHECK 同值 |
| 2 | `_task_pct` S_CHECK | 硬编码 85, 不看 subs 实际 |
| 3 | `_task_pct` S_ACTIVE | subs 部分完成上限被钉 85 |

核心: 状态机加权与 subtask 完成度耦合, active 段天花板 85。

## 修法 (ponytail 最小 diff)

重写 `_task_pct`: **进度只由 subtask 完成度驱动, 状态机阶段仅影响无 subs 边界**。

```python
def _task_pct(t: dict[str, Any]) -> int:
    # task 进度 = subtask 完成度 (有 subs) / 状态机阶段 (无 subs).
    # ponytail: 进度反映客观完成度, 不混状态机加权 — subs 全 done 即 100,
    #   哪怕 task 仍在 active/check (状态机推进由人/finish 命令, 不影响进度数).
    st = t["status"]
    if st == S_DONE:
        return 100
    subs: list[dict[str, Any]] = t.get("subtasks", [])
    if subs:
        return sum(_sub_pct(s) for s in subs) // len(subs)
    # 无 subs: 用状态机阶段 (planning/exec/check 收尾的单点 task)
    if st == S_CHECK:
        return 85
    if st == S_ACTIVE:
        return 10
    return 5   # S_PENDING (planning 中)
```

### 效果
- subs 全 done → 100 (修缺陷 1/2/3)
- 13/14 done → 92 (不再钉 85)
- check 阶段无 subs → 85 (保留)
- 单调: active 随 subs 0→100

### 影响面
`_task_pct` 单点改, 16 处调用点 (board/vision/list/view/serve) 自动生效, 零额外改动。

### 不碰 (YAGNI, 独立小问题)
- `_sub_pct` 无验收项=0 (缺陷 5)
- vision overall 整除丢小数 (缺陷 6)

## subtask 拆解

1. **st1**: 重写 `_task_pct` (skein.py:2762)
2. **st2** (deps st1): 加 `_task_pct` 测试 (test_skein.py), 覆盖 4 场景

## 验证

- `uv run pytest` 全绿
- `uv run mypy` clean
