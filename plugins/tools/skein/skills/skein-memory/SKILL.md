---
name: skein-memory
description: 两层规则记忆 (基于 .skein/spec)。planning 时召回相关规则、task finish 后沉淀学习时使用 — core 常驻硬规 + recall 按需召回, 经 sediment 判定门 (checklist) + AskUserQuestion 审批写盘。SKEIN 差异化核心。空仓冷启动 (.skein/spec 为空) 时可提议扫既有代码库约定播种规则基线 (一次性)。既有记忆大面积失效 (大重构/换技术栈/记忆漂移) 时可完全重构 (reconstruct): 可逆归档旧规则后依代码+项目内容按项目类型分型重建
argument-hint: "[recall/sediment]"
arguments: "[recall/sediment]"
model: inherit
effort: medium
---

# skein-memory — 两层规则记忆

**差异化核心**。不同于「按需沉淀单一 spec 文件」, SKEIN 记忆分两层, 基于 `.skein/spec`:

> **绑定 agent `skein-memorier`** (相互绑定, 它 frontmatter `skills: skein:skein-memory`): 只读记忆员, 承载两类作业 —— recall 检索 (planning) + sediment 草案 (finish 读 diff + subagent 回传摘要 跑判定门产候选)。main 派它产**草案**, 审批 (`AskUserQuestion`) + 写盘 (`skein-memory`) 仍归 main。

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

## sediment (task finish 阶段, main) — 判定门 + 审批写盘

task finish 后走「判定门 checklist → 分层归类 → AskUserQuestion 审批 (写盘前硬停, main 亲做) → skein-memory sediment 写盘 + 自动 reindex」四步 (含升降级)。完整判定 trace 模板、分层/归类规则、写盘命令详见 [references/sediment-workflow.md](references/sediment-workflow.md)。

## 空仓冷启动播种 (一次性, main)

新仓 `.skein/spec` 为空时前几十轮 planning 无规则可召回。此时 main **可**提议从既有代码库提炼约定作冷启动基线 —— 派 skein-researcher 扫五维 (命名/错误处理/测试/架构边界/构建), 候选逐条判 core/recall/drop, 复用上文 sediment 审批门落盘。

一次性动作, `AskUserQuestion` 征同意再跑 (禁自动); 用户拒 → 走正常 planning, 规则随 finish sediment 增量积累。完整流程 (触发条件 / 五维明细 / 判层表 / 落盘) 见 [references/bootstrap-seeding.md](references/bootstrap-seeding.md)。

## 完全重构 (reconstruct, main) — 依代码/项目内容重建整库

既有记忆大面积失效 (大重构 / 换技术栈 / 记忆漂移 / 接手可疑旧库) 时, 把两层规则**可逆归档**后依当前代码 + 项目内容从零重建。区别于 bootstrap (仅空仓、纯增量): 重构多 `skein-memory archive` 前置 (可逆清库) + **按项目类型分型扫描**。

```
skein-memory archive            # 可逆归档旧规则到 .skein/spec/.archive/<ts>/
skein-memory restore <ts>       # 回滚 (撞名不覆盖新规则)
```

流程: 快照 → 归档 → 识别项目类型 → 分型扫描 (researcher bootstrap 模式 + 类型侧重) → 逐条判层 → sediment 审批写盘 → 验证 + 保留归档。`AskUserQuestion` 征同意再跑 (归档虽可逆仍是全局动作, 禁自动)。**事无巨细设计 + 8 类项目 (backend/frontend/cli/monorepo/data-ml/infra/mobile/docs) 分型扫描侧重、探针、core 倾向、规则示例、陷阱** 见 [references/reconstruct-memory.md](references/reconstruct-memory.md)。

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
| sediment 未输出判定 trace         | 逐项 /输出                              |
| 无增量硬凑沉淀                    | 全否跳过                                |
| 派 subagent 做审批 (它不能问用户) | main 亲做 AskUserQuestion               |
| 写盘不同步 index.md               | skein-memory sediment 自动同步, 禁手改绕过 |
| 什么都塞 core 常驻                | 默认 recall, core 只留硬约束            |
