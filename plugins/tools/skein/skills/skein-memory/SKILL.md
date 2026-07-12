---
name: skein-memory
description: 两层规则记忆 (基于 .skein/spec)。planning 时召回相关规则、task finish 后沉淀学习时使用 — core 常驻硬规 + recall 按需召回, 经 sediment 判定门 (checklist) + AskUserQuestion 审批写盘。SKEIN 差异化核心。空仓冷启动 (.skein/spec 为空) 时可提议扫既有代码库约定播种规则基线 (一次性)
disable-model-invocation: true
user-invocable: false
argument-hint: "[recall/sediment]"
arguments: "[recall/sediment]"
model: inherit
effort: medium
---

# skein-memory — 两层规则记忆

**差异化核心**。不同于「按需沉淀单一 spec 文件」, SKEIN 记忆分两层, 基于 `.skein/spec`:

| 层         | 路径                             | 加载                                                 | 适合                             |
| ---------- | -------------------------------- | ---------------------------------------------------- | -------------------------------- |
| **core**   | `.skein/spec/core/<类目>/*.md`   | 每 session 常驻 (SessionStart hook 注入正文)         | 硬约束 / 命令式契约 (后续必再踩) |
| **recall** | `.skein/spec/recall/<类目>/*.md` | 按需语义召回 (planning 时 grep index → model 读全文) | 长尾、上下文密集经验             |

**两层 × 类目**: 层内按类目 (category) 分子目录 —— git / test / arch / build / style / domain / ops... 自由取名、按需建。索引三份: 每层 `<layer>/index.md` (层内全规则, 带 category 列) + 顶层 `index.md` (两层聚合概览)。core 常驻有软预算 (8000 字符, 超则告警降级, 契合「常驻只放最小硬规」)。

## recall (planning 阶段, main)

```
python3 <plugin>/scripts/memory.py recall "<任务关键词>"
```

- grep `recall/index.md` 输出命中行 → **model 读命中规则全文, 判是否真相关** → 相关的注入当前 task 上下文 (dispatch prompt「已知」段带上)。
- core 规则已由 SessionStart hook 常驻, 无需 recall。

## sediment (task finish 阶段, main) — 判定门 + 审批写盘

task finish 后走「判定门 checklist → 分层归类 → AskUserQuestion 审批 → memory.py sediment 写盘 + 自动 reindex」四步 (含升降级)。完整判定 trace 模板、分层/归类规则、写盘命令详见 [references/sediment-workflow.md](references/sediment-workflow.md)。

## 空仓冷启动播种 (一次性, main)

新仓 `.skein/spec` 为空时前几十轮 planning 无规则可召回。此时 main **可**提议从既有代码库提炼约定作冷启动基线 —— 派 skein-researcher 扫五维 (命名/错误处理/测试/架构边界/构建), 候选逐条判 core/recall/drop, 复用上文 sediment 审批门落盘。

一次性动作, `AskUserQuestion` 征同意再跑 (禁自动); 用户拒 → 走正常 planning, 规则随 finish sediment 增量积累。完整流程 (触发条件 / 五维明细 / 判层表 / 落盘) 见 [references/bootstrap-seeding.md](references/bootstrap-seeding.md)。

## 反例

| 禁                                | 改为                                    |
| --------------------------------- | --------------------------------------- |
| sediment 未输出判定 trace         | 逐项 /输出                              |
| 无增量硬凑沉淀                    | 全否跳过                                |
| 派 subagent 做审批 (它不能问用户) | main 亲做 AskUserQuestion               |
| 写盘不同步 index.md               | memory.py sediment 自动同步, 禁手改绕过 |
| 什么都塞 core 常驻                | 默认 recall, core 只留硬约束            |
