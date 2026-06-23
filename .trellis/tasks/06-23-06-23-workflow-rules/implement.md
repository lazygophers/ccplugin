# Implement — trellisx workflow 执行规范

## 执行层

实质改动派 sub-agent (general-purpose) 落地, main 只编排。4 个写盘 subtask **文件集互斥 → 同批并行**; 验证 subtask 串在写盘之后。共享决策 (C1–C5) 在 design.md 已定, 每个 writer prompt 内联对应 canonical 文本, 禁各自改写。

## Subtask 分解 (五要素)

### S1 — flow 骨架 + 硬规 (canonical 源)
- **目标**: trellisx-flow/SKILL.md 体现 4 规范。
- **产出**: 骨架 (现 ~55-65 行) 替换为 design.md C5; 硬规段嵌入 C1 四规范 + C2 边界。
- **验证**: grep 骨架含 `agent_with_retry` / `meta.phases` 带 type / `phase('finalize')`; 硬规含 4 规范 + 无 task 豁免。体积 ≤ 1.5x。
- **资源**: design.md C1/C2/C5。文件: `skills/trellisx-flow/SKILL.md` (独占)。
- **依赖**: 无 (可并行)。

### S2 — apply 注入点编码
- **目标**: 注入项目规则的运行期约束含 4 规范。
- **产出**: `workflow-injection.md` 注入点0 加 C2 判定表; 注入点2 in_progress 硬规编码 C1+C3; 注入点4 finish_force step⓪ 用 C4。`finishcmd-injection.md` step⓪ 对齐 C4。
- **验证**: grep 两文件含判定表 / retry / TaskStop step⓪。体积 ≤ 1.5x。
- **资源**: design.md C1/C2/C3/C4。文件: `skills/trellisx-apply/references/workflow-injection.md` + `finishcmd-injection.md` (独占)。
- **依赖**: 无 (可并行)。

### S3 — orchestrate retry + 边界对齐
- **目标**: 消除建task判定冲突, retry 分工对齐。
- **产出**: `failure-recovery.md` retry 分工对齐 C3; `orchestrate/SKILL.md` L25 建task判定改引 C2 (消除与 flow 冲突)。
- **验证**: grep orchestrate 建task措辞 == C2; failure-recovery 含两层重试分工。
- **资源**: design.md C2/C3。文件: `skills/trellisx-orchestrate/references/failure-recovery.md` + `skills/trellisx-orchestrate/SKILL.md` (独占)。
- **依赖**: 无 (可并行)。

### S4 — apply SKILL / README / finish.py docstring 对齐
- **目标**: 维度表 + 脚本边界注释与 C1/C4 一致。
- **产出**: `apply/SKILL.md` 维度行措辞对齐 C1/C4; `README.md` 维度表同步; `scripts/trellisx-finish.py` docstring 边界注释对齐 C4 (仅注释, 不动逻辑)。
- **验证**: `python3 -c "import ast; ast.parse(open('scripts/trellisx-finish.py').read())"` AST_OK; grep 三处 git层/AI层 措辞一致。
- **资源**: design.md C1/C4。文件: `skills/trellisx-apply/SKILL.md` + `README.md` + `scripts/trellisx-finish.py` (独占)。
- **依赖**: 无 (可并行)。

### S5 — 一致性 + 端到端验证 (check)
- **目标**: 跨文件一致 + 注入产物达标。
- **产出**: 验证报告。
- **验证**:
  - AC3: `grep -rn "建 task\|必建 task\|豁免" flow + orchestrate + workflow-injection` 措辞一致。
  - AC4: ④收尾 git层/AI层 在 flow / workflow-injection / finishcmd / finish.py 四处一致。
  - AC6: tmp 目录 `task.py init` + `/trellisx-apply` 端到端, 确认注入的项目规则含 4 规范 (按 trellisx 测试规程, 不浅测)。
- **资源**: 全部 AC。
- **依赖**: S1–S4 全部完成后 (串行, barrier)。

## 调度

```
parallel: [S1, S2, S3, S4]   # 文件集互斥, 同批派 general-purpose, 各 isolation:worktree
  ↓ barrier (全 keep)
S5 verify (单 agent, 跨文件只读 grep + tmp 端到端)
  ↓
finalize: TaskStop 清悬挂 → task.py finish (commit→merge→销 worktree→archive)
```

## Review gates

- G1 (本步, start 前): 用户审 prd/design/implement → 同意后 `task.py start`。
- G2 (S1–S4 后): 每个 writer commit, main 核对 verify 项 + grep 一致性; 任一不达标 → revert 该 commit 重派 (≤3)。
- G3 (S5 后): 端到端验证通过 → finalize。

## Rollback

- 单 writer 失败/不达标: `git revert <commit>`, 互斥文件不影响他人。
- 整体放弃: revert S1–S4 全部 commit, task.py 不 finish。
