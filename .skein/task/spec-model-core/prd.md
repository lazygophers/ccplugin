# spec.py 模型层: namespace×inclusion 正交 — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] 解耦 `layer` 一身兼两职 — 现在 `core`/`recall`/`external` 每个都同时定义了「内容类型」与「加载策略」两件事, 导致想新增内容分类 (如产品现状 wiki) 时无法回答「它的加载策略是什么」
- [ ] 拆成正交两维: **namespace** (内容类型, 目录级, 自由扩展) × **inclusion** (加载策略, 文件 frontmatter 级, 四选一封闭集)
- [ ] 对齐主流: Cursor `.cursor/rules/*.mdc` 与 Kiro `.kiro/steering/*.md` 均为「文件平铺 + frontmatter 决定加载」, 无一家用目录分层定加载策略
- [ ] 成功长什么样: `spec/<namespace>/<category>/<topic>.md` 可自由新增 namespace 零配置; 同一 namespace 内可混放 `inclusion: always` 与 `auto` 页; `degrade` 从「跨层 git mv」简化为「改一个 frontmatter 字段」

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: `scripts/spec.py` 模型层 — 常量、加载路径、预算、索引/FTS、CLI 参数面、degrade、maintain 判据分表
- [ ] 范围内: 向后兼容 — `--layer` 保留为 deprecated alias (core→always / recall→auto), 旧配置键 `spec_core_budget` 读作 fallback
- [ ] 范围外: 数据迁移 (归 `spec-migrate`)、`hooks.py` 适配 (归 `spec-hooks-adapt`)、`product`/`map` namespace 的业务逻辑 (归各自 task)
- [ ] 范围外: 文档与 agent 措辞同步 (归 `spec-skills-agents-adapt`)
- [ ] 约束: 纯 stdlib, 禁引新依赖 (`spec.py` 模块 docstring 既有铁律)
- [ ] 约束: 章节粒度不变 — 文件夹=类目, 文件=主题, `## 标题`=一条; 索引/FTS/反链仍按章节建
- [ ] 约束: hook 命令名 (`session-start` / `subagent-start` / `inject-core`) 不改, 只改内部语义, 保证 `plugin.json` 接线零改动

## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] `NAMESPACES` 默认含 `rules/product/map/external`, 但实际可用 namespace 由**目录扫描**得 — 手建 `spec/foo/bar/x.md` 后 `reindex` 能识别并产 `spec/foo/index.md`
- [ ] `INCLUSIONS` 为封闭四值 `always|auto|fileMatch|manual`; `sediment --inclusion` 非法值报错退出
- [ ] `inclusion: always` 的页由 `inject-core` / `session-start` / `subagent-start` 注入, **与所在 namespace 无关** (可验: 在 `product/` 放一页 `always` 页, session-start 能注入)
- [ ] `always_budget()` 读 `spec_always_budget` 默认 8000; 缺该键时读旧键 `spec_core_budget` 作 fallback; 两键皆缺回 8000
- [ ] `.recall.db` 的 `rules` 表含 `namespace` / `inclusion` / `anchors` 列, 且**全 namespace 入索引** (含 always 页, 因 recall 需可查)
- [ ] `recall "<q>" --src rules|product|map|all` 可按 namespace 过滤; 默认 `all`
- [ ] `sediment` 支持 `--namespace` (自由字符串) / `--inclusion` (四选一, 默认 auto) / `--globs` / `--anchors`; `--layer` 仍可用且映射正确 (core→always, recall→auto), 并打 deprecated 提示
- [ ] `sediment --status` 接受新增的 `proposed`
- [ ] `inclusion: fileMatch` 的页缺 `globs` 时 `maintain` 报为问题项
- [ ] `degrade <file>` 只改 frontmatter `inclusion: always→auto` + reindex, **不移动文件** (可验: 文件路径前后一致, git status 无 rename)
- [ ] `degrade --auto` 循环降级直到全部 `always` 页总字符 < `always_budget()`
- [ ] `maintain` 判据按 namespace 分表: `rules` 用 180 天 stale; `product` **不用时间判据**且失效项只报告不自动 archive; `map` 只认 anchors 失效
- [ ] `maintain` 断链判据覆盖 `anchors` 路径失效 (文件不存在即报)
- [ ] `pytest scripts/tests/test_spec.py` 全绿, 新增用例覆盖: namespace 自由扩展 / inclusion 筛选 / 预算 fallback / degrade 不移文件 / product 不自动 archive
- [ ] `python3 scripts/skein.py doctor --quality` 通过 (mypy + pytest)

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list spec-model-core`)
