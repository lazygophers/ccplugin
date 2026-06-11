---
name: trellisx-apply
description: 把 worktree 隔离 + subtask 拆分两个维度增量注入当前项目 .trellis/ (workflow.md 的 planning/in_progress 块 + spec 背书文档 + 平台 hook worktree 自动化)。**纯增量, 不修改 trellis 原生流程** (task 创建/check/finish/前缀全保持原生)。幂等 (marker 包裹)。
when_to_use: 用户主动在某 trellis 项目内运行, 把该项目的 .trellis 改造成符合 trellisx 规范。短语 "trellisx apply" "应用 trellisx" "改造 .trellis" "内化 trellisx 规则" "/trellisx-apply"。
argument-hint: [scope]
arguments: [范围]
---

# trellisx-apply — 把 trellisx 规则内化进 .trellis

把 **worktree 隔离 + subtask 拆分** 两个维度增量注入当前项目 `.trellis/`。**纯增量, 绝不修改 trellis 原生流程** —— task 创建 / check / finish / 前缀全部保持 trellis 原生不动。跑完后由 trellis 原生 `inject-workflow-state` hook 注入这 2 个维度。

## 立场

| 立场 | 说明 |
| --- | --- |
| 内化优于外挂 | 规则写进 `.trellis/`, 由 trellis 自身机制生效; 不靠 trellisx 持续 hook |
| 幂等 | 所有注入用 `<!-- trellisx:start:<key> -->...<!-- trellisx:end:<key> -->` marker 包裹; 重复跑只更新 marker 内, 不重复堆叠 |
| 尊重 trellis 原生 | 融合而非取代: 引用 trellis 已有 (task.py / add-subtask / jsonl / trellis-check), 仅补 trellis 缺的 (worktree / subtask 文件编排) |
| 显式审批 | 改 `.trellis/` 前展示 diff plan, 经用户批准 (AskUserQuestion) 才写盘 |
| **增量优化, 不重构** | apply 只按 trellisx 方向**增量增强**现有 .trellis (marker 注入 + 加新文件 + 加新 hook); **绝不重构/重写**用户原有 workflow / spec / 文档内容。spec 的破坏式完全重构是 `trellisx-spec` skill 的职责, 不是 apply 的 |
| **清理无效注释** | apply 优化 workflow 时移除无效的模板内部注释 (trellis 给维护者看的 `<!-- ... -->` 说明, 对 AI 执行无价值, 占 context); **保留** trellisx 功能 marker `<!-- trellisx:start/end:X -->` |
| **i18n: 整个文档跟随设备语言** | apply 完成后, **整个 workflow.md + 新增 spec 的叙述文本** MUST 与设备语言一致 (不只 trellisx 注入部分)。若 trellis 原生 workflow 是英文而设备是中文 → **翻译全文档叙述为设备语言**。保留不译: workflow-state 标签 `[workflow-state:X]` / trellisx marker key / task.py 命令 / 文件路径 / 代码块 / 变量名 (这些是机器标识, 译了会坏)。语言转换是 i18n 优化, 不算语义重构 |

## 前置检查

```bash
ls .trellis/ || { echo "非 trellis 项目, 终止"; exit 1; }
ls .trellis/workflow.md          # 注入目标
ls .trellis/spec/ 2>/dev/null    # spec 目标
ls .claude/hooks/ 2>/dev/null    # 平台 hook 目标
# 检测设备/项目语言 (决定注入文本语言)
echo "${LANG:-}"                  # 系统 locale (如 en_US / zh_CN / ja_JP)
head -5 CLAUDE.md AGENTS.md 2>/dev/null   # 项目主语言佐证
```

**语言检测**: 综合 `$LANG` locale + 项目 CLAUDE.md/README 主语言 + 当前会话交互语言, 确定**目标语言**。

**全文档语言对齐 (步骤 2.5)**: 检测 workflow.md 现有叙述主语言, 若 ≠ 目标语言 → 翻译**整个 workflow.md 叙述文本** + 新增 spec 为目标语言。**保留不译**: `[workflow-state:X]` 标签 / `<!-- trellisx:start:X -->` marker / `task.py ...` 命令 / 路径 / 代码块 / frontmatter key。

非 trellis 项目 → 报错终止。

## 工作流 (5 步)

| 步骤 | 行动 | 详细内容 |
| --- | --- | --- |
| 1 | 诊断 .trellis 现状 + 检测已有 trellisx marker | 读 `references/diagnose.md` |
| 2 | 注入 workflow.md (workflow-state 块 + Phase 描述) | 读 `references/workflow-injection.md` |
| 2.5 | **全文档语言对齐** + **清理无效注释**: 翻译全文叙述为设备语言; 移除无效模板注释 (保留标签/marker/命令/路径/代码) | 读 `references/workflow-injection.md` §i18n + §清理 |
| 3 | 注入 spec/ (trellisx 规范文档, 设备语言) | 读 `references/spec-injection.md` |
| 4 | 注入平台 hook (worktree 自动建/销) | 读 `references/hook-injection.md` |
| 5 | AskUserQuestion 审批 → 一次写盘 → 验证 + **流程闭环验证** (确保 create→planning→worktree→execute→check→finish 无断点) | 读 `references/apply-verify.md` |

## 注入维度 (纯增量, 只加 2 个)

apply **只增加** worktree + subtask 两个维度, **绝不修改** trellis 原生流程 (task 创建 / check / finish / 前缀):

| 维度 | 注入内容 | 落地位置 |
| --- | --- | --- |
| **subtask 拆分** | task 拆 ≥ 2 subtask + 独立文件 + 调度图 | workflow.md `[workflow-state:planning]` 块末尾追加 |
| **worktree 隔离** | task.py start 自动建 <git根>/.worktrees/<worktree>; 源码改动隔离; archive 销毁 | workflow.md `[workflow-state:in_progress]` 块末尾 + 平台 hook (PostToolUse) |
| (背书) worktree spec | **仅新增** trellisx-worktree.md (不存在才建, 不动现有 spec) | .trellis/spec/guides/ |
| (副作用) worktree hook | PostToolUse 监测 task.py start/archive 自动建/销 (不改 task.py) | 用户项目 .claude/settings.json |

**绝不碰**: `[workflow-state:no_task]` (task 创建触发) / Phase 流程 / 完成判定 / 回复前缀 —— 全部保持 trellis 原生。

> 教训: 早期 apply 注入 no_task + 重写 Phase, 破坏了 trellis 原生 task 创建触发。apply 必须最小侵入。

## 参考集 (按需读)

| 文件 | 用途 |
| --- | --- |
| `references/diagnose.md` | 步骤 1: 现状诊断 + marker 检测 |
| `references/workflow-injection.md` | 步骤 2: workflow-state 块 + Phase 注入内容 (核心) |
| `references/spec-injection.md` | 步骤 3: spec 规范文档 |
| `references/hook-injection.md` | 步骤 4: 平台 hook worktree 自动化 + 前缀注入 |
| `references/apply-verify.md` | 步骤 5: 审批 + 写盘 + 验证 |

## 相关 skill

- `trellisx-orchestrate` — planning 阶段编排 PRD/design/implement/subtask (被内化的 workflow 引用)
- `trellisx-spec` — spec 破坏式优化
