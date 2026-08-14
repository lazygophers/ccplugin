---
name: skein-spec
description: 规则记忆库 (基于 .skein/spec)。namespace (自由目录, 默认 rules/product/map/external, 目录扫描得非白名单) × inclusion (封闭四值 always/auto/fileMatch/manual, 写在 frontmatter) 正交两维 —— 目录管内容分类, inclusion 管加载策略, 互不决定, 搬目录不改加载策略。planning 时 recall 召回相关规则、task finish 后 sediment 沉淀学习 + maintain 自动精简过期/重复/断链/超预算, 经判定门自动写盘 (不逐次问用户)。product namespace 是需求现状 wiki (delta 变更历史 vs state 现状快照分离, 按功能域切页), 现状过时用 amend 改写既有章节 (而非无限追加并存); map namespace 现算目录树+符号骨架 (`map --skeleton`) 合并人写语义页; analyze 对 task 跑只读一致性核查 (验收覆盖率/硬规冲突/范围蔓延/proposed 置信度/接缝存在性); 旧两层结构 (core/recall) 迁移新 namespace 结构见 migrate。另支持空仓 bootstrap 播种规则基线、记忆大面积失效 (大重构/换栈) 时 reconstruct 可逆归档后按项目类型分型重建、maintain 手动体检 (超预算/stale/断链/重复/废弃, 判据按 namespace 分表, --apply 自动修复)、auto-fix (Stop hook 写 .pending-fix 标记 → main 派 skein-specer bg 跑 maintain --apply 全自动修, 断链只报告)。
user-invocable: true
argument-hint: "[模式: recall/召回, sediment/沉淀, amend/改写, map/结构现算, analyze/一致性核查, bootstrap/播种, reconstruct/重构, maintain/维护 (加 --apply 自动修)] [--deep=recall/low/full/deep/max/high (reconstruct 模式可选)]"
arguments: "['recall(召回)|sediment(沉淀)|amend(改写)|map(结构现算)|analyze(一致性核查)|bootstrap(播种)|reconstruct(重构)|maintain(维护)', '--deep=recall/low/full/deep/max/high']"
model: inherit
effort: medium
context: fork
---

# skein-spec — 规则记忆库 (namespace × inclusion)

> 🔒 全局流程规则（状态机/调度/优先级等）以 skein-flow/references/ 为单一真值源。

**差异化核心**。不同于「按需沉淀单一 spec 文件」, SKEIN 记忆按两个正交维度组织, 基于 `.skein/spec`:

> **绑定 agent (按读/写拆两个, 均 frontmatter `skills: skein:skein-spec`)**:
>
> - **读路径 → `skein-recaller`** (只读同步召回员, 单一 recall 职责): recall 检索 (planning) 派它, **main 等召回结果进 planning** (dispatch prompt「已知」段带上)。
> - **写路径 → `skein-specer`** (记忆写盘员): sediment/amend/reconstruct·maintain/prune 五类写作业 (finish 读 diff + subagent 回传摘要 跑判定门产候选 + 写盘 + reindex)。**异步 fire-and-forget 模式** (被 skein-flow finish 阶段在 finish 闭环后派发): specer 自主跑判定门 + `skein-spec sediment`/`amend` 写盘 + reindex, **无需 main 等待回传** (main 派发即结束回合, 回传到达后只补 output trace; 判定门通过即自主写, 不逐次询问用户)。仅 bootstrap/reconstruct 全局动作跑前一次征同意。

## namespace × inclusion 正交两维

**两者正交**: namespace 决定放哪个目录 (内容分类), inclusion 决定怎么加载 (写在每篇 frontmatter 里, 与目录无关) —— 把文件从一个 namespace 目录搬到另一个**不会**改变它的加载策略, 这条曾被文档写反过, 教用户把文件搬目录来「降级」, 而那什么也不会发生。

| namespace ＼ inclusion      | always 常驻注入 (SessionStart)                                  | auto 按需召回 (默认)                                | fileMatch 按 globs 命中注入 | manual 纯手动检索             |
| --------------------------- | --------------------------------------------------------------- | --------------------------------------------------- | --------------------------- | ----------------------------- |
| **rules** (硬规 / 经验规则) | 硬约束 / 命令式契约 (软预算 `spec.always_budget`, 超则告警降级) | 长尾经验规则 (默认落点)                             | 特定路径触发的规则          | 极冷门参考                    |
| **product** (需求现状 wiki) | 极少见 (核心边界铁律)                                           | 功能域现状页 (默认落点, 见下文)                     | —                           | 历史存档快照                  |
| **map** (代码结构语义页)    | —                                                               | 职责 / 数据流说明页, 配合 `map --skeleton` 现算骨架 | —                           | —                             |
| **external** (外部长文档)   | —                                                               | 索引摘要                                            | —                           | 原文全文, 手动检索 (默认落点) |

namespace 开放不设白名单 (目录扫描得, 新增 namespace 不改代码, 常见 rules/product/map/external), inclusion 是封闭四值。索引: 每个 `<namespace>/index.md` (该 namespace 全规则, 带 category / inclusion / anchors 列) + 顶层 `index.md` 聚合概览。

## 寻找纪律 (planning/调研/找方案时)

**动手前优先跑 `skein-spec recall "<关键词>"`** — 现有规则沉淀比凭记忆重推快且准, `inclusion: always` 的规则已常驻无需 recall。
顺序: recall spec (全 namespace, FTS5 BM25 排序) → vault → 项目本地 (Read/Grep) → 外部搜索。
recall 命中 → model 读全文判相关 → 相关的注入当前 task 上下文 (dispatch prompt「已知」段带上)。
external 层 (不入 hook, 纯手动) 存长文档/外部资料, 同经 `recall` 跨层检索。

## recall (planning 阶段, 派 skein-recaller)

> 召回由 `skein-recaller` (只读同步召回员) 承载, main 等其结果进 planning。

```
skein-spec recall "<任务关键词>" [--src rules/product/map/code/all]
```

- grep `<namespace>/index.md` 输出命中行 → **model 读命中规则全文, 判是否真相关** → 相关的注入当前 task 上下文 (dispatch prompt「已知」段带上)。
- `inclusion: always` 的规则已由 SessionStart hook 常驻, 无需 recall。
- `--src` 分源: `rules`/`product`/`map` 限定单 namespace, `code` 专召 map namespace 语义页 + anchors 汇总, 缺省 `all` 跨 namespace 检索。

## sediment (task finish 阶段, 异步 fire-and-forget) — 判定门 + 自主写盘

task finish 闭环后由 skein-flow finish 阶段异步 fire-and-forget 派 `skein-specer` 跑「判定门 checklist → 分层归类 → `skein-spec sediment` 自主写盘 + reindex」三步 (含升降级)。**异步**: main 派 skein-specer 即结束回合, 不等回传 (finish 已闭环, 禁为 sediment 阻塞); skein-specer 自主写盘, 回传到达后 main 只补 output trace 供审阅。**判定门 (语义) 通过即写, 不逐次 AskUserQuestion** —— 记忆积累高频, 每次询问是噪声; 误沉淀后续调 inclusion/删文件可逆纠正。完整判定 trace 模板、分层/归类规则、写盘命令详见 [references/sediment-workflow.md](references/sediment-workflow.md)。

sediment 只**追加**新章节 —— 现状类内容 (尤其 product wiki) 过时后要**改写**旧结论而非无限并存新版本, 追加 vs 改写的抉择见下文 amend。

## prune (sediment 后自动精简, skein-specer) — 判定门 + 自主归档

sediment 写盘后 skein-specer 顺带跑一轮精简: 扫全 namespace, 按判据检出 candidate 并**自动 archive** (可逆) 而非只报告。**异步 fire-and-forget**: 同 sediment, main 派即放手, 不等回传。

- 判据分两层 —— 全局恒跑 (always 超预算 / 断链) + 按 namespace 分表 (product 只报告, 需求真值只有人知道该不该删)。**完整判据表与判定顺序见 [references/prune-workflow.md](references/prune-workflow.md)**, 本文件不重抄。
- **archive 即可逆, 不删文件** — 归档到 `.skein/spec/.archive/<ts>/`, `restore <ts>` 可回滚。
- **保护标记**: 规则头 `protected: true` 跳过不精简。
- **无命中 → 跳过**, 如实报「无精简项」, 不空跑 archive。

## 写盘参照模板 (软骨架, 非强制)

规则 body 各有脊柱, sediment 写盘前 skein-specer 参照对应模板填:

- **always** 规则 (命令式契约) 参照 [references/templates/rules-always.md.tmpl](references/templates/rules-always.md.tmpl): 铁律/禁 (MUST/禁, 一句一规则) + 反例表 (禁/改为) + 可选关联。
- **auto** 规则 (ADR/陷阱型) 参照 [references/templates/rules-auto.md.tmpl](references/templates/rules-auto.md.tmpl): 触发场景 / 陷阱-正解 / 反例 / 案例 / 适用 / 关联。
- **product** 现状页参照 [references/templates/product.md.tmpl](references/templates/product.md.tmpl): 现状 / 边界 / 为什么这样 / anchors / 关联。
- **map** 语义页参照 [references/templates/map.md.tmpl](references/templates/map.md.tmpl): 职责 / 入口 / 数据流 / anchors。

> **参考骨架非强制** — sediment 是 fire-and-forget, 模板仅作 skein-specer 填 body 的结构引导, **不强校验、不阻塞写盘**; 实际规则按内容取舍段名 (elastic spine), 缺段不报错。

## product wiki (现状记忆, namespace=product)

> 编写 product wiki 时参考 [skein-flow/references/writing-for-agents.md](../skein-flow/references/writing-for-agents.md) 的 information hierarchy — 现状页 (state) 用 in-file reference 格式，决策变更 (delta) 落 rules namespace 作 ADR 式记录。

区别于 rules 的「决策 / 规则」(为什么这样改), product namespace 只存**当前系统现状** —— 单一功能域此刻是什么样, 不叠加历史决策链。

- **delta vs state**: sediment 沉淀的是「决策变更」(踩过的坑 / 为什么这样约定), 落 rules namespace; product 只留**现状快照**, 旧结论过时直接 `amend` 改写, 不追加并存多个矛盾版本 (这一条决定了 product 与 rules 的判据也不同, 见上文 prune 分表)。
- **按功能域切页**: 一个功能域 (登录 / 计费 / 权限...) 一个 topic 文件, 不与 rules 按类目混放。
- **finish 时回写候选**: skein-flow finish 阶段跑 `skein-spec finish-candidates <tid>`, 三路降级产候选 —— ① diff 改动文件反查 anchors 命中的既有 product 页 → ② 皆无命中则用 prd 关键词 `recall --src product` 找弱候选 → ③ 仍无则报「无候选, 可能是新功能域, 建议新建」, **禁硬凑**。main 拿到候选后派 specer 用 `amend` (改写既有页) 或 `sediment --namespace product` (新建页) 落盘。
- **不自动精简**: product 是需求真值, maintain 判据只有 anchors 失效才报告 (禁自动 archive, 需人判断), 无 stale / keywords 重复 / 废弃 / 孤立判据。

## amend (改写既有章节, 而非追加)

sediment 只会**追加**新章节; 现状类内容 (product wiki 尤甚) 过时后要**改写**旧结论, 而非无限并存新版本, 用 `amend`:

```
skein-spec amend --topic <ns/cat/topic> --section <章节名> --body-file <正文文件> [--rename-section <新章节名>]
```

- 改前先 `archive` 旧版本 (可逆), 其余章节与 frontmatter 逐字不动。
- **目标章节不存在 → 报错并列出该主题现有章节名**, 不静默追加新章节 (❌ 静默追加; 追加新章节走 `sediment`)。
- `--rename-section` 同步更新库内反链 (`[[topic#旧章节名]]` → 新名), 缺省不改章节名。
- 写盘后自动 `reindex`。

**amend vs sediment 抉择**: 是「改写现状」(旧结论已过时, 只该有一份真值) 用 amend; 是「新增条目」(新踩的坑 / 新决策, 不否定旧条目) 用 sediment。详细抉择树见 [references/sediment-workflow.md](references/sediment-workflow.md)。

## map (代码结构现算, namespace=map)

```
skein-spec map [--skeleton] [--paths <逗号分隔路径>]
```

现算目录树 + 符号 + 行数, **不写盘**:

- `--skeleton`: 仅顶层符号 (Python `def`/`class`/`async def`, JS/TS `function`/`class`/`export ...`, Go `func`/`type`), 正则非 AST (ponytail: 装饰器 / 嵌套 / 多行签名抓不准, 升级路径 tree-sitter)。
- `--paths`: 文件清单注入 (逗号分隔; 缺省 `git ls-files`, 非 git 仓降级 rglob 并排除 `node_modules`/`__pycache__` 等衍生目录)。
- map namespace 的语义页 (人写的职责 / 数据流说明) 与现算骨架合并展示; `recall --src code` 专召 map namespace 语义页 + anchors 汇总。

## analyze (task 一致性核查, 只读)

```
skein-spec analyze <tid> [--json]
```

对齐 spec-kit `/speckit.analyze`, 五类只读检查 (不写任何盘), 全启发式关键词/子串匹配, 措辞统一带「候选」字样, 零命中就如实报零冲突, **禁断言违规**:

| 检查            | 比对                                                                  |
| --------------- | --------------------------------------------------------------------- |
| 验收覆盖率      | prd 验收标准 ↔ subtask 验收项, 报关键词无命中的验收条 (候选未覆盖)    |
| 硬规冲突        | design.md ↔ `inclusion: always` 规则的否定式表述, 报候选 (不断言违规) |
| 范围蔓延        | subtask 名/desc ↔ prd 全文关键词, 报无命中的 subtask (候选蔓延)       |
| proposed 置信度 | design.md 提及的规则标题 ↔ 该规则 `status: proposed`, 报未验证引用    |
| 接缝存在性      | design.md「测试接缝」段声明的路径/符号 ↔ codebase, 报未找到           |

`--json` 输出机器可读结果供 `skein-checker` 消费; `for-check.md` 的一致性核查段直接调这条, 不再手工 diff 比对。

## migrate (旧两层结构 → namespace × inclusion)

旧 `spec/core/` + `spec/recall/` 两层结构迁移到 `rules/product/map/external` namespace × inclusion 新结构: `skein-setup` 在已初始化仓检出 `spec/core/` 存在时提示跑迁移, `init` 对全新仓直接建新结构目录。两阶段全流程 —— 阶段 1 机械改名 (旧 core→rules/inclusion:always, 旧 recall→rules/inclusion:auto) / 阶段 2 语义分拣 (把该归 product 的现状类内容、该归 map 的结构说明从 rules 分拣出去) —— 详见 [references/migration-v2.md](references/migration-v2.md)。

## 空仓冷启动播种 (一次性, main)

新仓 `.skein/spec` 为空时前几十轮 planning 无规则可召回。此时 main **可**提议从既有代码库提炼约定作冷启动基线 —— 派 skein-researcher 扫五维 (命名/错误处理/测试/架构边界/构建), 候选逐条定 namespace×inclusion 或 drop, 复用上文 sediment 写盘流程落盘 (bootstrap 跑前一次征同意覆盖整轮, 内部候选自动写)。

一次性动作, `AskUserQuestion` 征同意再跑 (禁自动); 用户拒 → 走正常 planning, 规则随 finish sediment 增量积累。完整流程 (触发条件 / 五维明细 / ns×inclusion 判定表 / 落盘) 见 [references/bootstrap-seeding.md](references/bootstrap-seeding.md)。

## 完全重构 (reconstruct, main) — 依代码/项目内容重建整库

既有记忆大面积失效 (大重构 / 换技术栈 / 记忆漂移 / 接手可疑旧库) 时, 把全库规则**可逆归档**后依当前代码 + 项目内容从零重建。区别于 bootstrap (仅空仓、纯增量): 重构多 `skein-spec archive` 前置 (可逆清库) + **按项目类型分型扫描**。

**六档深度** (`--deep=<recall|low|full|deep|max|high>`, 默认 full): 档位同时决定 ②archive 范围 (长尾 namespace / 全库) 与 ④扫描深度 (五维基线 / 全 8 型探针 / 加旧规则逐条比对), 逐档明细见 [references/reconstruct-memory.md §1.5](references/reconstruct-memory.md)。

```
skein-spec archive --namespace <ns>   # 只归档指定 namespace (recall/low 档)
skein-spec archive                    # 全 namespace 归档 (full/deep/max/high 档)
skein-spec restore <ts>               # 回滚 (撞名不覆盖新规则, 加 restored- 前缀并存)
# 注: 深度档 (recall/low/full/deep/max/high) 是本 skill 的参数, 决定「归档多大范围 + 扫多深」,
#     不是 CLI 参数 —— archive 只认 --namespace。
```

流程: 快照 → 归档 → 识别项目类型 → 分型扫描 (researcher bootstrap 模式 + 类型侧重) → 逐条定 ns×inclusion → sediment 自动写盘 → 验证 + 保留归档。🛑 `AskUserQuestion` 征同意再跑 (归档全库虽可逆仍是全局动作 · STOP, 禁自动)。**事无巨细设计 + 8 类项目 (backend/frontend/cli/monorepo/data-ml/infra/mobile/docs) 分型扫描侧重、探针、always 倾向、规则示例、陷阱** 见 [references/reconstruct-memory.md](references/reconstruct-memory.md)。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                                     | 一线修复                                                              | 仍失败兜底                                                       |
| ---------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------- |
| recall grep 无命中                       | 放宽 / 换关键词重 grep 一次 (同义词 / 上位类目)                       | 仍无 → planning 走无规则路径, 不阻塞; 靠 finish sediment 增量补  |
| `skein-spec sediment/amend/reindex` 报错 | 读脚本 stderr 定位 (路径 / 权限 / 类目名非法 / amend 章节名不存在)    | 仍失败 → 该候选暂存草案不落盘, 记 `需要: 手工核对`, 禁半写坏盘   |
| `always` 常驻超预算告警                  | prune 自动降级最少复用的 always 规则到 auto (`sediment` 调 inclusion) | 仍超 → 停手, 提示用户 always 层膨胀, 需人工裁剪硬规集            |
| reconstruct 重建不满意                   | `skein-spec restore <ts>` 从归档恢复 (撞名加 restored- 前缀并存)      | 仍失败 → 归档目录仍在 `.skein/spec/.archive/<ts>/`, 手动核对取舍 |

## ✅ 正向配方 (命中反面=流程错误)

> 🔒 铁律: sediment+prune 异步 fire-and-forget 禁阻塞 finish; `inclusion: always` 只留命令式硬约束。

| 场景                               | 正确做法 (❌ 反面)                                                        |
| ---------------------------------- | ------------------------------------------------------------------------- |
| sediment 写盘 / prune 自动 archive | 逐项输出判定 trace, skein-specer 回传后 main 补 (❌ 未输出判定 trace)     |
| 判定门全否                         | 跳过不沉淀 (❌ 无增量硬凑沉淀)                                            |
| 判定门通过要不要问用户             | 自主写盘, 只输出 trace 不硬停 (❌ 逐次 AskUserQuestion 问用户批不批)      |
| finish 闭环 vs sediment/prune      | 异步 fire-and-forget, finish 先 archive (❌ 为等 sediment/prune 阻塞闭环) |
| 写盘更新 index.md                  | skein-spec sediment/amend 自动同步 (❌ 不同步 index.md / 手改绕过)        |
| 规则分层                           | 默认落 `inclusion: auto`, `always` 只留硬约束 (❌ 什么都塞 always 常驻)   |
| product wiki 现状过期              | `amend` 改写既有章节 (❌ sediment 追加并存多个矛盾版本)                   |
| amend 目标章节不存在               | 报错列现有章节名, 改走 `sediment` 建新章节 (❌ 静默追加)                  |

## maintain (手动体检, main)

规则库漂移时的**手动全量体检** (供 user 在 sediment+prune 之外独立审查, 只报告不动手): `skein-spec maintain [--namespace <ns>]`。判据按 namespace 分表 (超预算/断链全局恒跑, stale/keywords 重复/废弃/孤立按上文 prune 分表规则, product 只报告) + 输出格式详见 [references/maintain.md](references/maintain.md)。加 `--apply` 则同一扫描自动修复可修项 (超预算→循环降级 always→auto / stale→归档 / keywords 重复→归档保留最新 / 废弃→归档 / product namespace 的 anchors 失效仍只报告), 每步写 `.audit-log` (7 天轮转), 详见 auto-fix 模式与 [references/maintain.md](references/maintain.md)。

## auto-fix (Stop hook 触发, 异步 fire-and-forget) — 全自动 spec 修复

sediment+prune 是 finish 后顺跑一轮, 仍可能漏 (如 session 中途 always 层膨胀超预算 / 新增断链)。auto-fix 用 **Stop hook + .pending-fix 标记** 做异步兜底修复, 全程无需用户介入。

```
skein-spec maintain --apply   # 同一次扫描自动修可修项 (product namespace/断链只报告)
```

**流程**:

1. **检测 (Stop hook)** — 回合结束 Stop hook 跑轻量 spec 体检, 检出任一可修项 (超预算 / stale / keywords 重复 / 废弃 / 断链) → 写 `.skein/spec/.pending-fix` 标记 (含命中项摘要 + ts)。
2. **派发 (main)** — main 检测到 `.pending-fix` → 异步 bg 派 `skein-specer` (fire-and-forget, 派出即结束回合, 不等回传, 与 sediment 同模式)。
3. **修复 (skein-specer)** — 读标记 → `skein-spec maintain --apply` 一次性自动修可修项 (判据同 prune 分表, 见 [references/prune-workflow.md](references/prune-workflow.md); 处置动作见 [references/maintain.md](references/maintain.md) `--apply` 段)。
4. **收尾** — reindex → 清 `.pending-fix` 标记。每步追加写 `.audit-log` (7 天轮转)。所有动作可逆 (archive 可 `restore <ts>` 回滚, inclusion 可改回), 误修后续手工纠正。

**双保险**: skein-flow finish 阶段闭环后也检测一次 `.pending-fix` 标记 (防 Stop hook 漏检), 详见 skein-flow finish 阶段流程。

**不修断链 / product**: `[[slug]]` 目标缺失无法自动决断该修链还是建目标, product namespace 的 anchors 失效无法自动决断需求是否真已过时, 均只在回传里列清单待人判断; 其余判据 (rules/external 的 stale/keywords 重复/废弃, map 的 anchors) 明确、处置可逆, 直接自动修。
