# Matt Pocock `/ask-matt` → skein 原生机制映射

本文件是 Matt Pocock `/ask-matt` 场景路由器与 skein 原生机制的对照映射, 供熟悉 ask-matt 的用户快速定位 skein 对应能力。

**skein 零外部 skill 硬依赖**: 下表「外部引用 (可选)」列出现的 skills (grill-with-docs / wayfinder / triage 等) 仅作为可选增强引用。**未安装则跳过, skein 用自身原生机制完整覆盖同一场景**, 不因缺任一外部 skill 而失效。

ask-matt 的「路由」理念 skein 已内建: skein-flow (强制走 task) + skein-plan (research 判定门 / brainstorm / grill) + skein-exec / skein-check / skein-finish 四步闭环 (plan → exec → check → finish) 自包含。

---

## 主流程 (idea → ship)

| ask-matt skill | 职责 (ask-matt 原义) | skein 原生对应 | 外部引用 (可选) |
|---|---|---|---|
| `/grill-with-docs` | interview 撑锐 idea, stateful 存 CONTEXT.md / ADR | skein-plan brainstorm + grill 硬门 (prd.md / design.md 持久化) | grill-with-docs (未装跳过, skein-plan grill 替代) |
| `/to-spec` | 把 thread 转 spec | skein-plan 产出 prd.md + design.md (即 spec) | — |
| `/to-tickets` | 拆 tracer-bullet tickets (各声明 blocking edges) | skein-plan `subtask add --deps` (subtask DAG + depends_on) | — |
| `/implement` | 驱动 tdd 建每个 issue, 末跑 code-review, 提交 | skein-exec (claim → 派 Agent → done 循环) + skein-check | — |
| `/tdd` | red-green 一片片建行为 | skein-exec subtask 内部 TDD 实践 (skein 不强制 TDD, 由 subtask 验收标准约束) | — |
| `/code-review` | 两轴评审 (Standards + Spec) diff | skein-check (lint / type / test / 契约 + 一致性核查) | — |

## On-ramps

| ask-matt skill | 职责 (ask-matt 原义) | skein 原生对应 | 外部引用 (可选) |
|---|---|---|---|
| `/triage` | 把涌入 issue 过 triage 角色产 agent-ready issue | skein-plan「登记前查未完成 task」(查重归并) + skein-dedup (异步查重织 DAG) | — |
| `/diagnosing-bugs` | 难 bug, 先 tight feedback loop 再修 + 回归测试 | skein-exec subtask 失败自愈闭环 (定点修 / 加修复 subtask) + skein-check | — |
| `/wayfinder` | 巨大模糊努力, decision-ticket 地图推雾 | skein-plan research 判定门 (保守灰区自动派 researcher) + 复杂度天花板 (拆多 task) + supertask | wayfinder (未装跳过, research 判定门替代) |

## 代码健康

| ask-matt skill | 职责 (ask-matt 原义) | skein 原生对应 | 外部引用 (可选) |
|---|---|---|---|
| `/improve-codebase-architecture` | 闲时保代码库 agent-friendly, surface deepening 机会 | skein 独立 task (`skein create --kind` 改进类), 走标准 plan → exec → check → finish | — |

## Vocabulary (模型调用的词表参考)

| ask-matt skill | 职责 (ask-matt 原义) | skein 原生对应 | 外部引用 (可选) |
|---|---|---|---|
| `/domain-modeling` | 撑锐项目 domain 语言, 解 overloaded 词, ADR 记难逆决策 | skein-plan brainstorm (词汇澄清) + design.md「当前方案」+ sediment spec (难逆决策落 core spec) | — |
| `/codebase-design` | deep-module 词表 (module / interface / depth / seam) 设计模块形状 | skein-plan design.md (架构 / 取舍 / 技术选型 / 可能性分支) | — |

## 会话穿越

| ask-matt skill | 职责 (ask-matt 原义) | skein 原生对应 | 外部引用 (可选) |
|---|---|---|---|
| `/handoff` | 压缩对话成 md 文件, 新 session 引用承上下文 (fork) | **已由 skein task.json + prd/design/findings 工件 + sediment spec 完整替代, 不单列** (skein 有 task 持久层, 无需 handoff) | — |
| `/compact` (内置) | 同 session 总结 | 同 skein (用 harness 内置 compact, skein 无需自造) | — |

## Standalone

| ask-matt skill | 职责 (ask-matt 原义) | skein 原生对应 | 外部引用 (可选) |
|---|---|---|---|
| `/grill-me` | 无 codebase 的 stateless interview | skein-plan brainstorm (无 codebase 时仍跑, prd / design 落 `.skein/` 即可) | — |
| `/prototype` | throwaway 程序答一个设计问题 | skein-researcher (只读勘察) 或独立 sandbox task (不落主仓库) | — |
| `/research` | 后台 agent 调查 primary sources 留 cited md | skein-researcher (planning 阶段调研, 结论落 `research/` + findings.md 收敛) | — |
| `/teach` | 多 session 学概念, 当前目录作 stateful workspace | skein 不覆盖 (非工程任务, 超范围) | — |
| `/writing-great-skills` | 写 / edit skill 参考 | 本仓库 `skills/skill-dev/` (skein 同仓的 skill 开发方法论) | — |

## 前置

| ask-matt skill | 职责 (ask-matt 原义) | skein 原生对应 | 外部引用 (可选) |
|---|---|---|---|
| `/setup-matt-pocock-skills` | 配 issue tracker / triage labels / doc layout | `skein init` (配 `.skein/config.yaml`, skein 自有工件布局) | — |

---

映射关系是理念对照非功能依赖 — skein 四步闭环 (plan → exec → check → finish) 自包含, 上表外部 skill 列仅为熟悉 ask-matt 者的导航, 装了可选增强, 没装 skein 照跑。
