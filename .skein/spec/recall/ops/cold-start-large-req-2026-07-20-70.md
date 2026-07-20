---
title: agent 意外终止丢产出教训
layer: recall
category: ops
keywords: [agent,意外终止,commit,dispatch,教训,即时commit]
source: cold-start-large-req-2026-07-20
authored-by: skein-spec
created: 1784541865
status: active
related: []
updated: 1784541865
---

# agent 意外终止丢产出教训

## 触发场景
subagent 意外终止（如 SIGKILL / OOM / 系统崩溃）时，未 commit 的产出全部丢失。

## 教训来源
- st6 首次意外终止：无 commit 丢全部产出
- dispatch 加教训：即时 commit 勿积累大批量最后提交
- subagent 重派时：dispatch prompt 明示此教训

## 防护措施
| 层级 | 措施 |
|------|------|
| **subagent 自写** | 完成关键产出后立即 `git commit`，不等全部完成 |
| **dispatch 提醒** | 派 subagent 时 prompt 明确："即时 commit，勿积累" |
| **finish 闭环** | finish 时强制 commit（防遗漏） |

## commit 策略
- **小批量多次**：每完成一个产出一个 commit
- **禁积累大批量**：禁等全部完成再最后 commit
- **标记清晰**：commit message 含 `feat:`, `fix:`, `refactor:` 前缀

## 适用场景
- 所有 subagent 派发（dispatch、researcher、任何 agent）
- 长任务（>30 min）必须中途 checkpoint commit

## 关联
- 参考 `core 层索引` 中的 ops 相关规则
