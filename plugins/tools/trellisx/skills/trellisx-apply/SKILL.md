---
name: trellisx-apply
description: 把 强推task + subtask拆分 + worktree隔离 + 闭环收尾 四维度增量注入当前项目 .trellis/ (workflow.md 的 no_task/planning/in_progress 块 + spec 背书文档 + trellis 生命周期 hook worktree 自动化)。强推 task 与闭环为纯 prompt 软约束 (非平台 hook 硬拦截)。**纯增量追加, 绝不替换 trellis 原生文本** (no_task 分类+征同意/check/finish/前缀全保留)。幂等 (marker 包裹)。
when_to_use: 用户主动在某 trellis 项目内运行, 把该项目的 .trellis 改造成符合 trellisx 规范。短语 "trellisx apply" "应用 trellisx" "改造 .trellis" "内化 trellisx 规则" "/trellisx-apply"。
argument-hint: [scope]
arguments: [范围]
---

# trellisx-apply — 把 trellisx 规则内化进 .trellis

把 **强推 task + subtask 拆分 + worktree 隔离 + 闭环收尾 + task.md 看板** 五维增量注入 `.trellis/`。跑完后由 trellis 原生 `inject-workflow-state` hook 每轮注入。

**两条铁律 (贯穿全程)**:
- 🔒 **纯增量追加, 绝不替换原生**: no_task 原生分类+征同意 / Phase 流程 / check / finish / 完成判定 / 回复前缀 —— **一字不改**, trellisx 内容只在块末尾追加 (`apply-verify` 强制断言原生正文非空)。详见下方「教训」。
- 🪶 **软约束路线**: 强推 task 与闭环都是注入 workflow.md 的**强措辞 prompt** (AI 仍有裁量), 非平台 enforcement hook (PreToolUse 拦截 / Stop 阻断)。有意取舍: 避免硬拦截打扰。需硬性强制 (写码必过 task / 不闭环不让停) → 使用者另加平台 hook, apply 不做。

> 强推 task = "除极简任务外一律走 task; 不确定主动问用户" (注入 no_task 块)。
> 闭环收尾 = "plan→exec→check→**finish** 必走完整, 不停在 in_progress" (注入 in_progress 块)。

## 立场

| 立场 | 说明 |
| --- | --- |
| 内化优于外挂 | 规则写进 `.trellis/`, 由 trellis 自身机制生效; 不靠 trellisx 持续 hook |
| 增量增强, 不重构 | apply 只**增量增强** (marker 注入 + 加新文件 + 加新 hook); **绝不重写**用户原有 workflow / spec / 文档。spec 的破坏式重构是 `trellisx-spec` 的职责 |
| 尊重 trellis 原生 | 融合而非取代: 引用 trellis 已有 (task.py / add-subtask / jsonl / trellis-check), 仅补 trellis 缺的 (worktree / subtask 文件编排) |
| 显式审批 | 改 `.trellis/` 前展示 diff plan, 经 AskUserQuestion 批准才写盘 |
| 清理无效内容 | 移除对当前平台无价值的冗余: ① 模板内部维护者注释 (`<!-- ... -->`); ② 跨平台枚举 (`[Claude Code, Cursor, OpenCode, Kiro, ...]`) 收敛为 Claude Code。**保留** trellisx marker + workflow-state 标签 |
| i18n: 全文档跟随设备语言 | 完成后**整个 workflow.md + 新增 spec 叙述**与设备语言一致 (不只注入部分)。原生英文+设备中文 → 翻译全文叙述。**保留不译**: `[workflow-state:X]` 标签 / marker key / task.py 命令 / 路径 / 代码块 / 变量名。语言转换是 i18n, 不算语义重构 |

## 前置检查

```bash
ls .trellis/ || { echo "非 trellis 项目, 终止"; exit 1; }
ls .trellis/workflow.md          # 注入目标
ls .trellis/spec/ 2>/dev/null    # spec 目标
ls .trellis/config.yaml          # trellis 生命周期 hook 注入目标
ls .claude/agents/trellis*.md 2>/dev/null   # trellis agent background:true 注入目标
echo "${LANG:-}"                  # 系统 locale (如 en_US / zh_CN), 决定注入文本语言
head -5 CLAUDE.md AGENTS.md 2>/dev/null   # 项目主语言佐证
```

**目标语言** = 综合 `$LANG` locale + 项目 CLAUDE.md/README 主语言 + 当前会话语言。非 trellis 项目 → 报错终止。

## 工作流 (5 步)

| 步骤 | 行动 | 详细内容 |
| --- | --- | --- |
| 1 | 诊断 .trellis 现状 + 检测已有 trellisx marker | 读 `references/diagnose.md` |
| 2 | 注入 workflow.md (workflow-state 块 + Phase 描述) | 读 `references/workflow-injection.md` |
| 2.5 | **全文档语言对齐** (翻译全文叙述为设备语言) + **清理无效内容** (移除维护者注释 + 跨平台枚举收敛 Claude Code; 保留标签/marker/命令/路径/代码) | `references/workflow-injection.md` §i18n + §清理 |
| 3 | 注入 spec/ (trellisx 规范文档, 设备语言) | 读 `references/spec-injection.md` |
| 4 | 注入 trellis 生命周期 hook (config.yaml after_create/start/archive → worktree 自动建/销 + task.md 看板自动维护; 复制插件 scripts/ 两脚本) | 读 `references/hook-injection.md` |
| 4.5 | 注入 trellis agent `background: true` (.claude/agents/trellis*.md, 缺则加 / 非 true 强制改) | 读 `references/agent-injection.md` |
| 5 | 🔴 **AskUserQuestion 审批 (STOP)** → 一次写盘 → 验证 + 闭环验证 (create→planning→worktree→execute→check→finish 无断点) | 读 `references/apply-verify.md` |

> 🔴 **CHECKPOINT · 🛑 STOP (步骤 5)**: 改 `.trellis/` 前 **MUST 展示 diff plan + 经 AskUserQuestion 批准**才写盘。禁纯文本"是否同意"代替工具; 用户未明确批准 → 0 写入, 终止。

## 注入维度 (一律末尾追加, 不动原生)

| 维度 | 注入内容 | 落地位置 |
| --- | --- | --- |
| **强推 task** | "除极简外默认建 task + 边界模糊 MUST 问用户" (软约束) | workflow.md `[workflow-state:no_task]` 块末尾 |
| **subtask 拆分** | 按 trellis 原生 parent/child 语义 (多个独立可验收交付才拆 child, 不看数量); 多交付 → parent+child+各 worktree+并行调度图, 单交付 → 轻量 inline | workflow.md `[workflow-state:planning]` 块末尾 |
| **worktree 隔离 + 闭环** | worktree: start 自动建 `<git根>/.worktrees/<worktree>`, 源码改动隔离, archive 销毁; 闭环: plan→exec→check→finish 必走完整, 未 archive 禁宣告 Done (软约束) | workflow.md `[workflow-state:in_progress]` 块末尾 + config.yaml hook |
| **task.md 看板** | hook (`trellisx-taskmd.py`) 维护确定性列 (id/名称/描述/状态) + create/start/archive upsert + 7 天清理; AI (`trellisx-workspace`) 补主观列 (阶段/进度/worktree) | .trellis/scripts/ + config.yaml hooks + workflow.md marker |
| (背书) worktree spec | **仅新增** trellisx-worktree.md (不存在才建) | .trellis/spec/guides/ |
| (副作用) worktree hook | config.yaml `hooks.after_start/after_archive` 触发 `trellisx-worktree.py` 建/销 (不改 task.py) | .trellis/config.yaml + .trellis/scripts/ |
| **agent 后台化** | 所有 `trellis*` agent frontmatter 加 `background: true` (缺则加 / 非 true 强制改); 只动 background 一字段 | .claude/agents/trellis*.md |

> 🔒 **教训 (两条铁律之一的来由)**: 早期 apply **重写** no_task + Phase 流程, 破坏了 trellis 原生 task 创建触发。**根因是替换原生文本, 非追加本身。** 修正: no_task 可末尾追加强推 task 规约, 但 MUST 保留原生「First classify... / task-creation consent」+ Phase 流程 + 完成判定 + 回复前缀, 一字不改 (apply-verify 强制断言)。

## 失败处理 (触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 无 `.trellis/` (前置检查失败) | 提示用户先 `trellis init` | 非 trellis 项目 → 终止, 0 注入 |
| 已存在 trellisx marker (重复跑) | 幂等: 只更新 marker 内, 不堆叠 (`references/diagnose.md`) | marker 损坏/嵌套错乱 → 报告冲突位置, 请用户确认覆盖再写 |
| 缺 `config.yaml` / `.claude/agents/trellis*.md` | 跳过对应步骤 (4/4.5), 其余维度照注 | 全部目标缺失 → 仅注 workflow.md, 报告未注入维度 |
| 用户在步骤5 AskUserQuestion 驳回 | 立即停, 0 写盘, 返回"用户驳回" | — (审批门硬规, 不绕过) |
| 多文件写盘中途失败 | 回滚已写文件 (git checkout / backup) | 回滚失败 → 报告脏文件清单, 请用户手工核对 |
| workflow 原文英文而设备中文 | i18n: 翻译全文叙述 (步骤 2.5), 保留标签/marker/命令/路径 | 语言判不准 → 综合 `$LANG`+CLAUDE.md+会话语言, 仍不准则保持原文不译 |

## 参考集 (按需读)

| 文件 | 用途 |
| --- | --- |
| `references/diagnose.md` | 步骤 1: 现状诊断 + marker 检测 |
| `references/workflow-injection.md` | 步骤 2: workflow-state 块 + Phase 注入 (核心) |
| `references/spec-injection.md` | 步骤 3: spec 规范文档 |
| `references/hook-injection.md` | 步骤 4: trellis 生命周期 hook (config.yaml) worktree 自动化 |
| `references/agent-injection.md` | 步骤 4.5: trellis agent `background: true` 注入 |
| `references/apply-verify.md` | 步骤 5: 审批 + 写盘 + 验证 |

## 相关 skill

- `trellisx-orchestrate` — planning 阶段编排 PRD/design/implement/subtask
- `trellisx-spec` — spec 破坏式优化
- `trellisx-workspace` — 维护 `.trellis/task.md` 任务看板
