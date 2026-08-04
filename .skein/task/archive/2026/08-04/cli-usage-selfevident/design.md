# CLI 用法自明化 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 根因

`skein subtask` 用 `ctx.args` 收自由形式位置参数 (`cli.py:365`), typer 无法按 action 表达差异化必填,
于是 `--help` 把 9 个选项一律列成可选; 而 `add` 的 sid/name/desc/estimate 是运行时手写
`typer.BadParameter` 校验的 (`cli.py:375-378`)。结果: 文档没写 `--estimate`, `--help` 也看不出,
调用方只能先失败一次、读报错、再重调。其余子命令走 typer 声明式参数, `--help` 能正确标 `[required]`,
不在此列。

## 标注约定 (本次统一)

| 记号 | 含义 |
|---|---|
| `<名>` | 必填, 尖括号内是值的语义 |
| `[--opt <值>]` | 可选且接值 |
| `[--flag]` | 可选布尔开关, 不接值 (如 `confirm --summary`) |
| `a\|b` | 枚举取值 |

## 关键取舍

- **改文案不改校验**: 运行时 `BadParameter` 校验保留原样 —— 它是最后一道防线, 且 `subtask` 的
  action 分流结构短期不重构。只让 docstring 和文档把这道门口的规则提前讲清楚。
- **不把 `subtask` 拆成 typer 子命令**: 那样能让 `--help` 自动标必填, 但会改掉 `subtask <action> <tid>`
  的调用形态, 波及全部文档与 agent。收益不抵改动面, 留作后续。

## 已知同类缺口 (本次一并覆盖或记录)

- `prd write --type` 只接受 目标/边界/验收标准, 但 confirm 门要求 验证方式 与 Testing Decisions
  也填实 —— 存在「CLI 无写入路径却卡门」的缺口, 只能手改 prd.md。本次记录, 是否扩 `--type` 白名单
  归后续裁定 (超出「只改表达」的边界)。

## 测试接缝 (seam)

**接缝 = `bin/skein` 进程边界** —— 从 shell 照抄一条命令进去, 看退出码与 stderr。
选它的理由: 这正是 agent 实际的调用面, 最高层外部行为; 既有 `tests/test_docs_commands.py`
已经在这一层扫文档命令, 属复用而非新建; 一个接缝覆盖全部三个 subtask 的验证需求。

不选的接缝: `cli.py` 函数级直调 (绕过 typer 解析, 测不到必填门)、docstring 字符串断言
(测的是措辞不是行为, 与文案改动互锁)。

## 测试接缝 (seam)
check 阶段验证的是`行为对不对`而非`跑没跑起来`, 全靠这里选对接缝。三条规则:
1. 优先复用现有接缝, 不新建
2. 取最高接缝 (越靠外部行为越好)
3. 越少越好, 理想 = 1 个


