# Planner 常见错误

## 1. 过度拆分

简单操作不应拆成多任务。每个任务应是完整的可独立验证的工作单元。

错误：创建配置/写入配置/保存配置 → 正确：创建并配置API配置文件(1个任务)

## 2. 验收标准模糊

必须使用数值指标(≥90%, <200ms)和明确验证方式，禁止主观描述("好"/"正常")。

错误：`["代码质量好"]` → 正确：`["覆盖率≥90%", "API返回正确状态码", "Lint 0错误"]`

## 3. 缺少中文注释

Agent和Skills必须带中文注释：`name（中文说明）`。

错误：`"agent": "coder"` → 正确：`"agent": "coder（开发者）"`

## 4. 循环依赖

违反DAG原则，导致死锁。用拓扑排序验证。

错误：T1→T2→T3→T1 → 正确：T1→T2→T3(无环)

## 5. 并行度超限

最多2个并行任务。优先并行无依赖任务。

错误：`[["T1","T2","T3"]]` → 正确：`[["T1","T2"],["T3"]]`

## 6. 结构化验收标准错误

必需字段：`id`+`type`+`description`+`priority`。类型特定：`exact_match`需`verification_method`，`quantitative_threshold`需`metric`+`operator`+`threshold`。

operator支持：`>=`,`<=`,`>`,`<`,`==`(非Unicode符号)。tolerance为相对值(0.05=5%)。不确定时用字符串格式。

## 7. 缺少Agent/Skills

tasks非空时每个任务必须指定agent+至少1个skill(带中文注释)。

来源可选：Task插件(`task:planner`) | 其他插件(`golang:dev`) | 项目自定义(`.claude/agents/`) | 通用(`coder（开发者）`)

特殊：功能已存在时返回空tasks数组，无需agent/skills。
