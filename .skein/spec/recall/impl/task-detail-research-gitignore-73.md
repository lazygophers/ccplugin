---
title: init 衍生文件 gitignore 幂等补缺
layer: recall
category: impl
keywords: [init,gitignore,幂等,补缺,衍生文件]
source: task-detail-research-gitignore
authored-by: skein-spec
created: 1784560020
status: active
related: []
updated: 1784560020
---

# 触发场景

skein.py init 生成 `.skein/.gitignore` 时，现逻辑 `if not gi.exists()` 仅在文件不存在时写入，已存在则不覆写。导致已 init 仓库无法补新条目（如 `.pending-fix`、`trash/` 等衍生文件）。

## 陷阱-正解

init 渲染的**衍生文件忽略清单**需**幂等补缺**：读现有行→set diff→append missing（类 config 缺键回填模式）。

**反例**（已存在不覆写，新仓库永缺条目）：
```python
if not gi.exists():
    gi.write_text(content)  # 已存在则跳过
```

**正解**（幂等补缺）：
```python
# 读取现有行 → 计算 diff → 仅 append missing
existing = set(gi.read_text().splitlines()) if gi.exists() else set()
needed = {"spec/.pending-fix", "spec/.audit-log", "spec/.recall.db", "trash/"}
missing = needed - existing
if missing:
    with gi.open("a") as f:
        for line in sorted(missing):
            f.write(f"{line}\n")
```

## 反例

| 禁 | 改为 |
|---|---|
| `if not gi.exists()` 条件写入 | 读现有→diff→append missing |
| 已存在跳过，新条目永缺 | 幂等补缺，不覆盖现有行 |
| 每次手动改 gitignore | init 自动补最新条目 |

## 案例

skein.py init L440 `.skein/.gitignore` 模板：现硬编 4 条（task.md/vision.md/*.lock/spec/.archive/），漏 `.pending-fix`/`trash/`/`.audit-log`/`.recall.db`。改用幂等补缺后，已 init 仓库 re-run init 即自动补 4 条。

## 适用

- 任何 init 渲染的**配置/清单文件**（gitignore/模板配置）
- 需要**幂等更新**而非覆写的场景
- 类 config 缺键回填模式（`_sync()` 衍生顶层镜像同理）

## 关联

- `[impl] task 状态机顶层镜像同步`（task.json 与 per-task 同步，同模式）
- `[arch] 衍生文件排除范式`（定义哪些该排除，此规则讲补缺手法）
- `[arch] config 缺键回填`（同一模式在 config 中的应用）
