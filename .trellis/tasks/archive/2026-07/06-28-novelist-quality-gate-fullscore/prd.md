# PRD — novelist 检测门控满分 + 维度细分 + 检测修复合并入参模式

## 背景

novelist 插件的文字校对 (novelist-proofread) 与一致性审查 (novelist-check) 现行门控阈值 `>95`，未达满分；维度粒度偏粗（proofread 5 维 / check 6 维）；check 只读、修复跨 skill 交给 rewrite，不满足「检测/修复同 skill 入参决定」诉求。

## 用户诉求（逐字）

1. 「对于错别字的相关检测以及上下文关联的相关检测，必须保证是满分的才可以通过。」
2. 「对于检测和修复进行更细致的划分，在同一个 scale 里面同时支持某一项的检测以及某一项的修复。」
3. 「对于 skills 的检测和修复需要更细致的划分。而需要更更加细分的维度。」
4. 「对于修复、检测应该是在同一个 skills 进行，通过入参决定是检测还是修复。」

## 用户确认的方案决策（AskUserQuestion 4 问）

| Q | 决策 |
|---|---|
| check 与 rewrite 是否合并 | **不合并**：check + rewrite 各自加 `mode=detect\|fix` 入参，架构不并 |
| 维度细分粒度 | **细粒度**：proofread 5→12 子项；check 6→18 子项 |
| 满分门控 | **零容忍 ==100**：🟢建议级冲突也阻断满分 |
| 执行方式 | **Trellis 全流程**（prd + design + implement） |

## 目标

- O1 门控满分：proofread 质量分 / check 健康分 / rewrite 定稿分 / pipeline PASS_* 阈值统一 `==100`（零错误 / 零冲突含 🟢）。
- O2 维度细分：proofread 5 维 → 12 子项；check 6 维 → 18 子项；每子项独立 detect + fix + 计数。
- O3 检测/修复同 skill 入参决定：novelist-proofread / novelist-check / novelist-rewrite 三 skill 统一支持 `mode=detect|fix` 入参。
- O4 scale 内检测+修复：每个子项 scale 既能报告问题（detect）也能就地修复（fix）。

## 范围

### 改动文件（11 个）

| 文件 | 改动 |
|---|---|
| `skills/novelist-proofread/SKILL.md` | 维度 5→12；加 mode=detect\|fix；门控 ==100 |
| `skills/novelist-proofread/references/proofread-checklist.md` | 5 维清单 → 12 子项清单 |
| `skills/novelist-check/SKILL.md` | 维度 6→18；加 mode=detect\|fix；门控 ==100 |
| `skills/novelist-check/references/conflict-rubric.md` | 6 维清单 → 18 子项；🟢 也阻断说明 |
| `skills/novelist-rewrite/SKILL.md` | 加 mode=detect\|fix；定稿分棘轮 ==100 |
| `skills/novelist-rewrite/references/rewrite-modes.md` | mode 入参与三模式关系 |
| `agents/proofreader.md` | 维度 12 子项 + detect 只读 / fix 就地改 |
| `agents/continuity-auditor.md` | 审查模式拆 detect / fix 两态（fix 派 chapter-writer） |
| `agents/chapter-writer.md` | 注明被 check fix / rewrite fix 共用 |
| `skills/novelist-pipeline/workflow.js` | PASS_* 95→100；checker/fixer 调用对齐满分；子项计数 |
| `skills/novelist-pipeline/SKILL.md` | 门控说明同步 ==100 |

### 不改

- novelist-write / novelist-humanize / 其他 skills（不在用户诉求范围）。
- 三 skill 核心职责（proofread=文字层 / check=一致性 / rewrite=重写）不变。
- chapter-writer agent 主体（仅注明被多方调用）。

## 验收标准

AC1. novelist-proofread SKILL.md 含 12 子项表 + `mode=detect|fix` 入参 + 门控 `质量分 == 100`（零错误）。
AC2. novelist-check SKILL.md 含 18 子项表 + `mode=detect|fix` 入参 + 门控 `健康分 == 100`（零冲突含 🟢）。
AC3. novelist-rewrite SKILL.md 含 `mode=detect|fix` 入参 + 定稿分棘轮 `==100`。
AC4. proofread-checklist.md / conflict-rubric.md 子项清单与 SKILL.md 一致（12 / 18）。
AC5. proofreader / continuity-auditor agent 描述与 SKILL 的 mode + 子项一致。
AC6. workflow.js `PASS_TOTAL / PASS_CONSISTENCY / PASS_HUMANNESS` = 100；computeScores 满分逻辑对齐。
AC7. 项目 CLAUDE.md 质检命令对三个 SKILL.md 跑通（AI 能正确识别 mode 入参与满分门控）。
AC8. description < 512 字符；when_to_use < 128 字符（项目底线）。
AC9. 改动自动 git add 进暂存区（项目 CLAUDE.md 规则）。

## 风险

- R1 满分零容忍致 pipeline 反复 fix 死循环：workflow.js `MAX_FIX_ATTEMPTS=Infinity` 已是用户既定，保留；但在 SKILL 加「连续 N 次未满分 → STOP 转人工」兜底。
- R2 check mode=fix 与 rewrite 模式 A 职责重叠：design.md 明确边界（check fix = 单点小修不改结构 / rewrite 模式 A = 跨章定点重写派 chapter-writer）。
- R3 18 子项清单膨胀 conflict-rubric.md：用表格压缩，每子项一行（维度 / 子项 / 缺陷例）。

## 依赖

- 无外部依赖。纯文档 + workflow.js 常量/逻辑改动。

## 退出条件

全部 AC 满足 + 质检命令通过 + 自检行输出。
