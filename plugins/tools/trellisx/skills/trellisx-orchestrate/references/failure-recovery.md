# 失败回退 + 关闭与回收

planning 阶段必须把"失败时怎么办"写进 design / implement, 不要等出问题再想。

## 失败回退表 (触发 → 一线修复 → 仍失败兜底)

| 失败类型 | 触发 | 一线修复 | 仍失败兜底 (终态) |
| --- | --- | --- | --- |
| 工具瞬时错误 | 网络 / IO 抖动 / index.lock | main 立即重派同一 subtask, 上限 2 次 (指数退避语义) | 转 Blocked, 报错误原文给 main |
| 编译 / 测试 / lint 不通过 | check 红 | 修后重跑, 计入 retry | 3 次累计 → 回 planning 重拆 |
| 资源不可用 (端口占用 / 文件锁) | 资源被占 | 等待 60s 后重试 1 次 | 超时 → 转 Blocked, 报占用方 |
| 依赖产出缺失 | 上游未出产物 | 上游回 Running 补产出 | 本 subtask 转 Blocked, 不重试 |
| 拆分错误 (subtask 过大 / 边界不清) | 边界反复冲突 | — | 中止 → 回 planning 重拆 → 重新编排 |
| sub-agent 错误停机 | agent 崩溃 | 给额外指令恢复 1 次 | spawn 替代者, 弃旧 agent |
| 单 subtask 失败 | subtask 抛错 | 重派该 subtask | 耗尽重试 → 该项标 Blocked, 不阻塞其他 deliverable |
| 用户驳回审批 | 用户 reject | — | 回 planning 修订 PRD / design / implement |

> 同一 subtask 累计失败 3 次禁第 4 次盲目重试; 必须**回 planning 重拆 + 重写 dispatch prompt**, 否则只是反复烧 token。

### 两层重试 (各管一类失败, main 主导)

- **瞬时错误重试** (网络抖动 / 工具超时 / index.lock) — main 立即重派同一 subtask, 默认 2 次, 指数退避语义。
- **main 重派** (逻辑失败: 自验 ✗ / 产物不达标) — 对齐 apply 修复循环, 同一 subtask 累计 ≤3 次, 第 4 次禁盲目重试, 回 planning 重拆。
- 重试计数 per-agent; 全部重试耗尽 → 该 subtask 标 Blocked 上报, 不阻塞其他 deliverable。

## Trellis 特定

| 失败 | 回退到 |
| --- | --- |
| sub-agent 失败 3 次 | 主会话回 trellis Phase 1, 重拆 subtask + 重写 dispatch prompt |
| 实施发现 PRD 缺漏 | 回 planning 改 PRD, 同步改 design / implement / jsonl |
| 检查发现 design 错误 | 回 planning 改 design, 不直接在 implement 阶段绕过 |
| 全 task 卡死 | `task.py status set blocked`, 写阻塞原因到 journal |

## 完成后必跑

trellis Phase 3:
- 3.1 quality verification (实际 check sub-agent)
- 3.2 debug retrospective (按需)
- 3.3 spec update (走 `trellisx-spec` skill 沉淀模式)
- 3.4 commit
- 3.5 wrap-up

每条必跑, 不跑不算完成。

## 关闭与回收

| 执行层 | 关闭动作 |
| --- | --- |
| sub-agent | 任务完成自动回收; 禁 SendMessage 唤醒已完成 sub-agent 跑无关新任务 (应 spawn 新的) |
| agent-team teammate | leader 显式发 shut down; teammate 批准退出 |
| agent-team (整团) | 所有 teammate 关闭后 leader 执行 cleanup, 删共享资源 |
| fork | 完成后关闭对应面板行 |
| 手动 worktree 会话 | `git worktree remove <path>` |

## planning 阶段写什么

每条 subtask 在 implement.md 内必带 rollback 字段:

```
回滚: <commit hash 或具体步骤>
```

design.md 模块表加风险/缓解列, 或独立"风险"节:

```markdown
## 风险

| 风险 | 影响 | 缓解 | 触发条件 |
| --- | --- | --- | --- |
| DB migration 失败 | 数据损坏 | 加 backup 步骤 + 回滚脚本 | 任何 SQL 错误 |
```

## 自检

- [ ] 每条 subtask 有 rollback 字段
- [ ] 不可回滚操作有 review gate 前置
- [ ] design 列出 ≥ 3 个最高风险及缓解
- [ ] 失败上报路径明确 (谁看 / 在哪 / 多久内响应)
