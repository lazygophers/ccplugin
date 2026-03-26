<!-- STATIC_CONTENT: Phase 3流程文档，可缓存 -->

# Phase 3: Deep Research

## 概述

深度研究阶段在任务复杂度较高或多次失败时触发，通过Explore subagent深入调研最佳实践和技术方案。

## 目标

- 评估任务复杂度（4维度）
- 触发深度研究（自动/手动）
- Explore subagent并行探索
- 整合研究结果

## 触发条件

### 自动触发（复杂度 > 8分）

任务复杂度由4个维度评估（总分10分）：

| 维度 | 权重 | 低复杂度 | 高复杂度 |
|------|------|---------|---------|
| 技术栈陌生度 | 30% | 熟悉的技术 | 新技术/框架 |
| 文件数量 | 25% | 1-3个文件 | 10+个文件 |
| 依赖关系 | 25% | 无外部依赖 | 多个外部服务 |
| 业务复杂度 | 20% | 简单CRUD | 复杂业务逻辑 |

**复杂度计算公式**：

```
complexity = (
    tech_unfamiliarity * 0.3 +
    file_count_score * 0.25 +
    dependency_score * 0.25 +
    business_complexity * 0.2
) * 10
```

**触发阈值**：
- complexity > 8：自动触发深度研究
- complexity 6-8：询问用户是否需要
- complexity < 6：跳过深度研究

### 手动触发

- 连续失败2次后询问用户
- 用户可选择拒绝

## 执行流程

```python
# Phase 1: 复杂度评估
complexity_result = Agent(
    agent="task:complexity-analyzer",
    prompt=f"""评估任务复杂度：

任务：{user_task}

评估维度：
1. 技术栈陌生度（30%）
   - 是否使用新技术/框架？
   - 团队是否熟悉？

2. 文件数量（25%）
   - 预计涉及多少文件？
   - 文件之间的耦合度？

3. 依赖关系（25%）
   - 是否依赖外部服务？
   - 依赖是否稳定？

4. 业务复杂度（20%）
   - 业务逻辑是否复杂？
   - 是否有特殊边界情况？

返回：
- 各维度得分（0-10）
- 综合复杂度（0-10）
- 复杂度等级（low/medium/high）
"""
)

complexity_score = complexity_result["complexity_score"]
complexity_level = complexity_result["complexity_level"]

print(f"[MindFlow·Research] 任务复杂度：{complexity_score}/10 ({complexity_level})")

# Phase 2: 决定是否触发深度研究
should_research = False

if complexity_score > 8:
    # 自动触发
    print(f"[MindFlow·Research] 复杂度较高，自动触发深度研究")
    should_research = True

elif complexity_score >= 6:
    # 询问用户
    user_choice = AskUserQuestion({
        "question": f"任务复杂度为 {complexity_score}/10，是否需要深度研究？",
        "header": "深度研究",
        "multiSelect": False,
        "options": [
            {"label": "是，进行深度研究", "description": "调研最佳实践和技术方案（耗时5-10分钟）"},
            {"label": "否，直接开始规划", "description": "跳过研究阶段"}
        ]
    })
    should_research = (user_choice == "是，进行深度研究")

elif context.get("failure_count", 0) >= 2:
    # 连续失败2次后询问
    print(f"[MindFlow·Research] 检测到连续失败，建议进行深度研究")
    user_choice = AskUserQuestion({
        "question": "任务已连续失败2次，是否需要深度研究来寻找更好的方案？",
        "header": "深度研究",
        "multiSelect": False,
        "options": [
            {"label": "是，进行深度研究", "description": ""},
            {"label": "否，继续当前方案", "description": ""}
        ]
    })
    should_research = (user_choice == "是，进行深度研究")

# Phase 3: 执行深度研究
if should_research:
    print(f"[MindFlow·Research] 正在启动深度研究...")

    # 定义研究方向
    research_directions = [
        {
            "topic": "技术选型与最佳实践",
            "focus": "最新技术栈、工具选择、性能对比"
        },
        {
            "topic": "架构设计与模式",
            "focus": "架构模式、设计模式、代码组织"
        },
        {
            "topic": "常见陷阱与解决方案",
            "focus": "常见错误、边界情况、安全问题"
        }
    ]

    # 并行探索（最多2个方向）
    research_results = []
    for direction in research_directions[:2]:
        result = Agent(
            subagent_type="Explore",
            description=f"研究：{direction['topic']}",
            prompt=f"""深度研究任务相关的{direction['topic']}：

任务：{user_task}
研究重点：{direction['focus']}

要求：
1. 搜索最新文档和最佳实践（2024-2025）
2. 对比不同技术方案的优劣
3. 提取关键发现和建议
4. 生成研究报告（≤500字）
""",
            run_in_background=True if len(research_directions) > 1 else False
        )
        research_results.append(result)

    # 等待所有研究完成
    print(f"[MindFlow·Research] 研究进行中...")
    # (后台任务会自动等待完成)

    # Phase 4: 整合研究结果
    integrated_research = Agent(
        agent="task:researcher",
        prompt=f"""整合深度研究结果：

任务：{user_task}

研究结果：
{format_research_results(research_results)}

要求：
1. 提取关键发现
2. 生成技术选型建议
3. 标注潜在风险
4. 生成综合报告（≤300字）
"""
    )

    print(f"[MindFlow·Research] ✓ 深度研究完成")
    print(f"\n【研究报告】")
    print(integrated_research["summary"])
    print(f"\n【关键发现】")
    for finding in integrated_research["key_findings"]:
        print(f"  • {finding}")
    print(f"\n【技术建议】")
    for recommendation in integrated_research["recommendations"]:
        print(f"  • {recommendation}")

    # 保存到上下文
    context["research_report"] = integrated_research
    context["research_completed"] = True

else:
    print(f"[MindFlow·Research] 跳过深度研究")
    context["research_completed"] = False
```

## 复杂度评估详情

### 技术栈陌生度（30%）

- **0-3分**：团队完全熟悉的技术
- **4-6分**：部分熟悉，需要学习新API
- **7-10分**：全新技术栈，需要深入学习

### 文件数量（25%）

- **0-3分**：1-3个文件
- **4-6分**：4-9个文件
- **7-10分**：10+个文件

### 依赖关系（25%）

- **0-3分**：无外部依赖或依赖稳定
- **4-6分**：依赖少量外部服务
- **7-10分**：依赖多个外部服务，可能不稳定

### 业务复杂度（20%）

- **0-3分**：简单CRUD操作
- **4-6分**：中等复杂度业务逻辑
- **7-10分**：复杂业务逻辑，多种边界情况

## 研究方向

### 1. 技术选型与最佳实践

- 最新技术栈调研
- 工具/库选择对比
- 性能benchmarks
- 社区活跃度

### 2. 架构设计与模式

- 适用的架构模式
- 设计模式推荐
- 代码组织方式
- 模块划分建议

### 3. 常见陷阱与解决方案

- 常见错误和解决方案
- 边界情况处理
- 安全问题注意事项
- 性能优化要点

## 输出

- 深度研究报告
- 关键发现列表
- 技术选型建议
- 潜在风险标注

## 研究报告示例

```markdown
【研究报告】
基于调研，推荐使用JWT + Redis实现用户认证：
- JWT优势：无状态、易扩展、跨域支持
- Redis优势：token黑名单、refresh token存储
- 风险：token泄露、XSS攻击

【关键发现】
  • JWT HS256算法已被RS256取代（2025最佳实践）
  • bcrypt cost建议值已提升至12（2024更新）
  • 需要实现refresh token机制防止长期有效token泄露

【技术建议】
  • 使用golang-jwt/jwt v5库（最新版本）
  • token有效期设置为15分钟，refresh token 7天
  • 实现token rotation机制
  • 添加rate limiting防止暴力破解
```

## 状态转换

- **研究完成** → 计划设计（Phase 4）
- **跳过研究** → 计划设计（Phase 4）

## 相关文档

- [deep-research-triggers.md](../deep-research-triggers.md) - 深度研究触发决策

<!-- /STATIC_CONTENT -->
