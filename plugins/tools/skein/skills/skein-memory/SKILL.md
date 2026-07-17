---
name: skein-memory
description: 两层规则记忆 (基于 .skein/spec)。planning 时召回相关规则、task finish 后沉淀学习时使用 — core 常驻硬规 + recall 按需召回, 经 sediment 判定门 (checklist) 自动写盘 (无需逐次询问用户)。SKEIN 差异化核心。空仓冷启动 (.skein/spec 为空) 时可提议扫既有代码库约定播种规则基线 (一次性)。既有记忆大面积失效 (大重构/换技术栈/记忆漂移) 时可完全重构 (reconstruct): 可逆归档旧规则后依代码+项目内容按项目类型分型重建
argument-hint: "[recall/sediment/bootstrap/reconstruct [recall|full|deep]]"
arguments: "[recall/sediment/bootstrap/reconstruct [recall|full|deep]]"
model: inherit
effort: medium
---

# skein-memory — 两层规则记忆

**差异化核心**。不同于「按需沉淀单一 spec 文件」, SKEIN 记忆分两层, 基于 `.skein/spec`:

> **绑定 agent `skein-memorier`** (相互绑定, 它 frontmatter `skills: skein:skein-memory`): 记忆员, 承载两类作业 —— recall 检索 (planning) + sediment (finish 读 diff + subagent 回传摘要 跑判定门产候选 + 写盘)。**异步 fire-and-forget 模式** (被 `skein-finish` 在 finish 闭环后派发): memorier 自主跑判定门 + `skein-memory sediment` 写盘 + reindex, **无需 main 等待回传** (main 派发即结束回合, 回传到达后只补 output trace; 判定门通过即自动写, 不逐次询问用户)。仅 bootstrap/reconstruct 全局动作跑前一次征同意。

| 层         | 路径                             | 加载                                                 | 适合                             |
| ---------- | -------------------------------- | ---------------------------------------------------- | -------------------------------- |
| **core**   | `.skein/spec/core/<类目>/*.md`   | 每 session 常驻 (SessionStart hook 注入正文)         | 硬约束 / 命令式契约 (后续必再踩) |
| **recall** | `.skein/spec/recall/<类目>/*.md` | 按需语义召回 (planning 时 grep index → model 读全文) | 长尾、上下文密集经验             |

**两层 × 类目**: 层内按类目 (category) 分子目录 —— git / test / arch / build / style / domain / ops... 自由取名、按需建。索引三份: 每层 `<layer>/index.md` (层内全规则, 带 category 列) + 顶层 `index.md` (两层聚合概览)。core 常驻有软预算 (8000 字符, 超则告警降级, 契合「常驻只放最小硬规」)。

## recall (planning 阶段, main)

```
skein-memory recall "<任务关键词>"
```

- grep `recall/index.md` 输出命中行 → **model 读命中规则全文, 判是否真相关** → 相关的注入当前 task 上下文 (dispatch prompt「已知」段带上)。
- core 规则已由 SessionStart hook 常驻, 无需 recall。

## sediment (task finish 阶段, 异步 fire-and-forget) — 判定门 + 自主写盘

task finish 闭环后由 `skein-finish` 异步 fire-and-forget 派 `skein-memorier` 跑「判定门 checklist → 分层归类 → `skein-memory sediment` 自主写盘 + reindex」三步 (含升降级)。**异步**: main 派 memorier 即结束回合, 不等回传 (finish 已闭环, 禁为 sediment 阻塞); memorier 自主写盘, 回传到达后 main 只补 output trace 供审阅。**判定门 (语义) 通过即写, 不逐次 AskUserQuestion** —— 记忆积累高频, 每次询问是噪声; 误沉淀后续调层/删文件可逆纠正。完整判定 trace 模板、分层/归类规则、写盘命令详见 [references/sediment-workflow.md](references/sediment-workflow.md)。

## 空仓冷启动播种 (一次性, main)

新仓 `.skein/spec` 为空时前几十轮 planning 无规则可召回。此时 main **可**提议从既有代码库提炼约定作冷启动基线 —— 派 skein-researcher 扫五维 (命名/错误处理/测试/架构边界/构建), 候选逐条判 core/recall/drop, 复用上文 sediment 写盘流程落盘 (bootstrap 跑前一次征同意覆盖整轮, 内部候选自动写)。

一次性动作, `AskUserQuestion` 征同意再跑 (禁自动); 用户拒 → 走正常 planning, 规则随 finish sediment 增量积累。完整流程 (触发条件 / 五维明细 / 判层表 / 落盘) 见 [references/bootstrap-seeding.md](references/bootstrap-seeding.md)。

## 完全重构 (reconstruct, main) — 依代码/项目内容重建整库

既有记忆大面积失效 (大重构 / 换技术栈 / 记忆漂移 / 接手可疑旧库) 时, 把两层规则**可逆归档**后依当前代码 + 项目内容从零重建。区别于 bootstrap (仅空仓、纯增量): 重构多 `skein-memory archive` 前置 (可逆清库) + **按项目类型分型扫描**。

**三档程度** (`reconstruct <recall|full|deep>`, 落在 ②archive 范围 + ④扫描深度, 非脚本参数):

| 档 | archive 范围 | 扫描 | 适用 |
| --- | --- | --- | --- |
| **recall** (轻) | `archive --layer recall` (保留手工 core) | 五维基线 + 主类型侧重 | 漂移/污染集中长尾, core 仍可信 |
| **full** (全) | `archive` 两层全归档 | 五维基线 + 主类型侧重 | 换栈/架构翻新, core 也过期 |
| **deep** (深) | `archive` 两层全归档 | 五维 + **全 8 型探针深扫** + 旧规则逐条比对 | 接手可疑成熟仓/来源不明, 从零核 |

```
skein-memory archive            # 可逆归档旧规则到 .skein/spec/.archive/<ts>/ (full/deep)
skein-memory archive --layer recall  # 只归档 recall (recall 档)
skein-memory restore <ts>       # 回滚 (撞名不覆盖新规则)
```

流程: 快照 → 归档 → 识别项目类型 → 分型扫描 (researcher bootstrap 模式 + 类型侧重) → 逐条判层 → sediment 自动写盘 → 验证 + 保留归档。🛑 `AskUserQuestion` 征同意再跑 (归档全库虽可逆仍是全局动作 · STOP, 禁自动)。**事无巨细设计 + 8 类项目 (backend/frontend/cli/monorepo/data-ml/infra/mobile/docs) 分型扫描侧重、探针、core 倾向、规则示例、陷阱** 见 [references/reconstruct-memory.md](references/reconstruct-memory.md)。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                          | 一线修复                                          | 仍失败兜底                                                   |
| ----------------------------- | ------------------------------------------------- | ------------------------------------------------------------ |
| recall grep 无命中            | 放宽 / 换关键词重 grep 一次 (同义词 / 上位类目)   | 仍无 → planning 走无规则路径, 不阻塞; 靠 finish sediment 增量补 |
| `skein-memory sediment/reindex` 报错 | 读脚本 stderr 定位 (路径 / 权限 / 类目名非法)    | 仍失败 → 该候选暂存草案不落盘, 记 `需要: 手工核对`, 禁半写坏盘 |
| core 常驻超 8000 字符告警     | 把最少复用的 core 规则降级到 recall (`sediment` 调层) | 仍超 → 停手, 提示用户 core 膨胀, 需人工裁剪硬规集            |
| reconstruct 重建不满意        | `skein-memory restore <ts>` 从归档恢复 (撞名加 restored- 前缀并存) | 仍失败 → 归档目录仍在 `.skein/spec/.archive/<ts>/`, 手动核对取舍 |

## 反例

| 禁                                | 改为                                    |
| --------------------------------- | --------------------------------------- |
| sediment 未输出判定 trace         | 逐项 /输出 (memorier 回传后 main 补)    |
| 无增量硬凑沉淀                    | 全否跳过                                |
| 逐次 AskUserQuestion 问用户批不批    | 判定门通过即自主写, 只输出 trace 不硬停 |
| finish 为等 sediment 阻塞闭环     | sediment 异步 fire-and-forget, finish 先 archive |
| 写盘不同步 index.md               | skein-memory sediment 自动同步, 禁手改绕过 |
| 什么都塞 core 常驻                | 默认 recall, core 只留硬约束            |
