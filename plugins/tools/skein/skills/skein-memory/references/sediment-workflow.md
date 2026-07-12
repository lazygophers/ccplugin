# sediment 沉淀流程 (task finish 阶段, main) — 判定门 + 审批写盘

## 1. 判定门 (任一正向触发即沉淀)

正向 (任一命中):
- ① 新命令式契约 (MUST/禁, 后续同类任务会再踩)
- ② 踩坑 ≥2 轮 (根因可写可验证契约, 非一次性 bug)
- ③ 反复 ≥2 task (grep 可验)
- ④ 跨任务可复用决策 (选型/架构边界/API 约定)
- ⑤ 验收基准 (可复用断言)

排除 (命中则不沉淀): 一次性 bug / 本 task 私有细节 / 已有规则覆盖。

- 判定归 model (语义判断, 脚本做不了)。全无增量则跳过, 禁硬凑。
- 结论一句话交代: 触发哪项 → 沉淀 / 全否 → 跳过。

## 2. 分层 + 归类 (触发后)

- **层**: 硬约束 / 命令式契约 / 后续必再踩 → **core** (常驻); 长尾 / 上下文密集 / 偶尔相关 → **recall** (按需); 拿不准 → 默认 recall (不轻易增 core 常驻负担)。
- **类目**: 归到 git / test / arch / build / style / domain / ops 之一 (无合适则新取名或 `misc`)。类目决定沉淀落哪个子目录 + 索引归类。

## 3. 审批门 (main 亲做, 禁 subagent / 禁纯文本)

沉淀提案 (层 + 标题 + 正文 + 关键词) → `AskUserQuestion` 交用户批。**停手: 未过审批禁写盘**。

## 4. 写盘

```
python3 <plugin>/scripts/memory.py sediment --layer core|recall --category git \
  --title "契约标题" --keywords "worktree,merge" --source <task-id> --body-file <正文.md>
```

自动写规则文件到 `<layer>/<category>/<source>-<seq>.md` (带 frontmatter: title/layer/category/keywords/source/authored-by/created) + **自动 reindex** (重建两层 index + 顶层 index, 否则新规则漏检)。

## 升降级 (可选, 按需再加)

core↔recall 频率驱动升降级暂不实现 (YAGNI)。手动: 移动文件到目标层/类目子目录 + `python3 <plugin>/scripts/memory.py reindex` 重建索引。
