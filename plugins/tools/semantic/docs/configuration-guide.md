# Semantic 插件配置指南

本文档详细说明 Semantic 插件的配置选项和最佳实践。

## 配置文件位置

配置文件位于：
```
~/.lazygophers/ccplugin/semantic/config.yaml
```

或者项目根目录：
```
.lazygophers/ccplugin/semantic/config.yaml
```

## 配置项详解

### 相似度阈值 (similarity_threshold)

**默认值**: `0.5`

**作用**: 控制搜索结果的最小相似度要求，过滤掉低相关性的结果。

#### 取值范围

| 阈值 | 效果 | 适用场景 |
|------|------|---------|
| `0.4` | 较宽松 | 返回更多结果但可能包含不相关内容 |
| `0.5` | **默认** | 日常使用，平衡准确度和召回率 |
| `0.6` | 较严格 | 精确查找，只返回高度相关的结果 |
| `0.7+` | 非常严格 | 可能错过部分相关结果 |

#### 配置示例

```yaml
# config.yaml
similarity_threshold: 0.5
```

#### 命令行覆盖

即使配置文件中设置了阈值，您仍可以通过命令行参数临时覆盖：

```bash
# 使用配置文件中的阈值（默认 0.5）
/semantic search "用户登录"

# 临时使用 0.6 的阈值
/semantic search "用户登录" --threshold 0.6
/semantic search "用户登录" -t 0.6

# 临时使用 0.4 的阈值（更宽松）
/semantic search "用户登录" --threshold 0.4
```

#### 实际效果示例

假设有以下搜索结果及其相似度：

```
相似度: 0.95 - UserController.authenticate()    ✓
相似度: 0.85 - UserService.login()             ✓
相似度: 0.75 - LoginView.render()             ✓
相似度: 0.58 - UserSession.validate()         ✗ (低于 0.5)
相似度: 0.45 - UserProfile.update()           ✗ (低于 0.5)
相似度: 0.32 - UserSettings.get()             ✗ (低于 0.5)
```

- **阈值 0.5**: 返回前 3 个结果（默认）
- **阈值 0.4**: 返回前 4 个结果
- **阈值 0.6**: 返回前 2 个结果

#### 如何选择阈值

**选择 0.4（宽松）**:
- 初次探索代码库
- 不确定具体的函数名
- 想要看到更多相关结果

**选择 0.5（默认）**:
- 日常代码搜索
- 平衡准确度和召回率
- 大多数使用场景

**选择 0.6+（严格）**:
- 精确定位功能
- 减少噪音结果
- 已知代码结构

### 嵌入模型选择 (embedding_model)

**默认值**: `multilingual-e5-large`

选择合适的模型可以平衡搜索准确度和性能。

#### 推荐配置

| 模型 | 维度 | 特点 | 适用场景 |
|------|------|------|---------|
| `bge-small-en` | 384 | 轻量快速 | 资源受限环境 |
| `bge-small-zh` | 512 | 中文优化 | 中文项目 |
| `bge-large-en` | 1024 | 高精度 | 生产环境 |
| `gte-large` | 1024 | 综合性能优秀 | 高质量搜索 |
| `jina-code` | 768 | 代码专用 | 代码理解 |
| `multilingual-e5-large` | 1024 | 多语言高精度 | 默认模型 |

### 代码分块配置

**chunk_size**: 代码分块大小（字符数），默认 500
**chunk_overlap**: 分块重叠大小（字符数），默认 50

```yaml
chunk_size: 500
chunk_overlap: 50
```

#### 推荐配置

| 项目类型 | chunk_size | chunk_overlap |
|---------|-----------|--------------|
| 小型项目 | 300-400 | 30-40 |
| 中型项目（默认） | 500 | 50 |
| 大型项目 | 800-1000 | 80-100 |

### 搜索引擎配置 (engines)

Semantic 提供三个独立引擎：

```yaml
engines:
  fastembed:
    enabled: True
    model: "multilingual-e5-large"
  codemodel:
    enabled: True
    model: "codet5+"
  symbols:
    enabled: True
```

#### FastEmbed 引擎

- **优点**: 速度快，资源占用低
- **缺点**: 对代码语义理解有限
- **适用**: 快速搜索、资源受限环境

#### CodeModel 引擎

- **优点**: 对代码语义理解深入
- **缺点**: 资源占用高，索引慢
- **适用**: 代码理解、重构分析
- **需要**: `uv sync --all-extras`

#### Symbols 引擎

- **优点**: 极快速度，精确名称匹配
- **缺点**: 不支持语义搜索
- **适用**: 快速定位已知函数/类

### 检索策略 (search_strategy)

```yaml
search_strategy: hybrid
```

#### 策略类型

| 策略 | 描述 | 适用场景 |
|------|------|---------|
| `fast` | 仅 FastEmbed | 小项目、快速原型 |
| `hybrid` | 融合三个引擎（推荐） | 大项目、生产环境 |
| `code` | 仅 CodeModel | 代码理解、重构 |
| `symbols` | 仅符号索引 | 快速定位 |

### 融合权重配置 (fusion_weights)

仅在使用 `hybrid` 策略时生效：

```yaml
fusion_weights:
  symbols: 0.1      # 符号索引权重
  fastembed: 0.5    # 向量搜索权重
  codemodel: 0.4    # 代码模型权重
```

#### 推荐配置

**语义搜索优先**（默认）:
```yaml
symbols: 0.1
fastembed: 0.5
codemodel: 0.4
```

**精确匹配优先**:
```yaml
symbols: 0.6
fastembed: 0.2
codemodel: 0.2
```

**完全均衡**:
```yaml
symbols: 0.33
fastembed: 0.34
codemodel: 0.33
```

### 语言配置 (languages)

启用/禁用特定编程语言：

```yaml
languages:
  python: true
  golang: true
  javascript: false
  typescript: false
```

### 排除模式 (exclude_patterns)

索引时排除的文件/目录：

```yaml
exclude_patterns:
  - node_modules
  - .git
  - .venv
  - venv
  - __pycache__
  - "*.min.js"
  - "*.min.css"
```

## 完整配置示例

```yaml
# 向量数据库后端
backend: lancedb

# 嵌入模型
embedding_model: "multilingual-e5-large"

# GPU 加速
use_gpu: True

# 代码分块
chunk_size: 500
chunk_overlap: 50

# 相似度阈值
similarity_threshold: 0.7

# Git 忽略
gitignore: True

# 搜索引擎
engines:
  fastembed:
    enabled: True
    model: "multilingual-e5-large"
  codemodel:
    enabled: True
    model: "codet5+"
  symbols:
    enabled: True

# 检索策略
search_strategy: hybrid

# 融合权重
fusion_weights:
  symbols: 0.1
  fastembed: 0.5
  codemodel: 0.4

# 启用的语言
languages:
  python: true
  golang: true
  javascript: true
  typescript: true

# 排除模式
exclude_patterns:
  - node_modules
  - .git
  - .venv
  - __pycache__
```

## 命令行操作

### 查看配置

```bash
# 查看当前配置
/semantic config

# 查看支持的语言
/semantic languages
```

### 初始化和索引

```bash
# 初始化索引
/semantic init

# 重建索引
/semantic-index
```

### 搜索

```bash
# 基本搜索（使用配置文件的阈值）
/semantic search "用户登录"

# 指定阈值
/semantic search "用户登录" --threshold 0.8

# 限制结果数量
/semantic search "用户登录" --limit 20

# 限定语言
/semantic search "用户登录" --lang python-skills
```

## 配置测试

运行测试脚本验证配置：

```bash
cd scripts
python3 test_config.py
```

输出示例：
```
✅ 配置加载测试通过！

总结:
  - 配置文件路径: ~/.lazygophers/ccplugin/semantic/config.yaml
  - 相似度阈值: 0.7
  - 推荐用途: 日常使用（默认），平衡准确度和召回率
```

## 最佳实践

1. **从默认配置开始**
   - 使用 `similarity_threshold: 0.5`
   - 使用 `search_strategy: hybrid`

2. **根据项目规模调整**
   - 小项目: 减小 `chunk_size`
   - 大项目: 增加 `chunk_size`

3. **根据需求调整阈值**
   - 初次探索: 降低到 0.4
   - 精确查找: 提高到 0.6

4. **使用命令行参数临时调整**
   - 不需要频繁修改配置文件
   - 使用 `--threshold` 临时覆盖

5. **定期重建索引**
   - 代码更新后运行 `/semantic index`
   - 确保搜索结果准确

## 常见问题

### Q: 如何提高搜索准确度？

A:
1. 提高相似度阈值到 0.6
2. 使用 `hybrid` 检索策略
3. 启用所有三个引擎

### Q: 为什么没有搜索结果？

A:
1. 检查相似度阈值是否过高
2. 尝试降低阈值到 0.4
3. 确认已建立索引

### Q: 搜索太慢怎么办？

A:
1. 切换到 `fast` 检索策略
2. 禁用 CodeModel 引擎
3. 减小 `limit` 参数

### Q: 如何临时改变阈值？

A: 使用命令行参数：
```bash
/semantic search "查询" --threshold 0.8
```

## 更新日志

**2025-01-07**
- ✅ 更新 `similarity_threshold` 默认值为 0.5
- ✅ 支持命令行参数覆盖
- ✅ 添加配置测试脚本
