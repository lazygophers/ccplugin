# 子 PRD: D 方向 — memory→spec 概念演进 (rename + 知识库化 + 启程维护)

> skein-trellis-optimize-v2 子项。A/B/C 已闭环。D 方向把 memory 定位从「经验记录」演进为「项目知识库 spec」(规范+约定+经验+ADR+域知识合集)。

## 基石罗盘 (用户已确认)
- **概念演进**: rename 是表象, 真目的是 memory→spec 定位升级 (spec=项目记忆/规范/约定/知识库合集)
- **全义 rename**: 对外命令 + 内部文件名/类名/目录名/agent 名全改 (非窄义)
- **软模板骨架**: body 参照模板填 (core spine/recall spine 两套), 不强校验, 不破 fire-and-forget
- **maintain 手动+提示**: 手动跑 maintain + session-start 检测 stale 信号时附提示行
- **vault 不互通**: spec 仅仓内 wikilink, 不与 Obsidian 同步

## 勘察结论 (researcher 全量: research/d-spec-knowledge-design.md)

### 现状短板
- sediment body 透传无骨架 (memory.py:208), 事实标准段 (适用28/反例22/触发场景15/案例13/关联10) 无强制, 各自为政
- frontmatter 7 字段硬编码, 无 status/related/updated (updated 已有1条手填需求)
- core 偏规约/契约 (命令式+反例表), recall 偏 ADR/陷阱 (触发场景→正解→案例) — 两层文体不同
- 无 maintain/启程维护命令; 无 stale 检测
- [[wikilink]] 自发用(10条)但 reindex 不解析, 断链无检测

### 外部框架借鉴 (带 URL, 见报告 B 节)
- BMAD "Essential Spine + Adapt-In Menu": core=spine(invariant) / recall=structural(case) 分层
- ADR Context-Decision-Consequence + Status 生命周期字段
- zettelkasten 双链 + related frontmatter
- spec-kit [NEEDS CLARIFICATION] 强制标记 (skein 已有 `需要:` 协议同频)

## 设计方案

### frontmatter 增字段 (memory.py:209-219, 7→10 字段)
```
status: active        # 新: active | deprecated | superseded (sediment 默认 active)
related: [<slug>]     # 新: 关联规则 stem 列表 (空则 [])
updated: <ts>         # 新: 最后修订 (sediment 写时=created; maintain/手改刷新)
```
旧 spec 缺字段不报错 (frontmatter 解析容错 + spec-meta hook SPEC_REQUIRED 只查 title/layer/created/keywords 不含新字段)。

### core spine 模板 (references/templates/core.md.tmpl)
```
# <标题>

## 铁律 / 契约
<命令式: MUST X / 禁 Y. 一句一规则>

## 反例 (命中=违规)
| 禁 | 改为 |
|---|---|

## (可选) 关联
[[<wikilink>]]
```

### recall spine 模板 (references/templates/recall.md.tmpl)
```
# <标题>

## 触发场景
## 陷阱 / 正解
## 反例
## 案例
## 适用
## 关联
```

模板是参考文件, memorier 写盘前参照填 body, memory.py 不强校验 body 结构。

### maintain 命令 (memory.py 新增)
```
skein-spec maintain                    # 全量体检 (stale + broken-link + 超预算 + keywords重复)
skein-spec maintain --layer recall     # 仅 recall
```
输出报告 (人读, 非自动执行):
```
[超预算] core 8200 > 8000 — 考虑降级: script/conventions-00
[stale] recall/arch/legacy-00 (created 1750, 14月前, status active)
[断链] [[nonexistent]] ✗ 目标缺失
[重复 keywords] "worktree,merge" ×3: git/worktree-00, ops/x, arch/y
```
stale 判据: created>180天且无updated | status=deprecated/superseded | broken wikilink | keywords组≥3条。recall 命中埋点 YAGNI 后置。

### session-start 提示 (复用 session_start() 末尾, ≤1行)
触发: core > CORE_BUDGET(8000) | 最老规则 >180天。输出 `⚠️ 跑 skein-spec maintain 体检`。

### 全义 rename (memory→spec)
| 对象 | 旧 | 新 |
|---|---|---|
| bin 入口 | bin/skein-memory | bin/skein-spec |
| 脚本 | scripts/memory.py | scripts/spec.py |
| 类名 | class Memory | class Spec |
| skill 目录 | skills/skein-memory/ | skills/skein-spec/ |
| skill name (frontmatter) | skein-memory | skein-spec |
| agent | skein-memorier | skein-specer |
| prog (memory.py:348) | memory.py | spec.py |
| authored-by frontmatter | skein-memory | skein-spec (新写盘; 旧 spec 保留历史值) |

**hooks command 同步 (🔴 最高风险)**: plugin.json SessionStart(:80) + SubagentStart(:112) `bin/skein-memory`→`bin/skein-spec`, 改错 → core 注入静默失效。
**hooks.py ENGINE 正则同步 (:24,29,31,33)**: memory.py→spec.py, skein-memory→skein-spec (guard 命令识别)。

## subtask 拆分 (4 个)

| sid | 目标 | 文件 | agent | 依赖 |
|---|---|---|---|---|
| d1 | 全义 rename: bin/scripts(spec.py)/class Spec/skill 目录+name/agent skein-specer/plugin.json hooks command(2处)+ENGINE 正则/skein.py:2538 路径/test_memory→test_spec+导入/docs+README+agents 命令引用全量 sed + doctor/质量门验证 | ~25-30 文件 | skein-executor | 无 (必先做, 免后续引用混) |
| d2 | frontmatter 增 status/related/updated (spec.py sediment 写盘段 +3 行; reindex 可选加 status 列); 旧 spec 不迁移 (默认 active) | spec.py | skein-executor | d1 |
| d3 | 软模板骨架: references/templates/{core,recall}.md.tmpl + SKILL.md + skein-specer.md 加"参照模板填 body"段 | skills/skein-spec/ + agents/skein-specer.md | skein-executor | d2 |
| d4 | maintain 命令: spec.py 新增 maintain 方法+子命令+4判据+报告格式 + session-start 提示行 + SKILL.md 文档 | spec.py + SKILL.md | skein-executor | d2 (可与 d3 并行) |

**依赖图**: d1 → d2 → (d3, d4 并行)

## 验收
- grep `skein-memory`/`memory.py`/`class Memory`/`skein-memorier` 在 scripts/bin/skills/agents/plugin.json/docs 零命中 (旧 spec frontmatter authored-by 历史值除外)
- `skein-spec session-start` + `skein-spec subagent-start` 注入正常 (hooks command 路径生效, core 注入不失效)
- `skein-spec sediment` 写盘含 status/related/updated 三字段
- templates/{core,recall}.md.tmpl 存在, SKILL/specer.md 引用模板
- `skein-spec maintain` 跑通, 输出体检报告 (stale/broken-link/超预算/keywords重复)
- session-start core 超预算时附 maintain 提示行
- 改后过质量门 (claude -p) + test_spec 全过
- hooks.py ENGINE 正则识别新命令名 (guard 不误判)

## 风险
- 🔴 hooks command 路径改错 → core 注入静默失效 (无报错)。验证: rename 后 doctor + 质量门 + 实测注入
- 🟠 class Memory→Spec 全引用同步 (self./import/test)。降险: d1 单 subtask 集中改, 改完跑 test_spec
- 🟠 hooks.py ENGINE 正则漏改 → guard 不识别新命令名 (skein-spec 被当非本插件放行/拦截错)。d1 必须含 hooks.py:24,29,31,33
- 🟡 skill 目录名改需同步 plugin.json:35 + agent skills: 引用。grep 全量核对
- 🟡 maintain stale 判据阈值 (180天) 主观, 可调

## Backlog (本批不做)
- recall 命中埋点 (.skein/.hits) → maintain stale 判据增强 (YAGNI 后置)
- 旧 spec 批量补 status/related/updated (默认 active, 按需手补)
- body 模板 hooks 强校验 (候选2, 与两层文体冲突, 不做)
