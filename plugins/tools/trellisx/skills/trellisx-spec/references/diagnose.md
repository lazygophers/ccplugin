# Spec 诊断 (optimize 模式阶段 1)

读全部 `.trellis/spec/**` 输出体检报告。只读, 不改盘。

## 体检项目

| 指标 | 计算 | 阈值 |
| --- | --- | --- |
| 文件清单 + 行数 | `find .trellis/spec -name '*.md' -exec wc -l {} +` | — |
| 命令式比例 | `grep -E 'MUST\|MUST NOT\|禁\|必须\|严禁' ÷ 总段落` | ≥ 60% 为达标 |
| 描述式残留 | `grep -E '建议\|可以\|通常\|尽量\|应该\|考虑'` | 0 为达标, > 0 需改写 |
| 死链 / 锚点失效 | 提取所有 `[..](..)` 与 `[[..]]`, 检查目标存在 | 0 死链为达标 |
| 与外部已加载文档重复 | 与项目根 CLAUDE.md / AGENTS.md / README.md 段落相似度 ≥ 80% | 标 EXTRACT 提案 |
| 与代码现状脱节 | 规则提的 API / 文件 grep, 不存在则脱节 | 标 DELETE / REWRITE 提案 |
| 描述性垃圾条目 | 无可执行验证手段, 纯感叹 / 期望词 | 标 DELETE / REWRITE |
| task manifest 引用使用率 | 每个 spec 文件被多少 `implement.jsonl` / `check.jsonl` 引用 | 0 引用考虑 DELETE |

## 体检报告模板

```
spec 体检报告
═════════════
扫描时间: <ISO>
扫描范围: $范围
文件总数: N (总行数 M)

[健康度评分]
- 命令式比例: X% (达标 ≥ 60%)
- 描述式残留: Y 处 (达标 = 0)
- 死链: Z 处 (达标 = 0)
- 外部重复段落: K 处
- 脱节条目: L 处
- 零引用文件: P 处

[文件级清单]
guides/code-reuse-thinking-guide.md (123 行)
  命令式 35% | 描述式残留 12 处 | 死链 0 | 被引用 2 次 (task A, task B)
  问题: "建议在重用前考虑..." / "通常应该..."
  建议动作: REWRITE

guides/cross-layer-thinking-guide.md (87 行)
  命令式 70% | 描述式残留 2 处 | 死链 1 | 被引用 5 次
  问题: 引用 `.trellis/spec/legacy-x.md` 不存在
  建议动作: 修死链 + 微调描述式 (非破坏)

guides/legacy-x.md (不存在但被引用)
  建议动作: 创建占位 或 修引用方

[建议提案统计]
- DELETE: <N> 项
- REWRITE: <N> 项
- MERGE: <N> 组 (共 <M> 文件)
- SPLIT: <N> 项
- EXTRACT: <N> 项
- 微调 (非破坏式): <N> 项
```

## 诊断脚本

完成诊断可用辅助命令 (主会话直接跑):

```bash
# 命令式比例
total=$(grep -cE '^[-*]|^[0-9]+\.' .trellis/spec/**/*.md | awk -F: '{s+=$2} END {print s}')
must=$(grep -cE 'MUST|MUST NOT|禁|必须|严禁' .trellis/spec/**/*.md | awk -F: '{s+=$2} END {print s}')
echo "命令式比例: $(( must * 100 / total ))%"

# 描述式残留
grep -nE '建议|可以|通常|尽量|应该|考虑' .trellis/spec/**/*.md

# 死链
grep -nE '\[\[[^]]+\]\]|\]\([^)]+\)' .trellis/spec/**/*.md > /tmp/links.txt
# 人工或脚本逐条检查目标存在性
```

## 输出要求

- 报告写到主会话, **不落盘**
- 每个文件给 3 类标签: 健康 / 微调 / 破坏式重写
- 报告末尾列具体提案候选, 进入阶段 2

## 模式特异

- **init 模式跳过本阶段** (无 spec 可诊断)
- **sediment 模式跳过本阶段** (本任务学习是输入, 不诊断现状)
- **optimize 模式必跑**
