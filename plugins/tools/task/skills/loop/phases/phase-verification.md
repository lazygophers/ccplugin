<!-- STATIC_CONTENT: Verification 流程文档，可缓存 -->

# Verification

系统性检查所有任务执行结果，确保满足验收标准。

## 执行流程

**前置条件检查**：进入验证阶段前，必须确认所有任务已执行完成（plan文件中所有任务状态为✅或❌）。未满足则触发错误。

1. **【强制】调用 verifier skill**：禁止跳过此步骤
   ```
   Skill(skill="task:verifier", args="执行结果验证：\n项目路径：{project_path}\n任务ID：{task_id}\n任务目标：{user_task}\n迭代：{iteration}\n计划文件：{plan_md_path}\n工作目录：{working_directory}\n要求：1.获取任务状态+验收标准 2.系统性验证 3.回归测试 4.生成验收报告(≤100字) 5.决定状态")
   ```
2. 输出 `[MindFlow·{task}·结果验证/{N}·{status}]` + 验收报告
3. 更新 plan 文件 frontmatter（status + completed_count）
4. 保存检查点 `save_checkpoint(phase="verification")`

**跳过检测机制**：如果未调用 verifier 就进入下一阶段（Adjustment 或 Finalization），将触发验证错误并强制回退到本阶段。

## 强制状态转换

**验证完成后必须立即按状态分支继续，禁止在本阶段后结束回复：**

| 状态 | 条件 | 质量分 | 下一步 | 强制要求 |
|------|------|--------|--------|---------|
| passed | 全部验收通过，无建议 | ≥80 | Finalization（完成） | **必须立即**进入 Finalizer 清理 |
| suggestions | 全部通过，有优化空间 | 60-79 | Planning（自动重规划） | **必须立即**回到计划设计（`replan_trigger="verifier"`） |
| failed | 至少一项验收未通过 | <60 | Adjustment（失败调整） | **必须立即**进入失败调整 |

suggestions 自动继续，不询问用户。

**禁止**：验证完成后就结束回复。Loop 流程不可中断，必须继续到 Finalizer。

## 验收维度

功能完整性 | 验收标准(acceptance_criteria) | 代码质量 | 测试覆盖 | 回归测试

## Verifier→Adjuster 数据契约

当 Verifier 返回 `failed` 状态时，输出必须包含结构化的失败信息，供 Adjuster 精准定位问题：

```json
{
  "status": "failed",
  "quality_score": 45,
  "failed_criteria": [
    {
      "criterion": "验收标准原文",
      "actual": "实际观察到的结果",
      "expected": "期望的结果",
      "suggestion": "建议的修复方向"
    }
  ]
}
```

**强制规则**：`failed_criteria` 数组不可为空，每项必须包含 `criterion`/`actual`/`expected`/`suggestion` 四个字段。Loop 在调用 Adjuster 时，必须将 `failed_criteria` 完整传递到 Adjuster 的 args 中。

详见：[verifier/SKILL.md](../verifier/SKILL.md) | [flows/verify.md](../flows/verify.md)

<!-- /STATIC_CONTENT -->
