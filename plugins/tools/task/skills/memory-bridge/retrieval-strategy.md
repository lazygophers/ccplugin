# 记忆检索策略

## 检索场景

| 场景 | 触发时机 | 检索目标 | 方法 |
|------|---------|---------|------|
| 相似任务匹配 | Planner信息收集 | 情节记忆(成功/失败) | `search_similar_episodes()` |
| 失败模式匹配 | Adjuster失败分析 | 情节记忆(失败) | `search_failure_patterns()` |
| 项目知识加载 | Loop初始化 | 语义记忆(核心) | `load_semantic_memories()` |
| 上下文预加载 | 文件操作前 | 相关语义记忆 | `preload_context()` |

## 1. 相似任务匹配

**算法**：提取关键词→构建查询（可按task_type过滤）→Memory插件搜索→计算相似度→排序返回top-N

**相似度计算**（0-1）：字符串相似度×40% + 关键词重叠率(Jaccard)×40% + 任务类型匹配×20%

**关键词提取**：中英文分词→过滤停用词→技术术语加权(×2)→返回top-5

**任务类型推断**：feature(实现/添加) | bugfix(修复/fix) | refactor(重构/优化) | docs(文档) | test(测试)

**相似度阈值**：0.8-1.0 强烈推荐 | 0.6-0.8 可参考 | 0.4-0.6 仅参考 | <0.4 不推荐

## 2. 失败模式匹配

**算法**：提取失败关键词（优先错误类型/组件/操作词）→搜索失败情节(result=failed)→计算失败相似度→按恢复成功优先排序

**失败相似度**：错误类型匹配×50% + 关键词重叠×30% + 字符串相似度×20%

**错误类型分类**：ConfigurationError | DependencyInjectionError | DatabaseError | NetworkError | ValidationError | ParseError | ImportError | RuntimeError | TypeError | PermissionError

## 3. 上下文预加载

**触发**：Planner分析/Executor修改/Verifier验证时

**算法**：推断文件领域(architecture/testing/deployment/conventions)→按领域搜索知识→按文件扩展名搜索技术栈→按操作类型搜索约定(create:命名结构/edit:风格模式)→去重排序返回top-10

## 4. 性能优化

- **缓存**：LRU缓存相似任务检索结果（5分钟有效，maxsize=50）
- **索引**：建议对episodes按task_type/result/timestamp建索引，knowledge按domain/priority建索引

## 5. 质量评估

| 指标 | 目标 |
|------|------|
| 准确率 | ≥70% |
| 召回率 | ≥60% |
| 响应时间 | <2秒 |

改进：定期校准权重、用户反馈、A/B测试算法。
