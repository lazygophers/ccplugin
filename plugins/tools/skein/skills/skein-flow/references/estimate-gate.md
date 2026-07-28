# 预计工时硬门 (estimate)

SKEIN task 的预计工时 (小时, 浮点数) 是 plan 阶段必填项, `skein confirm` (待处理→就绪) 硬校验, 缺失或非正数一律拒绝进就绪。

定义见 `skein.py` `create()`/`estimate()`/`_validate_estimate()`。

---

## 铁律

- **plan 阶段必填**: task 的预计工时须在 `skein confirm` 前填实, 与 prd 四章节、subtask 拆分同为 confirm 硬门条件 (见 `plan 阶段完成判据`)。
- **存储**: `task.json` 的 `estimate` 字段 (数字, 单位小时; 未填为 `null`)。
- **校验规则**: `estimate` 非 `None`/非空串, 且为正数 (`> 0`) 才算填实; `0`、负数、缺失均判未填。
- **不通过**: `confirm` 内 `_validate_estimate` 检出未填 → `raise SystemExit`, 报错含可操作提示 (`skein estimate <id> --set <小时数>`), 阻断进就绪。

---

## 填写方式

| 方式 | 命令 | 阶段 |
|---|---|---|
| 创建时指定 | `skein create <id> --name .. --desc .. --estimate 4` | create |
| 规划时补填/修改 | `skein estimate <id> --set 6` | pending / ready (start 后不可再改) |
| 查看当前值 | `skein estimate <id>` (省略 `--set`) | 任意阶段, 纯读 |
| 默认值 | 无默认, 缺省即未填 (`null`), confirm 会拒绝 | - |

```python
# skein.py create(): 任务字典
"estimate": getattr(a, "estimate", None),  # 预计工时(小时), plan 阶段必填, confirm 硬门校验
```

```python
# skein.py _validate_estimate()
def _validate_estimate(self, tid, t):
    est = t.get("estimate")
    if est is None or est == "" or not (isinstance(est, (int, float)) and est > 0):
        raise SystemExit(f"{tid} 预计工时未填 — 先 `skein estimate {tid} --set <小时数>` 填实再 confirm")
```

---

## 与 prd/subtask 硬门的关系

`skein confirm` 一次校验三项 (顺序): ① subtask ≥1 (`subtask add` 已落 DAG) → ② prd 四章节齐备无 TODO 占位 (`_validate_prd`) → ③ 预计工时已填实 (`_validate_estimate`)。任一不满足即 `SystemExit` 阻断, 不进就绪。

`skein start` (就绪→进行中) 不重复校验预计工时 — 工时估算只影响 plan/confirm 阶段的规划质量把关, 不像 prd 那样需要 double-check 防中途改空 (预计工时填后极少被回改)。

---

## 编辑限制

- 仅 `pending`(待处理) / `ready`(就绪) 状态可 `skein estimate --set` 改动; `start` 后 (进行中及以后) 状态锁定, 拒绝修改 (工时估算是规划期决策, 执行期不应回改)。
- 与 `repos`/`deps` 命令同构: 省略 `--set` 即查看当前值, 纯读不加写锁。
