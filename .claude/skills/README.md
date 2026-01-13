# CCPlugin Skills 库

此目录包含 CCPlugin 项目的技术规范和最佳实践文档。这些文档为开发者提供了一套统一的编码标准、架构决策和实现指南。

## 📚 文档清单

### 核心规范

#### 1. [embedding-and-storage.md](./embedding-and-storage.md)
**向量嵌入和存储管理**

涵盖代码向量化、嵌入模型选择、向量数据库管理的完整规范。

**主要内容：**
- 嵌入模型选择和配置（支持 20+ 模型）
- 向量生成流程和验证机制
- LanceDB 存储实现和架构
- TextSearchStorage 后备方案
- 数据持久化和 .gitignore 配置

**关键概念：**
- 模型维度（384 到 1024）
- 向量验证（NaN/Inf 检查）
- 自动后备切换机制
- 批量索引优化

---

#### 2. [project-root-detection.md](./project-root-detection.md)
**项目根目录检测**

定义了统一的项目根目录检测策略，确保脚本在任何工作目录下都能正确运行。

**主要内容：**
- 检测优先级：`.git` > `.lazygophers` > 当前目录
- 检测算法和实现（最多 6 级目录遍历）
- 应用场景（数据路径、环境初始化、索引路径）
- 跨目录执行支持
- 边界情况处理

**关键特性：**
- 自动查找项目根目录
- 支持首次初始化
- 兼容嵌套 Git 仓库
- 毫秒级性能开销

---

#### 3. [code-indexing.md](./code-indexing.md)
**代码索引和解析**

多语言代码解析、代码块提取和索引流程的完整规范。

**主要内容：**
- 支持 20+ 编程语言（按优先级分类）
- 代码解析架构（工厂模式）
- 代码块结构和提取算法
- 完整索引流程
- 文件扫描和过滤（.gitignore 支持）
- 错误处理和性能优化

**支持的语言：**
- 高优先级：Python, Go, Rust, Java, Kotlin, TypeScript（AST/完整解析）
- 中优先级：JavaScript, C++, C#, Swift, Flutter（基础解析）
- 低优先级：C, PHP, Ruby, Bash, SQL, Markdown（简单分块）

**关键算法：**
- 语义分块（函数/类级别）
- 固定大小分块（可配置重叠）
- 安全文件扫描（权限检查）

---

## 🏗️ 架构层次

```
用户脚本
├── 项目根目录检测
│   └── 数据路径获取
├── 环境初始化
│   └── 配置管理
└── 代码索引流程
    ├── 文件扫描
    ├── 代码解析
    ├── 向量生成
    └── 数据存储
        ├── LanceDB（主）
        └── TextSearch（备）
```

## 📖 使用指南

### 开发者工作流

#### 1. 理解项目结构
- 首先阅读 [project-root-detection.md](./project-root-detection.md)
- 了解目录组织和数据位置

#### 2. 学习向量化流程
- 阅读 [embedding-and-storage.md](./embedding-and-storage.md)
- 理解嵌入模型和向量存储

#### 3. 实现代码解析
- 阅读 [code-indexing.md](./code-indexing.md)
- 了解代码块提取和语言支持

#### 4. 编写新功能
- 遵循相应 skill 中的 API 参考
- 参考代码示例
- 测试边界情况

### 快速参考

**需要初始化环境？**
→ [project-root-detection.md #环境初始化](./project-root-detection.md#应用场景)

**需要添加新的编程语言支持？**
→ [code-indexing.md #解析器实现](./code-indexing.md#解析器实现)

**需要优化向量存储性能？**
→ [embedding-and-storage.md #性能考虑](./embedding-and-storage.md#性能考虑)

**遇到了向量维度问题？**
→ [embedding-and-storage.md #向量验证](./embedding-and-storage.md#向量验证)

## ✅ 规范遵守清单

在编写代码时，确保：

### 项目根目录
- [ ] 使用 `get_data_path()` 获取数据目录，而不是硬编码路径
- [ ] 支持 `--path` 参数覆盖自动检测
- [ ] 在子目录下也能正确运行

### 向量嵌入
- [ ] 验证向量维度一致性
- [ ] 检查 NaN/Inf 值
- [ ] 使用 `numpy.float32` 确保类型统一
- [ ] 实现自动后备切换机制

### 代码索引
- [ ] 支持多种编程语言
- [ ] 生成有意义的代码块（函数/类级别）
- [ ] 实现安全的文件扫描
- [ ] 提供增量索引选项

### 错误处理
- [ ] 捕获 LanceDB 兼容性错误并切换到文本搜索
- [ ] 跳过解析失败的文件，继续处理其他文件
- [ ] 记录详细的错误日志

## 🔗 相关文件

### 核心实现
- `plugins/semantic/scripts/semantic.py` - CLI 主入口
- `lib/embedding/__init__.py` - 向量生成接口
- `lib/embedding/storage.py` - LanceDB 存储实现
- `lib/embedding/text_search.py` - 文本搜索后备
- `lib/database/indexer.py` - 代码索引器
- `lib/parsers/__init__.py` - 代码解析工厂

### 配置文件
- `.lazygophers/ccplugin/semantic/config.yaml` - 索引配置
- `.lazygophers/.gitignore` - 数据目录忽略规则

### 测试
- `lib/tests/` - 单元测试套件

## 🚀 常见任务

### 添加新的嵌入模型
1. 在 `embedding_model` 配置中定义模型
2. 确保模型维度在支持列表中
3. 重新索引项目以应用新模型

### 支持新的编程语言
1. 在 `lib/parsers/` 创建新的解析器类
2. 注册到 `lib/parsers/__init__.py` 的工厂函数
3. 在 `lib/constants/SUPPORTED_LANGUAGES` 中定义文件扩展名
4. 在此 README 中文档化语言

### 优化索引性能
1. 调整 `chunk_size` 和 `batch_size`
2. 选择合适的向量索引类型（IVF_PQ vs HNSW）
3. 启用 `incremental` 增量索引
4. 参考 [code-indexing.md #性能优化](./code-indexing.md#性能优化)

## 📝 文档维护

### 更新规则
- 功能变更时同时更新相应 skill 文档
- 新增 API 时添加 API 参考部分
- 发现新的最佳实践时更新指南
- 定期审查示例代码确保准确性

### 贡献指南
1. 根据变更类型选择相应的 skill 文件
2. 保持格式和结构一致
3. 添加代码示例和工作流说明
4. 更新相关交叉引用

## 📚 延伸阅读

- **项目总体说明** → `/README.md`
- **项目配置** → `/pyproject.toml`
- **全局规范** → `/CLAUDE.md`
- **API 文档** → `/lib/README.md`

---

**最后更新：** 2026-01-13
**版本：** 1.0
**作者：** CCPlugin 开发团队
