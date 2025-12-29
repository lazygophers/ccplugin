---
name: sprint-planning
description: Scrum Sprint 规划和执行指南
auto-activate: file-pattern
file-patterns:
  - "**/sprint*.md"
  - "**/SPRINT*.md"
  - "**/planning*.md"
tags:
  - sprint
  - scrum
  - agile
---

# Sprint Planning Skill

本 Skill 提供 Scrum Sprint 规划和执行的最佳实践。

## Sprint 规划流程

### 准备阶段（Sprint 前 1-2 天）

1. **整理 Product Backlog**
   ```python
   # 查看所有 backlog 任务
   task_list(priority=4, limit=100)

   # 按优先级排序
   # 确保高价值任务在前
   ```

2. **评估团队容量**
   - 计算可用工作日
   - 考虑假期、会议等
   - 预留 20% buffer

3. **准备用户故事**
   - 确保故事符合 INVEST 原则
   - 验收标准清晰
   - 技术依赖明确

### 规划会议（2-4 小时）

#### 第一部分：What（做什么）

1. **创建 Sprint Epic**
   ```python
   task_create(
       title="Sprint 23: 用户认证系统优化",
       description="""
       时间: 2024-01-15 ~ 2024-01-29 (2周)
       目标: 优化登录流程，提升安全性
       团队: 5 人 × 10 天 = 50 人天
       """,
       task_type="epic",
       priority=1,
       tags=["sprint-23", "q1-2024"]
   )
   # 记录返回的 Epic ID: tk-sprint23
   ```

2. **选择用户故事**
   ```python
   # 从 backlog 选择高优先级故事
   stories = [
       {
           "title": "用户故事：双因素认证",
           "estimate": "8 人天",
           "value": "high"
       },
       {
           "title": "用户故事：记住登录状态",
           "estimate": "5 人天",
           "value": "medium"
       }
   ]

   for story in stories:
       task_create(
           title=story["title"],
           task_type="feature",
           priority=1,
           tags=["sprint-23", "user-story"]
       )
   ```

#### 第二部分：How（怎么做）

1. **拆分技术任务**
   ```python
   # 用户故事 1：双因素认证
   tasks = [
       {
           "title": "设计双因素认证数据模型",
           "assignee": "backend@example.com",
           "estimate": "2 人天"
       },
       {
           "title": "实现 TOTP 生成和验证",
           "assignee": "backend@example.com",
           "estimate": "3 人天"
       },
       {
           "title": "开发双因素设置页面",
           "assignee": "frontend@example.com",
           "estimate": "3 人天"
       }
   ]

   for task in tasks:
       task_id = task_create(
           title=task["title"],
           task_type="task",
           priority=1,
           assignee=task["assignee"],
           tags=["sprint-23", "2fa"]
       )

       # 关联到用户故事
       task_dep_add(
           task_id=task_id,
           depends_on_id="tk-story-2fa",
           dep_type="parent-child"
       )
   ```

2. **建立依赖关系**
   ```python
   # 前端依赖后端 API
   task_dep_add(
       task_id="tk-frontend-2fa-ui",
       depends_on_id="tk-backend-2fa-api",
       dep_type="blocks",
       reason="前端需要后端 API 完成后才能集成"
   )
   ```

3. **分配任务**
   ```python
   # 根据专长和工作量分配
   # 确保每个人的任务量适中
   ```

### Sprint 目标

定义清晰的 Sprint 目标：
```
# ✅ 好的 Sprint 目标
"实现双因素认证，提升账户安全性"
"完成支付流程重构，减少支付失败率"

# ❌ 不好的 Sprint 目标
"完成 10 个任务"
"修复一些 bug"
```

## Sprint 执行

### 每日站会（15 分钟）

**会前准备**：
```python
# 查看进行中的任务
task_list(
    status="in_progress",
    tags=["sprint-23"],
    brief=False
)

# 查看阻塞任务
task_blocked()

# 查看就绪任务
task_ready(tags=["sprint-23"], limit=10)
```

**站会内容**：
1. 昨天完成了什么？（已关闭的任务）
2. 今天计划做什么？（准备开始的就绪任务）
3. 有什么阻碍？（blocked 任务）

**会后行动**：
```python
# 开始今天的任务
task_update(task_id="tk-xxx", status="in_progress")

# 解决阻碍
# 如果阻碍解除，更新任务状态
task_update(task_id="tk-blocked", status="open")
```

### 任务板管理

**看板列**：
```
Backlog | Ready | In Progress | Review | Done
```

**映射到状态**：
```
Backlog       → status: open (不在当前 Sprint)
Ready         → status: open + tags: sprint-23 + 无阻塞依赖
In Progress   → status: in_progress
Review        → status: in_progress + tags: review-needed
Done          → status: closed
```

### 中期检查（Sprint 中点）

**燃尽图检查**：
```python
# 统计完成情况
task_stats()

# 检查是否按计划进行
closed = task_list(status="closed", tags=["sprint-23"])
total = task_list(tags=["sprint-23"])

# 如果完成度 < 40%，需要调整
```

**风险识别**：
```python
# 查看高优先级的阻塞任务
task_list(
    status="blocked",
    priority=0,
    tags=["sprint-23"]
)

# 评估是否需要移除某些任务
```

## Sprint 评审

### 准备 Demo（Sprint 最后一天）

1. **确认完成的功能**
   ```python
   # 列出已完成的用户故事
   task_list(
       status="closed",
       task_type="feature",
       tags=["sprint-23"],
       brief=False
   )
   ```

2. **准备演示环境**
   - 部署到演示环境
   - 准备测试数据
   - 验证功能正常

3. **准备展示脚本**
   - 按用户价值排序
   - 突出亮点
   - 准备问题回答

### 评审会议（1-2 小时）

**展示内容**：
1. Sprint 目标回顾
2. 完成的用户故事演示
3. 未完成的任务说明
4. 收集反馈

**会后行动**：
```python
# 根据反馈创建新任务
task_create(
    title="根据评审反馈：优化登录按钮位置",
    task_type="task",
    priority=2,
    tags=["feedback", "sprint-24"]
)
```

## Sprint 回顾

### 准备数据（评审会后）

```python
# Sprint 统计
task_stats()

# 完成的任务
completed = task_list(status="closed", tags=["sprint-23"])

# 未完成的任务
incomplete = task_list(
    status=["open", "in_progress"],
    tags=["sprint-23"]
)

# 阻塞任务分析
blocked_history = task_list(
    status="blocked",
    tags=["sprint-23"]
)
```

### 回顾会议（45-60 分钟）

#### 1. 数据回顾（10 分钟）
- 计划 vs 实际完成
- 速度趋势
- 阻塞原因分析

#### 2. 好的方面（15 分钟）
- 什么做得好？
- 哪些实践应该保持？

#### 3. 改进空间（15 分钟）
- 什么可以改进？
- 遇到了哪些问题？

#### 4. 行动项（15 分钟）
```python
# 创建改进任务
task_create(
    title="改进：引入代码评审检查清单",
    task_type="chore",
    priority=1,
    tags=["improvement", "sprint-24"]
)
```

### 处理未完成任务

```python
# 选项 1：移动到下一个 Sprint
task_update(
    task_id="tk-incomplete",
    tags=["sprint-24"]  # 移除 sprint-23，添加 sprint-24
)

# 选项 2：重新评估优先级
task_update(
    task_id="tk-incomplete",
    priority=4,  # 降低到 backlog
    tags=["backlog"]  # 移除 Sprint 标签
)

# 选项 3：拆分任务
# 已完成部分关闭，剩余部分创建新任务
task_close(task_id="tk-incomplete")
task_create(
    title="完成剩余工作：xxx",
    tags=["sprint-24"]
)
```

## Sprint 指标

### 关键指标

1. **速度（Velocity）**
   ```
   速度 = Sprint 中完成的故事点数
   用于预测未来 Sprint 容量
   ```

2. **燃尽图（Burndown Chart）**
   ```
   跟踪剩余工作量
   识别进度偏差
   ```

3. **完成率**
   ```
   完成率 = 完成任务数 / 计划任务数
   目标: >80%
   ```

4. **阻塞时间**
   ```
   任务处于 blocked 状态的总时间
   目标: 最小化
   ```

### 数据收集

```python
# 每日记录
daily_stats = {
    "date": "2024-01-15",
    "remaining_tasks": 15,
    "completed_tasks": 10,
    "blocked_tasks": 2
}

# Sprint 结束统计
sprint_metrics = {
    "planned_tasks": 25,
    "completed_tasks": 22,
    "completion_rate": "88%",
    "avg_cycle_time": "2.5 days",
    "blocked_incidents": 5
}
```

## 最佳实践

### Do's ✅

1. **明确的 Sprint 目标**
   - 业务价值导向
   - 可测量
   - 团队共识

2. **合理的任务拆分**
   - 任务不超过 2-3 天
   - 独立可验证
   - 有清晰的验收标准

3. **积极沟通**
   - 及时更新任务状态
   - 主动报告阻碍
   - 寻求帮助

4. **定期检查**
   - 每日站会
   - 中期检查
   - 评审和回顾

5. **持续改进**
   - 记录问题
   - 实施改进
   - 跟踪效果

### Don'ts ❌

1. **避免 Sprint 中途增加任务**
   - 保持 Sprint 目标稳定
   - 紧急任务除外

2. **避免跳过站会**
   - 保持团队同步
   - 及时发现问题

3. **避免忽略阻碍**
   - 及时解决阻塞
   - 寻求帮助

4. **避免过度承诺**
   - 根据历史速度规划
   - 留有缓冲时间

5. **避免跳过回顾**
   - 回顾是改进的基础
   - 每个 Sprint 都要回顾

## 常见问题

### Q: Sprint 中发现紧急 bug 怎么办？

**A**: 评估紧急程度
```python
if severity == "critical":
    # 立即处理，可能需要移除低优先级任务
    task_create(
        title="紧急修复：xxx",
        task_type="bug",
        priority=0,
        tags=["sprint-23", "hotfix"]
    )
else:
    # 加入下一个 Sprint
    task_create(
        title="修复：xxx",
        task_type="bug",
        priority=2,
        tags=["sprint-24"]
    )
```

### Q: 任务完成度低于预期怎么办？

**A**: 中期调整策略
1. 分析原因（技术难度/估算偏差/外部依赖）
2. 移除低优先级任务
3. 寻求帮助（跨团队协作）
4. 调整下一个 Sprint 的容量规划

### Q: 团队成员技能不均衡怎么办？

**A**: 平衡分配和成长
1. 配对编程
2. 知识分享会
3. 技能矩阵规划
4. 逐步增加难度

## 工具和模板

### Sprint Planning Checklist

```markdown
## Sprint Planning 检查清单

### 准备阶段
- [ ] Product Backlog 已优先级排序
- [ ] 用户故事有验收标准
- [ ] 团队容量已计算
- [ ] 依赖关系已识别

### 规划会议
- [ ] Sprint 目标已定义
- [ ] 用户故事已选择
- [ ] 技术任务已拆分
- [ ] 依赖关系已建立
- [ ] 任务已分配

### 执行阶段
- [ ] 每日站会正常进行
- [ ] 任务状态及时更新
- [ ] 阻碍及时解决
- [ ] 中期检查已完成

### 结束阶段
- [ ] Sprint 评审已完成
- [ ] 反馈已记录
- [ ] Sprint 回顾已完成
- [ ] 改进措施已制定
- [ ] 未完成任务已处理
```

## 相关资源

- [任务管理最佳实践](./task-management.md)
- [Scrum 指南](https://scrumguides.org/)
- [敏捷宣言](https://agilemanifesto.org/)

---

**最后更新**: 2024-01-15
**版本**: 1.0.0
