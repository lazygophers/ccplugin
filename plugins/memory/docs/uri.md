# URI 命名空间

Memory 插件使用的 URI 命名空间。

## 命名空间列表

| 命名空间 | 用途 | 示例 |
|----------|------|------|
| `project://` | 项目级记忆 | `project://structure` |
| `workflow://` | 工作流记忆 | `workflow://commands` |
| `user://` | 用户级记忆 | `user://preferences` |
| `task://` | 任务级记忆 | `task://current` |
| `system://` | 系统操作 | `system://boot` |

## project://

### 用途

存储项目相关的记忆，如结构、依赖、配置等。

### 示例

```
project://structure     # 项目结构
project://dependencies  # 项目依赖
project://config        # 项目配置
project://api           # API 设计
```

## workflow://

### 用途

存储工作流相关的记忆，如命令、模式、解决方案等。

### 示例

```
workflow://commands     # 常用命令
workflow://patterns     # 设计模式
workflow://solutions    # 解决方案
```

## user://

### 用途

存储用户相关的记忆，如偏好、标准、上下文等。

### 示例

```
user://preferences      # 用户偏好
user://standards        # 编码标准
user://context          # 上下文信息
```

## task://

### 用途

存储任务相关的记忆，如待办、进度、阻塞等。

### 示例

```
task://current          # 当前任务
task://todo             # 待办事项
task://blocked          # 阻塞问题
```

## system://

### 用途

系统操作，如启动、索引、最近访问等。

### 示例

```
system://boot           # 启动加载
system://index          # 索引操作
system://recent         # 最近访问
```

## 优先级系统

| 级别 | 含义 | 自动加载 |
|------|------|----------|
| 0-2 | 核心记忆 | 始终加载 |
| 3-5 | 重要记忆 | 按需加载 |
| 6-8 | 参考记忆 | 手动加载 |
| 9-10 | 归档记忆 | 不加载 |
