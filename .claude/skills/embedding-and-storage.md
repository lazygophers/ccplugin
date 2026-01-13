---
name: 向量嵌入和存储管理
description: 代码向量化、嵌入生成和向量数据库管理的规范和最佳实践
---

# 向量嵌入和存储管理

## 概述

本 skill 定义了 CCPlugin 项目中向量嵌入生成、存储和检索的规范。涵盖代码嵌入模型、向量数据库、数据持久化和兼容性处理。

## 核心模块

### 1. 嵌入生成（lib/embedding/）

#### 模型选择
- **主模型**：`multilingual-e5-large`（1024维，多语言高精度）
- **备选模型**：
  - `bge-large-en`（1024维，英文高精度）
  - `bge-small-zh`（512维，中文优化）
  - `jina-code`（768维，代码专用）

#### 向量生成流程
```python
from lib.embedding import EmbeddingGenerator

# 初始化生成器
embedder = EmbeddingGenerator(
    model_id="multilingual-e5-large",
    use_gpu=True  # 自动检测 GPU
)

# 加载模型
if not embedder.load():
    raise Exception("模型加载失败")

# 编码文本
embedding = embedder.encode(code_text)  # 返回 [embedding_vector]
embedding_query = embedder.encode_query(query_text)  # 查询编码
```

#### 向量验证
- **维度检查**：确保所有向量维度一致（通常 384, 512, 768, 1024）
- **NaN/Inf 检查**：验证不存在无效值
- **类型转换**：使用 `numpy.float32` 确保数据类型统一

```python
import numpy as np
import math

# 向量验证
def validate_vector(vector, expected_dim):
    if len(vector) != expected_dim:
        raise ValueError(f"维度不匹配: {len(vector)} vs {expected_dim}")

    valid_values = []
    for v in vector:
        fv = float(v)
        if math.isnan(fv) or math.isinf(fv):
            raise ValueError(f"无效向量值: {fv}")
        valid_values.append(fv)

    # 转换为 numpy 数组确保类型一致
    return np.array(valid_values, dtype=np.float32).tolist()
```

### 2. 向量存储（lib/embedding/storage.py）

#### LanceDB 存储
- **数据库**：LanceDB（轻量级向量数据库）
- **表名**：`code_index`
- **索引策略**：IVF_PQ（100+ 代码块时自动创建）

#### 表结构
```python
{
    "id": str,                    # 代码块唯一ID
    "file_path": str,             # 文件路径
    "language": str,              # 编程语言
    "code_type": str,             # function/class/block
    "name": str,                  # 函数名/类名
    "code": str,                  # 代码内容
    "start_line": int,            # 起始行
    "end_line": int,              # 结束行
    "vector": List[float],        # 向量（变长列表）
    "metadata": str,              # JSON 元数据
    "indexed_at": str,            # 索引时间戳
}
```

#### 关键特性
- **延迟初始化**：表在第一次插入时由 LanceDB 自动创建
- **变长向量列表**：使用 `pa.list_(pa.float32())` 而不是 fixed-size list
- **自动 Schema 推断**：避免 PyArrow 转换问题
- **类型一致性**：所有向量先转为 numpy.float32 后再转为列表

### 3. 文本搜索后备方案（lib/embedding/text_search.py）

#### 触发条件
当 LanceDB 出现 `ArrowInvalid` 或 `ListType` 错误时自动切换到文本搜索。

#### TextSearchStorage 实现
- **索引存储**：使用 pickle 序列化的字典
- **搜索方式**：BM25-like 关键词搜索
- **倒排索引**：构建词汇到文档的映射

```python
from lib.embedding.storage import create_storage_with_fallback

# 自动切换到文本搜索
storage = create_storage_with_fallback(config)
storage.initialize(data_path)
storage.insert(items)
results = storage.search(query_text=query, limit=10)
```

## 数据库索引流程

### 完整索引流程
```
扫描文件 → 解析代码 → 生成代码块 → 创建嵌入 → 验证向量 → 存储到数据库 → 创建索引
```

### 代码块生成
```python
from lib.parsers import parse_file

# 解析单个文件
chunks = parse_file(file_path, language)
# 返回: List[{type, name, code, start_line, end_line, language, file_path}]
```

### 向量生成和存储
```python
from lib.database.indexer import CodeIndexer

indexer = CodeIndexer(config, data_path)
indexer.initialize()

# 索引单个文件
chunk_count = indexer.index_file(file_path)

# 索引整个项目
stats = indexer.index_project(root_path)
# stats: {total_files, indexed_files, total_chunks, failed_files}
```

## 配置管理

### 嵌入模型配置
配置文件：`.lazygophers/ccplugin/semantic/config.yaml`

```yaml
# 嵌入模型选择
embedding_model: multilingual-e5-large

# 硬件加速（自动检测）
# - Apple Silicon: MPS (Metal Performance Shaders)
# - NVIDIA: CUDA
# - CPU: 默认

# 代码分块参数
chunk_size: 500          # 字符数
chunk_overlap: 50        # 重叠字符数

# 向量数据库后端
backend: lancedb         # 仅支持 lancedb

# 搜索引擎配置
engines:
  fastembed:
    enabled: true
    model: multilingual-e5-large
  codemodel:
    enabled: true
    model: codet5+
  symbols:
    enabled: true

# 检索策略
search_strategy: hybrid  # fast/hybrid/code/symbols

# 融合权重（hybrid 模式下）
fusion_weights:
  symbols: 0.1
  fastembed: 0.5
  codemodel: 0.4
```

## 错误处理

### LanceDB 兼容性处理
```python
try:
    storage.insert(indexed_chunks)
except Exception as e:
    if "ArrowInvalid" in str(e) or "ListType" in str(e):
        # 自动切换到文本搜索
        from lib.embedding.storage import create_storage_with_fallback
        storage = create_storage_with_fallback(config)
        storage.initialize(data_path)
        storage.insert(indexed_chunks)
    else:
        raise
```

### 向量验证失败
- 跳过 NaN/Inf 向量
- 维度不匹配时标记失败
- 统计失败率并输出警告

## 性能考虑

### 向量维度与模型对应
| 模型 | 维度 | 特点 |
|------|------|------|
| multilingual-e5-small | 384 | 快速轻量 |
| bge-small-zh | 512 | 中文优化 |
| bge-base-en | 768 | 均衡性能 |
| multilingual-e5-large | 1024 | 高精度 |
| gte-large | 1024 | 综合优秀 |

### 批量索引优化
- 批大小：100-200 个代码块（可配置）
- 创建索引条件：>= 100 个代码块时
- 索引类型：IVF_PQ（大规模）或 HNSW（精度优先）

## 数据持久化

### 存储位置
```
.lazygophers/ccplugin/semantic/
├── config.yaml           # 配置文件
├── lancedb/              # LanceDB 数据库
│   └── code_index.lance
└── text_search/          # 文本搜索后备
    └── index.pkl         # 序列化索引
```

### .gitignore 配置
```
.lazygophers/
├── .gitignore
│   └── /ccplugin/semantic/  # 忽略所有 semantic 数据
```

## API 使用示例

### 初始化和索引
```python
# 初始化环境
uv run plugins/semantic/scripts/semantic.py init

# 索引代码
uv run plugins/semantic/scripts/semantic.py index

# 指定路径索引
uv run plugins/semantic/scripts/semantic.py index --path lib/parsers
```

### 搜索
```python
# 语义搜索
uv run plugins/semantic/scripts/semantic.py search "函数定义"

# 混合搜索
uv run plugins/semantic/scripts/semantic.py search "API" --limit 20

# 按语言过滤
uv run plugins/semantic/scripts/semantic.py search "class" --lang python
```

### 配置管理
```python
# 查看配置
uv run plugins/semantic/scripts/semantic.py config

# 设置模型
uv run plugins/semantic/scripts/semantic.py config --model bge-large-en

# 管理引擎
uv run plugins/semantic/scripts/semantic.py engines enable --engine codemodel
uv run plugins/semantic/scripts/semantic.py engines strategy --strategy hybrid
```

## 注意事项

1. **向量维度一致性**：同一项目中所有向量必须维度一致
2. **模型更换**：切换模型后需要重新索引整个项目
3. **GPU 可用性**：自动检测，如无 GPU 则自动降级到 CPU
4. **文件编码**：仅支持 UTF-8 编码文件
5. **大文件处理**：自动分块，可调整 `chunk_size` 参数

## 相关文件

- `lib/embedding/__init__.py` - 嵌入生成核心模块
- `lib/embedding/generator.py` - EmbeddingGenerator 实现
- `lib/embedding/code_model.py` - 代码模型引擎
- `lib/embedding/storage.py` - LanceDB 存储实现
- `lib/embedding/text_search.py` - 文本搜索后备方案
- `lib/database/indexer.py` - 代码索引器
