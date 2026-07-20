---
title: claude -p 理解门 + test-prompts 回归
layer: recall
category: test
keywords: [claude-p,test,skill,command,quality]
source: reconstruct
authored-by: skein-spec
created: 1784346643
status: active
related: []
updated: 1784346643
---

## 铁律

- MUST：代码改动前后用 `claude -p "<内容>" --output-format stream-json | jq` 验证 AI 可正确识别
- MUST：skill 目录配置 `test-prompts.json`，包含 prompt/expected 对进行回归
- MUST：仅返回结果非空、符合预期时，才认为优化/简化有效

## 反例表

| 禁 | 改为 |
|---|---|
| 未经 claude -p 验证直接提交简化 | 先跑 claude -p 确认输出正确再提交 |
| test-prompts.json 缺失或过时 | 添加或更新测试用例 |
| 简化后输出为空或不符预期 | 回滚或调整简化 |
