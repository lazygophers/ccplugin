---
name: task-usage-commands
description: 任务管理使用指南和命令参考 - 包括命令用法、任务元信息、使用场景、常见场景和错误处理
---

# 任务管理使用指南和命令参考

## 任务元信息

每个任务包含以下元信息：

- **id** - 任务 ID（自动生成，6 位随机字符串）
- **title** - 任务名称（必填）
- **description** - 任务描述
- **type** - 任务类型（feature/bug/refactor/test/docs/config）
- **status** - 任务状态（pending/in_progress/completed/blocked/cancelled）
- **acceptance_criteria** - 验收标准
- **dependencies** - 前置依赖任务 ID 列表（逗号分隔）
- **parent_id** - 父任务 ID（支持层级关系）

## 使用场景

当用户以下情况时，必须使用 task：

1. **任务相关**
   - "添加任务"、"创建 TODO"
   - "任务列表"、"查看任务"
   - "更新任务状态"、"完成任务"
   - "删除任务"

2. **需求管理**
   - "记录这个需求"
   - "添加功能需求"
   - "追踪需求状态"

3. **项目规划**
   - "项目计划"
   - "开发计划"
   - "功能列表"

4. **进度跟踪**
   - "当前进度"
   - "还有哪些任务"
   - "任务统计"

## 任务管理命令

### 创建任务

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add "任务标题"
```

### 完整参数创建

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add "任务标题" \
  --description "详细描述" \
  --type feature \
  --status pending \
  --acceptance "验收标准" \
  --depends "task_id1,task_id2" \
  --parent "parent_task_id"
```

**任务类型 (type)**：

- `feature` - 新功能 ✨
- `bug` - 缺陷修复 🐛
- `refactor` - 代码重构 ♻️
- `test` - 测试 🧪
- `docs` - 文档 📝
- `config` - 配置 ⚙️

示例：

```bash
# 功能开发
uvx --from git+https://github.com/lazygophers/ccplugin task add "实现用户登录功能" --type feature --acceptance "用户可以使用邮箱和密码登录"

# Bug修复
uvx --from git+https://github.com/lazygophers/ccplugin task add "修复登录超时" --type bug --description "生产环境登录接口在并发>100时超时超过30秒" --acceptance "并发100时响应时间<2秒，成功率>99%"

# 测试任务
uvx --from git+https://github.com/lazygophers/ccplugin task add "编写登录API单元测试" --type test --depends "实现用户登录"

# 文档任务
uvx --from git+https://github.com/lazygophers/ccplugin task add "编写API文档" --type docs --depends "实现用户登录"
```

### 更新任务

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --status <status>
```

状态选项：

- `pending` - 待处理
- `in_progress` - 进行中
- `completed` - 已完成
- `blocked` - 已阻塞
- `cancelled` - 已取消

可用参数：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --title "新标题"
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --description "新描述"
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --type bug
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --status in_progress
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --acceptance "验收标准"
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --depends "task_id1,task_id2"
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --parent "parent_task_id"
```

示例：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task update abc123 --status in_progress   # 开始任务
uvx --from git+https://github.com/lazygophers/ccplugin task update abc123 --status completed     # 完成任务
uvx --from git+https://github.com/lazygophers/ccplugin task update abc123 --acceptance "用户可使用邮箱、手机号注册并完成验证"
```

### 列出任务

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task list                    # 所有任务
uvx --from git+https://github.com/lazygophers/ccplugin task list pending           # 待处理
uvx --from git+https://github.com/lazygophers/ccplugin task list --type bug        # 所有bug类型任务
uvx --from git+https://github.com/lazygophers/ccplugin task list --status completed --type feature  # 组合筛选
uvx --from git+https://github.com/lazygophers/ccplugin task list --limit 50  # 查看所有任务并统计
```

### 查看任务详情

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task get <id>
```

显示任务的完整信息，包括验收标准和依赖关系。

### 子任务操作

```bash
# 创建子任务
uvx --from git+https://github.com/lazygophers/ccplugin task add "子任务标题" --parent "parent_task_id"

# 列出子任务
uvx --from git+https://github.com/lazygophers/ccplugin task list --parent "parent_task_id"
```

### 导出任务

```bash
/task-export tasks.md        # 导出到文件
```

注意：`/task-export` 必须指定输出文件路径。推荐导出到 `.claude/` 目录。

## 与 TodoWrite 配合

当使用 TodoWrite 工具管理会话任务时，必须同步到 task：

```python
# 会话任务列表
todos = [
    {"content": "实现用户登录", "status": "in_progress"},
    {"content": "编写API文档", "status": "pending"}
]

# 同步到 task
for todo in todos:
    content = todo["content"]
    status = todo["status"]

    # 添加任务时设置状态
    if status == "pending":
        /task add f'"{content}"'
    elif status == "completed":
        task_id = /task add f'"{content}" --status completed'
    else:
        task_id = /task add f'"{content}" --status {status}'
```

## 任务生命周期

```
待处理 (pending)
    ↓
进行中 (in_progress)
    ↓
已完成 (completed)

或

待处理 (pending)
    ↓
已阻塞 (blocked)
    ↓
进行中 (in_progress)
    ↓
已完成 (completed)
```

## 常见场景

### 场景 1：用户添加功能需求

用户："需要添加用户头像上传功能"

响应：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add "实现用户头像上传功能" \
  --type feature \
  --description "支持裁剪、压缩、格式转换，限制大小2MB" \
  --acceptance "用户可以上传头像，自动裁剪为正方形，支持JPG/PNG格式，文件大小<2MB"
```

### 场景 2：开始工作

用户："开始实现登录功能"

响应：

```bash
# 1. 找到任务ID
uvx --from git+https://github.com/lazygophers/ccplugin task list pending | grep "登录"

# 2. 更新状态
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --status in_progress
```

### 场景 3：完成任务

用户："登录功能做完了"

响应：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task done <id>
```

### 场景 4：查看进度

用户："当前项目进度如何？"

响应：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task stats
uvx --from git+https://github.com/lazygophers/ccplugin task list
```

### 场景 5：发现 Bug

用户："发现登录有问题，经常超时"

响应：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add "修复登录超时问题" \
  --type bug \
  --description "用户反馈登录经常超时，需要排查" \
  --acceptance "修复后连续24小时无超时投诉，监控显示超时率<0.1%" \
  --priority "高"
```

### 场景 6：代码重构

用户："用户模块代码太乱了，需要重构"

响应：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add "重构用户模块代码" \
  --type refactor \
  --description "当前代码结构混乱，需要重构以提高可维护性" \
  --acceptance "代码通过review，单元测试覆盖率保持>80%，性能无明显下降"
```

## 错误处理

### 脚本执行失败

确保 uv 可用：

```bash
uv --version
```

### 权限问题

确保 `.lazygophers` 目录可写：

```bash
mkdir -p .lazygophers/ccplugin/task
chmod 755 .lazygophers/ccplugin/task
```
