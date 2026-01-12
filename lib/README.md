# CCPlugin Common Library - 使用指南

## 概述

这是 CCPlugin Market 的公共库，包含所有插件都可以复用的通用组件。

```
lib/
├── config/         - 配置和路径管理
├── constants/      - 常量定义（语言映射等）
├── utils/          - 通用工具函数
├── embedding/      - 向量嵌入和存储
├── parsers/        - 代码解析器
├── search/         - 搜索和查询处理
├── database/       - 数据库操作
├── mcp/            - MCP 服务支持
└── tests/          - 测试套件
```

---

## 快速开始

### 在你的插件中使用公共库

#### 第一步：设置导入路径

在你的脚本顶部添加以下代码：

```python
#!/usr/bin/env python3

import sys
from pathlib import Path

# 添加项目根目录到 sys.path
script_path = Path(__file__).resolve().parent
project_root = script_path.parent.parent.parent  # 根据你的目录深度调整

# 如果自动查找失败，使用备选策略
if not (project_root / 'lib').exists():
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / 'lib').exists():
            project_root = current
            break
        current = current.parent

sys.path.insert(0, str(project_root))
```

#### 第二步：导入需要的模块

```python
# 配置和路径管理
from lib.config import get_data_path, get_config_path, load_config

# 常量定义
from lib.constants import SUPPORTED_LANGUAGES

# 工具函数
from lib.utils import check_and_auto_init

# 其他模块
from lib.embedding import EmbeddingGenerator
from lib.parsers import CodeParser
from lib.search import QueryProcessor
```

---

## 模块详解

### 1. Config - 配置管理 (P0)

**用途**：管理项目配置和数据路径

```python
from lib.config import get_data_path, load_config

# 获取项目数据目录
data_path = get_data_path()
# 返回: /project/.lazygophers/ccplugin/[plugin_name]/

# 加载配置文件（如果不存在返回默认配置）
config = load_config()
# 返回: {'backend': 'lancedb', 'embedding_model': 'default', ...}

# 指定项目根目录
config = load_config('/custom/project/root')
```

**常见用途**：
- 获取插件的数据存储目录
- 加载插件配置文件
- 获取配置默认值

---

### 2. Constants - 常量定义 (P0)

**用途**：提供编程语言和文件扩展名的映射

```python
from lib.constants import SUPPORTED_LANGUAGES

# 获取所有支持的语言
all_languages = list(SUPPORTED_LANGUAGES.keys())
# ['python', 'golang', 'javascript', 'typescript', ...]

# 获取特定语言的扩展名
python_exts = SUPPORTED_LANGUAGES['python']  # ['.py']
js_exts = SUPPORTED_LANGUAGES['javascript']  # ['.js', '.jsx', '.mjs']

# 检查文件是否支持
file_path = 'example.py'
file_ext = '.' + file_path.split('.')[-1]
is_supported = any(
    file_ext in exts
    for exts in SUPPORTED_LANGUAGES.values()
)
```

**支持的语言**：
- Python, Go, JavaScript, TypeScript, Rust, Java
- C, C++, C#, Kotlin, Swift, Dart, PHP, Ruby
- Bash, SQL, Markdown, Dockerfile, PowerShell

---

### 3. Utils - 工具函数 (P0)

**用途**：通用的工具函数

```python
from lib.utils import check_and_auto_init

# 检查系统初始化状态
if check_and_auto_init():
    print("System ready")
else:
    print("System not initialized")
```

---

### 4. Embedding - 向量嵌入 (P1)

**用途**：文本和代码的向量化

```python
from lib.embedding import EmbeddingGenerator

# 创建嵌入生成器
gen = EmbeddingGenerator('bge-small-en')  # 384维

# 生成向量
embeddings = gen.encode(['hello', 'world'])
# 返回: [[...384 floats...], [...384 floats...]]

# 获取向量维度
dim = gen.get_dim()  # 384
```

**支持的模型**：
- BGE 系列（推荐）
- Jina 系列
- Sentence Transformers
- Arctic 系列
- E5 系列

---

### 5. Parsers - 代码解析器 (P1)

**用途**：解析多种编程语言的代码

```python
from lib.parsers import CodeParser, PythonParser

# 创建解析器
parser = PythonParser()

# 解析文件
symbols = parser.parse_file('example.py')
# 返回: [
#   {'type': 'function', 'name': 'foo', 'start_line': 1, ...},
#   {'type': 'class', 'name': 'Bar', 'start_line': 10, ...}
# ]

# 解析代码字符串
code = "def hello(): pass"
symbols = parser.parse_code(code, 'temp.py')
```

**支持的解析器**：
- PythonParser, JavaScriptParser, GoParser, RustParser
- JavaParser, KotlinParser, FlutterParser, 等

---

### 6. Search - 搜索和查询 (P1)

**用途**：搜索和查询处理

```python
from lib.search import QueryProcessor, BM25Searcher

# 处理查询意图
processor = QueryProcessor()
intent = processor.process_query('find function definition')
# 返回: QueryIntent.FIND_DEFINITION

# 关键词搜索
searcher = BM25Searcher()
results = searcher.search('my function', ['file1.py', 'file2.py'])
```

---

### 7. Database - 数据库操作 (P2)

**用途**：符号索引和数据库管理

```python
from lib.database import SymbolIndex

# 创建索引
index = SymbolIndex()
index.initialize()

# 添加符号
index.add_symbol({
    'id': 'sym_001',
    'name': 'my_function',
    'file': 'example.py'
})
```

---

## 测试

### 运行所有测试

```bash
# 使用 pytest
pytest lib/tests/ -v

# 或使用 unittest
python3 -m unittest discover lib/tests -v
```

### 运行特定模块的测试

```bash
pytest lib/tests/test_config.py -v
pytest lib/tests/test_constants.py -v
pytest lib/tests/test_integration.py -v
```

---

## 常见问题

### Q: 如何在新插件中使用公共库？

A:
1. 参考"快速开始"部分设置导入路径
2. 从 lib 目录导入需要的模块
3. 查看本指南了解具体 API

### Q: 如何添加新的模块到公共库？

A:
1. 在 `lib/[category]/` 下创建新文件
2. 添加 docstring 和使用示例
3. 编写单元测试 `lib/tests/test_[module].py`
4. 更新本 README

### Q: 如何处理特定插件的配置？

A:
```python
from lib.config import get_data_path

# 获取插件特定的数据目录
plugin_data = get_data_path() / 'my_plugin'
plugin_data.mkdir(exist_ok=True)
```

### Q: 导入失败怎么办？

A:
1. 确保项目根目录（包含 lib 文件夹）在 sys.path 中
2. 检查 Python 版本（要求 3.8+）
3. 确保所有依赖已安装：`uv pip install [package_name]`

---

## 依赖列表

### P0（核心模块 - 无外部依赖）
- ✓ config
- ✓ constants
- ✓ utils

### P1（嵌入和搜索 - 需要额外依赖）

```bash
# 向量嵌入
uv pip install fastembed sentence-transformers

# 向量存储
uv pip install lancedb pyarrow

# 代码解析
uv pip install tree-sitter

# 搜索和查询
uv pip install bm25l

# MCP 支持
uv pip install mcp pydantic
```

### P2（数据库 - 可选）

```bash
# SQLite 和 YAML
uv pip install pyyaml  # Python 内置支持 sqlite3
```

---

## 贡献指南

如果你想向公共库添加新功能：

1. **设计**：与团队讨论新模块的设计
2. **实现**：在 `lib/[category]/` 下创建文件
3. **测试**：为新代码编写单元测试
4. **文档**：更新本 README 和代码注释
5. **审查**：提交 PR 进行代码审查
6. **合并**：审查通过后合并到主分支

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-01-12 | 初始版本：35 个模块，完整测试覆盖 |

---

## 联系和支持

- 📧 提问或报告问题：提交 GitHub Issue
- 🤝 贡献代码：提交 Pull Request
- 📚 查看完整报告：[MIGRATION_REPORT.md](./MIGRATION_REPORT.md)

---

## 许可证

与 CCPlugin Market 项目相同

---

**最后更新**：2026-01-12
**维护者**：CCPlugin Team
**状态**：✅ 生产就绪（Production Ready）
