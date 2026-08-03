---
title: agent-json
category: spec
keywords: []
status: active
inclusion: auto
---

## agent 入参只传必要信息

# agent/skill JSON 接口规范 — PRD

## 目标
- [ ] 所有 agent 入参只传必要信息 (tid/sid/工作目录), 可 skein 获取的信息不传递
- [ ] 所有 agent 返回必须是 JSON, 只含必要信息 (执行结果必须传), 不过度返回
- [ ] skills 调用 skein 命令默认 JSON 输出, 用户可指定非 JSON
- [ ] prd 相关操作改用 skein 命令 (skein prd read/write/check/uncheck) 而非直接改文件

## 边界
- [ ] 范围内: 9 个 agent.md 的入参/返回 JSON 规范
- [ ] 范围内: skein CLI 命令加 --json 默认 (或新增全局 --json flag)
- [ ] 范围内: skills/agents 里涉及 prd 直接编辑的措辞改为用 skein prd 命令
- [ ] 范围外: 不改 agent 的核心职责定义
- [ ] 约束: 现有非 JSON 输出不破坏 (需向后兼容)

## User Stories
1. As a dispatch, I want agent prompt 只含 tid/sid/workdir, so that agent 自己去读详情而非依赖 prompt 转述
2. As a main, I want agent 返回精简 JSON, so that 我不浪费 token 解析无用信息
3. As a 用户, I want skein 命令默认 JSON, so that 程序化调用更方便
4. As a AI, I want 用 skein prd write 而非直接改文件, so that 引擎校验不绕过

## 验收标准
- [ ] 9 个 agent.md 的 dispatch 示例只含 tid/sid/workdir 三参数
- [ ] 9 个 agent.md 的返回格式是 JSON, 只含必要字段
- [ ] skein CLI 有 --json 全局 flag (或核心命令有)
- [ ] skills/agents 里无「直接编辑 prd.md」措辞, 改为 skein prd write/check
- [ ] 全量 pytest ≥ 425

## Testing Decisions
- [ ] 结构性 grep: agent.md 里 dispatch 示例只 3 参数
- [ ] 结构性 grep: 无「直接编辑 prd」措辞

## 索引
- 详细设计: [design.md](design.md)
- 任务/子任务/调度: task.json

## agent 返回必须是 JSON

## skein 命令默认 JSON 输出

## prd 操作改用 skein 命令


