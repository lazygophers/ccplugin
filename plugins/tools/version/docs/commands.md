# 命令系统

Version 插件提供版本管理命令。

## 命令列表

| 命令 | 描述 | 用法 |
|------|------|------|
| `/version show` | 显示当前版本 | `/version show` |
| `/version info` | 显示版本详情 | `/version info` |
| `/version bump` | 更新版本 | `/version bump <level>` |
| `/version set` | 设置版本 | `/version set <version>` |

## /version show

### 功能

显示项目当前版本号。

### 用法

```bash
/version show
```

### 输出示例

```
当前版本：1.2.3.4
```

## /version info

### 功能

显示版本详细信息，包括各部分数值和 Git 提交状态。

### 用法

```bash
/version info
```

### 输出示例

```
版本详情：
- Major: 1
- Minor: 2
- Patch: 3
- Build: 4
- Git 状态: 已提交
```

## /version bump

### 功能

根据指定级别自动更新版本号。

### 用法

```bash
/version bump build    # 构建版本 +1
/version bump patch    # 补丁版本 +1
/version bump minor    # 次版本 +1
/version bump major    # 主版本 +1
```

### 更新规则

| 级别 | 变更 | 示例 |
|------|------|------|
| `build` | Build +1 | 1.2.3.4 → 1.2.3.5 |
| `patch` | Patch +1, Build = 0 | 1.2.3.5 → 1.2.4.0 |
| `minor` | Minor +1, Patch = Build = 0 | 1.2.4.0 → 1.3.0.0 |
| `major` | Major +1, 其他 = 0 | 1.3.0.0 → 2.0.0.0 |

## /version set

### 功能

手动设置版本号到指定值。

### 用法

```bash
/version set 1.0.0.0
/version set 2.0       # 自动补全为 2.0.0.0
```

### 格式

支持完整版本号或部分版本号：

- `1.2.3.4` - 完整版本号
- `1.2.3` - 自动补全为 1.2.3.0
- `1.2` - 自动补全为 1.2.0.0
- `1` - 自动补全为 1.0.0.0
