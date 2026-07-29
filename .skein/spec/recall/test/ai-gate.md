---
title: ai-gate
layer: recall
category: test
keywords: [claude-p,test,skill,command,quality]
status: active
---

## claude -p 理解门 + test-prompts 回归

### 铁律

- MUST：代码改动前后跑 claude -p 理解门验证 AI 可正确识别；命令形式见 `recall/test/claude-p-quality-gate.md`（单一真值源）
- MUST：skill 目录配置 `test-prompts.json`，包含 prompt/expected 对进行回归
- MUST：仅返回结果非空、符合预期时，才认为优化/简化有效

### 反例表

| 禁 | 改为 |
|---|---|
| 未经 claude -p 验证直接提交简化 | 先跑 claude -p 确认输出正确再提交 |
| test-prompts.json 缺失或过时 | 添加或更新测试用例 |
| 简化后输出为空或不符预期 | 回滚或调整简化 |
