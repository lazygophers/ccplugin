---
name: 项目根目录检测
description: 统一的项目根目录检测逻辑和路径管理规范
---

# 项目根目录检测

## 概述

CCPlugin 采用统一的项目根目录检测策略，确保在任何工作目录下运行脚本时都能正确定位项目资源。

## 检测优先级

### 优先级顺序
1. **优先：`.git` 目录** - Git 仓库根目录（最准确）
2. **其次：`.lazygophers` 目录** - 已初始化的插件环境
3. **最后：当前目录** - 回退方案

### 检测算法
```python
def find_project_root(max_levels: int = 6) -> Path:
    """查找项目根目录"""
    current = Path.cwd()

    for _ in range(max_levels):
        # 优先查找 .git（Git 项目根）
        if (current / ".git").exists():
            return current

        # 其次查找 .lazygophers（已初始化项目）
        if (current / ".lazygophers").exists():
            return current

        # 向上递归
        current = current.parent

    # 都找不到，使用当前目录
    return Path.cwd()
```

## 应用场景

### 1. 数据路径获取
```python
def get_data_path(project_root: Optional[str] = None) -> Path:
    """获取数据目录路径"""
    if project_root is None:
        project_root = str(find_project_root())

    data_path = Path(project_root) / ".lazygophers/ccplugin/semantic"
    return data_path
```

### 2. 环境初始化
```python
def init_environment(force: bool = False) -> bool:
    """初始化语义搜索环境"""
    project_root = find_project_root()

    # 创建必要的目录和配置
    data_path = project_root / ".lazygophers/ccplugin/semantic"
    data_path.mkdir(parents=True, exist_ok=True)

    # 初始化配置文件
    config_path = data_path / "config.yaml"
    if not config_path.exists():
        save_config(default_config, str(project_root))

    return True
```

### 3. 索引路径决定
```python
def index(path: Optional[str] = None) -> None:
    """索引代码库"""
    if path:
        # 用户指定了路径，直接使用
        root_path = Path(path).resolve()
    else:
        # 自动查找项目根目录
        project_root = find_project_root()
        root_path = project_root

    # 执行索引
    indexer = CodeIndexer(config, data_path)
    stats = indexer.index_project(root_path)
```

## 关键实现位置

### semantic.py 中的应用
1. **`get_data_path()`** - 第 282 行
   - 获取 `.lazygophers/ccplugin/semantic` 路径
   - 支持手动指定 project_root

2. **`init_environment()`** - 第 649 行
   - 初始化环境和配置
   - 创建必要目录

3. **`check_gitignore()`** - 第 739 行
   - 维护 `.lazygophers/.gitignore`
   - 防止数据被提交到 Git

4. **`index()` 命令** - 第 1365 行
   - 确定索引的根目录
   - 支持 `--path` 参数覆盖

## 配置和数据组织

### 目录结构
```
<project_root>/                      # Git 仓库根目录
├── .git/                            # Git 数据（标识项目根）
├── lib/                             # 共享库
├── plugins/
│   └── semantic/
│       └── scripts/
│           └── semantic.py          # CLI 脚本
├── .claude/                         # Claude Code 配置
│   └── skills/                      # 规范文档
├── .lazygophers/                    # 插件数据目录（不提交）
│   ├── .gitignore
│   └── ccplugin/
│       └── semantic/
│           ├── config.yaml          # 配置文件
│           ├── lancedb/             # 向量数据库
│           └── text_search/         # 文本搜索备份
└── .gitignore                       # Git 主配置
```

### .lazygophers/.gitignore
```
# 忽略插件数据
/ccplugin/semantic/
```

## 跨目录执行支持

### 场景 1：项目目录下执行
```bash
$ cd /path/to/ccplugin
$ uv run plugins/semantic/scripts/semantic.py index
# ✓ 自动查找到 .git，正确识别项目根目录
```

### 场景 2：子目录下执行
```bash
$ cd /path/to/ccplugin/lib/config
$ /path/to/ccplugin/plugins/semantic/scripts/semantic.py index
# ✓ 向上遍历，找到 .git，正确识别项目根目录
```

### 场景 3：上层目录执行
```bash
$ cd /path/to
$ uv run ccplugin/plugins/semantic/scripts/semantic.py index
# ✓ 脚本内部查找 .git，正确识别项目根目录
```

## 边界情况处理

### 非 Git 项目
- 如果没有 `.git` 目录，查找 `.lazygophers` 目录
- 如果也没有 `.lazygophers`，使用当前目录
- 确保脚本在任何目录下都能运行

### 嵌套 Git 仓库
- 仅查找最近的 `.git` 目录（Git 标准行为）
- 适用于 monorepo 或子模块场景

### 首次初始化
```bash
# 首次运行时 .lazygophers 不存在
$ uv run plugins/semantic/scripts/semantic.py init
# 1. 查找 .git 确定项目根目录
# 2. 创建 .lazygophers/ccplugin/semantic/
# 3. 生成 config.yaml
```

## API 参考

### 公开函数

#### `get_data_path(project_root: Optional[str] = None) -> Path`
获取数据目录路径。

**参数：**
- `project_root` - 项目根目录路径（可选，自动查找）

**返回：**
- Path 对象，指向 `.lazygophers/ccplugin/semantic`

**示例：**
```python
from plugins.semantic.scripts.semantic import get_data_path
data_path = get_data_path()
print(data_path)  # /path/to/ccplugin/.lazygophers/ccplugin/semantic
```

#### `init_environment(force: bool = False, silent: bool = False) -> bool`
初始化语义搜索环境。

**参数：**
- `force` - 强制重新初始化（默认 False）
- `silent` - 静默模式，不输出信息（默认 False）

**返回：**
- 初始化成功为 True，失败为 False

**示例：**
```python
success = init_environment(force=False, silent=True)
```

### 内部实现细节

#### 查找范围
- 最多向上遍历 **6 级** 目录
- 足以覆盖典型项目的深度（plugins/semantic/scripts/ -> 项目根 = 3 级）

#### 性能考虑
- 每个检查为简单的文件系统操作（Path.exists()）
- 复杂度：O(min(depth, 6))
- 通常在毫秒级完成

#### 线程安全性
- `Path.cwd()` 在单线程环境下安全
- 多线程应用应避免改变当前工作目录

## 最佳实践

### 1. 脚本编写
```python
# ✓ 推荐：自动查找项目根目录
data_path = get_data_path()

# ✗ 避免：硬编码路径
data_path = Path("/home/user/projects/ccplugin/.lazygophers")
```

### 2. 配置管理
```python
# ✓ 推荐：自动查找后加载配置
config = load_config()  # 内部自动查找项目根目录

# ✗ 避免：手动指定路径
config = load_config("/home/user/projects/ccplugin")
```

### 3. 相对路径
```python
# ✓ 推荐：使用相对于项目根的路径
lib_path = project_root / "lib" / "parsers"

# ✗ 避免：使用相对于脚本的路径
lib_path = Path(__file__).parent.parent.parent / "lib"
```

## 相关文件

- `plugins/semantic/scripts/semantic.py` - 实现检测逻辑
- `.claude/skills/project-root-detection.md` - 本文档
- `.lazygophers/.gitignore` - 数据目录 Git 配置
