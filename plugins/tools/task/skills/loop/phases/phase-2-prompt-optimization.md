<!-- STATIC_CONTENT: Phase 2流程文档，可缓存 -->

# Phase 2: Prompt Optimization

## 概述

提示词优化阶段确保用户输入清晰、完整、可执行，仅在首次迭代时执行。

## 目标

- 质量评估（清晰度、完整性、可执行性）
- 5W1H结构化提问
- WebSearch最新最佳实践（质量<6分）
- 生成优化后的提示词

## 触发条件

- **仅在 iteration=0 执行**
- 后续迭代跳过此阶段

## 执行流程

```python
if iteration == 0:
    print(f"[MindFlow] 正在优化用户提示词...")

    # Phase 1: 质量评估
    quality_assessment = Agent(
        agent="task:prompt-optimizer",
        prompt=f"""评估用户提示词质量：

提示词：{user_task}

评估维度（各10分）：
1. 清晰度：目标是否明确
2. 完整性：是否包含必要信息
3. 可执行性：是否可直接执行

返回：
- 总分（0-30）
- 各维度得分
- 缺失信息列表
"""
    )

    quality_score = quality_assessment["total_score"]
    print(f"[MindFlow·Optimization] 提示词质量：{quality_score}/30")

    # Phase 2: 结构化提问（质量<24分）
    if quality_score < 24:
        print(f"[MindFlow·Optimization] 提示词质量不足，开始结构化提问...")

        # 生成5W1H问题
        questions = generate_5w1h_questions(
            user_task=user_task,
            missing_info=quality_assessment["missing_info"]
        )

        # 向用户提问
        answers = {}
        for question in questions:
            answer = AskUserQuestion(question)
            answers[question["id"]] = answer

        # 整合答案
        enriched_context = integrate_answers(user_task, answers)

    else:
        enriched_context = user_task

    # Phase 3: WebSearch最佳实践（质量<18分）
    if quality_score < 18:
        print(f"[MindFlow·Optimization] 质量严重不足，搜索最新最佳实践...")

        search_query = extract_search_keywords(user_task)
        search_results = WebSearch(
            query=f"{search_query} best practices 2025",
            max_results=5
        )

        # 提取关键信息
        best_practices = Agent(
            agent="task:researcher",
            prompt=f"""从搜索结果提取最佳实践：

任务：{user_task}
搜索结果：{search_results}

要求：
1. 提取关键技术选型建议
2. 提取常见陷阱
3. 提取推荐工具/库
"""
        )

        enriched_context += f"\n\n【最佳实践】\n{best_practices['summary']}"

    # Phase 4: 生成优化后的提示词
    optimized_prompt = Agent(
        agent="task:prompt-optimizer",
        prompt=f"""生成优化后的提示词：

原始提示词：{user_task}
补充上下文：{enriched_context}

要求：
1. 清晰的目标陈述
2. 明确的约束条件
3. 可量化的验收标准
4. 参考最佳实践（如有）
5. 保持简洁（≤500字）
"""
    )

    print(f"[MindFlow·Optimization] ✓ 提示词优化完成")
    print(f"优化后的提示词：{optimized_prompt['content']}")

    # 更新任务描述
    user_task = optimized_prompt["content"]
    context["original_task"] = "$ARGUMENTS"  # 保存原始输入
    context["optimized_task"] = user_task

else:
    print(f"[MindFlow] 跳过提示词优化（非首次迭代）")
```

## 质量评估维度

### 1. 清晰度（0-10分）

- **10分**：目标明确，无歧义
- **7-9分**：目标基本明确，有轻微歧义
- **4-6分**：目标模糊，需要澄清
- **0-3分**：目标不清晰，无法理解

### 2. 完整性（0-10分）

- **10分**：包含所有必要信息（what, why, how）
- **7-9分**：包含大部分信息，缺少少量细节
- **4-6分**：缺少关键信息，需要补充
- **0-3分**：信息严重不足，无法执行

### 3. 可执行性（0-10分）

- **10分**：可直接执行，无需额外信息
- **7-9分**：基本可执行，需要少量假设
- **4-6分**：需要补充信息才能执行
- **0-3分**：无法执行，缺少关键依赖

## 5W1H结构化提问

### What（做什么）

- 具体要实现什么功能？
- 期望的输出是什么？

### Why（为什么）

- 这个任务的目的是什么？
- 解决什么问题？

### Who（谁使用）

- 目标用户是谁？
- 有什么权限要求？

### When（何时）

- 有截止时间吗？
- 是否有阶段性目标？

### Where（在哪里）

- 涉及哪些模块/文件？
- 部署在什么环境？

### How（怎么做）

- 有技术栈限制吗？
- 有性能要求吗？

## WebSearch触发条件

当质量评分 < 18 时，搜索最新最佳实践：

1. **提取搜索关键词**
   - 从任务描述中提取核心技术
   - 添加"best practices"、"2025"等关键词

2. **搜索范围**
   - 最新技术文档
   - Stack Overflow讨论
   - GitHub优秀项目

3. **信息提取**
   - 技术选型建议
   - 常见陷阱和解决方案
   - 推荐工具/库

## 输出

- 优化后的任务描述（质量≥8分/维度）
- 澄清的上下文和约束
- 最佳实践参考（如有）

## 示例

### 输入（质量：12/30）

```
实现用户登录
```

### 优化后（质量：27/30）

```
实现基于JWT的用户登录功能

目标：
- 用户可以通过用户名/密码登录
- 登录成功后返回JWT token
- token有效期24小时

技术栈：
- 后端：Go 1.21 + Gin
- 数据库：PostgreSQL
- 加密：bcrypt

验收标准：
1. 登录接口 POST /api/login 返回200和token
2. 密码错误返回401
3. token可以通过中间件验证
4. 单元测试覆盖率>80%

参考最佳实践：
- 使用bcrypt加密密码（cost=10）
- token存储在Authorization header
- 实现refresh token机制
```

## 状态转换

- **优化完成** → 计划设计（Phase 4）或深度研究（Phase 3，如需要）

## 相关文档

- [../prompt-optimizer/SKILL.md](../prompt-optimizer/SKILL.md) - 提示词优化器规范

<!-- /STATIC_CONTENT -->
