# Task Plugin 基本使用示例

> 这是 Task Plugin 的快速入门指南，展示常见使用场景和示例代码。

## 目录

- [快速开始](#快速开始)
- [基本操作](#基本操作)
  - [创建任务](#创建任务)
  - [列出任务](#列出任务)
  - [查看任务详情](#查看任务详情)
  - [更新任务](#更新任务)
  - [关闭任务](#关闭任务)
- [依赖管理](#依赖管理)
  - [添加依赖](#添加依赖)
  - [查看依赖](#查看依赖)
  - [移除依赖](#移除依赖)
- [查询工具](#查询工具)
  - [查找就绪任务](#查找就绪任务)
  - [查看阻塞任务](#查看阻塞任务)
  - [任务统计](#任务统计)
- [工作空间管理](#工作空间管理)
- [高级场景](#高级场景)

## 快速开始

### 初始化工作空间

```python
# 通过 MCP 工具调用
workspace_init()
# 输出：✅ 工作空间初始化成功
#       工作空间 ID: a1b2c3d4e5f6g7h8
#       根目录: /Users/username/myproject
#       数据库路径: /Users/username/myproject/.task_data/tasks_a1b2c3d4e5f6g7h8.db
#       数据库版本: abc123
```

### 创建第一个任务

```python
# 创建简单任务
task_create(
    title="实现用户登录功能",
    description="开发用户登录页面和 API",
    priority=1
)
# 输出：✅ 任务创建成功
#       ID: tk-abc123def456
#       标题: 实现用户登录功能
#       状态: open
#       优先级: 1 (high)
```

## 基本操作

### 创建任务

#### 创建基本任务

```python
task_create(
    title="修复登录 bug",
    description="用户无法通过邮箱登录",
    task_type="bug",
    priority=0  # critical
)
```

#### 创建带负责人的任务

```python
task_create(
    title="优化数据库查询性能",
    description="分析慢查询并优化索引",
    task_type="task",
    priority=2,  # medium
    assignee="developer@example.com",
    tags=["performance", "database"]
)
```

#### 创建 Epic 任务

```python
task_create(
    title="用户认证系统重构",
    description="升级到 OAuth 2.0",
    task_type="epic",
    priority=1,
    tags=["architecture", "security"]
)
```

### 列出任务

#### 列出所有任务（简化模式）

```python
task_list(brief=True)
# 输出：找到 3 个任务:
#       [tk-123] 修复登录 bug (bug, 0)
#       [tk-456] 优化数据库查询性能 (task, 2) [developer@example.com]
#       [tk-789] 用户认证系统重构 (epic, 1)
```

#### 按状态过滤

```python
# 只列出进行中的任务
task_list(status="in_progress", brief=True)

# 只列出已完成的任务
task_list(status="closed", brief=False)  # 详细模式
```

#### 按优先级过滤

```python
# 列出所有 critical 任务
task_list(priority=0, brief=True)

# 列出所有 high 和 critical 任务（需要多次调用）
task_list(priority=0, brief=True)
task_list(priority=1, brief=True)
```

#### 按类型过滤

```python
# 只列出 bug
task_list(task_type="bug", brief=True)

# 只列出 feature
task_list(task_type="feature", brief=True)
```

#### 限制返回数量

```python
# 只返回最近的 5 个任务
task_list(limit=5, brief=True)
```

### 查看任务详情

```python
task_show(task_id="tk-abc123def456")
# 输出：任务详情:
#       ID: tk-abc123def456
#       标题: 实现用户登录功能
#       描述: 开发用户登录页面和 API
#       类型: task
#       状态: open
#       优先级: 1 (high)
#       创建时间: 2024-01-15 10:30:00
#       ...
```

### 更新任务

#### 更新任务状态

```python
# 开始处理任务
task_update(
    task_id="tk-abc123def456",
    status="in_progress"
)

# 标记为阻塞
task_update(
    task_id="tk-abc123def456",
    status="blocked"
)
```

#### 更新多个字段

```python
task_update(
    task_id="tk-abc123def456",
    title="实现用户登录和注册功能",  # 修改标题
    status="in_progress",              # 更新状态
    priority=0,                        # 提高优先级
    assignee="developer@example.com"   # 分配负责人
)
```

#### 添加验收标准

```python
task_update(
    task_id="tk-abc123def456",
    acceptance_criteria="""
    1. 用户可以通过邮箱和密码登录
    2. 登录失败显示明确的错误提示
    3. 登录成功后跳转到首页
    4. 记住登录状态（可选）
    """
)
```

### 关闭任务

```python
# 完成任务
task_close(task_id="tk-abc123def456")
# 输出：✅ 任务已关闭: 实现用户登录功能

# 重新打开已关闭的任务
task_reopen(task_id="tk-abc123def456")
# 输出：✅ 任务已重新打开: 实现用户登录功能
```

### 删除任务

```python
# 删除任务（不可恢复）
task_delete(task_id="tk-abc123def456")
# 输出：✅ 任务已删除: tk-abc123def456
```

## 依赖管理

### 添加依赖

#### 添加阻塞依赖

```python
# 任务 A 依赖任务 B（B 必须先完成）
task_dep_add(
    task_id="tk-taskA",
    depends_on_id="tk-taskB",
    dep_type="blocks"
)
# 输出：✅ 依赖添加成功: tk-taskA → tk-taskB (blocks)
```

#### 添加关联依赖

```python
# 任务 A 和任务 B 相关（软关联）
task_dep_add(
    task_id="tk-taskA",
    depends_on_id="tk-taskB",
    dep_type="related"
)
```

#### 添加父子依赖

```python
# Epic 和子任务的层级关系
task_dep_add(
    task_id="tk-subtask",
    depends_on_id="tk-epic",
    dep_type="parent-child"
)
```

#### 添加发现依赖

```python
# 在处理任务 A 时发现了任务 B
task_dep_add(
    task_id="tk-taskA",
    depends_on_id="tk-taskB",
    dep_type="discovered-from",
    reason="在实现过程中发现需要先优化数据库查询"
)
```

### 查看依赖

```python
task_dep_list(task_id="tk-taskA")
# 输出：任务 tk-taskA 的依赖:
#       - tk-taskB (blocks)
#       - tk-taskC (related)
```

### 移除依赖

```python
task_dep_remove(
    task_id="tk-taskA",
    depends_on_id="tk-taskB"
)
# 输出：✅ 依赖已移除: tk-taskA → tk-taskB
```

## 查询工具

### 查找就绪任务

就绪任务是指：
- 状态为 `open`（待处理）
- 没有未完成的阻塞依赖

```python
# 查找所有就绪任务
task_ready(limit=10)
# 输出：找到 3 个就绪任务:
#       [tk-123] 实现注册页面 (task, 1)
#       [tk-456] 添加单元测试 (task, 2)
#       [tk-789] 更新文档 (chore, 3)
```

### 查看阻塞任务

阻塞任务是指：
- 状态为 `blocked`（已阻塞）

```python
task_blocked()
# 输出：找到 2 个阻塞任务:
#       [tk-111] 部署到生产环境 (task, 0) - 阻塞原因: 等待安全审查
#       [tk-222] 集成第三方 API (task, 1) - 阻塞原因: API 文档未完成
```

### 任务统计

```python
task_stats()
# 输出：## 任务统计
#
#       ### 按状态
#       - 总任务数: 15
#       - 待处理: 5
#       - 进行中: 3
#       - 已阻塞: 2
#       - 已延期: 1
#       - 已完成: 4
#
#       ### 按类型
#       - Bug: 3
#       - Feature: 5
#       - Task: 6
#       - Epic: 1
#       - Chore: 0
```

## 工作空间管理

### 初始化工作空间

```python
# 使用当前目录
workspace_init()

# 指定工作空间目录
workspace_init(workspace_root="/path/to/project")
```

### 查看工作空间信息

```python
workspace_info()
# 输出：## 工作空间信息
#
#       - 工作空间 ID: a1b2c3d4e5f6g7h8
#       - 根目录: /Users/username/myproject
#       - 数据库路径: /Users/username/myproject/.task_data/tasks_a1b2c3d4e5f6g7h8.db
#       - 数据库存在: True
#       - 数据库健康: True
#       - 数据库版本: abc123
```

## 高级场景

### 场景 1：Scrum Sprint 规划

```python
# 1. 创建 Sprint Epic
task_create(
    title="Sprint 23",
    description="2024年1月15日 - 2024年1月29日",
    task_type="epic",
    priority=1,
    tags=["sprint-23"]
)
# 记录返回的 ID: tk-sprint23

# 2. 创建用户故事并关联到 Sprint
story1 = task_create(
    title="用户故事：作为用户，我想重置密码",
    description="验收标准：...",
    task_type="feature",
    priority=1,
    tags=["sprint-23", "user-story"]
)
# ID: tk-story1

# 3. 建立父子关系
task_dep_add(
    task_id="tk-story1",
    depends_on_id="tk-sprint23",
    dep_type="parent-child"
)

# 4. 将故事拆分为技术任务
task_create(
    title="设计重置密码 API",
    task_type="task",
    priority=1,
    assignee="backend@example.com",
    tags=["sprint-23", "backend"]
)
# ID: tk-task1

task_create(
    title="实现重置密码前端页面",
    task_type="task",
    priority=1,
    assignee="frontend@example.com",
    tags=["sprint-23", "frontend"]
)
# ID: tk-task2

# 5. 设置依赖（前端依赖后端 API）
task_dep_add(
    task_id="tk-task2",
    depends_on_id="tk-task1",
    dep_type="blocks"
)

# 6. 查看 Sprint 进度
task_list(tags=["sprint-23"], brief=True)
task_stats()
```

### 场景 2：Bug 修复工作流

```python
# 1. 创建 bug 任务
task_create(
    title="登录页面在 Safari 上无法显示",
    description="用户报告：在 Safari 浏览器上无法看到登录表单",
    task_type="bug",
    priority=0,  # critical
    assignee="frontend@example.com",
    tags=["bug", "safari", "login"]
)
# ID: tk-bug123

# 2. 开始调查
task_update(
    task_id="tk-bug123",
    status="in_progress",
    description="用户报告：在 Safari 浏览器上无法看到登录表单\n\n调查进展：发现是 CSS Grid 兼容性问题"
)

# 3. 发现需要先修复另一个问题
task_create(
    title="更新 CSS Grid 浏览器兼容性",
    description="Safari 14 不支持某些 Grid 属性",
    task_type="task",
    priority=0,
    assignee="frontend@example.com",
    tags=["css", "compatibility"]
)
# ID: tk-task-css

# 4. 建立依赖关系
task_dep_add(
    task_id="tk-bug123",
    depends_on_id="tk-task-css",
    dep_type="discovered-from",
    reason="需要先解决 CSS Grid 兼容性问题"
)

# 5. 标记原始 bug 为阻塞状态
task_update(
    task_id="tk-bug123",
    status="blocked"
)

# 6. 先完成 CSS 任务
task_update(task_id="tk-task-css", status="in_progress")
# ... 完成工作 ...
task_close(task_id="tk-task-css")

# 7. 继续修复原始 bug
task_update(task_id="tk-bug123", status="in_progress")
# ... 完成修复 ...
task_close(task_id="tk-bug123")
```

### 场景 3：多人协作

```python
# 1. Team Lead 创建 Epic
task_create(
    title="用户认证系统重构",
    description="从 JWT 迁移到 OAuth 2.0",
    task_type="epic",
    priority=1,
    tags=["q1-2024", "architecture"]
)
# ID: tk-epic-auth

# 2. 拆分为并行任务
backend_task = task_create(
    title="实现 OAuth 2.0 服务端",
    task_type="task",
    priority=1,
    assignee="backend@example.com",
    tags=["backend", "oauth"]
)
# ID: tk-backend-oauth

frontend_task = task_create(
    title="实现 OAuth 2.0 客户端",
    task_type="task",
    priority=1,
    assignee="frontend@example.com",
    tags=["frontend", "oauth"]
)
# ID: tk-frontend-oauth

# 3. 前端依赖后端
task_dep_add(
    task_id="tk-frontend-oauth",
    depends_on_id="tk-backend-oauth",
    dep_type="blocks"
)

# 4. 后端开发者开始工作
task_update(task_id="tk-backend-oauth", status="in_progress")

# 5. 前端开发者查看就绪任务（会发现前端任务不在列表中，因为被阻塞）
task_ready()

# 6. 后端完成后，前端任务变为就绪
task_close(task_id="tk-backend-oauth")
task_ready()  # 现在会显示前端任务

# 7. 前端开始工作
task_update(task_id="tk-frontend-oauth", status="in_progress")
task_close(task_id="tk-frontend-oauth")

# 8. 关闭 Epic
task_close(task_id="tk-epic-auth")
```

### 场景 4：每日站会准备

```python
# 1. 查看自己负责的进行中任务
task_list(
    status="in_progress",
    assignee="developer@example.com",
    brief=True
)

# 2. 查看自己负责的阻塞任务
task_list(
    status="blocked",
    assignee="developer@example.com",
    brief=False  # 详细模式查看阻塞原因
)

# 3. 查看就绪任务（计划今天要做的）
task_ready(limit=5)

# 4. 查看整体进度
task_stats()
```

## 最佳实践

### 1. 任务命名

- ✅ 好的命名：`实现用户登录功能`
- ❌ 不好的命名：`登录`

### 2. 使用标签分类

```python
task_create(
    title="优化数据库查询",
    tags=["performance", "database", "sprint-23", "p1"]
)
```

### 3. 设置合理的优先级

- `0 (critical)`: 紧急且重要（生产环境故障）
- `1 (high)`: 重要但不紧急（计划内的重要功能）
- `2 (medium)`: 一般任务
- `3 (low)`: 低优先级改进
- `4 (backlog)`: 待定需求

### 4. 及时更新任务状态

```python
# 开始工作时
task_update(task_id="tk-xxx", status="in_progress")

# 遇到阻塞时
task_update(
    task_id="tk-xxx",
    status="blocked",
    description="原描述\n\n阻塞原因：等待 API 文档"
)

# 完成时
task_close(task_id="tk-xxx")
```

### 5. 合理使用依赖类型

- `blocks`: 硬阻塞（必须先完成依赖任务）
- `related`: 软关联（相关但不阻塞）
- `parent-child`: 层级关系（Epic 和子任务）
- `discovered-from`: 发现关系（工作中发现的新任务）

## 故障排查

### 问题 1：任务不在就绪列表中

可能原因：
1. 任务状态不是 `open`
2. 任务有未完成的 `blocks` 类型依赖

解决方法：
```python
# 1. 检查任务状态
task_show(task_id="tk-xxx")

# 2. 检查依赖
task_dep_list(task_id="tk-xxx")

# 3. 如果依赖已不需要，移除它
task_dep_remove(task_id="tk-xxx", depends_on_id="tk-yyy")
```

### 问题 2：无法删除任务

可能原因：
- 其他任务依赖此任务

解决方法：
```python
# 先查看哪些任务依赖它（需要实现反向查询工具）
# 然后移除这些依赖关系
task_dep_remove(task_id="tk-other", depends_on_id="tk-xxx")
# 再删除任务
task_delete(task_id="tk-xxx")
```

## 下一步

- 查看 [API 参考文档](../docs/API参考.md)
- 了解 [插件配置](../docs/配置指南.md)
- 探索 [高级功能](../docs/高级功能.md)
