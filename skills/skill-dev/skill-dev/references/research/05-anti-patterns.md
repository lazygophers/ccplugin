# 维度 5：反模式与失败案例

> 反例比正例更能约束 LLM。本维度是产物「反模式黑名单」的素材库。

## 来源清单

| # | 来源 | URL |
|---|------|-----|
| A | I Built 106 Claude Skills. 12 Dos and Don'ts | https://medium.com/@mohit15856/i-built-106-claude-skills-here-are-the-12-dos-and-donts-i-wish-id-known-earlier-8f4f13903f28 |
| B | Common Claude Skills Mistakes — Charlie O'Brien | https://www.linkedin.com/posts/charlie-obrien01_... |
| C | I Watched 100+ People Hit the Same Problems | https://natesnewsletter.substack.com/p/i-watched-100-people-hit-the-same |
| D | Claude Skills Explained Complete Guide | https://x.com/Meer_AIIT/article/ |
| E | SitePoint Claude Agent Skills Tutorial | https://www.sitepoint.com/claude-agent-skills-tutorial/ |
| F | Anthropic best-practices anti-patterns 节 | 见 01 号 |
| G | darwin-skill dim9 反例黑名单 | ~/.claude/skills/darwin-skill/SKILL.md |

## 反模式汇总（按频次排序）

### P0 — 致命（skill 失效）

| # | 反模式 | 来源 | 后果 | 正例 |
|---|--------|------|------|------|
| 1 | **vague description** | A B C D F | Claude 不触发或误触发 | 第三人称 + key terms + 做什么+何时用 |
| 2 | **frontmatter YAML 语法错误**（缩进/引号/特殊字符） | 官方讨论 #244 | skill 静默不被检测 | `--debug` 查 parse 错误 |
| 3 | **description 被截断丢关键词** | 官方 + C | skill 在长列表中失发现 | key use case 前置；用 skillOverrides name-only 释放预算 |
| 4 | **路径错误 / skill 孤立** | 官方 troubleshooting | 静默失败 | 验证目录结构 + What skills are available? |

### P1 — 严重（效果劣化）

| # | 反模式 | 来源 | 后果 | 正例 |
|---|--------|------|------|------|
| 5 | **解释 Claude 已知的事**（浪费 token） | D F | context 污染 | 只加 Claude 不知道的 |
| 6 | **SKILL.md 过长**（>500 行） | F | 加载后持续占 context | 拆 reference/ |
| 7 | **给太多选项** | F | Claude 困惑选不对 | 给 default + escape hatch |
| 8 | **嵌套引用过深**（a→b→c） | F | head -100 预读信息不全 | 只深一层 |
| 9 | **没有 eval 就发布** | F A | 解决臆想问题 | 先建 ≥3 场景 eval |
| 10 | **Windows 路径反斜杠** | F | 跨平台报错 | 统一正斜杠 |

### P2 — 中等（质量损耗）

| # | 反模式 | 来源 | 后果 | 正例 |
|---|--------|------|------|------|
| 11 | **术语混用**（field/box/element） | F | Claude 理解漂移 | 选定一个贯穿 |
| 12 | **时间敏感信息**（「2025年8月前用旧 API」） | F | 过期变错 | 放 old patterns `<details>` |
| 13 | **脚本 punt 错误给 Claude** | F | 不可靠崩溃 | 显式 try/except + 默认值 |
| 14 | **voodoo constants**（TIMEOUT=47） | F | 不可维护 | 注释为何这个值 |
| 15 | **假设包已安装** | F | 运行时崩溃 | 显式 `pip install` |

### P3 — 结构性（darwin-skill dim9 黑名单）

| # | 反模式 | 来源 | 后果 |
|---|--------|------|------|
| 16 | **只写正例不写反例** | A G | LLM 撞常见坑 | 反例黑名单成章 |
| 17 | **「必须」措辞代替视觉标记** | G HL-1 | LLM 不扫语义只扫标记 | 🔴 CHECKPOINT / 🛑 STOP |
| 18 | **两列 fallback 表（症状/解法）** | G HL-2 | 失败路径不完整 | 三段式（触发/一线/兜底） |
| 19 | **过度优化硬凑 MAX_ROUNDS** | G HL-4 | over-engineering | Δ<2 连续 2 轮即 break |
| 20 | **runtime 钉死单一平台** | G | 不可迁移 | 中立 badge + 中立措辞 |

## Charlie O'Brien「我犯过所有错」要点（B）

LinkedIn 帖核心：description 是 skill 选择的唯一入口——「Helps with marketing」会在错误时机触发。必须具体到「做什么 + 何时用」。

## 106 skills 作者教训（A）

核心：**anti-patterns are valuable because they catch failure modes that prescriptive instructions miss**。「Do this」告诉 Claude 好的样子，但「Don't do that」才能抓住指令遗漏的失败模式。

## 产物框架应用点

本维度直接成为产物 SKILL.md 的「反模式黑名单」section（dim9 反向约束），与正例流程对照。产物自身编写时也须逐项自检（尤其 P0 的 1-4 项）。
