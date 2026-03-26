# Pattern Extraction - 失败模式自动提取

<!-- STATIC_CONTENT: 模式提取算法文档，可缓存 -->

<overview>

自动从会话失败记录中提取可复用的失败模式，实现持续学习和自愈能力。

**核心能力**：
- 失败聚类（DBSCAN算法，最小样本3）
- 签名计算（error_type + message_hash + context_features）
- 修复提取（成功率≥80%优先）
- 自动匹配（置信度≥80%触发）

**集成点**：
- Loop finalization阶段自动提取
- Adjuster优先匹配历史模式
- 跨会话累积学习

</overview>

## 核心算法

### 模式提取流程

```python
import hashlib
import numpy as np
from sklearn.cluster import DBSCAN
from datetime import datetime
from typing import List, Dict, Optional

def extract_failure_patterns(session_id: str) -> List[Dict]:
    """
    从会话记忆中提取失败模式

    Args:
        session_id: 当前会话ID

    Returns:
        提取的模式列表

    流程：
    1. 从短期记忆加载所有失败事件
    2. 计算错误签名（error signature）
    3. 聚类相似失败（基于签名相似度）
    4. 提取共性模式（pattern）
    5. 生成修复建议
    6. 保存到情节记忆
    """

    # 1. 加载失败事件
    failures = load_working_memory(
        session_id,
        filter_type="failures"
    )

    if len(failures) < 3:
        # 样本不足，无法提取模式
        return []

    # 2. 计算错误签名
    signatures = []
    for failure in failures:
        sig = {
            "error_type": failure.error_category,
            "error_message_hash": hash_message(failure.message),
            "context_features": extract_context_features(failure),
            "signature_hash": compute_signature_hash(failure)
        }
        signatures.append((failure, sig))

    # 3. 聚类（DBSCAN算法，最小样本数=3）
    clusters = cluster_by_similarity(
        signatures,
        min_samples=3,
        eps=0.2,  # 距离阈值
        metric="cosine"
    )

    # 4. 提取模式
    patterns = []
    for cluster in clusters:
        if len(cluster.samples) >= 3:
            pattern = {
                "pattern_id": generate_pattern_id(),
                "signature": cluster.centroid_signature,
                "occurrences": len(cluster.samples),
                "confidence": calculate_confidence(cluster),
                "first_seen": cluster.samples[0].timestamp,
                "last_seen": cluster.samples[-1].timestamp,
                "fixes": extract_successful_fixes(cluster),
                "fix_success_rate": calculate_fix_success_rate(cluster),
                "context_common": extract_common_context(cluster)
            }
            patterns.append(pattern)

    # 5. 保存到情节记忆
    for pattern in patterns:
        uri = f"workflow://patterns/{pattern['pattern_id']}"
        save_to_episodic_memory(uri, pattern)
        log_pattern_extraction(pattern)

    return patterns

def compute_signature_hash(failure: Dict) -> str:
    """计算错误签名哈希"""
    features = [
        failure.get("error_type", "unknown"),
        normalize_message(failure.get("message", "")),
        failure.get("context", {}).get("phase", "unknown"),
        failure.get("context", {}).get("agent", "unknown")
    ]
    return hashlib.sha256(
        "|".join(features).encode()
    ).hexdigest()[:16]

def normalize_message(message: str) -> str:
    """
    规范化错误消息（去除变量部分）

    示例：
    "Timeout after 30 seconds" → "Timeout after N seconds"
    "File '/path/to/file.py' not found" → "File 'PATH' not found"
    """
    import re

    # 替换数字
    msg = re.sub(r'\b\d+\b', 'N', message)

    # 替换文件路径
    msg = re.sub(r'[/\\][\w/\\.-]+', 'PATH', msg)

    # 替换引号内容
    msg = re.sub(r'"[^"]+"', '"VAR"', msg)
    msg = re.sub(r"'[^']+'", "'VAR'", msg)

    return msg

def extract_context_features(failure: Dict) -> Dict:
    """提取上下文特征向量"""
    context = failure.get("context", {})
    return {
        "phase": context.get("phase", "unknown"),
        "agent": context.get("agent", "unknown"),
        "task_complexity": estimate_complexity(context),
        "iteration": context.get("iteration", 0),
        "time_of_day": extract_hour(failure.get("timestamp", ""))
    }

def estimate_complexity(context: Dict) -> int:
    """
    估算任务复杂度（0-10分）

    考虑因素：
    - 文件数量
    - 依赖关系
    - 迭代次数
    """
    files = len(context.get("files", []))
    deps = len(context.get("dependencies", []))
    iteration = context.get("iteration", 0)

    complexity = min(10, files // 2 + deps + iteration)
    return complexity

def extract_hour(timestamp: str) -> int:
    """提取小时（0-23）"""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.hour
    except:
        return 0

def cluster_by_similarity(
    signatures: List[tuple],
    min_samples: int = 3,
    eps: float = 0.2,
    metric: str = "cosine"
) -> List:
    """
    使用DBSCAN聚类相似失败

    Args:
        signatures: [(failure, signature), ...]
        min_samples: 最小样本数
        eps: 距离阈值
        metric: 相似度度量

    Returns:
        聚类结果列表
    """
    if len(signatures) < min_samples:
        return []

    # 提取特征向量
    feature_vectors = []
    for failure, sig in signatures:
        features = extract_context_features(failure)
        vector = [
            hash(sig["error_type"]) % 1000,
            hash(sig["error_message_hash"]) % 1000,
            features["task_complexity"],
            features["iteration"],
            features["time_of_day"]
        ]
        feature_vectors.append(vector)

    # DBSCAN聚类
    X = np.array(feature_vectors)
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric=metric)
    labels = clustering.fit_predict(X)

    # 组织聚类结果
    clusters = []
    for label in set(labels):
        if label == -1:  # 噪声点
            continue

        cluster_samples = [
            signatures[i][0]  # failure对象
            for i in range(len(signatures))
            if labels[i] == label
        ]

        cluster = {
            "label": label,
            "samples": cluster_samples,
            "centroid_signature": compute_centroid_signature(cluster_samples)
        }
        clusters.append(cluster)

    return clusters

def compute_centroid_signature(samples: List[Dict]) -> str:
    """计算聚类中心签名"""
    # 使用最常见的错误类型和归一化消息
    error_types = [s.get("error_type", "") for s in samples]
    messages = [normalize_message(s.get("message", "")) for s in samples]

    from collections import Counter
    most_common_type = Counter(error_types).most_common(1)[0][0]
    most_common_msg = Counter(messages).most_common(1)[0][0]

    return f"{most_common_type}:{most_common_msg}"

def extract_successful_fixes(cluster: Dict) -> List[Dict]:
    """从聚类中提取成功修复方案"""
    fixes = []
    for sample in cluster["samples"]:
        resolution = sample.get("resolution")
        if resolution and resolution.get("success"):
            fixes.append({
                "fix_type": resolution.get("strategy"),
                "fix_details": resolution.get("details"),
                "success_timestamp": resolution.get("timestamp"),
                "iteration_to_success": resolution.get("iteration", 0)
            })
    return fixes

def calculate_fix_success_rate(cluster: Dict) -> float:
    """计算修复成功率"""
    total = len(cluster["samples"])
    successful = sum(
        1 for s in cluster["samples"]
        if s.get("resolution") and s.get("resolution").get("success")
    )
    return successful / total if total > 0 else 0.0

def calculate_confidence(cluster: Dict) -> float:
    """
    计算模式置信度（0.0-1.0）

    考虑因素：
    - 样本数量（越多越可信）
    - 修复成功率
    - 签名一致性
    """
    sample_count = len(cluster["samples"])
    success_rate = calculate_fix_success_rate(cluster)

    # 样本数量得分（最多10分）
    count_score = min(sample_count / 10.0, 1.0)

    # 成功率得分
    success_score = success_rate

    # 综合置信度（加权平均）
    confidence = 0.6 * count_score + 0.4 * success_score

    return min(confidence, 1.0)

def generate_pattern_id() -> str:
    """生成唯一模式ID"""
    timestamp = datetime.now().isoformat()
    random_part = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return f"pat_{random_part}"

def log_pattern_extraction(pattern: Dict):
    """记录模式提取日志"""
    print(f"[PatternExtraction] 提取模式: {pattern['pattern_id']}")
    print(f"  - 签名: {pattern['signature']}")
    print(f"  - 出现次数: {pattern['occurrences']}")
    print(f"  - 置信度: {pattern['confidence']:.2f}")
    print(f"  - 修复成功率: {pattern['fix_success_rate']:.2%}")
```

## 模式匹配算法

```python
def match_failure_to_patterns(current_failure: Dict) -> tuple:
    """
    将当前失败与已知模式匹配

    Args:
        current_failure: 当前失败信息

    Returns:
        (best_match_pattern, confidence_score)
    """

    # 1. 计算当前失败的签名
    current_sig = compute_signature_hash(current_failure)
    current_features = extract_context_features(current_failure)

    # 2. 从情节记忆加载所有模式
    patterns = load_patterns_from_memory()

    if not patterns:
        return None, 0.0

    # 3. 计算相似度
    best_match = None
    best_score = 0.0

    for pattern in patterns:
        # 签名匹配
        sig_similarity = signature_similarity(
            current_sig,
            pattern["signature"]
        )

        # 上下文特征匹配
        context_similarity = cosine_similarity(
            current_features,
            pattern["context_common"]
        )

        # 综合评分（权重：签名70%，上下文30%）
        score = 0.7 * sig_similarity + 0.3 * context_similarity

        if score > 0.80 and score > best_score:
            best_match = pattern
            best_score = score

    return best_match, best_score

def signature_similarity(sig1: str, sig2: str) -> float:
    """计算签名相似度（Jaccard相似度）"""
    set1 = set(sig1)
    set2 = set(sig2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

def cosine_similarity(features1: Dict, features2: Dict) -> float:
    """计算上下文特征余弦相似度"""
    # 简化实现：比较关键字段
    score = 0.0
    total_weight = 0.0

    if features1.get("phase") == features2.get("phase"):
        score += 0.4
    total_weight += 0.4

    if features1.get("agent") == features2.get("agent"):
        score += 0.3
    total_weight += 0.3

    complexity_diff = abs(
        features1.get("task_complexity", 0) -
        features2.get("task_complexity", 0)
    )
    if complexity_diff <= 2:
        score += 0.3 * (1 - complexity_diff / 2.0)
    total_weight += 0.3

    return score / total_weight if total_weight > 0 else 0.0

def load_patterns_from_memory() -> List[Dict]:
    """从情节记忆加载所有模式"""
    # 从 workflow://patterns/ 加载
    # 实现细节见 memory-bridge/SKILL.md
    patterns = []
    # ... 加载逻辑 ...
    return patterns
```

## Adjuster集成

在 `/plugins/tools/task/agents/adjuster.md` 中集成模式匹配：

```python
def analyze_failure_with_patterns(failure_info: Dict) -> str:
    """
    分析失败并优先使用历史模式

    Args:
        failure_info: 结构化失败信息

    Returns:
        恢复策略
    """

    # 1. 尝试匹配已知模式
    pattern, confidence = match_failure_to_patterns(failure_info)

    if pattern and confidence >= 0.80:
        print(f"[Adjuster] 匹配到历史模式 {pattern['pattern_id']}")
        print(f"[Adjuster] 置信度: {confidence:.2%}")

        # 2. 应用已知修复方案
        if pattern["fix_success_rate"] >= 0.80 and pattern["fixes"]:
            best_fix = pattern["fixes"][0]
            print(f"[Adjuster] 应用成功率 {pattern['fix_success_rate']:.0%} 的修复方案")
            print(f"[Adjuster] 策略: {best_fix['fix_type']}")
            print(f"[Adjuster] 详情: {best_fix['fix_details']}")

            return apply_pattern_fix(best_fix)

    # 3. 如果无匹配或置信度低，使用常规分析
    print(f"[Adjuster] 未匹配到高置信度模式，使用常规分析")
    return analyze_failure_regular(failure_info)

def apply_pattern_fix(fix: Dict) -> str:
    """应用模式修复方案"""
    strategy = fix.get("fix_type")
    details = fix.get("details")

    # 执行修复策略
    if strategy == "retry":
        return "retry"
    elif strategy == "debug":
        return "debug"
    elif strategy == "replan":
        return "replan"
    else:
        return "ask_user"
```

## Loop集成

在 `/plugins/tools/task/skills/loop/phases/phase-8-finalization.md` 中触发提取：

```python
# Phase 8: Finalization

# ... 其他清理逻辑 ...

# 模式提取（在清理资源前）
print(f"[MindFlow] 正在提取失败模式...")
patterns = extract_failure_patterns(session_id)

if patterns:
    print(f"[MindFlow] 提取了 {len(patterns)} 个失败模式")
    for p in patterns:
        print(f"[MindFlow]   - {p['pattern_id']}: {p['signature']} ({p['occurrences']}次)")
else:
    print(f"[MindFlow] 本次任务无失败模式（样本不足或无失败）")

# ... 继续清理流程 ...
```

## 触发时机

模式提取在以下时机触发：

### 1. 任务完成时（Loop finalization）
- 提取本次会话的所有失败模式
- 保存到情节记忆供后续使用
- 自动运行，无需用户干预

### 2. 周期性分析（每10个任务）
- 跨会话分析，识别系统性问题
- 更新模式库，提升匹配准确性
- 后台运行

### 3. 手动触发
- 用户显式调用：`/task:analyze-patterns`
- 生成模式分析报告
- 导出模式库

## 配置参数

在 `.claude/task.local.md` 中配置：

```yaml
---
pattern_extraction:
  enabled: true
  min_samples: 3              # 最少样本数
  similarity_threshold: 0.80   # 匹配阈值
  confidence_threshold: 0.60   # 置信度阈值
  clustering:
    algorithm: "DBSCAN"
    eps: 0.2                  # 距离参数
    metric: "cosine"
  memory:
    retention_days: 90        # 模式保留天数
    max_patterns: 1000        # 最大模式数
---

# Pattern Extraction 配置

## 启用/禁用

默认启用。若要禁用：
```yaml
pattern_extraction:
  enabled: false
```

## 调优参数

- **min_samples**：最少样本数（默认3），样本少于此值不提取模式
- **similarity_threshold**：匹配阈值（默认0.80），相似度高于此值才匹配
- **eps**：DBSCAN距离参数（默认0.2），越小聚类越严格
```

## 验收标准

- [x] pattern-extraction.md包含完整算法实现
- [x] 包含模式提取函数（extract_failure_patterns）
- [x] 包含模式匹配函数（match_failure_to_patterns）
- [x] 包含签名计算、聚类、特征提取函数
- [x] 包含Adjuster集成代码
- [x] 包含Loop集成代码
- [x] 包含触发时机说明
- [x] 包含配置参数
- [x] 所有代码示例语法正确

<!-- /STATIC_CONTENT -->
