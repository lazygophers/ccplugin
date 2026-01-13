---
name: 代码索引和解析
description: 多语言代码解析、代码块提取和索引流程的规范
---

# 代码索引和解析

## 概述

CCPlugin 的代码索引系统支持 20+ 编程语言的代码解析、提取和向量化。采用分层架构：语言检测 → 代码解析 → 代码块提取 → 向量化 → 存储。

## 支持的编程语言

### 按优先级分类

#### 高优先级（AST/完整解析）
- **Python** - 使用 AST，提取函数/类/装饰器/类型提示
- **Go** - 提取函数/接口/结构体
- **Rust** - 提取函数/结构体/特质/impl
- **Java** - 提取类/接口/注解
- **Kotlin** - 提取类/函数/对象/扩展
- **TypeScript** - 提取类/接口/类型

#### 中优先级（基础解析）
- **JavaScript** - 提取函数/类/箭头函数
- **C++** - 提取类/模板
- **C#** - 提取类/接口
- **Swift** - 提取类/结构体/协议
- **Flutter/Dart** - 提取 Widget/类/方法

#### 低优先级（简单分块）
- **C** - 按行分块
- **PHP** - 按行分块
- **Ruby** - 按行分块
- **Bash** - 按行分块
- **SQL** - 按行分块
- **Markdown** - 按章节分块

### 文件扩展名映射

| 语言 | 扩展名 |
|------|--------|
| Python | .py |
| Go | .go |
| JavaScript | .js, .jsx |
| TypeScript | .ts, .tsx |
| Rust | .rs |
| Java | .java |
| Kotlin | .kt |
| C | .c, .h |
| C++ | .cpp, .hpp, .cc, .cxx |
| C# | .cs |
| Swift | .swift |
| PHP | .php |
| Ruby | .rb |
| Bash | .sh, .bash |
| SQL | .sql |
| Markdown | .md |
| Dockerfile | Dockerfile |
| Dockerfile | .dockerfile |
| Android | .java, .kt |
| Flutter | .dart |

## 代码解析架构

### 解析器工厂

```python
from lib.parsers import parse_file

# 自动检测语言并解析
chunks = parse_file(file_path, language_hint=None)
# 返回: List[Dict] - 代码块列表
```

### 代码块结构

每个代码块包含：
```python
{
    "type": str,           # function/class/block/decorator/type_hint
    "name": str,           # 函数名/类名（可为空）
    "code": str,           # 代码内容
    "start_line": int,     # 起始行号
    "end_line": int,       # 结束行号
    "language": str,       # 编程语言
    "file_path": str,      # 文件路径
    "metadata": Dict,      # 额外元数据
}
```

### 解析器实现

#### Python 解析器（PythonParser）
```python
from lib.parsers.python_parser import PythonParser

parser = PythonParser()
chunks = parser.parse_file(file_path)

# 提取的元素
# - 函数定义（包括装饰器）
# - 类定义（包括方法）
# - 类型提示注解
# - 导入语句
```

#### Go 解析器（GoParser）
```python
from lib.parsers.go_parser import GoParser

parser = GoParser("go")
chunks = parser.parse_file(file_path)

# 提取的元素
# - 函数声明
# - 结构体定义
# - 接口定义
# - 方法接收者
```

#### 通用解析器（SimpleParser）
```python
from lib.parsers.simple_parser import SimpleParser

parser = SimpleParser()
chunks = parser.parse_file(file_path)

# 按固定行数分块
# chunk_size = 50 行（可配置）
# chunk_overlap = 5 行（可配置）
```

## 代码块提取算法

### 分块策略

#### 语义分块（高优先级语言）
```
代码文件
├── 函数定义 → 单个代码块
├── 类定义
│   ├── 类头 → 单个代码块
│   ├── 方法 1 → 单个代码块
│   ├── 方法 2 → 单个代码块
│   └── 类体 → 单个代码块
└── 独立语句 → 分组成块
```

#### 固定大小分块（低优先级语言）
```
代码文件 (500 字符)
├── 块 1: 字符 0-500
├── 块 2: 字符 450-950（50 字符重叠）
├── 块 3: 字符 900-1400
└── ...
```

### 分块参数

| 参数 | 值 | 说明 |
|------|-----|------|
| chunk_size | 500 | 目标代码块大小（字符数） |
| chunk_overlap | 50 | 块之间的重叠（字符数） |
| max_overlap | 100 | 最大重叠（防止过度重复） |

## 索引流程

### 完整索引流程

```
1. 初始化
   └─ CodeIndexer(config, data_path)

2. 扫描文件
   ├─ 读取 .gitignore（如启用）
   ├─ 构建排除规则
   └─ 递归扫描目录

3. 过滤文件
   ├─ 检查排除模式
   ├─ 检查文件扩展名
   └─ 检查启用的语言

4. 处理每个文件
   ├─ 检测语言
   ├─ 解析代码 → 代码块列表
   ├─ 生成嵌入 → 向量
   ├─ 验证向量
   └─ 存储数据库

5. 后处理
   └─ 创建向量索引（100+ 代码块时）
```

### 代码实现

```python
from lib.database.indexer import CodeIndexer

# 初始化
config = load_config()
indexer = CodeIndexer(config, data_path)
if not indexer.initialize():
    raise Exception("索引器初始化失败")

# 索引项目
stats = indexer.index_project(
    root_path=Path("/path/to/project"),
    incremental=False,
    batch_size=100
)

print(f"扫描文件: {stats['total_files']}")
print(f"索引文件: {stats['indexed_files']}")
print(f"代码块数: {stats['total_chunks']}")
print(f"失败文件: {stats['failed_files']}")

# 关闭
indexer.close()
```

## 文件扫描和过滤

### .gitignore 支持

启用时（默认）：
```python
# 读取所有 .gitignore 文件
# 构建排除规则集合
# 跳过匹配的路径
```

默认排除模式：
```python
[
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".lazygophers",
    "dist",
    "build",
    "*.min.js",
    "*.min.css",
]
```

### 安全扫描
```python
def safe_rglob(path: Path):
    """安全的递归目录扫描"""
    for item in path.iterdir():
        try:
            if item.is_file():
                yield item
            elif item.is_dir() and not item.name.startswith('.'):
                yield from safe_rglob(item)
        except (OSError, PermissionError):
            # 跳过无法访问的路径
            continue
```

## 错误处理

### 解析失败处理
- 记录失败文件和错误信息
- 继续处理其他文件
- 向量化失败的块自动跳过

### 向量生成失败
```python
try:
    embedding = embedder.encode(code)
    if not embedding or not embedding[0]:
        skipped_chunks += 1
        continue
except Exception as e:
    logger.warning(f"向量生成失败: {e}")
    skipped_chunks += 1
    continue
```

### 数据库插入失败
```python
try:
    storage.insert(chunks)
except Exception as e:
    if "ArrowInvalid" in str(e) or "ListType" in str(e):
        # 切换到文本搜索
        storage = create_storage_with_fallback(config)
    else:
        raise
```

## 性能优化

### 批量处理
- **批大小**：100-200 代码块
- **内存管理**：逐个文件处理，不加载整个项目到内存
- **进度显示**：Rich 进度条实时反馈

### 增量索引
```python
# 增量索引（跳过已索引文件）
stats = indexer.index_project(
    root_path,
    incremental=True  # 仅处理新增和修改文件
)
```

### 向量索引优化
- **条件创建**：代码块 >= 100 时创建向量索引
- **索引类型**：IVF_PQ（速度）或 HNSW（精度）
- **自动创建**：索引完成后自动创建

## 代码块示例

### Python 函数
```python
@decorator
def my_function(arg1: str, arg2: int) -> bool:
    """函数文档"""
    return True
```

代码块提取：
```python
{
    "type": "function",
    "name": "my_function",
    "code": "@decorator\ndef my_function(arg1: str, arg2: int) -> bool:\n    \"\"\"函数文档\"\"\"\n    return True",
    "start_line": 1,
    "end_line": 5,
    "language": "python",
    "file_path": "example.py",
}
```

### Go 结构体
```go
type User struct {
    Name string
    Age  int
}

func (u User) String() string {
    return u.Name
}
```

代码块提取：
```python
[
    {
        "type": "struct",
        "name": "User",
        "code": "type User struct {\n    Name string\n    Age  int\n}",
        "start_line": 1,
        "end_line": 4,
        "language": "golang",
        "file_path": "user.go",
    },
    {
        "type": "method",
        "name": "String",
        "code": "func (u User) String() string {\n    return u.Name\n}",
        "start_line": 6,
        "end_line": 8,
        "language": "golang",
        "file_path": "user.go",
    }
]
```

## API 参考

### `parse_file(file_path: Path, language: str) -> List[Dict]`
解析单个文件并提取代码块。

**参数：**
- `file_path` - 文件路径
- `language` - 编程语言（自动检测）

**返回：**
- 代码块列表

### `CodeIndexer.index_project(root_path: Path, incremental: bool = False, batch_size: int = 100) -> Dict`
索引整个项目。

**参数：**
- `root_path` - 项目根目录
- `incremental` - 增量索引（默认 False）
- `batch_size` - 批处理大小（默认 100）

**返回：**
- 统计信息字典

### `CodeIndexer.index_file(file_path: Path) -> int`
索引单个文件。

**返回：**
- 索引的代码块数

## 命令行接口

```bash
# 索引整个项目
uv run plugins/semantic/scripts/semantic.py index

# 索引指定目录
uv run plugins/semantic/scripts/semantic.py index --path lib/parsers

# 增量索引
uv run plugins/semantic/scripts/semantic.py index --incremental

# 强制重建索引
uv run plugins/semantic/scripts/semantic.py index --force

# 自定义批大小
uv run plugins/semantic/scripts/semantic.py index --batch-size 50
```

## 相关文件

- `lib/parsers/__init__.py` - 解析器工厂
- `lib/parsers/python_parser.py` - Python 解析器
- `lib/parsers/go_parser.py` - Go 解析器
- `lib/parsers/simple_parser.py` - 通用解析器
- `lib/database/indexer.py` - 代码索引器
- `lib/embedding/__init__.py` - 向量生成
