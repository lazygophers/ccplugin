---
name: verify
description: 结果验证规范 - 验收标准检查、质量验证的执行规范
user-invocable: false
context: fork
---

# 结果验证规范

结果验证是 loop 循环的第五步，负责检查任务执行结果是否符合验收标准。

## 执行目标

- 验证所有任务的验收标准是否通过
- 记录验证结果
- 决定是否进入下一轮迭代

## 执行步骤

### 1. 检查验收标准

使用工具：TaskList, TaskGet

检查每个已完成任务的验收标准：
```
tasks = TaskList()
for task in tasks:
    if task.status == "completed":
        # 检查验收标准
        for criterion in task.acceptance_criteria:
            # 验证每一项
```

验收标准类型：
1. **自动化测试**：运行测试命令，检查通过率
2. **命令输出检查**：运行 lint、build 等，检查输出
3. **文件状态检查**：检查文件是否存在、内容是否正确

优先级：自动化测试 > 命令输出检查 > 文件状态检查

### 2. 更新验证结果

使用工具：TaskUpdate

记录每个任务的验证结果：
```
TaskUpdate(
  task_id=task_id,
  metadata={
    "verification_result": {
      "passed": true/false,
      "criteria_results": [
        {"criterion": "...", "passed": true/false, "details": "..."}
      ],
      "verified_at": timestamp
    }
  }
)
```

## 验收标准规范

### 好的验收标准

必须满足：
- **可自动化**：能通过运行命令或脚本验证
- **可观测**：有明确的通过/失败判断
- **独立**：不依赖其他标准的结果
- **具体**：描述具体的检查项

示例：
```
验收标准：
- [ ] pytest tests/test_user.py 全部通过
- [ ] ruff check src/ 无错误
- [ ] API 返回 200 且包含 user_id 字段
- [ ] 文件 config.yaml 包含 database 配置块
```

### 差的验收标准

避免：
- 模糊描述："测试通过"、"代码规范"、"质量好"
- 主观判断："代码可读性好"、"性能不错"
- 无法验证："用户满意"

## 验证决策

| 结果 | 定义 | 后续动作 |
|------|------|---------|
| **全部通过** | 所有验收标准通过 | loop 结束，任务完成 |
| **部分失败** | 部分验收标准未通过 | 进入步骤 6（失败调整） |

## 输出要求

验证完成后：
1. 所有任务的验证结果已通过 TaskUpdate 记录
2. 明确哪些标准通过、哪些失败
3. 失败的标准记录了失败原因
4. 决定是否进入下一轮迭代

## 注意事项

- 不要跳过验收标准检查
- 不要主观判断，必须可自动验证
- 验证失败时记录详细原因
- 不直接修复问题，而是进入调整阶段
