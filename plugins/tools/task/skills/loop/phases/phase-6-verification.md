<!-- STATIC_CONTENT: Phase 6流程文档，可缓存 -->

# Phase 6: Verification

系统性检查所有任务执行结果，确保满足验收标准。

## 执行流程

**前置条件检查**：进入验证阶段前，必须确认所有任务已执行完成（plan文件中所有任务状态为✅或❌）。未满足则触发错误。

1. **【强制】调用 verifier agent**：禁止跳过此步骤
   ```
   Agent(agent="task:verifier", prompt="执行结果验证：\n任务目标：{user_task}\n迭代：{iteration}\n要求：1.获取任务状态+验收标准 2.系统性验证 3.回归测试 4.生成验收报告(≤100字) 5.决定状态")
   ```
2. 输出 `[MindFlow·{task}·结果验证/{N}·{status}]` + 验收报告
3. 更新 plan 文件 frontmatter（status + completed_count）
4. 保存检查点 `save_checkpoint(phase="verification")`

**跳过检测机制**：如果未调用 verifier 就进入下一阶段（Phase 7 或 Phase 8），将触发验证错误并强制回退到本阶段。

## 状态转换

| 状态 | 条件 | 质量分 | 下一步 |
|------|------|--------|--------|
| passed | 全部验收通过，无建议 | ≥80 | Phase 8（完成） |
| suggestions | 全部通过，有优化空间 | 60-79 | Phase 4（自动重规划，`replan_trigger="verifier"`） |
| failed | 至少一项验收未通过 | <60 | Phase 7（失败调整） |

suggestions 自动继续，不询问用户。

## 验收维度

功能完整性 | 验收标准(acceptance_criteria) | 代码质量 | 测试覆盖 | 回归测试

详见：[verifier/SKILL.md](../verifier/SKILL.md) | [flows/verify.md](../flows/verify.md)

<!-- /STATIC_CONTENT -->
