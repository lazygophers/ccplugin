# CLI 用法自明化 — PRD (主入口)

> 禁写具体文件路径与代码片段 (会很快过期) —— 例外: prototype 产出的能精确编码决策的片段 (状态机/schema/type shape) 可内联, 且须注明来自 prototype。

## 目标
- [ ] agent/skill 照抄文档里的 bin 命令即可一次调用成功, 无需先失败读报错、也无需先跑 -h 探参数。
## 边界
- [ ] 只改命令用法的表达 (CLI docstring/help 文案 + 文档里的命令形态标注);禁改 CLI 的参数语义、必填规则本身、任何执行逻辑。
## User Stories
1. 作为派出去的 executor agent, 我照抄文档里的 `skein subtask add` 形态就能一次成功, 不必先吃一次 `Invalid value` 再补参数。
2. 作为 main, 我看命令形态就知道哪些参数省不掉, 不必为每个子命令先跑一次 `--help`。
3. 作为读文档的人, 我从 `<>` 和 `[]` 一眼分辨必填与可选, 不必去翻 cli.py 的校验分支。
4. 作为跑 `--help` 的人, 对 `subtask` 这种按 action 分流的命令, help 也告诉我每个 action 各自的必填项, 而不是把 9 个选项一律列成可选。
5. 作为写 prd 的人, 我能通过 CLI 填完 confirm 门要求的全部章节 (含验证方式 / Testing Decisions), 不必绕过 CLI 手改 prd.md。
6. 边界情况: 布尔开关型选项 (如 `confirm --summary`) 在形态里不带 `<值>`, 与接值选项可区分。

## 验收标准
- [x] subtask add 的 --estimate 必填在 -h 输出和全部文档形态里都可见;文档命令形态统一 <>必填 []可选;抽样照抄文档命令一次成功;test_docs_commands 全绿
## 验证方式
每条验收标准的验证手段与通过标准 (plan 阶段必填):
- [ ] `--estimate` 可见性: 跑 `skein subtask --help`, 输出里 add 的 sid/--name/--desc/--estimate 四项标为必填 —— 通过标准: 不看源码即可辨认。
- [ ] 文档形态一致: 对每条文档里的命令形态, 与对应 `--help` 的必填项逐条比对 —— 通过标准: 零处形态缺必填参数、零处把可选标成必填。
- [ ] 照抄即成功: 临时 git 仓建空工作区, 逐字照抄文档形态跑 create / subtask add / prd write / deps / contract / confirm —— 通过标准: 首次调用退出码全 0, 无 `Invalid value` / `unexpected extra argument`。
- [ ] 回归: `uv run pytest tests/test_docs_commands.py` 与全量 `tests/` —— 通过标准: docs_commands 全绿, 全量不超基线 (已知 test_mypy_strict 属 cli-typer-migration 遗留)。

## Testing Decisions
什么算好测试 (只测外部行为不测实现细节) / 测哪些模块 / codebase 内的同类测试先例:
- [ ] 不为纯文案改动新增单测, 复用既有 `tests/test_docs_commands.py` (它已在扫文档命令与 CLI 的对应关系, 是同类先例)。
- [ ] 「照抄即成功」走临时工作区手工实跑, 不做成自动化断言 —— 断言写死形态字符串会和文案改动互锁, 每次改措辞都要同步改测试, 得不偿失。
- [ ] 只测外部行为: 测「命令能否一次跑通」和「help 是否列出必填」, 不测 docstring 的具体措辞。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein subtask list cli-usage-selfevident`)
