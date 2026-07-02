# 异步等待输出任务清单表格 (flow + 注入 workflow)

## Goal

trellisx 异步等待场景 (workflow 异步跑等 notification / 后台 sub-agent 在跑 / 审批等待) 下, main 结束本回合前 MUST 输出当前 in_flight + pending task 清单 (表格), 让用户在异步间隙保持任务全景可视, 不失中途干预视角。

## Background

现有「进度通讯硬规」(`progress-communication.md`) 覆盖 sub-agent 完成/阻塞/teammate/workflow 阶段完成等场景, 但**未覆盖「异步等待」本身** —— 即 main 派出异步任务后、结束本回合前的时刻, 用户面对空白无任何"还剩什么没做完"的全景视图。

flow SKILL.md exec 阶段已有「workflow 异步禁 sleep/轮询, 调用后直接结束本回合」, 但只说"做什么"(不阻塞), 没说"结束前要输出什么"。

## Requirements

### R1 触发场景 (任一即触发)
- workflow 异步跑 (`run_in_background`), main 结束回合等 notification
- 后台 sub-agent 在跑, main 等返回
- 用户审批等待中 (有在跑的无人工依赖 subtask)

**不触发**: 同步前台阻塞等待 (main 自己在等, 无独立清单可输出); 无任何在跑任务。

### R2 输出格式 (表格)
列: `subtask-id` · `状态` (in_flight / pending / blocked) · `摘要` (≤30 字) · `阻塞原因` (blocked 时填, 否则 `-`)。

### R3 落点 (两处注入)
1. **flow SKILL.md** exec 阶段「workflow 异步禁 sleep」处补: 结束回合前 MUST 输出任务清单表格; 硬规段「其他必做」加一条「异步等待 MUST 输出任务清单」。
2. **progress-communication.md** 通讯场景表新增「异步等待」行 + 新增 §「异步等待清单格式」给表格模板 + 范例。

### R4 表格内容来源
main 维护的 in_flight/pending 状态视图 (scheduling.md DAG 态 + workflow /workflows 视图), 不新算, 复用已有调度态。

## Acceptance Criteria

- [ ] flow SKILL.md exec 阶段「workflow 异步」段补"结束回合前 MUST 输出任务清单表格"
- [ ] flow SKILL.md 硬规「其他必做」加一条「异步等待 MUST 输出任务清单」
- [ ] progress-communication.md 通讯场景表加「异步等待」行
- [ ] progress-communication.md 新增 §「异步等待清单格式」含表格模板 + 范例 + 不触发场景说明
- [ ] 两处表述一致 (列名 / 状态取值 / 触发场景统一)
- [ ] `claude -p` 验证: AI 读改动后能正确识别"异步等待时要输出什么表格"
- [ ] 改动仅限上述两文件, 无 scope 蔓延

## Constraints

- 仅文档变更 (两个 .md), 不动脚本/逻辑
- 表格列名 / 状态取值与现有 scheduling.md / progress-communication.md 术语一致 (subtask / in_flight / pending / blocked)
- 中文表述沿用周边风格 (强制规则列表, 紧凑)
