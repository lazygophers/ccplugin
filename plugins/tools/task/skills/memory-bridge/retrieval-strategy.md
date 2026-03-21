# 记忆检索策略（Retrieval Strategy）

## 概述

本文档定义 Memory Bridge 的记忆检索策略，包括相似任务匹配、失败模式匹配、上下文智能预加载等核心算法。

## 检索场景

| 场景 | 触发时机 | 检索目标 | 使用方法 |
|------|---------|---------|---------|
| **相似任务匹配** | Planner 信息收集 | 情节记忆（成功/失败） | `search_similar_episodes()` |
| **失败模式匹配** | Adjuster 失败分析 | 情节记忆（失败） | `search_failure_patterns()` |
| **项目知识加载** | Loop 初始化 | 语义记忆（核心知识） | `load_semantic_memories()` |
| **上下文预加载** | 文件操作前 | 相关语义记忆 | `preload_context()` |

## 1. 相似任务匹配策略

### 目标
找到与当前任务最相似的历史任务情节，提供规划参考。

### 算法步骤

```python
def search_similar_episodes(
    user_task: str,
    task_type: str = None,
    limit: int = 5
) -> list:
    """
    检索相似任务情节

    返回：按相似度排序的情节列表（包含 similarity_score）
    """

    # 1. 提取任务关键词
    keywords = extract_keywords(user_task)

    # 2. 构建搜索查询
    if task_type:
        # 优先搜索同类型任务
        search_query = f"{' '.join(keywords)}"
        search_domain = f"workflow://task-episodes/{task_type}"
    else:
        # 跨类型搜索
        search_query = f"{' '.join(keywords)}"
        search_domain = "workflow://task-episodes"

    # 3. 调用 Memory 插件搜索
    raw_results = Skill("memory", f"search '{search_query}' --domain workflow --limit 20")

    # 4. 计算相似度并排序
    scored_episodes = []
    for episode in raw_results:
        similarity = calculate_similarity(user_task, episode["task_desc"])
        scored_episodes.append({
            **episode,
            "similarity_score": similarity
        })

    # 5. 按相似度排序并返回 top-N
    scored_episodes.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored_episodes[:limit]
```

### 关键词提取算法

```python
import re
from collections import Counter

def extract_keywords(text: str, top_n: int = 5) -> list:
    """
    提取任务描述的关键词

    策略：
    1. 分词（支持中文、英文）
    2. 过滤停用词
    3. 提取高频词和技术术语
    """

    # 停用词表（中文 + 英文）
    stopwords = {
        # 中文
        "的", "了", "和", "是", "在", "有", "为", "与", "以", "及",
        "对", "等", "将", "到", "并", "等", "需要", "实现", "功能",
        # 英文
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "as", "is", "was", "are"
    }

    # 技术术语增强（提高权重）
    tech_terms = {
        "api", "rest", "graphql", "database", "redis", "mysql", "postgres",
        "authentication", "authorization", "login", "jwt", "oauth",
        "typescript", "javascript", "python", "java", "go", "rust",
        "react", "vue", "angular", "nestjs", "express", "fastapi",
        "test", "unit test", "integration test", "e2e",
        "refactor", "optimize", "migration", "upgrade"
    }

    # 1. 中文分词（简单实现，生产环境建议使用 jieba）
    # 匹配中文词、英文词、数字
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|[0-9]+', text.lower())

    # 2. 过滤停用词
    filtered_words = [w for w in words if w not in stopwords and len(w) > 1]

    # 3. 计算词频
    word_counts = Counter(filtered_words)

    # 4. 技术术语加权
    for term in tech_terms:
        if term in word_counts:
            word_counts[term] *= 2  # 技术术语权重翻倍

    # 5. 返回 top-N 关键词
    top_keywords = [word for word, count in word_counts.most_common(top_n)]

    return top_keywords
```

### 相似度计算算法

```python
from difflib import SequenceMatcher

def calculate_similarity(task1: str, task2: str) -> float:
    """
    计算两个任务描述的相似度（0.0-1.0）

    综合考虑：
    1. 字符串相似度（40%）
    2. 关键词重叠率（40%）
    3. 任务类型匹配（20%）
    """

    # 1. 字符串相似度（Levenshtein 距离）
    string_similarity = SequenceMatcher(None, task1.lower(), task2.lower()).ratio()

    # 2. 关键词重叠率
    keywords1 = set(extract_keywords(task1))
    keywords2 = set(extract_keywords(task2))

    if not keywords1 or not keywords2:
        keyword_overlap = 0.0
    else:
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        keyword_overlap = len(intersection) / len(union)

    # 3. 任务类型匹配（从任务描述推断）
    type1 = infer_task_type(task1)
    type2 = infer_task_type(task2)
    type_match = 1.0 if type1 == type2 else 0.5

    # 4. 加权综合
    final_similarity = (
        string_similarity * 0.4 +
        keyword_overlap * 0.4 +
        type_match * 0.2
    )

    return round(final_similarity, 2)


def infer_task_type(task_desc: str) -> str:
    """
    从任务描述推断任务类型
    """
    task_lower = task_desc.lower()

    if any(keyword in task_lower for keyword in ["实现", "添加", "新增", "开发", "implement", "add", "create"]):
        return "feature"
    elif any(keyword in task_lower for keyword in ["修复", "解决", "bug", "fix", "resolve", "issue"]):
        return "bugfix"
    elif any(keyword in task_lower for keyword in ["重构", "优化", "refactor", "optimize", "improve"]):
        return "refactor"
    elif any(keyword in task_lower for keyword in ["文档", "注释", "doc", "documentation", "comment"]):
        return "docs"
    elif any(keyword in task_lower for keyword in ["测试", "test", "unit", "e2e", "integration"]):
        return "test"
    else:
        return "unknown"
```

### 相似度阈值策略

| 相似度范围 | 推荐策略 |
|-----------|---------|
| 0.8 - 1.0 | 高度相似，强烈推荐参考 |
| 0.6 - 0.8 | 中度相似，可以参考 |
| 0.4 - 0.6 | 低度相似，仅供参考 |
| 0.0 - 0.4 | 不相似，不推荐 |

## 2. 失败模式匹配策略

### 目标
找到与当前失败相似的历史失败情节，提供恢复策略参考。

### 算法步骤

```python
def search_failure_patterns(
    failure_reason: str,
    task_type: str = None,
    limit: int = 5
) -> list:
    """
    检索相似失败模式和恢复策略

    返回：按相似度排序的失败情节列表
    """

    # 1. 提取失败关键词
    failure_keywords = extract_failure_keywords(failure_reason)

    # 2. 构建搜索查询
    search_query = f"{' '.join(failure_keywords)}"

    if task_type:
        search_domain = f"workflow://task-episodes/{task_type}"
    else:
        search_domain = "workflow://task-episodes"

    # 3. 搜索失败情节（只检索 result=failed）
    raw_results = Skill("memory", f"search '{search_query}' --domain workflow --limit 20")

    # 4. 过滤出失败情节并计算相似度
    failure_patterns = []
    for episode in raw_results:
        if episode.get("result") != "failed":
            continue

        episode_failure_reason = episode.get("failure", {}).get("reason", "")
        similarity = calculate_failure_similarity(failure_reason, episode_failure_reason)

        # 只保留中度以上相似的失败（>0.4）
        if similarity >= 0.4:
            failure_patterns.append({
                "episode_id": episode["episode_id"],
                "task_desc": episode["task_desc"],
                "failure_reason": episode_failure_reason,
                "error_type": episode.get("failure", {}).get("error_type", "Unknown"),
                "recovery_action": episode.get("failure", {}).get("recovery_action"),
                "recovery_success": episode.get("failure", {}).get("recovery_success", False),
                "lessons_learned": episode.get("failure", {}).get("lessons_learned", ""),
                "similarity_score": similarity
            })

    # 5. 排序：优先推荐恢复成功的失败情节
    failure_patterns.sort(key=lambda x: (x["recovery_success"], x["similarity_score"]), reverse=True)

    return failure_patterns[:limit]
```

### 失败关键词提取

```python
def extract_failure_keywords(failure_reason: str) -> list:
    """
    提取失败原因的关键词

    特别关注：
    1. 错误类型（Error、Exception、Failure）
    2. 错误组件（Service、Repository、Controller）
    3. 错误操作（connect、parse、validate、inject）
    """

    # 错误类型关键词（高权重）
    error_types = {
        "error", "exception", "failure", "crash", "timeout",
        "错误", "异常", "失败", "崩溃", "超时"
    }

    # 组件关键词
    components = {
        "service", "repository", "controller", "module", "middleware",
        "database", "api", "cache", "queue",
        "服务", "仓库", "控制器", "模块", "中间件", "数据库", "接口", "缓存", "队列"
    }

    # 操作关键词
    operations = {
        "connect", "parse", "validate", "inject", "import", "export",
        "build", "compile", "deploy", "start", "stop",
        "连接", "解析", "验证", "注入", "导入", "导出", "构建", "编译", "部署", "启动", "停止"
    }

    # 提取基本关键词
    keywords = extract_keywords(failure_reason, top_n=10)

    # 增强：优先保留错误类型、组件、操作关键词
    enhanced_keywords = []
    for word in keywords:
        if word in error_types or word in components or word in operations:
            enhanced_keywords.append(word)

    # 补充其他关键词
    for word in keywords:
        if word not in enhanced_keywords:
            enhanced_keywords.append(word)

    return enhanced_keywords[:8]  # 最多8个关键词
```

### 失败相似度计算

```python
def calculate_failure_similarity(reason1: str, reason2: str) -> float:
    """
    计算两个失败原因的相似度

    综合考虑：
    1. 错误类型匹配（50%）- 最重要
    2. 关键词重叠率（30%）
    3. 字符串相似度（20%）
    """

    # 1. 提取错误类型
    error_type1 = extract_error_type(reason1)
    error_type2 = extract_error_type(reason2)

    type_similarity = 1.0 if error_type1 == error_type2 else 0.3

    # 2. 关键词重叠率
    keywords1 = set(extract_failure_keywords(reason1))
    keywords2 = set(extract_failure_keywords(reason2))

    if not keywords1 or not keywords2:
        keyword_overlap = 0.0
    else:
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        keyword_overlap = len(intersection) / len(union)

    # 3. 字符串相似度
    string_similarity = SequenceMatcher(None, reason1.lower(), reason2.lower()).ratio()

    # 4. 加权综合
    final_similarity = (
        type_similarity * 0.5 +
        keyword_overlap * 0.3 +
        string_similarity * 0.2
    )

    return round(final_similarity, 2)


def extract_error_type(failure_reason: str) -> str:
    """
    从失败原因提取错误类型
    """
    reason_lower = failure_reason.lower()

    # 错误类型模式（按优先级排序）
    error_patterns = [
        # 配置错误
        ("ConfigurationError", ["configuration", "config", "配置"]),
        # 依赖注入错误
        ("DependencyInjectionError", ["dependency injection", "inject", "依赖注入", "注入"]),
        # 数据库错误
        ("DatabaseError", ["database", "db", "sql", "query", "数据库", "查询"]),
        # 网络错误
        ("NetworkError", ["network", "connection", "timeout", "网络", "连接", "超时"]),
        # 验证错误
        ("ValidationError", ["validation", "validate", "invalid", "验证", "非法"]),
        # 解析错误
        ("ParseError", ["parse", "parsing", "syntax", "解析", "语法"]),
        # 导入错误
        ("ImportError", ["import", "module", "导入", "模块"]),
        # 运行时错误
        ("RuntimeError", ["runtime", "运行时"]),
        # 类型错误
        ("TypeError", ["type", "类型"]),
        # 权限错误
        ("PermissionError", ["permission", "access", "权限", "访问"]),
    ]

    for error_type, patterns in error_patterns:
        if any(pattern in reason_lower for pattern in patterns):
            return error_type

    return "UnknownError"
```

## 3. 上下文智能预加载策略

### 目标
在文件操作前预加载相关的项目知识，提供上下文参考。

### 触发时机
- Planner 分析项目结构时
- Executor 修改文件前
- Verifier 验证代码时

### 算法步骤

```python
def preload_context(
    file_path: str,
    operation: str = "edit"  # edit/read/create
) -> list:
    """
    根据文件路径和操作类型预加载相关语义记忆

    返回：相关的语义记忆列表
    """

    # 1. 推断文件领域
    domain = infer_file_domain(file_path)

    # 2. 构建搜索查询
    search_queries = []

    if domain:
        # 精确领域搜索
        search_queries.append(f"search '' --domain project://knowledge/{domain}")

    # 3. 根据文件扩展名搜索相关知识
    file_ext = file_path.split('.')[-1]
    tech_stack_query = f"search '{file_ext}' --domain project://knowledge/tech-stack"
    search_queries.append(tech_stack_query)

    # 4. 根据操作类型搜索约定
    if operation == "create":
        search_queries.append("search 'naming structure' --domain project://knowledge/conventions")
    elif operation == "edit":
        search_queries.append("search 'style pattern' --domain project://knowledge/conventions")

    # 5. 执行搜索并合并结果
    context_memories = []
    for query in search_queries:
        results = Skill("memory", query)
        context_memories.extend(results)

    # 6. 去重并按优先级排序
    unique_memories = {m["uri"]: m for m in context_memories}
    sorted_memories = sorted(unique_memories.values(), key=lambda x: x.get("priority", 10))

    return sorted_memories[:10]  # 最多10条相关记忆


def infer_file_domain(file_path: str) -> str | None:
    """
    从文件路径推断知识领域
    """
    path_lower = file_path.lower()

    # 领域模式
    domain_patterns = {
        "architecture": ["repository", "service", "controller", "module", "entity", "dto"],
        "testing": ["test", "spec", "mock", "__tests__", "__mocks__"],
        "deployment": ["docker", "k8s", "deploy", "ci", "cd", ".github", ".gitlab"],
        "conventions": ["config", "settings", ".editorconfig", ".prettierrc"],
    }

    for domain, patterns in domain_patterns.items():
        if any(pattern in path_lower for pattern in patterns):
            return domain

    return None
```

## 4. 检索性能优化

### 缓存策略
```python
from functools import lru_cache
from datetime import datetime, timedelta

# 缓存相似任务检索结果（5分钟有效）
@lru_cache(maxsize=50)
def search_similar_episodes_cached(user_task: str, task_type: str = None) -> tuple:
    """
    带缓存的相似任务检索

    注意：返回 tuple 而非 list 以支持缓存
    """
    results = search_similar_episodes(user_task, task_type)
    return tuple(results)
```

### 索引优化建议

为提高检索性能，建议在 Memory 插件数据库中建立以下索引：

```sql
-- 情节记忆索引
CREATE INDEX idx_episodes_task_type ON memories(uri) WHERE uri LIKE 'workflow://task-episodes/%';
CREATE INDEX idx_episodes_result ON memories(content) WHERE json_extract(content, '$.result') = 'failed';
CREATE INDEX idx_episodes_timestamp ON memories(content, json_extract(content, '$.timestamp'));

-- 语义记忆索引
CREATE INDEX idx_knowledge_domain ON memories(uri) WHERE uri LIKE 'project://knowledge/%';
CREATE INDEX idx_knowledge_priority ON memories(priority) WHERE uri LIKE 'project://knowledge/%';

-- 全文搜索索引（如果支持）
CREATE VIRTUAL TABLE memories_fts USING fts5(uri, content, priority);
```

## 5. 检索质量评估

### 评估指标

| 指标 | 计算方法 | 目标值 |
|------|---------|--------|
| **准确率** | 推荐记忆中有用的占比 | ≥ 70% |
| **召回率** | 找到的相关记忆占所有相关记忆的比例 | ≥ 60% |
| **平均响应时间** | 检索耗时 | < 2 秒 |
| **用户满意度** | 用户反馈 | ≥ 4/5 |

### 质量改进策略

1. **定期校准**：每月分析检索日志，调整权重参数
2. **用户反馈**：在检索结果中添加"有用/无用"反馈按钮
3. **A/B 测试**：测试不同相似度算法的效果
4. **主动学习**：根据用户反馈优化关键词提取和相似度计算
