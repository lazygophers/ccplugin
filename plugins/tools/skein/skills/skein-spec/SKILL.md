---
name: skein-spec
description: 规则记忆库 (基于 .skein/spec)。planning 时 recall 召回相关规则、task finish 后 sediment 沉淀学习 + prune 自动精简过期/重复/断链规则。加载策略由 frontmatter `inclusion` 定 (always 常驻注入 / auto 按需召回 / fileMatch 按 globs / manual 纯手动), 与所在 namespace 目录正交; 经判定门自动写盘 (不逐次问用户)。产出 .skein/spec 下 <namespace>/<类目>/<主题>.md + index。另支持空仓 bootstrap 播种规则基线、记忆大面积失效 (大重构/换栈) 时 reconstruct 可逆归档后按项目类型分型重建、maintain 手动体检 (超预算/stale/断链/重复/废弃, --apply 自动修复)、auto-fix (Stop hook 写 .pending-fix 标记 → main 派 skein-specer bg 跑 maintain --apply 全自动修, 断链只报告)。
user-invocable: true
argument-hint: "[模式: recall/召回, sediment/沉淀, prune/精简, bootstrap/播种, reconstruct/重构, maintain/维护 (加 --apply 自动修)] [--deep=recall/low/full/deep/max/high (reconstruct 模式可选)]"
arguments: "[模式: recall/召回, sediment/沉淀, prune/精简, bootstrap/播种, reconstruct/重构] [--deep=recall/low/full/deep/max/high]"
model: inherit
effort: medium
---

# skein-spec — 规则记忆库 (namespace × inclusion)

> 🔒 全局流程规则（状态机/调度/优先级等）以 skein-flow/references/ 为单一真值源。

**差异化核心**。不同于「按需沉淀单一 spec 文件」, SKEIN 记忆按两个正交维度组织, 基于 `.skein/spec`:

> **绑定 agent (按读/写拆两个, 均 frontmatter `skills: skein:skein-spec`)**:
> - **读路径 → `skein-recaller`** (只读同步召回员, 单一 recall 职责): recall 检索 (planning) 派它, **main 等召回结果进 planning** (dispatch prompt「已知」段带上)。
> - **写路径 → `skein-specer`** (记忆写盘员): sediment/reconstruct·maintain/prune 三类写作业 (finish 读 diff + subagent 回传摘要 跑判定门产候选 + 写盘 + reindex)。**异步 fire-and-forget 模式** (被 skein-flow finish 阶段在 finish 闭环后派发): specer 自主跑判定门 + `skein-spec sediment` 写盘 + reindex, **无需 main 等待回传** (main 派发即结束回合, 回传到达后只补 output trace; 判定门通过即自主写, 不逐次询问用户)。仅 bootstrap/reconstruct 全局动作跑前一次征同意。

| 层 | 路径 | 加载 | 适合 |
|---|---|---|---|
| **core** | `.skein/spec/core/<类目>/*.md` | 每 session 常驻 (SessionStart hook 注入正文) | 硬约束 / 命令式契约 (后续必再踩) |
| **recall** | `.skein/spec/recall/<类目>/*.md` | 按需语义召回 (planning 时 grep index → model 读全文) | 长尾、上下文密集经验 |

**namespace × 类目**: namespace 内按类目 (category) 分子目录 —— git / test / arch / build / style / domain / ops... 自由取名、按需建。索引: 每个 `<namespace>/index.md` (该 namespace 全规则, 带 category / inclusion / anchors 列) + 顶层 `index.md` 聚合概览。`inclusion: always` 的页有软预算 (默认 1000 字符, 可改 config.yaml `spec.always_budget`; 超则告警降级, 契合「常驻只放最小硬规」) —— 预算算的是 **inclusion 值**, 与规则放哪个 namespace 目录无关。

## 寻找纪律 (planning/调研/找方案时)

**动手前优先跑 `skein-spec recall "<关键词>"`** — 现有规则沉淀比凭记忆重推快且准, core 已常驻无需 recall。
顺序: recall spec (全 namespace, FTS5 BM25 排序) → vault → 项目本地 (Read/Grep) → 外部搜索。
recall 命中 → model 读全文判相关 → 相关的注入当前 task 上下文 (dispatch prompt「已知」段带上)。
external 层 (不入 hook, 纯手动) 存长文档/外部资料, 同经 `recall` 跨层检索。

## recall (planning 阶段, 派 skein-recaller)

> 召回由 `skein-recaller` (只读同步召回员) 承载, main 等其结果进 planning。

```
skein-spec recall "<任务关键词>"
```

- grep `recall/index.md` 输出命中行 → **model 读命中规则全文, 判是否真相关** → 相关的注入当前 task 上下文 (dispatch prompt「已知」段带上)。
- core 规则已由 SessionStart hook 常驻, 无需 recall。

## sediment (task finish 阶段, 异步 fire-and-forget) — 判定门 + 自主写盘

task finish 闭环后由 skein-flow finish 阶段异步 fire-and-forget 派 `skein-specer` 跑「判定门 checklist → 分层归类 → `skein-spec sediment` 自主写盘 + reindex」三步 (含升降级)。**异步**: main 派 skein-specer 即结束回合, 不等回传 (finish 已闭环, 禁为 sediment 阻塞); skein-specer 自主写盘, 回传到达后 main 只补 output trace 供审阅。**判定门 (语义) 通过即写, 不逐次 AskUserQuestion** —— 记忆积累高频, 每次询问是噪声; 误沉淀后续调层/删文件可逆纠正。完整判定 trace 模板、分层/归类规则、写盘命令详见 [references/sediment-workflow.md](references/sediment-workflow.md)。

## prune (sediment 后自动精简, skein-specer) — 判定门 + 自主归档

sediment 写盘后, skein-specer 顺带跑一轮精简: 扫全 namespace 规则, 按 maintain 判据检出 candidate, 对命中项自动 archive (可逆) 而非只报告。**异步 fire-and-forget**: 同 sediment, main 派即放手, 不等回传。

**精简判定门** (命中任一条即 archive):

| 判据 | 触发 | 处置 |
|---|---|---|
| stale | created > 180 天且 updated 无后续 | `skein-spec archive <path>` |
| keywords 重复 | 同 keywords 组 ≥ 3 条 | 保留最新 (按 updated), 其余 archive |
| 废弃 | status=deprecated / superseded | `skein-spec archive <path>` |
| 断链 | `[[slug]]` 目标 stem 库内无匹配 | `skein-spec archive <path>` |
| core 超预算 | always 页全文超 `spec.always_budget` | 降级最少复用的 core 规则到 recall (`sediment` 调层) |

- **archive 即可逆, 不删文件** — 全走 `skein-spec archive` 可逆归档到 `.skein/spec/.archive/<ts>/`, 如需恢复 `restore <ts>`。
- **保护标记**: 规则头 `protected: true` 的跳过不精简 (手工核验后标记, 禁自动 archive)。
- **无命中 → 跳过** — 未检出任何 candidate 则如实报「无精简项」, 不空跑 archive。

完整流程见 [references/prune-workflow.md](references/prune-workflow.md)。

## 写盘参照模板 (软骨架, 非强制)

两类规则 body 各有脊柱, sediment 写盘前 skein-specer 参照对应模板填:

- **core** 规则 (命令式契约) 参照 [references/templates/core.md.tmpl](references/templates/core.md.tmpl): 铁律/契约 (MUST/禁, 一句一规则) + 反例表 (禁/改为) + 可选关联。
- **recall** 规则 (ADR/陷阱型) 参照 [references/templates/recall.md.tmpl](references/templates/recall.md.tmpl): 触发场景 / 陷阱-正解 / 反例 / 案例 / 适用 / 关联。

> **参考骨架非强制** — sediment 是 fire-and-forget, 模板仅作 skein-specer 填 body 的结构引导, **不强校验、不阻塞写盘**; 实际规则按内容取舍段名 (elastic spine), 缺段不报错。

## 空仓冷启动播种 (一次性, main)

新仓 `.skein/spec` 为空时前几十轮 planning 无规则可召回。此时 main **可**提议从既有代码库提炼约定作冷启动基线 —— 派 skein-researcher 扫五维 (命名/错误处理/测试/架构边界/构建), 候选逐条定 namespace×inclusion 或 drop, 复用上文 sediment 写盘流程落盘 (bootstrap 跑前一次征同意覆盖整轮, 内部候选自动写)。

一次性动作, `AskUserQuestion` 征同意再跑 (禁自动); 用户拒 → 走正常 planning, 规则随 finish sediment 增量积累。完整流程 (触发条件 / 五维明细 / ns×inclusion 判定表 / 落盘) 见 [references/bootstrap-seeding.md](references/bootstrap-seeding.md)。

## 完全重构 (reconstruct, main) — 依代码/项目内容重建整库

既有记忆大面积失效 (大重构 / 换技术栈 / 记忆漂移 / 接手可疑旧库) 时, 把全库规则**可逆归档**后依当前代码 + 项目内容从零重建。区别于 bootstrap (仅空仓、纯增量): 重构多 `skein-spec archive` 前置 (可逆清库) + **按项目类型分型扫描**。

**六档深度** (`reconstruct --deep=<recall|low|full|deep|max|high>`, 对应 ②archive 范围 + ④扫描深度):

| 档 | archive 范围 | 扫描 | 适用 |
|---|---|---|---|
| **recall** | `archive --namespace <长尾 ns>` (其余 namespace 保留) | 五维基线 + 主类型侧重 | 漂移/污染集中长尾, always 页仍可信 |
| **low** | `archive --namespace <长尾 ns>` (其余 namespace 保留) | 五维基线 | 轻量核查, 仅验证该 namespace 完整性 |
| **full** | `archive` 全 namespace 归档 | 五维基线 + 主类型侧重 | 换栈/架构翻新, always 页也过期 |
| **deep** | `archive` 全 namespace 归档 | 五维 + **全 8 型探针深扫** | 全面重建, 深挖长尾规则 |
| **max** | `archive` 全 namespace 归档 | 五维 + 全 8 型 + 旧规则逐条比对 | 彻底重建, 交叉验证新旧规则 |
| **high** | `archive` 全 namespace 归档 | 五维 + 全 8 型 + 旧规则逐条比对 + 交叉验证 | 接手可疑成熟仓/来源不明, 从零核 |

```
skein-spec archive --namespace <ns>   # 只归档指定 namespace (recall/low 档)
skein-spec archive                    # 全 namespace 归档 (full/deep/max/high 档)
skein-spec restore <ts>               # 回滚 (撞名不覆盖新规则, 加 restored- 前缀并存)
# 注: 深度档 (recall/low/full/deep/max/high) 是本 skill 的参数, 决定「归档多大范围 + 扫多深」,
#     不是 CLI 参数 —— archive 只认 --namespace。
```

流程: 快照 → 归档 → 识别项目类型 → 分型扫描 (researcher bootstrap 模式 + 类型侧重) → 逐条定 ns×inclusion → sediment 自动写盘 → 验证 + 保留归档。🛑 `AskUserQuestion` 征同意再跑 (归档全库虽可逆仍是全局动作 · STOP, 禁自动)。**事无巨细设计 + 8 类项目 (backend/frontend/cli/monorepo/data-ml/infra/mobile/docs) 分型扫描侧重、探针、always 倾向、规则示例、陷阱** 见 [references/reconstruct-memory.md](references/reconstruct-memory.md)。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| recall grep 无命中 | 放宽 / 换关键词重 grep 一次 (同义词 / 上位类目) | 仍无 → planning 走无规则路径, 不阻塞; 靠 finish sediment 增量补 |
| `skein-spec sediment/reindex` 报错 | 读脚本 stderr 定位 (路径 / 权限 / 类目名非法) | 仍失败 → 该候选暂存草案不落盘, 记 `需要: 手工核对`, 禁半写坏盘 |
| core 常驻超预算告警 | prune 自动降级最少复用的 core 到 recall (`sediment` 调层) | 仍超 → 停手, 提示用户 core 膨胀, 需人工裁剪硬规集 |
| reconstruct 重建不满意 | `skein-spec restore <ts>` 从归档恢复 (撞名加 restored- 前缀并存) | 仍失败 → 归档目录仍在 `.skein/spec/.archive/<ts>/`, 手动核对取舍 |

## ✅ 正向配方 (命中反面=流程错误)

> 🔒 铁律: sediment+prune 异步 fire-and-forget 禁阻塞 finish; core 只留命令式硬约束。

| 场景 | 正确做法 (❌ 反面) |
|---|---|
| sediment 写盘 / prune 自动 archive | 逐项输出判定 trace, skein-specer 回传后 main 补 (❌ 未输出判定 trace) |
| 判定门全否 | 跳过不沉淀 (❌ 无增量硬凑沉淀) |
| 判定门通过要不要问用户 | 自主写盘, 只输出 trace 不硬停 (❌ 逐次 AskUserQuestion 问用户批不批) |
| finish 闭环 vs sediment/prune | 异步 fire-and-forget, finish 先 archive (❌ 为等 sediment/prune 阻塞闭环) |
| 写盘更新 index.md | skein-spec sediment 自动同步 (❌ 不同步 index.md / 手改绕过) |
| 规则分层 | 默认落 recall, core 只留硬约束 (❌ 什么都塞 core 常驻) |

## maintain (手动体检, main)

规则库漂移时的**手动全量体检** (供 user 在 sediment+prune 之外独立审查, 只报告不动手): `skein-spec maintain [--namespace <ns>]`。5 判据 (超预算 / stale / 断链 / keywords 重复 / 归档残留) + 输出格式详见 [references/maintain.md](references/maintain.md)。加 `--apply` 则同一扫描自动修复可修项 (超预算→循环降级 always→auto / stale→归档 / keywords 重复→归档保留最新 / 废弃→归档; 断链仍只报告), 每步写 `.audit-log` (7 天轮转), 详见 auto-fix 模式与 [references/maintain.md](references/maintain.md)。

## auto-fix (Stop hook 触发, 异步 fire-and-forget) — 全自动 spec 修复

sediment+prune 是 finish 后顺跑一轮, 仍可能漏 (如 session 中途 core 膨胀超预算 / 新增断链)。auto-fix 用 **Stop hook + .pending-fix 标记** 做异步兜底修复, 全程无需用户介入。

```
skein-spec maintain --apply   # 同一次扫描自动修可修项 (断链只报告)
```

**流程**:

1. **检测 (Stop hook)** — 回合结束 Stop hook 跑轻量 spec 体检, 检出任一可修项 (超预算 / stale / keywords 重复 / 废弃 / 断链) → 写 `.skein/spec/.pending-fix` 标记 (含命中项摘要 + ts)。
2. **派发 (main)** — main 检测到 `.pending-fix` → 异步 bg 派 `skein-specer` (fire-and-forget, 派出即结束回合, 不等回传, 与 sediment 同模式)。
3. **修复 (skein-specer)** — 读标记 → `skein-spec maintain --apply` 一次性自动修:

| 问题 | 处置 |
|---|---|
| 超预算 (always 页超 `spec.always_budget`) | 循环降级 top-1 最大 always 页 → auto, 直到不超 |
| stale (created > 180 天) | archive (可逆) |
| keywords 重复 (同组 ≥ 3) | 保留最新, 余 archive (可逆) |
| 废弃 (deprecated/superseded) | archive (可逆) |
| 断链 (`[[slug]]` 目标缺失) | **只报告, 不修** — 需人判断修哪头 (改链or建目标) |

4. **收尾** — reindex → 清 `.pending-fix` 标记。每步追加写 `.audit-log` (7 天轮转)。所有动作可逆 (archive 可 `restore <ts>` 回滚, layer 可改回), 误修后续手工纠正。

**双保险**: skein-flow finish 阶段闭环后也检测一次 `.pending-fix` 标记 (防 Stop hook 漏检), 详见 skein-flow finish 阶段流程。

**不修断链**: `[[slug]]` 目标缺失无法自动决断该修链还是建目标, 只在回传里列清单待人判断; 其余 4 类判据明确、处置可逆, 直接自动修。
