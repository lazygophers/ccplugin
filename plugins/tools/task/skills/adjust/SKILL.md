---
description: 调整修正，分析失败原因并制定修正策略
memory: project
color: yellow
model: sonnet
permissionMode: plan
background: false
context: fork
agent: task:adjust
---

# Adjust Skill

## 执行流程

> 分析校验失败原因，制定修正策略
> **与用户交互确认调整方向，所有修复必须遵循项目现有风格**
> **停滞检测：相同错误 3 次或 A→B→A→B 振荡 → 立即 ask_user**

```python
# 读取校验结果和上下文
verify_result = environment["verify_result"]
align_file = f".lazygophers/tasks/{task_id}/align.json"
context_file = f".lazygophers/tasks/{task_id}/context.json"
align = read_json(align_file)
context = read_json(context_file)

# 获取锁定的项目风格
code_style = align.get("code_style_follow", {})

# 读取任务文件（如果存在）
task_file = f".lazygophers/tasks/{task_id}/task.json"
existing_plan = read_json(task_file) if exists(task_file) else None

# 无限制重试循环：直到用户确认调整方向
while True:
    # === 迭代开始 ===
    
    # 阶段1：分析失败原因（<2分钟）
    root_cause = analyze_failure({
        "verify_result": verify_result,
        "failed_criteria": verify_result.get("failed_criteria", []),
        "existing_plan": existing_plan,
        "code_style": code_style  # 考虑风格是否符合
    })
    
    # 阶段2：分类失败类型
    failure_type = classify_failure({
        "root_cause": root_cause,
        "context": context
    })
    
    # 阶段3：向用户展示分析结果并确认调整方向
    analysis_response = AskUserQuestion(
        questions=[{
            "question": f"失败分析结果：\\n\\n{format_failure_analysis(root_cause, failure_type)}\\n\\n是否遵循此分析？如需调整请说明。",
            "header": "失败分析确认",
            "options": [
                {"label": "确认分析", "description": "分析正确，按此调整"},
                {"label": "需要修正", "description": "分析有误，需要调整"}
            ],
            "multiSelect": False
        }]
    )
    
    # 如果用户认为分析有误，收集新的分析思路
    if analysis_response["失败分析确认"] == "需要修正":
        correction = AskUserQuestion(
            questions=[{
                "question": "请说明正确的失败原因",
                "header": "分析修正",
                "options": [
                    {"label": "上下文问题", "description": "对项目理解有误"},
                    {"label": "需求问题", "description": "需求理解有偏差"},
                    {"label": "实现问题", "description": "实现方式有问题"},
                    {"label": "风格问题", "description": "未遵循项目风格"}
                ],
                "multiSelect": True
            }]
        )
        # 根据用户选择重新分类失败类型
        failure_type = reclassify_failure(correction["分析修正"])
        # 重新开始循环，再次确认
        continue
    
    # 阶段4：基于确认的失败类型，确认调整策略
    strategy_response = AskUserQuestion(
        questions=[{
            "question": f"建议调整策略：{format_strategy(failure_type)}\\n\\n注意：所有修复都将遵循项目现有风格。\\n\\n是否采用此策略？",
            "header": "调整策略确认",
            "options": [
                {"label": "确认策略", "description": "策略正确，开始执行"},
                {"label": "调整策略", "description": "需要修改策略"}
            ],
            "multiSelect": False
        }]
    )
    
    # 如果用户需要调整策略
    if strategy_response["调整策略确认"] == "调整策略":
        new_strategy = AskUserQuestion(
            questions=[{
                "question": "请选择正确的调整策略",
                "header": "策略调整",
                "options": [
                    {"label": "补充上下文", "description": "需要更多信息，返回探索"},
                    {"label": "重新对齐", "description": "需求理解有误，返回对齐"},
                    {"label": "重新规划", "description": "计划有问题，重新规划"},
                    {"label": "优化迭代", "description": "当前方案接近，微调优化"}
                ],
                "multiSelect": False
            }]
        )
        # 更新失败类型，重新开始循环
        failure_type = new_strategy["策略调整"]
        continue
    
    # 阶段5：最终确认
    final_response = AskUserQuestion(
        questions=[{
            "question": f"最终确认调整方案：\\n\\n{format_adjustment_plan(failure_type, root_cause)}\\n\\n核心：修复将严格遵循项目现有风格，不引入新风格。\\n\\n确认后将进入相应阶段。",
            "header": "最终确认",
            "options": [
                {"label": "确认执行", "description": "方案正确，开始执行"},
                {"label": "需要调整", "description": "仍需修改方案"}
            ],
            "multiSelect": False
        }]
    )
    
    # 如果用户仍需要调整，继续重试
    if final_response["最终确认"] == "需要调整":
        further_adjustment = AskUserQuestion(
            questions=[{
                "question": "请说明需要如何调整",
                "header": "进一步调整",
                "options": [
                    {"label": "重新分析", "description": "重新审视失败原因"},
                    {"label": "修改策略", "description": "选择不同的调整策略"},
                    {"label": "补充细节", "description": "需要更多细节信息"}
                ],
                "multiSelect": True
            }]
        )
        # 根据用户选择处理
        if "重新分析" in further_adjustment["进一步调整"]:
            # 重新开始循环
            continue
        elif "修改策略" in further_adjustment["进一步调整"]:
            # 更新策略类型，重新开始循环
            failure_type = select_alternative_strategy(failure_type)
            continue
        # 补充细节后继续
    
    # === 用户明确确认"确认执行" ===
    # 退出循环，返回调整结果
    
    # 构建调整配置
    retry_config = build_retry_config({
        "strategy": failure_type,
        "root_cause": root_cause,
        "code_style": code_style  # 确保修复遵循项目风格
    })
    
    return {
        "status": failure_type,
        "reason": root_cause,
        "strategy": build_strategy_description(failure_type, retry_config),
        "retry_config": retry_config
    }
```

## 失败类型与策略

### 上下文缺失
```python
# 特征：对项目理解不足，关键信息缺失
# 策略：返回 explore 重新收集上下文
# 修复时注意：只收集任务相关信息，不改变项目风格
```

### 需求偏差
```python
# 特征：与用户需求理解不一致
# 策略：返回 align 重新对齐需求
# 修复时注意：不改变项目风格确认
```

### 进一步迭代优化
```python
# 特征：当前方案接近正确，需要微调
# 策略：返回 plan 重新规划（调整特定任务）
# 修复时注意：严格遵循项目现有风格
```

### 重新计划
```python
# 特征：方案不可行，需要重新设计
# 策略：返回 plan 完全重新规划
# 修复时注意：遵循项目现有风格
```

## 风格遵守检查

### 分析阶段
- [ ] 失败分析考虑了风格不符合因素
- [ ] 风格问题被识别为可能的失败原因

### 策略制定
- [ ] 调整策略明确要求"遵循项目现有风格"
- [ ] retry_config 包含 code_style 约束
- [ ] 不引入新的风格或模式

### 用户交互
- [ ] 向用户展示分析时强调风格检查
- [ ] 确认策略时强调"遵循现有风格"
- [ ] 最终确认时强调"不引入新风格"

## 检查清单

### 失败分析
- [ ] 根本原因已分析
- [ ] 失败类型已分类
- [ ] 风格符合性已检查

### 用户交互（核心）
- [ ] 已实现无限制重试机制
- [ ] 分析结果已向用户确认
- [ ] 调整策略已向用户确认
- [ ] 最终确认已向用户确认
- [ ] 所有确认都强调"遵循项目现有风格"

### 策略制定
- [ ] 修正策略已确定
- [ ] 可行性已评估
- [ ] 风格约束已包含

### 输出
- [ ] status: 上下文缺失 | 需求偏差 | 进一步迭代优化 | 重新计划
- [ ] reason: 失败原因
- [ ] strategy: 修正策略描述
- [ ] retry_config: 重试配置（含风格约束）

## 输出格式

所有输出必须包含前缀：`[flow·{task_id}·{state}]`

- task_id：当前任务ID
- state：当前状态（adjust）
