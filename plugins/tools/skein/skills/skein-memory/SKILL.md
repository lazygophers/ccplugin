---
name: skein-memory
description: 两层规则记忆 (基于 .claude/rules)。planning 时召回相关规则、task finish 后沉淀学习时使用 — core 常驻硬规 + recall 按需召回, 经 sediment 判定门 (checklist) + AskUserQuestion 审批写盘。SKEIN 差异化核心。
---

# skein-memory — 两层规则记忆

**差异化核心**。不同于「按需沉淀单一 spec 文件」, SKEIN 记忆分两层, 基于 `.claude/rules`:

| 层 | 路径 | 加载 | 适合 |
|---|---|---|---|
| **core** | `.claude/rules/core/<类目>/*.md` | 每 session 常驻 (SessionStart hook 注入正文) | 硬约束 / 命令式契约 (后续必再踩) |
| **recall** | `.claude/rules/recall/<类目>/*.md` | 按需语义召回 (planning 时 grep index → model 读全文) | 长尾、上下文密集经验 |

**两层 × 类目**: 层内按类目 (category) 分子目录 —— git / test / arch / build / style / domain / ops... 自由取名、按需建。索引三份: 每层 `<layer>/index.md` (层内全规则, 带 category 列) + 顶层 `index.md` (两层聚合概览)。core 常驻有软预算 (8000 字符, 超则告警降级, 契合「常驻只放最小硬规」)。

## recall (planning 阶段, main)

```
python3 <plugin>/scripts/memory.py recall "<任务关键词>"
```

- grep `recall/index.md` 输出命中行 → **model 读命中规则全文, 判是否真相关** → 相关的注入当前 task 上下文 (dispatch prompt「已知」段带上)。
- core 规则已由 SessionStart hook 常驻, 无需 recall。

## sediment (task finish 阶段, main) — 判定门 + 审批写盘

### 1. 判定门 checklist (逐项 ✅/❌ 输出 trace, 全否也输出)

```
sediment 判定 trace
═══════════════════
正向 (任一 ✅ 触发):
  ① 新命令式契约 (MUST/禁, 后续同类任务会再踩): ✅/❌ (具体: ..)
  ② 踩坑 ≥2 轮 (根因可写可验证契约, 非一次性 bug): ✅/❌ (具体: ..)
  ③ 反复 ≥2 task (grep 可验): ✅/❌ (具体: ..)
  ④ 跨任务可复用决策 (选型/架构边界/API 约定): ✅/❌ (具体: ..)
  ⑤ 验收基准 (可复用断言): ✅/❌ (具体: ..)
排除 (仅当对应正向也 ✅ 时判):
  一次性 bug / 本 task 私有细节 / 已有规则覆盖: ✅/❌
判定: <触发 → 沉淀 | 全否 → 跳过>
```

- 判定归 model (语义判断, 脚本做不了)。全无增量则跳过, 禁硬凑。
- **未输出 trace = 流程错误**。

### 2. 分层 + 归类 (触发后)

- **层**: 硬约束 / 命令式契约 / 后续必再踩 → **core** (常驻); 长尾 / 上下文密集 / 偶尔相关 → **recall** (按需); 拿不准 → 默认 recall (不轻易增 core 常驻负担)。
- **类目**: 归到 git / test / arch / build / style / domain / ops 之一 (无合适则新取名或 `misc`)。类目决定沉淀落哪个子目录 + 索引归类。

### 3. 审批门 (main 亲做, 禁 subagent / 禁纯文本)

沉淀提案 (层 + 标题 + 正文 + 关键词) → `AskUserQuestion` 交用户批。**未过审批禁写盘**。

### 4. 写盘

```
python3 <plugin>/scripts/memory.py sediment --layer core|recall --category git \
  --title "契约标题" --keywords "worktree,merge" --source <task-id> --body-file <正文.md>
```

自动写规则文件到 `<layer>/<category>/<source>-<seq>.md` (带 frontmatter: title/layer/category/keywords/source/authored-by/created) + **自动 reindex** (重建两层 index + 顶层 index, 否则新规则漏检)。

## 升降级 (可选, 按需再加)

core↔recall 频率驱动升降级暂不实现 (YAGNI)。手动: 移动文件到目标层/类目子目录 + `python3 <plugin>/scripts/memory.py reindex` 重建索引。

## ⛔ 反例

| 禁 | 改为 |
|---|---|
| sediment 未输出判定 trace | 逐项 ✅/❌ 输出 |
| 无增量硬凑沉淀 | 全否跳过 |
| 派 subagent 做审批 (它不能问用户) | main 亲做 AskUserQuestion |
| 写盘不同步 index.md | memory.py sediment 自动同步, 禁手改绕过 |
| 什么都塞 core 常驻 | 默认 recall, core 只留硬约束 |
