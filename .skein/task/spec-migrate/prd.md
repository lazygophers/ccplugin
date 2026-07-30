# 自动迁移 migrate 两阶段 — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] 已有 `.skein/spec` 库 (core/recall/external 三层) 必须能**自动**迁到新结构 (namespace × inclusion), 禁要求用户手改
- [ ] 迁移分两阶段, 各司其职: **脚本做 100% 确定的机械重排** (路径/frontmatter/配置键), **AI 做需要语义判断的分拣** (旧 recall 层里混着的产品现状描述该进 `product`)
- [ ] 全程可逆 — 迁移前整库 `archive <ts>` 快照, 出错可 `restore <ts>` 回滚, 不删任何文件
- [ ] 成功长什么样: 老仓跑一条 `skein-spec migrate` 即完成结构升级; 重复跑幂等无副作用; `--dry-run` 可先看报告

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: `spec.py migrate` 新命令 (阶段 1 机械迁移 + 阶段 2 候选启发式打分) + 幂等/可逆测试
- [ ] 范围内: 配置键迁移 `spec_core_budget` → `spec_always_budget` (值 1000 → 8000)
- [ ] 范围内: core/recall 同 `<category>/<topic>` 撞名时的章节级合并
- [ ] 范围外: 阶段 2 的**语义判定本身** (归 `skein-specer` agent 在运行时做, 本 task 只产候选与打分)
- [ ] 范围外: `product`/`map` 的业务逻辑 (归各自 task); 示例仓迁移 (归 `spec-docs-examples`)
- [ ] 约束: 依赖 `spec-model-core` 已落地 (新模型的常量与索引就位后才能迁)
- [ ] 约束: 复用现有 `restructure --map` 与 `archive`/`restore` 机制作底层实现, **禁重写一套迁移引擎**
- [ ] 约束: 纯 stdlib

## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] `migrate --dry-run` 只输出报告不动盘 (可验: 前后 `git status` 一致)
- [ ] 阶段 1 映射正确: `core/<cat>/<topic>.md` → `rules/<cat>/<topic>.md` 且注入 `namespace: rules` + `inclusion: always`
- [ ] 阶段 1 映射正确: `recall/<cat>/<topic>.md` → `rules/<cat>/<topic>.md` 且注入 `inclusion: auto`
- [ ] 阶段 1 映射正确: `external/<cat>/<topic>.md` 原地 + 注入 `namespace: external` + `inclusion: manual`
- [ ] core/recall 同 `<cat>/<topic>` 撞名 → 章节级合并进一页; `## 标题` 也撞 → 后者加 ` (recall)` 后缀并存并列入报告
- [ ] 旧 frontmatter 字段 `layer` / `created` / `updated` 被删除 (与「时间类字段一律不写」既有约定一致)
- [ ] 配置迁移: `spec_core_budget: 1000` → `spec_always_budget: 8000`; 用户显式设过非默认值时**保留原值**不覆盖
- [ ] 空目录 `spec/product/` 与 `spec/map/` 被创建
- [ ] 迁移前自动 `archive <ts>` 全库快照; `restore <ts>` 能完整回滚到迁移前状态
- [ ] **幂等**: 连跑两次 `migrate`, 第二次报「已是新结构, 无需迁移」且不产生任何文件变更
- [ ] 阶段 2 产候选报告: 按启发式打分输出 `product` / `map` 候选章节清单 (命令式词汇→rules; 描述性词汇且无命令式→product 候选; 描述模块职责+含路径→map 候选; 有反例表→rules 强信号)
- [ ] 阶段 2 **不自动搬动任何内容** — 只产候选清单供 `skein-specer` 判定 (保守优先: 误搬比误留难纠)
- [ ] `migrate --stage=1` / `--stage=2` / `--stage=all` (默认 all) 三种入口均可用
- [ ] 迁移后 `reindex` 产出的各 namespace index.md 条数与迁移前总条数一致 (无丢失; 合并页按章节数计)
- [ ] 新增 `scripts/tests/` 用例覆盖: 三层映射 / 撞名合并 / 幂等 / 可逆 / 配置保留用户值 / dry-run 不动盘
- [ ] `python3 scripts/skein.py doctor --quality` 通过

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list spec-migrate`)
