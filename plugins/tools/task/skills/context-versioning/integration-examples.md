# Context Versioning Integration Examples

## 与 Planner 集成

**规划前自动保存**：信息收集开始前调用 `save_context_snapshot(phase="pre-planning")`，输出快照 ID。

**执行成功后标记**：更新快照 `status="success"` + `completed_at`。

**验证失败时回滚**：检测 `replan_trigger=="verification_failed"` → 查询成功快照 → 询问用户（回滚/保持/对比）→ 回滚则恢复 context 和 iteration。

## 场景示例

| 场景 | 流程 |
|------|------|
| 正常迭代 | 保存快照 v1 → 执行成功 → 标记 success → 下轮保存 v2 |
| 验证失败回滚 | v3 失败 → 列出成功快照(v1,v2) → 用户选择回滚到 v2 → 恢复上下文重新开始 |
| 查询历史 | 列出所有快照及状态（✓success / ✗failed） |
