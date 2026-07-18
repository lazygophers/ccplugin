---
name: skein-spec
description: 两层规则记忆 (基于 .skein/spec)。planning 时 recall 召回相关规则、task finish 后 sediment 沉淀学习。core 常驻硬规 + recall 按需召回, 经判定门自动写盘 (不逐次问用户)。产出 .skein/spec 下 core/recall 规则文件 + index。另支持空仓 bootstrap 播种规则基线、记忆大面积失效 (大重构/换栈) 时 reconstruct 可逆归档后按项目类型分型重建、maintain 定期体检 (超预算/stale/断链/重复/废弃, 只报告)。硬约束: sediment 异步 fire-and-forget 不阻塞 finish; core 只留硬约束
argument-hint: "[模式: recall/召回, sediment/沉淀, bootstrap/播种, reconstruct/重构, maintain/维护] [--deep=recall/low/full/deep/max/high (reconstruct 模式可选)]"
arguments: "[模式: recall/召回, sediment/沉淀, bootstrap/播种, reconstruct/重构] [--deep=recall/low/full/deep/max/high]"
model: inherit
effort: medium
---

# skein-spec — 两层规则记忆

**差异化核心**。不同于「按需沉淀单一 spec 文件」, SKEIN 记忆分两层, 基于 `.skein/spec`:

> **绑定 agent `skein-specer`** (相互绑定, 它 frontmatter `skills: skein:skein-spec`): 记忆员, 承载两类作业 —— recall 检索 (planning) + sediment (finish 读 diff + subagent 回传摘要 跑判定门产候选 + 写盘)。**异步 fire-and-forget 模式** (被 `skein-finish` 在 finish 闭环后派发): memorier 自主跑判定门 + `skein-spec sediment` 写盘 + reindex, **无需 main 等待回传** (main 派发即结束回合, 回传到达后只补 output trace; 判定门通过即自动写, 不逐次询问用户)。仅 bootstrap/reconstruct 全局动作跑前一次征同意。

| 层         | 路径                             | 加载                                                 | 适合                             |
| ---------- | -------------------------------- | ---------------------------------------------------- | -------------------------------- |
| **core**   | `.skein/spec/core/<类目>/*.md`   | 每 session 常驻 (SessionStart hook 注入正文)         | 硬约束 / 命令式契约 (后续必再踩) |
| **recall** | `.skein/spec/recall/<类目>/*.md` | 按需语义召回 (planning 时 grep index → model 读全文) | 长尾、上下文密集经验             |

**两层 × 类目**: 层内按类目 (category) 分子目录 —— git / test / arch / build / style / domain / ops... 自由取名、按需建。索引三份: 每层 `<layer>/index.md` (层内全规则, 带 category 列) + 顶层 `index.md` (两层聚合概览)。core 常驻有软预算 (8000 字符, 超则告警降级, 契合「常驻只放最小硬规」)。

## recall (planning 阶段, main)

```
skein-spec recall "<任务关键词>"
```

- grep `recall/index.md` 输出命中行 → **model 读命中规则全文, 判是否真相关** → 相关的注入当前 task 上下文 (dispatch prompt「已知」段带上)。
- core 规则已由 SessionStart hook 常驻, 无需 recall。

## sediment (task finish 阶段, 异步 fire-and-forget) — 判定门 + 自主写盘

task finish 闭环后由 `skein-finish` 异步 fire-and-forget 派 `skein-specer` 跑「判定门 checklist → 分层归类 → `skein-spec sediment` 自主写盘 + reindex」三步 (含升降级)。**异步**: main 派 memorier 即结束回合, 不等回传 (finish 已闭环, 禁为 sediment 阻塞); memorier 自主写盘, 回传到达后 main 只补 output trace 供审阅。**判定门 (语义) 通过即写, 不逐次 AskUserQuestion** —— 记忆积累高频, 每次询问是噪声; 误沉淀后续调层/删文件可逆纠正。完整判定 trace 模板、分层/归类规则、写盘命令详见 [references/sediment-workflow.md](references/sediment-workflow.md)。

## 写盘参照模板 (软骨架, 非强制)

两类规则 body 各有脊柱, sediment 写盘前 memorier 参照对应模板填:

- **core** 规则 (命令式契约) 参照 [references/templates/core.md.tmpl](references/templates/core.md.tmpl): 铁律/契约 (MUST/禁, 一句一规则) + 反例表 (禁/改为) + 可选关联。
- **recall** 规则 (ADR/陷阱型) 参照 [references/templates/recall.md.tmpl](references/templates/recall.md.tmpl): 触发场景 / 陷阱-正解 / 反例 / 案例 / 适用 / 关联。

> **参考骨架非强制** — sediment 是 fire-and-forget, 模板仅作 memorier 填 body 的结构引导, **不强校验、不阻塞写盘**; 实际规则按内容取舍段名 (elastic spine), 缺段不报错。

## 空仓冷启动播种 (一次性, main)

新仓 `.skein/spec` 为空时前几十轮 planning 无规则可召回。此时 main **可**提议从既有代码库提炼约定作冷启动基线 —— 派 skein-researcher 扫五维 (命名/错误处理/测试/架构边界/构建), 候选逐条判 core/recall/drop, 复用上文 sediment 写盘流程落盘 (bootstrap 跑前一次征同意覆盖整轮, 内部候选自动写)。

一次性动作, `AskUserQuestion` 征同意再跑 (禁自动); 用户拒 → 走正常 planning, 规则随 finish sediment 增量积累。完整流程 (触发条件 / 五维明细 / 判层表 / 落盘) 见 [references/bootstrap-seeding.md](references/bootstrap-seeding.md)。

## 完全重构 (reconstruct, main) — 依代码/项目内容重建整库

既有记忆大面积失效 (大重构 / 换技术栈 / 记忆漂移 / 接手可疑旧库) 时, 把两层规则**可逆归档**后依当前代码 + 项目内容从零重建。区别于 bootstrap (仅空仓、纯增量): 重构多 `skein-spec archive` 前置 (可逆清库) + **按项目类型分型扫描**。

**六档深度** (`reconstruct --deep=<recall|low|full|deep|max|high>`, 对应 ②archive 范围 + ④扫描深度):

| 档 | archive 范围 | 扫描 | 适用 |
| --- | --- | --- | --- |
| **recall** | `archive --layer recall` (保留手工 core) | 五维基线 + 主类型侧重 | 漂移/污染集中长尾, core 仍可信 |
| **low** | `archive --layer recall` (保留手工 core) | 五维基线 | 轻量核查, 仅验证 recall 层完整性 |
| **full** | `archive` 两层全归档 | 五维基线 + 主类型侧重 | 换栈/架构翻新, core 也过期 |
| **deep** | `archive` 两层全归档 | 五维 + **全 8 型探针深扫** | 全面重建, 深挖长尾规则 |
| **max** | `archive` 两层全归档 | 五维 + 全 8 型 + 旧规则逐条比对 | 彻底重建, 交叉验证新旧规则 |
| **high** | `archive` 两层全归档 | 五维 + 全 8 型 + 旧规则逐条比对 + 交叉验证 | 接手可疑成熟仓/来源不明, 从零核 |

```
skein-spec archive --deep=recall|low    # 只归档 recall 层 (recall/low 档)
skein-spec archive --deep=full|deep|max|high  # 两层全归档 (full/deep/max/high 档)
skein-spec archive --deep=high           # 最重档 (full + 交叉验证)
skein-spec archive --layer recall        # 只归档 recall (兼容旧式)
skein-spec archive                       # 全归档 (兼容旧式, 等效 --deep=full)
skein-spec restore <ts>                  # 回滚 (撞名不覆盖新规则)
```

流程: 快照 → 归档 → 识别项目类型 → 分型扫描 (researcher bootstrap 模式 + 类型侧重) → 逐条判层 → sediment 自动写盘 → 验证 + 保留归档。🛑 `AskUserQuestion` 征同意再跑 (归档全库虽可逆仍是全局动作 · STOP, 禁自动)。**事无巨细设计 + 8 类项目 (backend/frontend/cli/monorepo/data-ml/infra/mobile/docs) 分型扫描侧重、探针、core 倾向、规则示例、陷阱** 见 [references/reconstruct-memory.md](references/reconstruct-memory.md)。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                          | 一线修复                                          | 仍失败兜底                                                   |
| ----------------------------- | ------------------------------------------------- | ------------------------------------------------------------ |
| recall grep 无命中            | 放宽 / 换关键词重 grep 一次 (同义词 / 上位类目)   | 仍无 → planning 走无规则路径, 不阻塞; 靠 finish sediment 增量补 |
| `skein-spec sediment/reindex` 报错 | 读脚本 stderr 定位 (路径 / 权限 / 类目名非法)    | 仍失败 → 该候选暂存草案不落盘, 记 `需要: 手工核对`, 禁半写坏盘 |
| core 常驻超 8000 字符告警     | 把最少复用的 core 规则降级到 recall (`sediment` 调层) | 仍超 → 停手, 提示用户 core 膨胀, 需人工裁剪硬规集            |
| reconstruct 重建不满意        | `skein-spec restore <ts>` 从归档恢复 (撞名加 restored- 前缀并存) | 仍失败 → 归档目录仍在 `.skein/spec/.archive/<ts>/`, 手动核对取舍 |

## ❌ 反例 (命中=操作错误)

> 🔒 Iron Law: sediment 异步 fire-and-forget 禁阻塞 finish; core 只留命令式硬约束。

| 禁                                | 改为                                    |
| --------------------------------- | --------------------------------------- |
| sediment 未输出判定 trace         | 逐项 /输出 (memorier 回传后 main 补)    |
| 无增量硬凑沉淀                    | 全否跳过                                |
| 逐次 AskUserQuestion 问用户批不批    | 判定门通过即自主写, 只输出 trace 不硬停 |
| finish 为等 sediment 阻塞闭环     | sediment 异步 fire-and-forget, finish 先 archive |
| 写盘不同步 index.md               | skein-spec sediment 自动同步, 禁手改绕过 |
| 什么都塞 core 常驻                | 默认 recall, core 只留硬约束            |

## maintain (定期体检, main) — 只报告不自动执行

规则库积累后会漂移 (core 膨胀 / 规则过时 / 断链 / keywords 重复 / 废弃未清)。`maintain` 扫两层产体检报告, **列出候选但绝不自动改盘** — 一切纠正 (降级 / 删 / 合并 / 归档) 由人决定 (删除走 `archive` 可逆纠正, 禁直删)。

```
skein-spec maintain                 # 全量体检两层
skein-spec maintain --layer recall  # 仅指定层
```

**4 判据 + 1 归档建议**:

| 判据 | 触发 | 输出示例 |
| --- | --- | --- |
| 超预算 | core 全文 > 8000 字符 | `[超预算] core 8200 > 8000 字符 — 考虑降级: git/big-00(2100)` |
| stale | created 年龄 > 180 天 (~6 月) 且 updated 也老 | `[stale] recall/ops/old-00 (created 14月,420天前, updated 14月,420天前, status active)` |
| 断链 | body 的 `[[slug]]` 目标 stem 库内无匹配 | `[断链] recall/ops/old-00: [[nonexistent]] ✗ 目标缺失` |
| keywords 重复 | 同 keywords 组 ≥ 3 条 | `[重复 keywords] "merge,worktree" ×3: recall/arch/a, recall/ops/b, recall/ops/c` |
| 归档建议 | status=deprecated / superseded | `[废弃] recall/test/old-00 (status deprecated) — 建议 archive` |

**stale 判据 (180 天) 主观可调** — 项目节奏快可收紧 (`STALE_DAYS` in `spec.py`); `created` 缺字段或非 epoch 容错跳过不报错。无任何 findings → 输出 `全清`。
