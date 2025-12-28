# Task Plugin 国际化 (i18n)

Task Plugin 内置多语言支持，目前支持简体中文和英文。

## 支持的语言

- 🇨🇳 简体中文 (`zh_CN`) - 默认
- 🇺🇸 英文 (`en_US`)

## 使用方法

### 基本用法

```python
from task.i18n import get_i18n, t

# 方法 1：使用全局函数
message = t("task.created", task_id="tk-123")
# 输出（中文）: "✅ 任务创建成功"
# 输出（英文）: "✅ Task created successfully"

# 方法 2：使用 i18n 管理器
i18n = get_i18n()
message = i18n.t("task.not_found", task_id="tk-999")
# 输出（中文）: "❌ 任务不存在: tk-999"
# 输出（英文）: "❌ Task not found: tk-999"
```

### 切换语言

```python
from task.i18n import set_locale

# 切换到英文
set_locale("en_US")

# 切换到中文
set_locale("zh_CN")
```

### 环境变量配置

通过环境变量设置默认语言：

```bash
# 设置为中文
export TASK_LOCALE=zh_CN

# 设置为英文
export TASK_LOCALE=en_US

# 或使用标准 LANG 变量
export LANG=zh_CN.UTF-8
```

## 消息键结构

消息键采用点号分隔的层级结构：

```
task.created          → 任务创建消息
task.updated          → 任务更新消息
dependency.added      → 依赖添加消息
workspace.initialized → 工作空间初始化消息
stats.title           → 统计标题
error.unknown_tool    → 未知工具错误
```

### 完整消息键列表

#### 任务相关 (task.*)
- `task.created` - 任务创建成功
- `task.updated` - 任务更新成功
- `task.closed` - 任务关闭（需要参数: `title`）
- `task.reopened` - 任务重新打开（需要参数: `title`）
- `task.deleted` - 任务删除（需要参数: `task_id`）
- `task.not_found` - 任务不存在（需要参数: `task_id`）
- `task.no_tasks` - 未找到任务
- `task.found_count` - 找到 N 个任务（需要参数: `count`）
- `task.ready_count` - 找到 N 个就绪任务（需要参数: `count`）
- `task.blocked_count` - 找到 N 个阻塞任务（需要参数: `count`）
- `task.no_ready` - 无就绪任务
- `task.no_blocked` - 无阻塞任务

#### 依赖相关 (dependency.*)
- `dependency.added` - 依赖添加成功（需要参数: `task_id`, `depends_on_id`, `dep_type`）
- `dependency.removed` - 依赖移除（需要参数: `task_id`, `depends_on_id`）
- `dependency.no_deps` - 无依赖
- `dependency.task_deps` - 任务的依赖（需要参数: `task_id`）

#### 工作空间相关 (workspace.*)
- `workspace.initialized` - 工作空间初始化成功
- `workspace.info_title` - 工作空间信息标题
- `workspace.workspace_id` - 工作空间 ID（需要参数: `workspace_id`）
- `workspace.root_dir` - 根目录（需要参数: `root`）
- `workspace.db_path` - 数据库路径（需要参数: `path`）
- `workspace.db_exists` - 数据库是否存在（需要参数: `exists`）
- `workspace.db_healthy` - 数据库健康状态（需要参数: `healthy`）
- `workspace.db_version` - 数据库版本（需要参数: `version`）

#### 统计相关 (stats.*)
- `stats.title` - 统计标题
- `stats.by_status` - 按状态分组标题
- `stats.by_type` - 按类型分组标题
- `stats.total_tasks` - 总任务数（需要参数: `count`）
- `stats.status_*` - 各状态任务数（需要参数: `count`）
- `stats.type_*` - 各类型任务数（需要参数: `count`）

#### 字段名称 (field.*)
- `field.id` - ID 字段
- `field.title` - 标题字段
- `field.description` - 描述字段
- `field.type` - 类型字段
- `field.status` - 状态字段
- `field.priority` - 优先级字段
- `field.assignee` - 负责人字段
- `field.tags` - 标签字段
- 等等...

#### 错误消息 (error.*)
- `error.unknown_tool` - 未知工具（需要参数: `name`）
- `error.invalid_args` - 无效参数
- `error.db_error` - 数据库错误（需要参数: `error`）
- `error.validation_error` - 验证错误（需要参数: `error`）

## 格式化参数

消息支持 Python 格式化字符串：

```python
# 单个参数
t("task.not_found", task_id="tk-123")
# → "❌ 任务不存在: tk-123"

# 多个参数
t("dependency.added", task_id="tk-1", depends_on_id="tk-2", dep_type="blocks")
# → "✅ 依赖添加成功: tk-1 → tk-2 (blocks)"

# 数字参数
t("task.found_count", count=5)
# → "找到 5 个任务:"
```

## 添加新语言

### 1. 创建语言文件

在 `locales/` 目录创建新的语言文件（如日文）：

```bash
cp locales/en_US.json locales/ja_JP.json
```

### 2. 翻译消息

编辑 `ja_JP.json`，翻译所有消息：

```json
{
  "task": {
    "created": "✅ タスクが正常に作成されました",
    "updated": "✅ タスクが正常に更新されました",
    ...
  },
  ...
}
```

### 3. 使用新语言

```python
set_locale("ja_JP")
```

## 最佳实践

### 1. 保持消息键一致

所有语言文件应包含相同的键结构：

```json
// ✅ 正确 - 所有语言都有相同的键
zh_CN.json: { "task": { "created": "..." } }
en_US.json: { "task": { "created": "..." } }
ja_JP.json: { "task": { "created": "..." } }

// ❌ 错误 - 键不一致
zh_CN.json: { "task": { "created": "..." } }
en_US.json: { "task": { "create": "..." } }  // 键名不同
```

### 2. 使用描述性键名

```python
# ✅ 好 - 清晰的键名
t("task.created")
t("dependency.added")

# ❌ 差 - 模糊的键名
t("msg1")
t("success")
```

### 3. 提供回退消息

i18n 管理器自动提供回退机制：
1. 尝试当前语言
2. 回退到备用语言（en_US）
3. 如果都找不到，返回键本身

```python
# 假设 zh_CN 中缺少某个键
set_locale("zh_CN")
message = t("task.some_missing_key")
# 自动回退到 en_US 中的翻译
```

### 4. 避免硬编码文本

```python
# ❌ 错误 - 硬编码中文
return f"✅ 任务创建成功: {task_id}"

# ✅ 正确 - 使用 i18n
return t("task.created", task_id=task_id)
```

## 测试

### 单元测试示例

```python
import pytest
from task.i18n import I18nManager

def test_translation_zh():
    """测试中文翻译。"""
    i18n = I18nManager("zh_CN")
    assert "任务创建成功" in i18n.t("task.created")

def test_translation_en():
    """测试英文翻译。"""
    i18n = I18nManager("en_US")
    assert "Task created successfully" in i18n.t("task.created")

def test_fallback():
    """测试回退机制。"""
    i18n = I18nManager("zh_CN")
    # 假设这个键只在英文中存在
    message = i18n.t("some.english.only.key")
    # 应该回退到英文
    assert message is not None
```

### 集成测试

```python
def test_server_with_i18n():
    """测试服务器使用 i18n。"""
    from task.i18n import set_locale
    from task.server import handle_task_create

    # 测试中文
    set_locale("zh_CN")
    result = await handle_task_create(session, {"title": "测试"})
    assert "任务创建成功" in result[0].text

    # 测试英文
    set_locale("en_US")
    result = await handle_task_create(session, {"title": "Test"})
    assert "Task created successfully" in result[0].text
```

## 故障排查

### 问题 1：翻译未生效

**检查**：
1. 语言文件是否存在？
2. JSON 格式是否正确？
3. 消息键是否拼写正确？
4. 是否正确设置了语言？

```python
# 调试信息
from task.i18n import get_i18n

i18n = get_i18n()
print(f"当前语言: {i18n.locale}")
print(f"可用语言: {list(i18n.messages.keys())}")
```

### 问题 2：格式化参数错误

**检查**：
1. 参数名是否匹配？
2. 参数类型是否正确？

```python
# ❌ 错误 - 参数名不匹配
t("task.not_found", id="tk-123")  # 应该是 task_id

# ✅ 正确
t("task.not_found", task_id="tk-123")
```

### 问题 3：编码问题

确保所有文件使用 UTF-8 编码：

```bash
file -I locales/zh_CN.json
# 应该显示: charset=utf-8
```

## 性能考虑

i18n 管理器在初始化时一次性加载所有语言文件：

```python
# 语言文件在初始化时加载，后续调用很快
i18n = I18nManager()  # 加载文件
i18n.t("task.created")  # 快速查找
i18n.t("task.updated")  # 快速查找
```

对于大型应用，考虑：
1. 使用全局单例（`get_i18n()`）
2. 延迟加载不常用的语言
3. 缓存常用翻译

## 相关资源

- [Python i18n 最佳实践](https://phrase.com/blog/posts/python-localization/)
- [JSON Schema for i18n](https://www.i18next.com/misc/json-format)
- [Unicode CLDR](http://cldr.unicode.org/)

---

**最后更新**: 2024-01-15
**维护者**: Task Plugin Team
