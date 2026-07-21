# 子 PRD: B 方向 — 单一真值源 + 死代码清理

> skein-trellis-optimize-v2 子项。A 方向 (skill/agent 瘦身) 已闭环 (merge 2c7ddf5d)。

## 基石罗盘 (用户已确认)
- **dedup**: 注册保留查重 — 贴合 skein "durable 登记 + 不堆重复 task" 不变量
- **真值源**: 机械统一 — general-purpose→skein-executor + agent 数量口径修正 + glossary executor 工具面同步

## 勘察结论 (researcher 全量: research/svof-deadcode-survey.md)

### 真值源硬冲突 3 条
1. **兜底 agent**: README.md:18,24 + plugin.json description 残留 `general-purpose`, 其余全已改 `skein-executor`
2. **具名 agent 数**: README.md:24 + docs/reference.md:91 + plugin.json description 说 "5 个", 实注册 6 (漏算 executor)
3. **Recursion Guard 表述**: docs/glossary.md:62 + docs/reference.md:93 说 "executor 有 Agent/Task 靠 prompt 兜", 实际 executor frontmatter 已剔 Agent/Task

### 死代码 4 条
1. **skein-dedup 孤儿** (关键): agents/skein-dedup.md 存在, plugin.json 未注册, 但 skein-plan SKILL.md:63,82 引用它 → **注册** (罗盘已定保留)
2. **sample-skein 8 示例**: docs/examples/sample-skein/task/*/task.json + task.md ~20 处 general-purpose → executor
3. **README + plugin.json**: general-purpose 残留 (同冲突1)
4. **test_skein.py fixture**: 8 处 `--agent general-purpose` (推测仅 fixture 字符串, 弱, 非必须)

## subtask 拆分 (5 个)

| sid | 目标 | 文件 | agent |
|---|---|---|---|
| b1 | 注册 skein-dedup 进 plugin.json agents[] + 验证 plan SKILL 引用可加载 | plugin.json, (验证 skein-plan SKILL) | skein-executor |
| b2 | general-purpose→skein-executor 全局机械替换 (README/plugin.json/8 示例) | README.md, plugin.json, docs/examples/sample-skein/** | skein-executor |
| b3 | agent 数量口径 "5个"→"5 受限具名 + 1 执行器" (README/docs/plugin.json) | README.md, docs/reference.md, plugin.json | skein-executor |
| b4 | glossary/reference Recursion Guard 表述同步 (executor 已剔 Agent/Task) | docs/glossary.md, docs/reference.md | skein-executor |
| b5 | test_skein.py fixture general-purpose→executor (弱, 验证无 assert 断裂) | scripts/test_skein.py | skein-executor |

## 依赖
- b1 独立 (dedup 注册)
- b2/b3/b4 都改 README/docs/plugin.json, **共享文件 → 串行** (b2→b3→b4 或合并到 1 agent 批改)
- b5 独立 (test 文件)

## 验收
- plugin.json agents[] 含 dedup, skein-plan SKILL 引用可解析
- grep `general-purpose` 在 agents/skills/README/docs/plugin.json 零命中 (示例 + test 除外)
- agent 数量口径全仓一致
- glossary/reference executor 工具面表述与 frontmatter 一致
- 改后过质量门 (claude -p)

## 风险
- b2/b3/b4 共享 README/docs/plugin.json, 并发改冲突 → 串行或单 agent 批改
- b5 test fixture 改动需验证无 assert 匹配断裂

## 进度
- [x] b5 DONE — 8 处 fixture 改完, agent 名 assert 无断裂
- [ ] b3 🔄 执行中
- [ ] b1/b2/b4 ⏳ 待派

## Backlog (b5 发现, 非本 B 范围)
- **test drift**: test_skein.py:220-241 断言 `.skein/task.html` 落盘, 但 skein.py board 只写 task.md (html 落盘链路已移除)。baseline 同样 fail, preexisting。另起 subtask: 删 assert 段 or 补 html 落盘。
