# Markdown 测试文件

## 项目概述

这是一个 **语义搜索** 插件，支持多种编程语言的代码解析和语义理解。

### 主要功能

- 🚀 **快速索引**: 基于 AST 的代码解析
- 🔍 **语义搜索**: 理解代码语义的智能搜索
- 🌐 **多语言支持**: 支持 40+ 编程语言

## 支持的语言

### 主要语言

| 语言 | 扩展名 | 状态 |
|------|--------|------|
| Python | `.py` | ✅ 完全支持 |
| Go | `.go` | ✅ 完全支持 |
| Rust | `.rs` | ✅ 完全支持 |
| JavaScript | `.js` | ✅ 完全支持 |
| TypeScript | `.ts` | ✅ 完全支持 |

### 其他语言

1. **系统编程语言**
   - C/C++
   - Java
   - C#
   - Swift
   - Kotlin

2. **脚本语言**
   - Ruby
   - PHP
   - Lua
   - Perl

3. **配置语言**
   - Bash
   - PowerShell
   - CMake
   - Makefile

## 安装方法

### 使用 uv（推荐）

```bash
# 克隆仓库
git-skills clone https://github.com/your-repo/semantic-plugin.git
cd semantic-plugin

# 同步依赖
uv sync

# 运行
uv run semantic.py
```

### 使用 pip

```bash
pip install -e .
```

## 配置示例

创建配置文件 `~/.semantic/config.json`:

```json
{
  "backend": "lancedb",
  "embedding_model": "multilingual-e5-large",
  "chunk_size": 500,
  "chunk_overlap": 50,
  "database_path": "~/.semantic/data"
}
```

## 使用指南

### 索引代码

```bash
# 索引当前目录
semantic-skills index .

# 索引指定目录
semantic-skills index /path/to/code

# 指定语言
semantic-skills index . --language python-skills
```

### 搜索代码

```bash
# 语义搜索
semantic-skills search "如何创建用户"

# 关键词搜索
semantic-skills search "User.create"

# 搜索特定文件
semantic-skills search "authenticate" --file "auth/*"
```

### 配置管理

```bash
# 查看配置
semantic-skills config

# 设置模型
semantic-skills config --model multilingual-e5-large
```

## API 文档

### 初始化

```python
from semantic-skills import SemanticSearch

# 创建搜索实例
search = SemanticSearch(
    backend="lancedb",
    embedding_model="multilingual-e5-large"
)

# 索引代码
search.index("/path/to/code")

# 搜索
results = search.search("创建用户的函数")
```

### 高级用法

```python
# 自定义分块
search.index(
    "/path/to/code",
    chunk_size=500,
    chunk_overlap=50
)

# 过滤结果
results = search.search(
    "用户认证",
    language="python",
    min_score=0.7
)
```

## 架构设计

```
semantic/
├── scripts/
│   ├── lib/
│   │   ├── parsers/        # 代码解析器
│   │   ├── embeddings/     # 嵌入模型
│   │   └── storage/        # 存储后端
│   └── semantic.py         # 主程序
├── test_data/              # 测试数据
└── pyproject.toml          # 项目配置
```

## 性能优化

### 硬件加速

插件自动检测并启用硬件加速：

- **Apple Silicon (M1/M2/M3)**: 自动启用 MPS 加速
- **NVIDIA GPU**: 自动启用 CUDA 加速
- **其他平台**: 使用 CPU 模式

### 性能指标

| 操作 | 时间 | 说明 |
|------|------|------|
| 索引 1000 行 | ~2s | 含解析和嵌入 |
| 搜索查询 | ~100ms | 语义搜索 |
| 关键词搜索 | ~50ms | 基于索引 |

## 故障排除

### 常见问题

**Q: 索引时提示 "tree-sitter-language-pack 未安装"？**

A: 运行以下命令安装依赖：
```bash
uv sync
```

**Q: 搜索结果不准确？**

A: 尝试使用更大的嵌入模型：
```bash
semantic-skills config --model multilingual-e5-large
```

**Q: Apple Silicon 上性能不佳？**

A: 确保已启用 MPS 加速：
```bash
echo "✓ 硬件加速: Apple Silicon MPS 加速"
```

## 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

### 开发流程

1. Fork 仓库
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 联系方式

- 项目主页: https://github.com/your-repo/semantic-plugin
- 问题反馈: https://github.com/your-repo/semantic-plugin/issues
- 邮箱: your-email@example.com

---

**提示**: 查看完整文档请访问 [docs/](docs/)
