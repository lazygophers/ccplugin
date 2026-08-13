# Validation-Gated 优化 Loop

> 源自 SkillOpt（arXiv 2605.23904）+ darwin-skill git ratchet。核心：**skill 当作 frozen agent 的外部可训练状态，用 weight-space 优化的纪律做 text-space 优化**。

## SkillOpt 四要素（本 skill 落地）

| SkillOpt 原则 | 原文 | 本 skill 落地 |
|--------------|------|--------------|
| **bounded edits** | add / delete / replace 三类有界编辑，非自由重写 | Phase 2 编辑词表 |
| **validation-gated** | 编辑仅当 held-out validation score 严格提升才 accept | Phase 3 before/after 对比 |
| **textual learning-rate** | 限制单轮编辑量，防大改失稳 | Phase 2 单变量 + 最小可验证粒度 |
| **rejected-edit buffer** | 失败编辑入缓冲，防重复尝试 | Phase 4 失败日志 `optimization-log.md` |
| **epoch-wise slow/meta** | 慢更新（单维）+ 元更新（簇级）分层 | Phase 2 单维 + Phase 2.5 重写 |

> SkillOpt 原文：6 benchmark × 7 model × 3 harness（direct chat / Codex / Claude Code）52 cell 全 best-or-tied；GPT-5.5 上 no-skill → +23.5（direct chat）/ +24.8（Codex）/ +19.1（Claude Code）。本 skill 未复现该基准，仅借用方法论。

## 完整 Loop（对应 SKILL.md 5 Phase）

```
Phase 1 诊断
  ├─ 9 维评分（行号引用证据）
  ├─ runtime 红灯扫描（gate）
  ├─ 相关簇短板识别（HL-3）
  └─ 🔴 CHECKPOINT 用户确认方向
        │
Phase 2 设计编辑
  ├─ SkillOpt 词表归类（add/delete/replace）
  ├─ 单变量约束（1 维度 / 1 相关簇）
  └─ 最小可验证粒度（HL-1：4 行撬 +3）
        │
Phase 3 validation gate（SkillOpt 核心）
  ├─ held-out test 设计（should-trigger + should-not-trigger + edge）
  ├─ spawn 独立子 agent before/after 盲评
  ├─ 接受准则：严格提升（触发准确性 + 输出质量 + 9 维总分）
  └─ dry_run 降级（> 30% → ⚠️ 失效警告）
        │
Phase 4 ratchet
  ├─ 通过 → git 提交（分支 optimize/<skill>-YYYYMMDD）
  ├─ 未通过 → 回滚 + 失败日志
  └─ HL-4：连续 2 轮 Δ<2 → break
        │
Phase 5 回归 + 汇总
  ├─ 原 eval 场景未 break
  ├─ 变更语义标注（触发词变更 = 破坏性）
  └─ 汇总报告（before/after/Δ/judge 共识/dry_run 比例）
```

## git ratchet（darwin 借鉴）

- 优化在**独立分支**进行：`optimize/<skill-name>-YYYYMMDD`
- 每个 accepted edit 一个 commit；rejected edit 不入历史
- 回滚 = `git checkout` 回前一 commit，分支可丢弃
- 主分支保持干净，优化结果 merge 需用户确认（破坏性变更）

> 本 skill 不强制 darwin 的 `results.tsv` 历史日志（那是 darwin 重型基建）；失败尝试记 `references/optimization-log.md` 即可。需要长期历史追踪 → 路由 darwin。

## judge 独立性（SkillLens 实证要求）

SkillLens 发现 LLM-as-judge 准确率 46.4% → 加 meta-skill 维度后 73.8%。仍未到可信区间，故：

- **禁同 context 自评自改**：改完立刻同 session 打分有「我刚改的肯定更好」偏差
- **spawn 独立子 agent**：fork context，盲评（不告知哪版是改后）
- **共识要求**：≥ 2 judge 一致，或 1 full_test 实测（spawn 子 agent 真跑 test prompt 看输出）
- **分歧处理**：judge 分歧大 → 加第 3 judge 或降为 full_test；仍分歧 → 标注「评估不可信」，人审

## full_test vs dry_run

| 模式 | 做法 | 置信度 | 触发 |
|------|------|--------|------|
| **full_test** | spawn 子 agent 带 skill 跑 test prompt，对比 baseline 输出 | 高 | 默认首选 |
| **dry_run** | 读完 skill 模拟执行思路，判断流程合理 | 低 | 子 agent 不可用 / 超时 |

- dry_run 比例 > 30% → dim8 实测维度形同虚设，**评估失效警告**
- darwin 早期 40 次记录 67% dry_run，0 revert（分数虚高，从未回滚）→ 教训
- 强制：每次优化 ≥ 1 个 full_test，否则 results 显式 ⚠️
