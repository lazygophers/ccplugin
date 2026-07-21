# task-detail-research-gitignore — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 用户需求 (2026-07-20)

1. **task 详情页显示 research 信息** — 现右栏 DOC_TABS 只 prd/design/findings, research 目录 (researcher 过程笔记多篇) 看不到。痛点: 用户在看板 `http://127.0.0.1:38296/task?id=spec-memory-extend` 点 task 详情, 调研过程不可见。
2. **`.pending-fix` + `.skein/trash/` 默认 gitignore** — init 生成的 `.skein/.gitignore` 漏这俩 (Stop hook 写的 `.skein/spec/.pending-fix` 标记 + 软删 task 的 `.skein/trash/`)。另补 `.audit-log` + `.recall.db` 衍生文件。

## 现状审计

### 前端 (assets/webapp/src/pages/task.js)
- L273-277 `DOC_TABS` 三 tab: design/prd/findings
- L250-251 design/findings 整篇 md 渲染 (`v-html="renderedDoc"`)
- L240-242 tab 无内容显「暂无内容」
- L389 `docLabel(k)` tab 标签查找

### 后端 (skein.py)
- `_task_detail` (L1969-1989): docs 只读 prd.md/design.md/findings.md 三文件 (L1985 loop), 无 research
- research 目录 (skein.py:17 docstring): `.skein/task/<id>/research/` researcher 过程笔记多篇

### gitignore (skein.py init L436-440)
现 `.skein/.gitignore` 内容 (L440 硬编):
```
# skein.py 自动渲染, 从 task.json 无损重建, 不入库
task.md
vision.md
*.lock
spec/.archive/
```
**漏**:
- `.skein/spec/.pending-fix` — Stop hook 写的 spec 问题标记 (skein.py:1225)
- `.skein/trash/` — 软删 task 转储 (skein.py:187, L815)
- `.skein/spec/.audit-log` — spec 审计日志 (spec.py, 7 天轮转衍生)
- `.skein/spec/.recall.db` — FTS5 衍生索引 (spec-memory-extend 加的, reindex 可重建)

## 修法

### 需求 1: research 显示

**后端 `_task_detail` 加 research 字段** (skein.py:1984-1988):
```python
docs: dict[str, Any] = {}
for fn in ("prd.md", "design.md", "findings.md"):
    f = tdir / fn
    docs[fn[:-3]] = f.read_text(encoding="utf-8", errors="replace") if f.exists() else None
# research 目录多篇笔记: {filename: content} (无目录则空 dict)
research: dict[str, str] = {}
rdir = tdir / "research"
if rdir.is_dir():
    for rf in sorted(rdir.glob("*.md")):
        research[rf.name] = rf.read_text(encoding="utf-8", errors="replace")
return {"task": data, "docs": docs, "research": research, "archived": archived, ...}
```

**前端 task.js**:
- `DOC_TABS` 加 research tab (放 findings 后, 调研过程次于收敛结论):
```js
const DOC_TABS = [
  { key: "design", label: "详细设计" },
  { key: "prd", label: "PRD" },
  { key: "findings", label: "调研收敛" },
  { key: "research", label: "调研过程" },
];
```
- research tab 渲染区 (L250-251 附近): research 是多篇 dict 非单篇 → 需独立渲染分支:
  - 空目录 → 「暂无调研笔记」
  - 多篇 → 文件列表侧栏 + 点选看内容 (类似 tab 套 tab), 或全展开竖排 (简单, ponytail)
  - **选全展开竖排** (最简): 每篇 `## <filename>` 标题 + md body, 与 design/findings 风格一致
- mountApp `docs` 数据源补 research (fetch task detail 已含, 前端读 `data.research`)
- `renderedDoc` 逻辑: research tab 不走单篇 renderedDoc, 改 `researchHtml` (多篇拼装或列表)

### 需求 2: gitignore 补全

**skein.py init L440** `.skein/.gitignore` 内容补:
```python
gi.write_text(
    "# skein.py 自动渲染, 从 task.json 无损重建, 不入库\n"
    "task.md\n"
    "vision.md\n"
    "*.lock\n"
    "spec/.archive/\n"
    "# 衍生/临时文件 (hook 标记/软删转储/审计日志/FTS 索引)\n"
    "spec/.pending-fix\n"
    "spec/.audit-log\n"
    "spec/.recall.db\n"
    "trash/\n"
)
```

**已存 `.skein/.gitignore` 补全** (幂等): init 现逻辑 `if not gi.exists()` — 已存不覆写。需改: 已存则检查缺行补上 (类似 config 缺键回填模式), 或加个 `_ensure_gitignore_entries()` 补缺行。

**主仓 `.skein/.gitignore` 也需手动补** (现仓已 init 过, init 不会重写) — 直接 Edit 现文件补 4 行。

## subtask 拆解

| # | subtask | 文件 | deps |
|---|---|---|---|
| st1 | research 显示 (后端 _task_detail + 前端 DOC_TABS + 渲染) | skein.py + task.js | 无 |
| st2 | gitignore 补全 (init 模板 + 幂等补缺 + 现仓 .skein/.gitignore) | skein.py + .skein/.gitignore | 无 |

st1/st2 不同区域可并行 (st1 改后端 detail + 前端; st2 改 init + gitignore 文件)。

## 验证

- serve 起看板: task 详情显 research tab, spec-memory-extend 的 6 篇笔记可见
- 空目录 task: research tab 显「暂无调研笔记」不崩
- 新仓 init: `.skein/.gitignore` 含 8 条忽略
- 现仓 `.skein/.gitignore` 补全后 `git status` 不显 `.pending-fix`/`trash/`
- `uv run pytest plugins/tools/skein/scripts/tests/` 全绿
- `uv run mypy plugins/tools/skein/scripts/skein.py` clean

## 不碰 (YAGNI)

- research 子目录递归 (现 researcher 落 `research/*.md` 平铺, 无嵌套)
- research tab 套 tab 文件侧栏 (全展开竖排够用, 多篇滚即可)
- 根 `.gitignore` (`.skein/.gitignore` 管 `.skein/` 内, 根 .gitignore 只管 worktree_root)
