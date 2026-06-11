---
name: trellisx-apply
description: 把 建task倾向 + subtask拆分 + worktree隔离 三维度增量注入当前项目 .trellis/ (workflow.md 的 no_task/planning/in_progress 块 + spec 背书文档 + trellis 生命周期 hook worktree 自动化)。**纯增量追加, 绝不替换 trellis 原生文本** (no_task 分类+征同意/check/finish/前缀全保留)。幂等 (marker 包裹)。
when_to_use: 用户主动在某 trellis 项目内运行, 把该项目的 .trellis 改造成符合 trellisx 规范。短语 "trellisx apply" "应用 trellisx" "改造 .trellis" "内化 trellisx 规则" "/trellisx-apply"。
argument-hint: [scope]
arguments: [范围]
---

# trellisx-apply — 把 trellisx 规则内化进 .trellis

把 **建 task 倾向 + subtask 拆分 + worktree 隔离** 三个维度增量注入当前项目 `.trellis/`。**纯增量追加, 绝不替换 trellis 原生文本** —— no_task 原生分类+征同意 / check / finish / 前缀全部保留不动, trellisx 内容只在块末尾追加。跑完后由 trellis 原生 `inject-workflow-state` hook 每轮注入这些维度。

> 建 task 倾向 = 用户偏好"更多使用 task; 不确定该不该建就主动问用户", 注入 no_task 块 (保留原生判定, 仅强化倾向)。

## 立场

| 立场 | 说明 |
| --- | --- |
| 内化优于外挂 | 规则写进 `.trellis/`, 由 trellis 自身机制生效; 不靠 trellisx 持续 hook |
| 幂等 | 所有注入用 `<!-- trellisx:start:<key> -->...<!-- trellisx:end:<key> -->` marker 包裹; 重复跑只更新 marker 内, 不重复堆叠 |
| 尊重 trellis 原生 | 融合而非取代: 引用 trellis 已有 (task.py / add-subtask / jsonl / trellis-check), 仅补 trellis 缺的 (worktree / subtask 文件编排) |
| 显式审批 | 改 `.trellis/` 前展示 diff plan, 经用户批准 (AskUserQuestion) 才写盘 |
| **增量优化, 不重构** | apply 只按 trellisx 方向**增量增强**现有 .trellis (marker 注入 + 加新文件 + 加新 hook); **绝不重构/重写**用户原有 workflow / spec / 文档内容。spec 的破坏式完全重构是 `trellisx-spec` skill 的职责, 不是 apply 的 |
| **清理无效内容** | apply 优化 workflow 时移除对当前平台无价值的冗余: ① 模板内部注释 (trellis 给维护者看的 `<!-- ... -->` 说明); ② 跨平台枚举清单 (`[Claude Code, Cursor, OpenCode, codex-sub-agent, Kiro, ...]` 等多平台名罗列) 收敛为当前平台 Claude Code。**保留** trellisx 功能 marker + workflow-state 标签 |
| **i18n: 整个文档跟随设备语言** | apply 完成后, **整个 workflow.md + 新增 spec 的叙述文本** MUST 与设备语言一致 (不只 trellisx 注入部分)。若 trellis 原生 workflow 是英文而设备是中文 → **翻译全文档叙述为设备语言**。保留不译: workflow-state 标签 `[workflow-state:X]` / trellisx marker key / task.py 命令 / 文件路径 / 代码块 / 变量名 (这些是机器标识, 译了会坏)。语言转换是 i18n 优化, 不算语义重构 |

## 前置检查

```bash
ls .trellis/ || { echo "非 trellis 项目, 终止"; exit 1; }
ls .trellis/workflow.md          # 注入目标
ls .trellis/spec/ 2>/dev/null    # spec 目标
ls .trellis/config.yaml          # trellis 生命周期 hook 注入目标
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
| 2.5 | **全文档语言对齐** + **清理无效内容**: 翻译全文叙述为设备语言; 移除无效模板注释 + 跨平台枚举收敛为 Claude Code (保留标签/marker/命令/路径/代码) | 读 `references/workflow-injection.md` §i18n + §清理 |
| 3 | 注入 spec/ (trellisx 规范文档, 设备语言) | 读 `references/spec-injection.md` |
| 4 | 注入 trellis 生命周期 hook (config.yaml after_start/after_archive → worktree 自动建/销) | 读 `references/hook-injection.md` |
| 5 | AskUserQuestion 审批 → 一次写盘 → 验证 + **流程闭环验证** (确保 create→planning→worktree→execute→check→finish 无断点) | 读 `references/apply-verify.md` |

## 注入维度 (纯增量追加, 绝不替换原生)

apply 增量追加以下维度, **绝不替换 / 重写** trellis 原生文本 (task 创建分类逻辑 / check / finish / 前缀全保留):

| 维度 | 注入内容 | 落地位置 |
| --- | --- | --- |
| **建 task 倾向** | 强化"更多用 task + 不确定就问用户"倾向 (保留原生分类+征同意, 仅末尾追加倾向) | workflow.md `[workflow-state:no_task]` 块末尾追加 |
| **subtask 拆分** | 按 trellis 原生 parent/child 语义判定 (有多个独立可验收交付才拆 child, 不看数量); 多交付 → parent+child+各 worktree+并行调度图, 单交付 → 轻量 inline | workflow.md `[workflow-state:planning]` 块末尾追加 |
| **worktree 隔离** | task.py start 自动建 <git根>/.worktrees/<worktree>; 源码改动隔离; archive 销毁 | workflow.md `[workflow-state:in_progress]` 块末尾 + trellis 生命周期 hook (config.yaml) |
| (背书) worktree spec | **仅新增** trellisx-worktree.md (不存在才建, 不动现有 spec) | .trellis/spec/guides/ |
| (副作用) worktree hook | config.yaml `hooks.after_start/after_archive` 触发 `.trellis/scripts/trellisx-worktree.py` 建/销 (不改 task.py) | .trellis/config.yaml + .trellis/scripts/ |

**绝不替换原生文本**: no_task 的原生「First classify... / task-creation consent」、Phase 流程、完成判定、回复前缀 —— 一字不改, trellisx 内容只末尾追加。

> 教训: 早期 apply **重写** no_task + Phase 流程, 破坏了 trellis 原生 task 创建触发。**根因是替换原生文本, 非追加本身。** 修正: no_task 可末尾追加建 task 倾向, 但 MUST 保留原生分类+征同意文本 (apply-verify 强制断言)。

## 参考集 (按需读)

| 文件 | 用途 |
| --- | --- |
| `references/diagnose.md` | 步骤 1: 现状诊断 + marker 检测 |
| `references/workflow-injection.md` | 步骤 2: workflow-state 块 + Phase 注入内容 (核心) |
| `references/spec-injection.md` | 步骤 3: spec 规范文档 |
| `references/hook-injection.md` | 步骤 4: trellis 生命周期 hook (config.yaml) worktree 自动化 |
| `references/apply-verify.md` | 步骤 5: 审批 + 写盘 + 验证 |

## 相关 skill

- `trellisx-orchestrate` — planning 阶段编排 PRD/design/implement/subtask (被内化的 workflow 引用)
- `trellisx-spec` — spec 破坏式优化
