# Pattern Extraction - 失败模式自动提取

<!-- STATIC_CONTENT: 模式提取算法文档，可缓存 -->

## 概述

自动从会话失败记录中提取可复用的失败模式，实现持续学习和自愈。

**核心能力**：失败聚类(DBSCAN,min_samples=3) | 签名计算(error_type+message_hash+context) | 修复提取(成功率≥80%优先) | 自动匹配(置信度≥80%触发)

**集成点**：Loop finalization自动提取 | Adjuster优先匹配历史模式 | 跨会话累积学习

## 核心算法

### 模式提取流程

1. **加载失败事件**：从短期记忆加载(filter_type=failures)，<3条样本则跳过
2. **计算错误签名**：error_type + normalize_message(数字→N,路径→PATH,引号内→VAR) + context_features(phase/agent/complexity/iteration)
3. **DBSCAN聚类**：特征向量(error_type_hash, message_hash, complexity, iteration, hour)，eps=0.2, metric=cosine
4. **提取模式**：pattern_id/signature/occurrences/confidence/first_seen/last_seen/fixes/fix_success_rate/context_common
5. **保存**：写入情节记忆 `workflow://patterns/{pattern_id}`

### 置信度计算

confidence = 0.6 × min(sample_count/10, 1.0) + 0.4 × fix_success_rate

## 模式匹配

1. 计算当前失败签名和上下文特征
2. 加载所有已知模式
3. 综合评分：签名相似度(Jaccard)×70% + 上下文相似度(phase×0.4+agent×0.3+complexity×0.3)×30%
4. score>0.80 且 fix_success_rate≥0.80 → 应用历史修复方案
5. 否则降级常规分析

## 触发时机

1. **Loop finalization**：自动提取本次失败模式并保存
2. **周期性分析**：每10个任务跨会话分析
3. **手动触发**：`/task:analyze-patterns`

## 配置

```yaml
pattern_extraction:
  enabled: true
  min_samples: 3
  similarity_threshold: 0.80
  confidence_threshold: 0.60
  clustering: { algorithm: DBSCAN, eps: 0.2, metric: cosine }
  memory: { retention_days: 90, max_patterns: 1000 }
```

<!-- /STATIC_CONTENT -->
