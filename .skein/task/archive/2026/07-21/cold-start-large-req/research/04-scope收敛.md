# 04 范围界定 / scope 收敛技巧

## 维度概述

scope 收敛 = 把模糊愿景里「什么都想要」压成「先做什么」。核心共识 (AltexSoft 等多源): **Walking Skeleton 是最适合 AI agent 单对话内跑完的轻量法** (它只问「最小端到端能跑通的几件事是什么」, 答案直接 = 第一个 task)。MoSCoW/Kano 偏分类排序 (适合 backlog 级, 偏重), RICE 偏打分 (需数据, AI 单对话难凑齐)。

## 条目表

| 条目 | 证据 | 来源 URL | 可信度 | 文档/社区/推断 |
|---|---|---|---|---|
| **Walking Skeleton 作 MVP 定序**: 「用于 MVP 功能定序, 定义哪些功能对产品能工作绝对关键」。即 walking skeleton 回答的不是「做不做」而是「最先做哪几件让骨架能走」 — 天然适合冷启动第一刀 | "the Walking Skeleton is used in prioritizing features in MVP and defines which of them are absolutely critical for the product to work" | https://www.altexsoft.com/blog/most-popular-prioritization-techniques-and-methods-moscow-rice-kano-model-walking-skeleton-and-others/ | 二手 (综述) | 文档写的 |
| **MoSCoW 四桶**: Must / Should / Could / Won't-have。快速对齐法, 单对话可跑 — 但**Won't-have 桶才是冷启动最关键的产出** (显式声明不做, 抑制 scope 膨胀) | "MoSCoW as an acronym-based prioritization technique that organizes requirements into four distinct categories (Must/Should/Could/Won't)" | https://plane.so/blog/feature-prioritization-frameworks-rice-moscow-and-kano-explained ; https://www.hotpmo.com/management-models/moscow-kano-prioritize/ | 二手 (多源一致) | 文档写的 |
| **Kano 模型**: 按功能对满意度影响分 (basic/must / performance / excitement/delight)。偏客户调研视角, 单对话内难凑数据, **不适合 AI agent 即时收敛**, 更适合 human PM 阶段 | "Kano model helps teams understand how different features influence customer satisfaction" | https://plane.so/blog/feature-prioritization-frameworks-rice-moscow-and-kano-explained | 二手 | 文档写的 |
| **Thin Slice (Agile)**: 尽早释放小功能组件拿反馈。与 vertical slice + walking skeleton 三位一体, 是 scope 收敛的「先切薄」操作 | "The concept of delivering a thin slice in Agile methodology is centered around the early release of functional components" | https://blog.newmathdata.com/agile-thin-slice-technique-explained-257d800b0592 | 二手 | 文档写的 |
| **liza Out-of-Scope 显式声明**: epic/spec 必须有「Out of Scope covers adjacent concerns the Coder might drift into」段, 即 anti-pattern「Scope Absorption」的对抗手段 — 显式列「源说 X, 你别顺手做 Y/Z」 | "Out of Scope covers adjacent concerns the Coder might drift into"; Scope Absorption anti-pattern | skills/detailed-spec-writing/SKILL.md §Self-Review + Anti-Patterns | 一手 | 文档写的 |
| **liza 「Multiple capabilities → flag for split, never mega-spec」**: scope 收敛的硬门 — 一个 spec 装多个独立能力 = 必拆, 禁默默产 mega 文档。冷启动遇「重构整个 X」类必命中此门 | "Multiple independent capabilities → flag to Orchestrator for split. Do not silently produce a mega-spec" | skills/detailed-spec-writing/SKILL.md §Protocol.1.Parse ; epic-writing §0.Size | 一手 | 文档写的 |

## 矛盾点 (保留不和稀泥)

- **MoSCoW 的 Could/Won't vs SKEIN「必建 task」约束**: MoSCoW 把需求分四桶, 但 SKEIN 只对 Must (可立即拆 subtask 的) 建 task; Should/Could 该落哪? 直接建 task 会违反「task 必有可拆 subtask」(这些还没到可拆程度)。**取舍**: Could/Won't 落 prd.md「非目标/未来」段, Should 落 prd.md「后续 task」占位但不 `skein create`, 待 Must 那批 finish 后再激活。
- **Kano 需数据 vs AI 单对话零数据**: Kano 要客户调研输入, AI agent 在单对话里没有这些数据, 强行套会编造。**结论**: cold-start 档不用 Kano (标「需 human PM 数据, 不适合 AI 即时」)。

## 对 SKEIN 的适用性标注

| 技巧 | 适用性 | 说明 |
|---|---|---|
| Walking Skeleton | **强适配 (冷启动第一刀)** | cold-start 拆能力域后, 强制第一个 task = walking skeleton (端到端最薄能跑通)。这是把模糊愿景变可验证的最快路径 |
| MoSCoW (取 Won't-have) | **适配 (只用 Won't 桶)** | cold-start 必产「显式不做」列表写进 prd.md 非目标段, 抑制 scope 膨胀。Must/Should/Could 分类对 SKEIN 价值不大 (SKEIN 用复杂度天花板 + capability 切分替代) |
| Thin Slice | **适配 (与 walking skeleton 合并)** | 不单列, 并入 walking skeleton 概念 |
| Kano | **不适用** | 需客户调研数据, AI 单对话难凑; cold-start 标「不引入」 |
| RICE 打分 | **不适用** | 需 reach/impact 数据, 同 Kano 问题 |
| Out-of-Scope 显式段 | **适配 (直接用)** | prd.md 强制有「非目标」段 (现有 prd 模板已有「边界/非目标」, 强化其强制力), 对抗 Scope Absorption |
| 多能力必拆门 | **适配 (与天花板合并)** | cold-start 命中复合嗅味/multi-capability → 强制走复杂度天花板分支拆多 task, 禁 mega task |
