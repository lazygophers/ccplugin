# Workflow 返回值被截断：读 task output 文件 + python 解析，不重跑

Workflow（ultracode）的返回值经 rtk / harness 转手会被截断（2026-10-24 实测
`truncated 23536 chars`，审计 workflow 的 agent 明细全丢）。截断的返回值不下
结论：

- 完整输出在该 task 的 output 文件里：读文件，用 `python3 -c` 解析 JSON 取
  需要的字段（agent 数、各 agent 结论），别让整个 JSON 进上下文。
- 不因「返回值不全」重跑 workflow——重跑是几十个 agent 的成本。

出处：2026-10-24 ask-me token 优化 session（session 概要；task output 文件
路径未随决策留存，按 harness task 通知给出的路径取）。
