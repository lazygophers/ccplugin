# Loop 迭代策略

# Loop 迭代策略和要求 - 基础

本文档包含最小迭代次数、迭代策略、增量交付和快速反馈循环。

## 最小迭代次数

### 动态迭代策略

**最小迭代次数：根据任务复杂度动态确定（1-3 轮），无最大轮数限制**

**复杂度评估维度**（总分 100）：
- 文件变更数（0-25分）：1-2文件=5分，3-5=15分，6+=25分
- 技术栈新颖度（0-25分）：熟悉=5分，新技术=15分，未知=25分
- 任务类型（0-25分）：bug修复=5分，新功能=15分，架构重构=25分
- 质量要求（0-25分）：基础=5分，生产级=15分，企业级=25分

**最小迭代配置**：
- Simple（0-30分）：最小 1 轮
- Moderate（31-60分）：最小 2 轮
- Complex（61-100分）：最小 3 轮

**质量阈值递进**（持续提升，无上限）：
- 轮次 1: 60分（Foundation - 基础）
- 轮次 2: 75分（Enhancement - 增强）
- 轮次 3: 85分（Refinement - 精化）
- 轮次 4+: 90分（Excellence - 卓越，保持）

**原因**：
- 避免一次性完成所有工作
- 每次迭代产生可验证的增量价值
- 通过多轮迭代逐步完善，持续改进直到完美
- 快速反馈，及时发现问题
- 根据任务复杂度调整最小迭代次数，但不限制最大轮数
- 质量驱动终止，而非轮数限制

**标准迭代节奏**（以 3 轮为例）：
- 首次迭代：快速构建核心功能（Foundation - 60分）
- 第二次迭代：完善细节和测试（Enhancement - 75分）
- 第三次迭代：优化和最终验证（Refinement - 85分）

### 特殊情况

**可以少于 3 次迭代的场景**：
- 特别简单的任务（如单文件小改动）
- 用户明确要求一次完成
- 任务本身就是原子性的（无法再分解）

**示例**：
```python
# 简单任务示例
task = "修改配置文件中的一个参数"
# 这种任务可以一次完成，不需要多次迭代
```

## 迭代策略

### 首次迭代（Foundation - 基础）

**目标**：建立基础，验证可行性

**关注点**：
- 完成核心功能
- 建立基础架构
- 验证技术可行性
- 搭建测试框架

**验收标准**：
- 核心功能可运行
- 基本测试通过
- 架构清晰合理

**示例**：
```
任务：实现用户认证功能

首次迭代目标：
- T1: 实现基础的 JWT 工具
- T2: 创建简单的认证中间件
- T3: 编写核心功能测试

不包括：
- 边界测试
- 性能优化
- 完整文档
```

### 第二次迭代（Enhancement - 增强）

**目标**：完善功能，提高质量

**关注点**：
- 完善功能细节
- 添加边界测试
- 修复首次迭代的问题
- 提高代码质量

**验收标准**：
- 功能完整
- 测试覆盖率达标（≥ 90%）
- 无明显缺陷

**示例**：
```
第二次迭代目标：
- T1: 添加 Token 过期处理
- T2: 实现权限检查
- T3: 补充边界测试（空值、超长输入）
- T4: 修复首次迭代发现的 Bug
```

### 第三次迭代（Refinement - 优化）

**目标**：优化和重构，达到生产标准

**关注点**：
- 代码优化和重构
- 补充文档
- 性能优化
- 最终验证

**验收标准**：
- 代码质量优秀
- 文档完整
- 性能达标
- 所有验收标准通过

**示例**：
```
第三次迭代目标：
- T1: 重构复杂函数
- T2: 优化数据库查询性能
- T3: 补充 API 文档
- T4: 最终集成测试
```

## 增量交付原则

### 渐进式交付

**每次迭代都产生可交付的增量**：
- 迭代 1：可运行的最小功能
- 迭代 2：功能完整的版本
- 迭代 3：生产级别的版本

**避免**：
- 前两次迭代没有可交付成果
- 所有工作集中在最后一次迭代
- 迭代之间没有明显的价值增量

### 价值优先

**优先交付高价值功能**：
1. 核心功能（必须有）
2. 重要功能（应该有）
3. 辅助功能（可以有）

**示例**：
```
用户认证功能优先级：
1. 核心：登录、登出、Token 验证 → 迭代 1
2. 重要：权限检查、Session 管理 → 迭代 2
3. 辅助：OAuth 集成、多因素认证 → 迭代 3（或后续）
```

## 快速反馈循环

### 迭代内反馈

**执行中的反馈**：
- 实时监控任务进度
- 及时发现执行问题
- 快速调整策略

**执行后的反馈**：
- 验证验收标准
- 运行测试套件
- 检查代码质量

### 迭代间反馈

**上一次迭代的教训**：
- 哪些做得好（继续保持）
- 哪些有问题（需要改进）
- 哪些可以优化（持续改进）

**调整下一次迭代**：
```python
def plan_next_iteration(previous_iteration):
    """基于上次迭代结果规划下次迭代"""

    lessons = analyze_iteration(previous_iteration)

    next_plan = {
        "focus_areas": lessons["areas_to_improve"],
        "avoid": lessons["what_went_wrong"],
        "continue": lessons["what_went_well"]
    }

    return next_plan
```

---

# Loop 迭代策略和要求

<overview>

本文档是迭代策略的索引入口。迭代策略决定了任务在多轮执行中如何递进提升质量——从首次迭代的基础实现，到后续迭代的增强和精化。策略内容按复杂度拆分为基础和高级两部分。

</overview>

<navigation>

## 基础迭代

文件：[iteration-basics.md](iteration-basics.md)

包含迭代的核心机制：最小迭代次数的动态计算（基于任务复杂度评估）、每轮迭代的具体策略（首次迭代关注功能实现，第二次关注质量增强，第三次关注精化优化）、增量交付原则（渐进式交付和价值优先排序）、快速反馈循环（迭代内和迭代间的反馈机制）。

## 高级迭代

文件：[iteration-advanced.md](iteration-advanced.md)

包含迭代的进阶策略：终止条件的三种类型（正常终止、提前终止、异常终止）、优化技巧（任务粒度控制、并行度优化、依赖关系优化、资源管理）、持续改进机制（迭代回顾、度量分析、知识积累、质量提升路径）。

</navigation>

---

# Loop 迭代策略和要求 - 高级

本文档包含迭代终止条件、迭代优化技巧和持续改进。

## 迭代终止条件

### 正常终止

**所有验收标准通过**：
- 功能完整
- 测试通过
- 质量达标
- 无遗留问题

**示例**：
```
验收标准检查清单：
✓ 所有任务完成
✓ 测试覆盖率 ≥ 90%
✓ 所有测试通过
✓ Lint 检查 0 错误
✓ 性能满足要求
✓ 文档完整

→ 正常终止迭代
```

### 提前终止

**功能已存在**：
- Planner 发现功能已实现
- 返回空 tasks 数组
- 直接跳转到完成阶段

**用户请求终止**：
- 用户明确要求停止
- 记录当前进度
- 生成终止报告

### 异常终止

**超过最大停滞次数**：
- stalled_count >= max_stalled_attempts
- 建议人工介入
- 输出停滞分析报告

**不可恢复的错误**：
- 系统级别错误
- 无法修复的配置问题
- 资源完全不可用

## 迭代优化技巧

### 任务粒度控制

**合适的任务粒度**：
- 单个任务执行时间：10-30 分钟
- 太大：难以并行，风险高
- 太小：管理成本高，效率低

**拆分过大的任务**：
```python
# 原任务（太大）
task = "实现完整的用户管理模块"

# 拆分后（合适）
tasks = [
    "实现用户模型和数据库操作",
    "实现用户 CRUD API",
    "实现用户认证逻辑",
    "编写用户模块测试"
]
```

### 并行度优化

**最大化并行度**：
- 识别无依赖的任务
- 优先并行执行
- 最多 2 个任务并行

**减少等待时间**：
```python
# 顺序执行（慢）
execute(T1)  # 10 分钟
execute(T2)  # 10 分钟
# 总时间：20 分钟

# 并行执行（快）
parallel_execute([T1, T2])  # max(10, 10) = 10 分钟
# 总时间：10 分钟
```

### 依赖关系优化

**最小化依赖**：
- 减少不必要的依赖
- 打破循环依赖
- 使用接口隔离

**并行友好的依赖**：
```
❌ 不好的依赖设计：
T1 → T2 → T3 → T4 → T5
（完全串行，无法并行）

✓ 好的依赖设计：
     ┌─ T2
T1 ─┤
     └─ T3 ─┬─ T4
            └─ T5
（部分并行，效率更高）
```

### 任务优先级

**定义优先级**：
```python
task_priorities = {
    "critical": 4,  # 关键任务，必须立即执行
    "high": 3,      # 高优先级任务
    "medium": 2,    # 中等优先级任务
    "low": 1        # 低优先级任务
}
```

**优先级调度**：
```python
def schedule_tasks(tasks):
    """按优先级调度任务"""
    # 按优先级排序
    sorted_tasks = sorted(
        tasks,
        key=lambda t: task_priorities.get(t.priority, 2),
        reverse=True
    )

    # 优先执行高优先级任务
    for task in sorted_tasks:
        if can_execute(task):
            execute(task)
```

### 资源管理

**合理分配资源**：
```python
resource_allocation = {
    "cpu_intensive": {"cpu": 2, "memory": "2GB"},
    "io_intensive": {"cpu": 1, "memory": "1GB"},
    "memory_intensive": {"cpu": 1, "memory": "4GB"}
}

def allocate_resources(task):
    """为任务分配资源"""
    task_type = classify_task(task)
    return resource_allocation.get(task_type)
```

**避免资源竞争**：
```python
def check_resource_conflict(task1, task2):
    """检查任务间是否有资源冲突"""
    # 检查文件冲突
    if set(task1.files) & set(task2.files):
        return True

    # 检查 Agent 冲突
    if task1.agent == task2.agent and not supports_parallel(task1.agent):
        return True

    return False
```

## 持续改进

### 迭代回顾

**每次迭代后的回顾**：
1. 什么做得好？
2. 什么可以改进？
3. 下次如何做得更好？

**记录改进点**：
```python
iteration_retrospective = {
    "what_went_well": [
        "并行执行节省了时间",
        "测试覆盖率达到 95%"
    ],
    "what_to_improve": [
        "任务粒度太大，下次拆分更细",
        "依赖关系可以进一步优化"
    ],
    "action_items": [
        "创建任务拆分检查清单",
        "建立依赖关系审查流程"
    ]
}
```

### 度量和分析

**关键指标**：
- 迭代完成时间
- 任务返工率
- 并行度利用率
- 测试覆盖率

**趋势分析**：
```python
def analyze_iteration_trend(iterations):
    """分析迭代趋势"""
    metrics = {
        "avg_time": average([i.duration for i in iterations]),
        "success_rate": sum([i.success for i in iterations]) / len(iterations),
        "improvement": calculate_improvement(iterations)
    }
    return metrics
```

### 学习和知识积累

**记录最佳实践**：
```python
def record_best_practice(iteration):
    """记录迭代中的最佳实践"""
    best_practices = {
        "task_decomposition": extract_decomposition_pattern(iteration),
        "dependency_design": extract_dependency_pattern(iteration),
        "testing_strategy": extract_testing_pattern(iteration)
    }

    # 保存到知识库
    save_to_knowledge_base(best_practices)
```

**知识复用**：
```python
def apply_learned_patterns(task):
    """应用已学习的模式"""
    # 查找相似任务的模式
    similar_patterns = find_similar_patterns(task)

    # 应用最佳实践
    for pattern in similar_patterns:
        if pattern.applicable(task):
            apply_pattern(task, pattern)
```

### 质量提升

**质量目标递进**：
```python
quality_targets = {
    1: {"test_coverage": 80, "code_quality": 70},
    2: {"test_coverage": 90, "code_quality": 80},
    3: {"test_coverage": 95, "code_quality": 90}
}

def get_quality_target(iteration):
    """获取当前迭代的质量目标"""
    return quality_targets.get(iteration, quality_targets[3])
```

**质量检查**：
```python
def quality_gate_check(iteration, results):
    """质量门控检查"""
    target = get_quality_target(iteration)

    # 检查测试覆盖率
    if results["test_coverage"] < target["test_coverage"]:
        return False, f"测试覆盖率不达标：{results['test_coverage']}% < {target['test_coverage']}%"

    # 检查代码质量
    if results["code_quality"] < target["code_quality"]:
        return False, f"代码质量不达标：{results['code_quality']} < {target['code_quality']}"

    return True, "质量门控通过"
```
