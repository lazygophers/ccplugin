---
description: Agentic RAG智能检索器 - 动态检索策略+GraphRAG知识图谱，精度高达99%
user-invocable: false
context: fork
model: sonnet
memory: project
---

# Agentic RAG 智能检索器

## 核心职责

基于Agentic RAG和GraphRAG技术，从多源并行检索高质量信息。

## 激活时机

研究任务的信息采集阶段，由 dgot-engine 驱动调用。

## 关键特性

### 1. Agentic RAG - 动态检索策略

嵌入自主AI代理，根据查询复杂度和结果质量动态调整策略：

- **深度优先**：单一主题深入挖掘
- **广度优先**：多角度快速覆盖
- **平衡搜索**：深度+广度结合（推荐）

### 2. GraphRAG 接口

知识图谱+向量搜索，语义理解精度高达99%：

- **向量搜索**：基于embedding的相似度匹配
- **知识图谱**：结构化关系推理
- **混合检索**：向量+图谱结合

### 3. 多源并行检索

8+信息源同时检索，按质量和相关性排序：

**学术源**：PubMed、IEEE、ACM、arXiv、Google Scholar
**技术源**：GitHub、Stack Overflow、技术博客
**商业源**：Gartner、IDC、McKinsey
**新闻源**：技术媒体、行业报告
**政府源**：标准文档、法规政策

## 智能过滤

四维评分机制（0-10分）：

```
总分 = 相关性×0.35 + 质量×0.30 + 时效性×0.20 + 重要性×0.15
```

**相关性**：与查询主题的匹配度
**质量**：来源权威性和内容深度
**时效性**：信息发布时间和更新频率
**重要性**：引用次数和影响力

## 执行流程

```
1. 查询分析：理解用户意图和信息需求
2. 策略选择：根据任务选择检索策略
3. 多源检索：并行查询8+信息源
4. 智能过滤：四维评分，过滤低分(<6.0)结果
5. 去重合并：识别重复内容，合并相似信息
6. 结果排序：按总分排序，返回Top-N
```

## 反思机制

检索结果不足时自动调整：

- **结果<5条**：放宽相关性阈值（0.7→0.6）
- **质量<7.0分**：扩展检索源，增加查询变体
- **时效性差**：优先最近1年的内容

## 详细文档

- [retrieval-strategies.md](retrieval-strategies.md) - 检索策略详解
- [graphrag-integration.md](graphrag-integration.md) - GraphRAG集成方法
- [sources.md](sources.md) - 信息源配置和优先级

## 使用示例

```python
# 平衡搜索（推荐）
results = retrieve(
    query="微服务架构最佳实践",
    strategy="balanced",
    min_score=7.0,
    max_results=20
)
```
