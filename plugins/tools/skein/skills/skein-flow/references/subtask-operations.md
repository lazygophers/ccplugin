# Subtask 操作规范

本文件只定义 `skein subtask add` 的参数与 DAG 一致性约束。新增、修复、并入等场景何时触发、如何续跑，统一见 [flow-loop.md](flow-loop.md)。

## 命令格式

```bash
skein subtask add <tid> <sid> \
  --name "<子任务名>" \
  --desc "<一句话描述>" \
  --estimate <小时数> \
  [--deps <sid1>,<sid2>] \
  [--check "验收1;验收2;验收3"] \
  [--skills "skill1,skill2"]
```

## 字段说明

| 参数 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `<tid>` | 是 | - | 目标 task id。 |
| `<sid>` | 是 | - | subtask id；kebab-case，task 内唯一。 |
| `--name` | 是 | - | 子任务名称，简短可读。 |
| `--desc` | 是 | - | 子任务描述；修复类 subtask 应写明根因与复现要求。 |
| `--estimate` | 是 | - | 预计工时，正数；见 [estimate-gate.md](estimate-gate.md)。 |
| `--deps` | 否 | 空 | 前置 subtask id 列表，逗号分隔。 |
| `--check` | 否 | 空 | 验收 checklist，分号分隔。 |
| `--skills` | 否 | 空 | 建议加载的 skill，逗号分隔。 |

## 通用约束

- sid 不可重复。
- `--estimate` 必须为正数。
- task estimate 须覆盖 subtask estimate 总和。
- `--deps` 不得形成环。
- subtask DAG 是调度真值源；不得用 markdown 图替代落盘。
- 正式状态流转见 [flow-loop.md §1.2](flow-loop.md#12-subtask-状态)；命令语义查 `skein subtask --help`。

## DAG 一致性

每次 `subtask add --deps` 必须保持无环。

| 陷阱 | 示例 | 正确做法 |
|---|---|---|
| 互相依赖 | A depends_on B，B depends_on A | 拆共享前置 C，A/B 都依赖 C。 |
| 修复 subtask 挂错 | fix depends_on failed sid，导致原失败项无法重跑 | fix 挂失败项原前置；原失败项再依赖 fix。 |
| 跨层跳挂 | 下游直接挂源头，绕过中间真实依赖 | 按真实数据/接口依赖挂边。 |

## 场景索引

- planning 新增 subtask：见 [flow-loop.md §4](flow-loop.md#4-plan-过程)。
- exec 自愈修复：见 [flow-loop.md §9.1](flow-loop.md#91-exec-自愈)。
- check 失败修复：见 [flow-loop.md §9.2](flow-loop.md#92-check-失败扭转)。
- 并入现有 task：见 [flow-loop.md §4](flow-loop.md#4-plan-过程)。
