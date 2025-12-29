---
name: task-management
description: Task Plugin 任务管理最佳实践和规范
auto-activate: always
tags:
  - task
  - management
  - workflow
---

# Task Management Skill

本 Skill 定义了使用 Task Plugin 进行任务管理的最佳实践、命名规范和工作流程。

## 核心原则

### 1. 任务命名规范

**标题格式**：
- ✅ 好：`实现用户登录功能`
- ✅ 好：`修复 Safari 浏览器登录页面显示问题`
- ❌ 差：`登录`
- ❌ 差：`bug`

**规则**：
- 使用动词开头（实现、修复、优化、添加、更新、删除）
- 简洁明确（建议 5-20 字）
- 包含关键信息（功能名称、问题描述）
- 避免技术细节（留给描述字段）

### 2. 优先级分配

```
0 (critical)  - 生产环境故障、安全漏洞、数据丢失风险
1 (high)      - 重要功能、阻塞其他任务、计划内的关键需求
2 (medium)    - 一般任务、常规功能开发
3 (low)       - 优化改进、非紧急 bug
4 (backlog)   - 待定需求、未来考虑的功能
```

**分配原则**：
- 默认使用 medium (2)
- critical (0) 限制在 <5% 任务
- 定期评审 backlog (4) 任务

### 3. 任务类型选择

```
bug      - 软件缺陷、错误行为
feature  - 新功能、用户故事
task     - 技术任务、开发工作
epic     - 大型功能集、项目阶段
chore    - 维护任务、工具升级
```

**选择指南**：
- 用户报告的问题 → `bug`
- 产品需求的新功能 → `feature`
- 技术债务、重构 → `task`
- 多个相关任务的集合 → `epic`
- 升级依赖、配置变更 → `chore`

### 4. 标签使用

**推荐标签体系**：
```
# 按领域
frontend, backend, database, api, ui, mobile

# 按 Sprint
sprint-23, sprint-24, q1-2024, q2-2024

# 按优先级辅助
p0, p1, p2, hotfix, urgent

# 按状态辅助
blocked, review-needed, testing, docs-needed

# 按功能模块
auth, payment, user-mgmt, analytics, notification
```

**规则**：
- 每个任务 3-5 个标签
- 使用小写和连字符
- 保持团队一致性

## 工作流程

### 任务生命周期

```
创建 (open)
  ↓
开始工作 (in_progress)
  ↓
[遇到阻塞] → 标记为阻塞 (blocked) → [阻塞解除] → 继续工作
  ↓
完成 (closed)
```

### 每日工作流

1. **早上**：查看就绪任务
   ```
   使用 task_ready 查找可以开始的任务
   选择最高优先级任务
   更新状态为 in_progress
   ```

2. **工作中**：及时更新状态
   ```
   遇到阻塞：更新为 blocked + 添加原因
   发现新任务：创建并建立依赖关系
   需要信息：添加到描述中
   ```

3. **完成时**：关闭任务
   ```
   task_close 标记完成
   检查依赖任务是否可以解除阻塞
   更新相关文档
   ```

### Sprint 规划流程

1. **Sprint 开始前**：
   ```python
   # 1. 创建 Sprint Epic
   task_create(
       title="Sprint 23",
       task_type="epic",
       tags=["sprint-23", "q1-2024"]
   )

   # 2. 从 backlog 选择任务
   task_list(priority=4, limit=50)

   # 3. 提升优先级并加入 Sprint
   task_update(task_id="tk-xxx", priority=2, tags=["sprint-23"])

   # 4. 拆分大任务
   # ... 创建子任务并建立依赖
   ```

2. **Sprint 进行中**：
   ```python
   # 每日站会
   task_list(status="in_progress", tags=["sprint-23"])
   task_blocked()
   task_ready(tags=["sprint-23"])
   ```

3. **Sprint 结束**：
   ```python
   # 查看完成情况
   task_stats()
   task_list(status="closed", tags=["sprint-23"])

   # 处理未完成任务
   task_list(status="open", tags=["sprint-23"])
   # 移动到下一个 Sprint 或 backlog
   ```

## 依赖管理规范

### 依赖类型选择

```
blocks          - A 必须等 B 完成（硬阻塞）
                  示例：前端 API 调用依赖后端 API 实现

related         - A 和 B 相关但不阻塞（软关联）
                  示例：同一功能的文档任务和代码任务

parent-child    - A 是 B 的子任务（层级关系）
                  示例：Epic 和其子任务

discovered-from - 在做 A 时发现了 B（发现关系）
                  示例：开发中发现需要先重构某个模块
```

### 避免循环依赖

**禁止**：
```
A depends on B
B depends on C
C depends on A  ❌ 循环依赖
```

**解决方案**：
1. 重新评估依赖关系
2. 拆分任务打破循环
3. 使用 `related` 代替 `blocks`

### 依赖最佳实践

1. **最小化依赖**：只在真正阻塞时使用 `blocks`
2. **明确原因**：使用 `reason` 参数说明依赖原因
3. **定期检查**：使用 `task_blocked` 查看阻塞情况
4. **及时解除**：完成任务后检查是否有依赖可以解除

## 团队协作规范

### 任务分配

**原则**：
- 明确负责人（每个任务只有一个 assignee）
- 根据专长分配（前端/后端/全栈）
- 考虑工作量平衡
- 尊重个人意愿

**方法**：
```python
# 创建时分配
task_create(
    title="实现用户注册 API",
    assignee="backend@example.com",
    tags=["backend", "api"]
)

# 后续分配
task_update(
    task_id="tk-xxx",
    assignee="developer@example.com"
)
```

### 沟通规范

1. **任务描述要详细**：
   - 背景信息
   - 验收标准
   - 参考资料
   - 预期产出

2. **及时更新进度**：
   - 状态变更后立即更新
   - 遇到问题在描述中记录
   - 完成后添加总结

3. **依赖沟通**：
   - 创建依赖前与相关人员确认
   - 阻塞时及时通知被依赖方
   - 定期同步依赖状态

## 性能和规模

### 大型项目建议

对于 >1000 个任务的项目：

1. **使用过滤器**：
   ```python
   # 避免
   task_list()  # 返回所有任务

   # 推荐
   task_list(status="open", limit=20)
   ```

2. **定期归档**：
   ```python
   # 定期关闭旧的已完成任务
   # 或移动到历史数据库
   ```

3. **分层管理**：
   ```python
   # 使用 epic 组织大型功能
   # 使用标签管理子项目
   ```

4. **批量操作**：
   ```python
   # 使用脚本进行批量更新
   # 而不是逐个手动操作
   ```

## 数据质量

### 定期维护

**每周**：
- 检查 blocked 任务是否仍然阻塞
- 清理重复或过时的任务
- 更新过期的优先级

**每月**：
- 审查 backlog 任务
- 归档旧的已完成任务
- 检查依赖关系的有效性

**每季度**：
- 评审标签体系
- 优化工作流程
- 总结最佳实践

### 数据验证

使用 `task_stats` 定期检查：
- blocked 任务比例（应 <10%）
- backlog 任务数量（避免无限增长）
- 平均完成时间（识别效率问题）
- 任务类型分布（是否平衡）

## 常见错误

### ❌ 错误做法

1. **不更新任务状态**
   ```
   开始工作但不标记为 in_progress
   完成工作但不关闭任务
   ```

2. **过度依赖**
   ```
   每个任务都依赖其他任务
   创建不必要的 blocks 依赖
   ```

3. **优先级滥用**
   ```
   所有任务都是 critical
   从不使用 medium 或 low
   ```

4. **标题不清晰**
   ```
   "bug"
   "fix"
   "update"
   ```

5. **忽略验收标准**
   ```
   不定义何时算完成
   标准模糊或不可测
   ```

### ✅ 正确做法

1. **及时更新状态**
   ```python
   # 开始工作
   task_update(task_id="tk-xxx", status="in_progress")

   # 完成工作
   task_close(task_id="tk-xxx")
   ```

2. **合理使用依赖**
   ```python
   # 只在真正阻塞时使用 blocks
   task_dep_add(
       task_id="frontend-task",
       depends_on_id="backend-api",
       dep_type="blocks",
       reason="前端需要后端 API 完成后才能开发"
   )
   ```

3. **合理分配优先级**
   ```python
   # 根据紧急程度和重要性
   task_create(
       title="修复支付失败问题",
       priority=0  # critical - 影响收入
   )
   ```

4. **清晰的标题**
   ```python
   task_create(
       title="实现用户密码重置功能",
       description="用户可以通过邮箱重置密码...",
       acceptance_criteria="1. 发送重置邮件\n2. 验证重置链接\n3. 更新密码"
   )
   ```

## 与其他工具集成

### Context Plugin
```python
# 将任务上下文保存到 Context Plugin
# 便于跨会话恢复工作
```

### Knowledge Plugin
```python
# 将任务相关的技术文档保存到 Knowledge
# 便于后续查找和复用
```

### Memory Plugin
```python
# 记录任务讨论和决策
# 形成知识图谱
```

## 相关资源

- [基本使用示例](../../examples/basic_usage.md)
- [配置指南](../config/README.md)
- [命令参考](../commands/README.md)

---

**最后更新**: 2024-01-15
**维护者**: Task Plugin Team
**版本**: 1.0.0
