# parser — 学习增量识别算法

> 从 transcripts 流中抽取**值得长期记住**的增量 (用户校正 / 关键决策 / 踩坑 / L0 硬性规则), 非学习内容 (寒暄 / 工具调用细节 / 短答) 全 skip.

## "学习增量" 定义

学习增量 = **下次再遇到同类问题时, 我希望已经知道这条**. 反例: "OK"、"好的"、"已完成"、纯进度更新.

## 四类增量 + 信号词

| 类型 | 触发词 / 模式 (用户消息为主) | 候选层级 | 备注 |
| --- | --- | --- | --- |
| **user-correction** | `no/wrong/not that/不对/错了/不是这样/应该是` 紧邻上下文 | L1-long / L2-mid | 用户校正 = 模型先前判断偏离, 必须长期记住 |
| **decision** | `let's use X/我们用 X/决定用/选 X/用 X 不用 Y/方案 A` | L2-mid / L3-short | 选型 / 技术决策; 跨项目通用度高 → L2, 仅本次 → L3 |
| **tip** (踩坑) | `X failed because/原因是/坑在/注意 X/踩坑/小心/会导致` | L2-mid | 踩坑经验, 默认 L2 (中期复用) |
| **L0-rule** (硬性规则) | `永远/硬性/never/严禁/绝不/必须 (强语气)/禁止` + 行为约束语境 | L0-core (ask) | 最高优先级; 永远 ask (即使 --apply) |

## 提取流程

```
for session in 全部 jsonl 文件 (按 mtime 老→新):
  buffer = []  # 上下文窗口 (前 3 条消息)
  for msg in stream(session):
    if msg.type == "user":
      text = extract_text(msg.content)
      增量 = match_signals(text, buffer)         # 跑四类匹配
      if 增量:
        候选 = build_candidate(增量, buffer, msg)
        yield 候选
    buffer.append(msg)
    if len(buffer) > 3: buffer.pop(0)
```

**关键**: 仅扫 `type=user` 消息 (用户主动表达 = 学习增量主源). assistant 消息只作上下文.

## 候选对象 schema

```json
{
  "id": "<sha256(text + timestamp)[:12]>",
  "session_file": "<absolute path to .jsonl>",
  "session_id": "<uuid>",
  "project_slug": "-Users-luoxin-x",
  "timestamp": "ISO 8601",
  "kind": "user-correction|decision|tip|L0-rule",
  "trigger_keywords": ["不对", "应该是"],
  "text_excerpt": "<前 80 字摘要, 保护敏感>",
  "context_before": ["<前 3 条消息 type:text 缩略 ≤ 40 字>"],
  "suggested_level": "L0-core|L1-long|L2-mid|L3-short",
  "weight": 0.0-1.0,
  "needs_user_review": true
}
```

`text_excerpt` 严格截前 80 字 + `...`, 防 dry-run plan 暴露完整敏感对话.

## 三轴判定 (复用 cortex-extract)

| 轴 | history-digest 信号源 |
| --- | --- |
| 抗遗忘度 | 消息 timestamp (老 = 已被遗忘, 优先 promote) |
| 强度 | 信号词权重 (永远=1.0 / 不对=0.7 / 决定=0.6 / 暂时=0.3 / 默认=0.5) |
| 复用面 | 跨 session 同类增量计数 (≥ 3 提议 promote-L2 标; ≥ 5 + weight ≥ 0.8 提议 promote-L1 标) |

具体算法 + 8 顺序决策权威见 `../../cortex-extract/references/classifier.md`. 本文件只列 history-digest 专属信号源映射.

## 字段不识别策略

- 行 parse error → skip + warn 输出 `{"file":..., "line":..., "error":...}`
- `content` 形态既非 string 也非 array → skip + warn
- `type` 缺失 → skip + warn
- 未知 `type` 值 → skip 静默 (容忍未来扩展, 不刷屏)

聚合 warning 计数最后输出 `{"warnings": N, "skipped_lines": [...]}`, 不污染候选 plan.

## 去重

同一候选可能被多 session 触发, 用 `id = sha256(归一化 text + ±1h timestamp 桶)[:12]` 合并, 累加 `occurrences` 计数 (用于复用面判定).

归一化: 去首尾空白 + 小写化 ASCII + 折叠连续空白. 中文 / Unicode 不动.

## 反例

下列**不应**产生候选:
- 用户消息纯空 / 只含 emoji / 只 "OK"
- 用户消息纯路径 / 命令行 (无自然语言)
- 用户消息长度 < 8 字符 (噪声)
- 单纯进度询问 "好了吗 / 怎么样了" (无学习内容)
- assistant 自我陈述 "我建议..." (非用户决策, 仅模型推荐)
