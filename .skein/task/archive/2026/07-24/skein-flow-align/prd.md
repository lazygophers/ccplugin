# skein-flow 图与执行逻辑对齐 — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] skein-flow.mmd 图与 skein 插件执行逻辑一致, 反映用户预期的 6 点修正, 且插件 skill 逻辑本身也对齐(点1/点3)。

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: skein-flow.mmd 重写 + 高清 png 重生成; exec skill 去 exec 阶段勾验收(点1); check skill 加 checkpoint 核对 + 场景自适应(点3)。
- [ ] 范围外: 不改 skein.py 脚本行为(create/check/finish 已符合预期); 不改其他 skill。
- [ ] 约束: skill 文案改动须过 `claude -p` 质量门; 严格遵守 config.yaml 配置核心(use_worktree/max_active/retain_days)。

## 验收标准
可执行、可核对的完成断言 (逐条):
- [x] exec skill 调度循环不再对 subtask 勾验收(check), 仅 done/fail; 勾验收(checkpoint)归 skein-check
- [x] check skill step1 = task+subtask checkpoint(--check 项)核对并标记完成; step2 = 场景自适应内置 check(编程 build/test/arch, 小说逻辑一致性)
- [x] skein-flow.mmd 修正 6 点: 建task=task.json+文件夹(点6); plan确认→start→exec连线(点5); exec无验收完成即done(点1); 单task全done→check/全task done→exec停(点2); check=checkpoint+场景check(点3); finish=merge→销wt→标记完成→异步spec(点4); 含配置核心节点
- [x] png 高清重生成
- [ ] 改动 skill 过 claude -p 质量门

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skein-flow-align`)
