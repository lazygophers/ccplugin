# Design — novelist 检测门控满分 + 维度细分 + 检测修复合并入参模式

## 1. mode=detect|fix 入参统一设计

三 skill 统一在 `argument-hint` + `arguments` 支持 `mode` 前缀入参。解析规则：用户输入首 token 为 `detect` / `fix` → 设 mode；否则按 skill 默认（向后兼容）。

| skill | detect | fix（默认） | 默认理由 |
|---|---|---|---|
| novelist-proofread | 只读扫描，产出报告，**不改正文** | 报告 + 就地 Edit 修正（现状） | 现 proofreader 已是 fix 一体；保持 fix 默认向后兼容 |
| novelist-check | 只读审查，产出冲突清单（现状） | 审查 + 派 chapter-writer 定点修单点冲突 | 现 check 是只读 detect；保持 detect 默认向后兼容 |
| novelist-rewrite | 只读诊断「哪些章/冲突需重写 + 建议模式 A/B/C」，不改文件 | 执行重写 A/B/C（现状） | 现 rewrite 是 fix-only；保持 fix 默认 |

### mode 解析（伪码，三 skill 一致）

```
input → 首token
  "detect" → mode=detect, 范围=剩余token
  "fix"    → mode=fix,    范围=剩余token
  其他     → mode=默认,    范围=原input
```

frontmatter `argument-hint` 统一改为 `[mode: detect|fix] [范围]` 形式。

## 2. check mode=fix 与 rewrite 模式 A 边界（R2 化解）

| 维度 | check mode=fix | rewrite 模式 A |
|---|---|---|
| 触发 | 单条冲突 / 小范围定点 | 跨多章 / 结构性冲突清单 |
| 手段 | continuity-auditor 直接在受影响段落 Edit（文字级修正事实） | 派 chapter-writer 重写整段/整章 |
| 改动尺度 | 段内单点改几个事实陈述 | 整段重写 |
| 不做 | 不重写整段、不删章、不改结构 | — |

判定规则：冲突可「改一处事实陈述」消除 → check fix；需「重写段落衔接」→ 仍走 rewrite 模式 A。SKILL 内写明分流。

continuity-auditor agent 现 tools 含 Edit，但审查模式禁用。改为：
- 审查模式（detect）：禁用 Edit（只写报告）
- 修复模式（fix）：允许 Edit 正文单点事实修正；段落级重写仍交 chapter-writer

## 3. 维度细分 — proofread 5→12 子项

| 维度 | 子项（12） |
|---|---|
| 1 错别字(3) | 1a 形近字（己/已、的/得/地）／1b 音近字／1c 多字漏字 |
| 2 语法(3) | 2a 成分残缺（缺主/谓/宾）／2b 搭配不当／2c 语序与关联词（含语序错乱、关联词误用） |
| 3 标点(2) | 3a 误用与缺失／3b 中英标点混用与引号书名号配对 |
| 4 用词(2) | 4a 啰嗦重复与口语书面混杂／4b 生造词 |
| 5 用字统一(2) | 5a 人物称呼译名（基准 人物/_索引.md）／5b 术语专有名词（基准 设定/_索引.md） |

计 3+3+2+2+2 = 12 ✓。每子项独立报告条数 + detect/fix。

## 4. 维度细分 — check 6→18 子项

| 维度 | 子项（18） |
|---|---|
| 1 设定冲突(3) | 1a 物品定义不一／1b 术语定义不一／1c 组织定义不一 |
| 2 人物矛盾(3) | 2a 关系突变无铺垫／2b 行为违背性格动机／2c 生死状态错乱（已死又出场等） |
| 3 世界观违规(3) | 3a 力量超 规则.md 边界／3b 未付代价／3c 势力格局自相矛盾 |
| 4 时间线错乱(3) | 4a 事件顺序矛盾／4b 年龄经历与 历史.md 对不上／4c 时长跨度不合理 |
| 5 伏笔遗漏(3) | 5a 过计划回收章未回收／5b 结尾悬空伏笔／5c 伏笔间相互矛盾 |
| 6 逻辑合理性(3) | 6a 因果断裂／6b 关键转折动机不足／6c 过度巧合 |

计 3×6 = 18 ✓。每子项独立 detect + 严重度 + 计数。

## 5. 满分门控公式（==100 零容忍）

### proofread 质量分（保持公式，改阈值）

```
每千字错误密度 = 修正前错误数(12子项合计) ÷ 章节千字数
质量分 = 100 − 密度 × 6   （下限 0）
门控：质量分 == 100（即 错误数 == 0）才过；< 100 → STOP 重校
```

零错误 ⟺ 满分。任一子项有错 → 密度>0 → <100 → 不过。

### check 健康分（保持公式，改阈值 + 🟢 计入）

```
健康分 = 100 − (致命×20 + 重要×5 + 建议×1)   （下限 0）
门控：健康分 == 100（即 致命=重要=建议=0）才过；< 100 → mode=fix 修复后重检
```

🟢建议级也扣 1 分 → 零容忍。18 子项任一有冲突（含 🟢）→ 不过。

### rewrite 定稿分棘轮（改阈值）

```
定稿分 = 一致性×0.5 + 文字×0.2 + 人味×0.3
棘轮：重写后定稿分 > 重写前 且 == 100 才定稿
```

==100 要求一致性/文字/人味三项全满分（因加权和==100 ⟺ 各项==100）。

### pipeline workflow.js

```js
const PASS_TOTAL = 100;       // 39 行 95→100
const PASS_CONSISTENCY = 100; // 40 行 95→100
const PASS_HUMANNESS = 100;   // 41 行 95→100
```

computeScores（74-81 行）cScore 现为二值（冲突?80:100）。满分门控下保持二值即可：有任一冲突 → cScore=80 < 100 不过；零冲突 → 100 过。tScore/hScore 由 extractScore 解析 proofread/humanize agent 返回的「X分」，满分门控要求 ==100。

**补强**：computeScores 增加「满分判定」——cScore<100 或 tScore<100 或 hScore<100 → total<100 → 不过。现有 `Math.round(c×0.5+t×0.2+h×0.3)` 在三项非全 100 时自然 < 100，已满足。仅需改阈值常量。

### workflow.js checker/proofread agent prompt 对齐

checker prompt（235-）增「18 子项」；proofread prompt（273-）增「12 子项」；fixer（282-）增 mode=fix 语义。agent prompt 文本改动，非逻辑改动。

## 6. 死循环兜底（R1）

满分零容忍 + `MAX_FIX_ATTEMPTS=Infinity` 可能死循环。三 SKILL 各加：

```
连续 3 次重检未达 ==100 → 🔴 STOP，报告未过子项 + 建议转人工裁决
```

workflow.js 由 `MAX_FIX_ATTEMPTS=Infinity` 保留（用户既定），但 finalizer 输出未满分时明确标「需人工」。

## 7. frontmatter 字数底线（AC8）

- description < 512 字符：三 SKILL 现 description 均 < 400，加 mode 说明后仍可控；改时校验。
- when_to_use < 128 字符：现均 < 120，加 `detect|fix` 触发词后校验。

## 8. chapter-writer 共用说明（AC5 补）

chapter-writer.md 加一段：「被 novelist-rewrite（模式 A/B/C）与 novelist-check（mode=fix 段落级修复）共用；check fix 时只重写冲突段落，不改章结构」。

## 9. 不变性

- 三 skill 核心职责不变（proofread=文字 / check=一致性 / rewrite=重写）。
- 破坏性操作（rewrite 模式 B 删章）确认+备份铁律不变。
- detect 模式一律只读不改（除 continuity-auditor 预检模式既有的路线图修正）。

## 10. 回滚

纯文档 + workflow.js 常量/字符串改动，git revert 即可。无数据迁移。
