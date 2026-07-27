# skein-wf-refs — 重组 skein-workflow references 为 per-consumer 聚合结构

## 背景

skein-workflow 设计为"流程规则单一真值源"，8 个原子 reference 文件（state-machine/dag-scheduling/subtask-operations/worktree-convention/rollback-protocol/state-before-action/priority-scale）+ 各 consumer SKILL.md 用文字"详见 skein-workflow/references/xxx.md"引用。

## 问题

1. **死链**: consumer 写 `skein-workflow/references/xxx.md`，但从 consumer 目录(如 skein-flow/)出发，实际路径是 `../skein-workflow/references/`，相对路径解析不到。
2. **未注册**: skein-workflow 没进 plugin.json skills 数组（只 8 个），不作为可 invoke skill 加载（不影响 references 作普通文件被 Read）。
3. **散落重复**: consumer SKILL.md 既内联复述规则正文（如 skein-flow:16-26 完整抄了 state-before-action），又写"详见 xxx.md"，规则正文多处存在，改一处要同步多处。
4. **引用散碎**: 每个 consumer 要引用 4-7 个 reference 文件，AI 运行时多次 Read，路径易错。

## 目标

- references 按"谁用"重组为 5 个 per-consumer 聚合文件（for-flow/exec/check/plan/finish.md），各 consumer 一次 Read 拿全所需规则。
- consumer SKILL.md 删除内联复述，改为一行引用 `../skein-workflow/references/for-X.md`，修复死链。
- 原子文件保留作为深详底座；for-xxx.md 聚合该 consumer 真正需要的规则正文（简短规则直接全文，冗长如 DAG 算法提炼关键条款 + 指向原子文件深详节号）。
- 缓存友好: consumer SKILL.md 极薄稳定 → SKILL.md 层 cache 命中；for-xxx.md 作为 tool result 读入无 cache，故须精炼只装必需规则。

## 非目标

- 不改 SessionStart/SubagentStart hook 注入机制（core 规则走 .skein/spec/core 体系，与本次 references 重组无关）。
- 不注册 skein-workflow 进 plugin.json（用户未选）。
- 不动各 consumer 自有 references（carrier-rules/scope-boundary/merge-conflict-resolution 等领域文档）。
- 不改 .skein/spec 规则记忆体系。

## consumer→reference 映射（实测）

| consumer | 用到的原子 references |
|---|---|
| flow | state-before-action, task-state-machine, subtask-state-machine, dag-scheduling, subtask-operations, worktree-convention, rollback-protocol |
| plan | task-state-machine, subtask-operations, dag-scheduling, subtask-state-machine |
| exec | worktree-convention, state-before-action(硬门2), dag-scheduling(§6), subtask-operations(§3), subtask-state-machine |
| check | state-before-action(硬门3), worktree-convention, rollback-protocol, subtask-operations(§4) |
| finish | worktree-convention |
