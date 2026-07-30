# docs + examples 示例仓迁移 — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] `docs/examples/sample-skein/spec/` 是**新用户第一眼看到的结构**, 停在旧两层结构会直接教错人 —— 必须迁
- [ ] 示例仓不只是迁移, 还要**补上 `product/` 与 `map/` 的示例页** —— 这两个 namespace 是本轮新增价值, 没有示例等于没人会用
- [ ] 顶层文档 (`README.md` / `CONTEXT.md` / `docs/*`) 的结构说明同步到 namespace × inclusion 模型
- [ ] 流程图 `docs/skein-flow.mmd` + `.png` 的 finish 阶段加 wiki 回写分支
- [ ] 成功长什么样: 一个新用户读 README + 看 examples, 能正确建出 `product` 页并知道 `inclusion` 该填什么

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: `docs/examples/sample-skein/spec/` 整体迁移 + 新增 product/map 示例页
- [ ] 范围内: `docs/README.md` / `docs/reference.md` / `docs/skein.md` / 插件根 `README.md` / `CONTEXT.md`
- [ ] 范围内: `docs/skein-flow.mmd` 加 wiki 回写分支 + 重生 `.png`
- [ ] 范围内: `docs/examples/README.md` 说明同步
- [ ] 范围外: skills / agents / plugin.json (归 `spec-skills-agents-adapt`)
- [ ] 范围外: 脚本代码 —— 本 task **纯文档**, 发现脚本缺能力则报告不改
- [ ] 约束: 依赖 `spec-skills-agents-adapt` 完成 (文档措辞要与 skill 提示词一致, 不能各说一套)
- [ ] 约束: 示例仓的 spec 页要**能真的跑通** —— 用 `spec.py reindex` 对示例仓跑一遍, 索引能正确生成才算对
- [ ] 约束: `.png` 重生需要 mermaid 工具链; 若环境不可用则**如实报告并只改 `.mmd`**, 禁提交与 `.mmd` 不符的旧 `.png`

## 验收标准
可执行、可核对的完成断言 (逐条):

### 示例仓迁移
- [ ] `sample-skein/spec/core/` + `recall/` → `rules/`, 各页注入 `namespace: rules` + 对应 `inclusion` (原 core→`always`, 原 recall→`auto`)
- [ ] 各页 frontmatter 删除 `layer` / `created` / `updated` 字段 (与「时间类字段一律不写」一致)
- [ ] **新增** `sample-skein/spec/product/` 至少 1 个功能域, 含 `overview.md` + 1 个细节页, 带 `anchors`
- [ ] **新增** `sample-skein/spec/map/` 至少 1 页语义页, 带 `anchors`
- [ ] 示例页展示四种 `inclusion` 中至少三种 (`always` / `auto` / `fileMatch`), `fileMatch` 页带 `globs`
- [ ] 对示例仓跑 `spec.py reindex` 能成功生成各 namespace `index.md` + 顶层 `index.md` + `backlinks.md`, 且条数与页内章节数一致
- [ ] 示例仓的 `config.yaml` (若有) 用 `spec_always_budget` 新键

### 顶层文档
- [ ] `README.md` (插件根): 差异化核心描述从「两层×类目」→ namespace × inclusion; 补 `product` wiki 与 `map` 的一句话说明
- [ ] `CONTEXT.md`: 结构说明同步
- [ ] `docs/reference.md`: 命令表补 `migrate` / `amend` / `map` / `analyze` / `finish-candidates`; `--layer` 标 deprecated
- [ ] `docs/skein.md`: spec 章节重写为四 namespace
- [ ] `docs/README.md` + `docs/examples/README.md`: 索引与说明同步
- [ ] 全部文档中**无写死的预算数值** (统一引用键名 `spec_always_budget`), 与 `spec-skills-agents-adapt` 的同一决策保持一致

### 流程图
- [ ] `docs/skein-flow.mmd` 的 finish 阶段加 wiki 回写分支 (finish 闭环 → 异步 sediment **+ amend 回写**)
- [ ] `.png` 已按新 `.mmd` 重生; **若 mermaid 工具链不可用则如实报告并只改 `.mmd`**, 不留与 `.mmd` 不符的旧 `.png`

### 兜底
- [ ] 结构性验证: 全仓 `docs/` 与 `README.md` / `CONTEXT.md` 内 grep 无残留「两层」措辞、无残留 `spec/core/` 路径 (除 migrate 说明处)
- [ ] `python3 scripts/skein.py doctor --quality` 通过

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list spec-docs-examples`)
