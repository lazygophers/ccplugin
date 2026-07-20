# task-detail-research-gitignore — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] task 详情页显示 research 调研过程笔记 (现 DOC_TABS 只 prd/design/findings, researcher 落 research/*.md 不可见)。
- [ ] 衍生/临时文件默认 gitignore (.skein/spec/.pending-fix + .skein/trash/ + .audit-log + .recall.db), 不污染 git status。
- [ ] 用户价值: 调研过程在看板可见; 新仓 init 自动忽略衍生文件。
- [ ] 成功: task 详情 research tab 显笔记; git status 不显 .pending-fix/trash。

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] **范围内**: skein.py `_task_detail` 加 research 字段; task.js DOC_TABS 加 research tab + 渲染分支; skein.py init L440 gitignore 模板补 4 行 + 幂等补缺; 现仓 `.skein/.gitignore` 手动补全。
- [ ] **范围外**: research 子目录递归 (平铺够); research tab 套 tab 文件侧栏 (全展开竖排够); 根 .gitignore 改动 (`.skein/.gitignore` 管 `.skein/` 内)。
- [ ] **已知约束**: research 是目录多文件非单文件 (渲染需独立分支); init 现 `if not gi.exists()` 已存不重写 (需加幂等补缺)。

## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] task 详情页显 research tab (DOC_TABS 4 tab)
- [ ] research tab 显 `.skein/task/<id>/research/*.md` 多篇 (spec-memory-extend 有 6 篇)
- [ ] 空目录 task research tab 显「暂无调研笔记」不崩
- [ ] `_task_detail` 返回含 `research` 字段 (dict filename→content)
- [ ] 新仓 `skein init` 生成 `.skein/.gitignore` 含 8 条忽略 (task.md/vision.md/lock/spec/.archive/ + .pending-fix/.audit-log/.recall.db/trash/)
- [ ] 现仓 `.skein/.gitignore` 补全 4 条 (幂等补缺逻辑或手动)
- [ ] `git status` 不显 `.pending-fix` / `trash/` / `.audit-log` / `.recall.db`
- [ ] `uv run pytest plugins/tools/skein/scripts/tests/` 全绿
- [ ] `uv run mypy plugins/tools/skein/scripts/skein.py` clean

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list task-detail-research-gitignore`)
