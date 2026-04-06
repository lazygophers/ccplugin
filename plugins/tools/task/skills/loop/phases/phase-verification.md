
# Verification

系统性检查所有任务执行结果，确保满足验收标准。

## 前置条件

进入验证阶段前，必须确认所有任务已执行完成（plan 文件中所有任务状态为 ✅ 或 ❌）。

## 关联资源

| 类型 | 名称 | 说明 |
|------|------|------|
| Agent | `task:verifier` | 验证代理 |
| Skill | `task:verifier` | 验收验证规范（两阶段验证、证据采集、质量评分） |

## 调用 Agent

```
Agent(subagent_type="task:verifier", prompt="执行结果验证：
  项目路径：{project_path}
  任务ID：{task_id}
  任务目标：{user_task}
  迭代：{iteration}
  计划文件：{plan_md_path}
  规格说明：.lazygophers/tasks/{task_id}/prompt.md
  工作目录：{working_directory}")
```

`规格说明`（prompt.md）包含验收标准，verifier 必须逐条对照判定 passed/failed，并据此决定是否需要下一轮迭代。

Verifier 内部完成：Stage 1 Spec Compliance → Stage 2 Code Quality → 写入 metadata.json result。详见 agent 定义。

**跳过检测**：如果未调用 verifier 就进入下一阶段，将触发验证错误并强制回退。

## 结果处理

读取 metadata.json 的 `result` 字段：

| result.status | 下一步 | 强制要求 |
|---------------|--------|---------|
| `passed` | QualityGate（质量评估） | **必须立即**进入质量评估 |
| `failed` | Adjustment（失败调整） | **必须立即**进入失败调整，传递 `failed_criteria` |

**Verifier→Adjuster 数据传递**：failed 时 result 包含 `failed_criteria[]`（每项含 criterion/actual/expected/suggestion），loop 调用 adjuster 时必须完整传递。

## QualityGate: 质量评估

Verification passed 后，检查 `result.quality_score` 是否达到当前迭代阈值（SSOT 在 flows/verify.md）。

| 条件 | 下一步 | 强制要求 |
|------|--------|---------|
| quality_score >= 阈值 | Cleanup（清理） | **必须立即**进入清理 |
| quality_score < 阈值 | PromptOptimization（改进） | **必须立即**回到提示词评估（非失败，需改进） |

**质量不达标不是失败**，不进入 Adjustment。

## 后续操作

1. 输出 `[MindFlow·{task_id}·结果验证/{iteration}·{status}]` + 验收报告
2. 更新 plan 文件 frontmatter（status + completed_count）
3. **更新索引**：更新 `.lazygophers/tasks/index.json` 中对应任务的 `quality_score`、`phase`、`updated_at`
4. 保存检查点 `save_checkpoint(phase="verification")`

**索引更新**：**禁止使用 Write/Edit 工具，必须使用 Bash 工具执行以下 jq 命令**。

**执行命令**（Bash + jq）：
```bash
TASK_ID="当前任务的task_id"      # 从 context 获取
QUALITY_SCORE=85  # 从 metadata.json 的 result.quality_score 读取
TIMESTAMP=$(date +%s)  # 整数时间戳

jq --arg tid "$TASK_ID" \
   --argjson score "$QUALITY_SCORE" \
   --argjson ts "$TIMESTAMP" \
   '
   map(
     if .task_id == $tid then
       .phase = "verification" |
       .quality_score = $score |
       .updated_at = $ts
     else . end
   ) | sort_by(.updated_at) | reverse
   ' .lazygophers/tasks/index.json > .lazygophers/tasks/index.json.tmp && \
   mv .lazygophers/tasks/index.json.tmp .lazygophers/tasks/index.json
```

**禁止**：验证完成后结束回复。Loop 流程不可中断。
