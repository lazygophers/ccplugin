# 子 PRD: C 方向 — hook 注入瘦身 (SubagentStart a+b 融合 + core 降级)

> skein-trellis-optimize-v2 子项。A (skill/agent 瘦身) + B (单一真值源+死代码) 已闭环。

## 基石罗盘 (用户已确认)
- **a+b 融合**: SubagentStart 读 stdin.agent_type → 类目过滤注 core 全文; 空映射/setup/dedup/memorier → 纯索引 fallback
- **c 分批**: 先降 Hook 链 + plugin.json 架构 2 条 core → recall (最小改动优先, core 11233 仍超预算但改善)
- **ST-2 不做**: hook 注入末尾已含 recall 提示, agent.md 兜底冗余

## 关键解锁 (深挖实证)
SubagentStart stdin 已含 `agent_type` (Claude Code 官方 Hooks schema)。a 方案无需改 dispatch/plugin.json/skein.py, 只改 memory.py:129 读 stdin 映射。
- Source: https://code.claude.com/docs/en/hooks (SubagentStart stdin = {session_id, agent_id, agent_type, ...})
- 现状 memory.py:129 subagent_start 完全没读 stdin

## 勘察结论 (全量: research/hook-injection-trim.md + research/combo-abc-landing.md)

### 注入现状 (病态)
- SubagentStart: head 53 + core 全文 4059 = 4118 tok → 硬截断 2005 (memory.py:139), 截断点落中间, 半失效
- SessionStart: core 索引 71 tok (已极简, 不动)
- UserPromptSubmit: 113 tok/prompt (dogfood 硬核, 不动)

### 新形态 (a+b 融合)
| 形态 | tok | 说明 |
|---|---|---|
| 现状截断 | 2005 | 半失效基线 |
| 命中类目 | ~1300 | head + 该类目 core 全文 + 全量索引 + recall 提示 |
| 空映射 fallback | 127 | head + 全量索引 + recall 提示 |
| **融合** | ~1450 | 命中注全文, 未命中索引, 均 < 2000 不截断 |

### agent → 类目映射 (6 注全文 + 3 索引)
| agent | 注入类目 | 形态 |
|---|---|---|
| skein-executor | script, arch, git | 全文 |
| skein-checker | script, arch | 全文 |
| skein-researcher | script, arch, skill | 全文 |
| skein-finisher | script, git | 全文 |
| skein-setup | (空) | 索引 |
| skein-dedup | (空) | 索引 |
| skein-memorier | (空) | 索引 |

### core 降级 (c, 分批先降 2 条)
| 标题 | 类目 | chars | 处置 |
|---|---|---|---|
| Hook 链设计 | hook | 2347 | **降 recall (本批)** |
| plugin.json 架构 | plugin-arch | 2660 | **降 recall (本批)** |
| Agent 定义规范 | agent | 1881 | 留 core (后续批) |
| PEP 563 注解陷阱 | arch | 1036 | 留 core (后续批) |
| spec 持久性陷阱 | arch | 875 | 留 core (后续批) |
| Command 定义 | command | 774 | 留 core (后续批) |
| Skill 组织 | skill | 1752 | 留 core (后续批) |
| skein agent 公共铁律 | agent | 1916 | 留 core |
| Git Worktree 隔离 | git | 1173 | 留 core |
| Python 脚本规约 | script | 1806 | 留 core |

降 2 条后 core: 实测 inject-core 输出 16897 chars (8 条, _strip_frontmatter 后; 勘察估 11233 偏低)。仍超 8000, 后续批再降 5 条 (Agent 定义/PEP563/spec 持久/Command/Skill) 可回预算。

## subtask 拆分 (3 个)

| sid | 目标 | 文件 | agent |
|---|---|---|---|
| c1 | memory.py:129 subagent_start 读 stdin.agent_type + AGENT_CATEGORIES 映射 + 类目过滤 + fallback 纯索引 | scripts/memory.py | skein-executor |
| c2 | sediment 降 Hook 链设计 core→recall (类目 hook) | .skein/spec/core/hook → recall/hook | skein-memorier (草案) + main sediment |
| c3 | sediment 降 plugin.json 架构 core→recall (类目 plugin-arch) | .skein/spec/core/plugin-arch → recall | skein-memorier (草案) + main sediment |

## 依赖
- c1 独立 (代码改)
- c2/c3 独立 (spec 沉淀, 与 c1 并行)
- c2/c3 完成后 c1 的类目过滤才会少注这 2 条 (但 c1 不依赖 c2/c3, 映射逻辑通用)

## 验收
- SubagentStart 不再截断 (注入 < 2000 tok 实测)
- 命中类目 agent 注该类目全文; 空映射 agent 注纯索引
- 非 skein agent / stdin 失败 → fallback 纯索引 (不崩)
- Hook 链 + plugin.json 架构 2 条 core 降 recall (主仓 .skein/spec/, 非 worktree)
- core 总量降到 ~11233 (改善, 非治本)
- memory.py 改后跑 test (test_skein.py preexisting task.html fail 不计入)
- 改后过质量门 (claude -p)

## 风险
- subagent 不 recall 则类目外规则丢 → 兜底: 命中类目全文已在上下文 + 全量索引常驻 + recall 提示
- stdin agent_type 字段名跨版本兼容 → 容错 None fallback 纯索引
- core 降级后 agent 引用路径变 → 降级用 sediment mv + reindex, 逻辑路径更新
- c2/c3 spec 持久性: 必沉主仓非 worktree (A 方向 learning [[skein-skill-agent-slim-02]])

## Backlog (本批不做)
- core 后续批降级 (Agent 定义/PEP563/spec 持久/Command/Skill 5 条) → core 回预算 8000
- test drift (task.html assert) — B 方向遗留
