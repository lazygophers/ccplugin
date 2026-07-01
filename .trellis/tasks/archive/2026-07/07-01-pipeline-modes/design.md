# Design — novelist-pipeline 多场景 mode 路由

## 总体架构

```
/novelist-pipeline [mode] [target] [--workflow|--no-workflow]
        │
   解析 mode + target + 载体 flag
        │
   ┌────┴──── 载体选择 ────┐
   │                       │
 (write && !--no-workflow)  其它
 || (--workflow)            ||
   ↓                       ↓
 Workflow(workflow.js)    subagent 编排 (main DAG 调度)
 mode 分支路由             派 general-purpose Agent × 章
```

## 载体选择规则

| 条件 | 载体 |
|---|---|
| mode=write 且无 --no-workflow | Workflow (默认) |
| mode=write 且 --no-workflow | subagent |
| mode≠write 且 --workflow | Workflow |
| mode≠write 且无 --workflow (默认) | subagent |

## mode 路由

### 路径 A: Workflow (workflow.js)

workflow.js 加 `mode` 入参分支。各 mode 的 phase 子集:

| mode | phases (保留) | 跳过 |
|---|---|---|
| write | 全部 (路线图→世界观→预检→write→三环→fix→定稿→统一check) | — (现状) |
| review | 查一致 + 统一检查 | 路线图/世界观/预检/写作/去AI味/校对/修复/定稿 |
| humanize | 去AI味(+fix 若 AI味 中/重) | 其余 |
| proofread | 校对(+fix 若文字硬伤) | 其余 |
| polish | 查一致+去AI味+校对+修复+定稿+统一检查 (跳 write+前置) | 路线图/世界观/预检/写作 |
| rewrite | 修复(rewrite fix 模式 A) + 统一检查 | 前置/write/三环检测/定稿 (rewrite 自带流程) |
| outline | 路线图 | 全部其余 |

**实现**: workflow.js 主流程加 `const MODE = _args.mode || "write"`，每个 phase 函数前加 `if (MODE !== "write" && !needsPhase(MODE, "phase名")) continue/skip`。write 路径零改动。

`needsPhase(mode, phase)` 映射表决定该 mode 跑哪些 phase。

### 路径 B: subagent 编排 (main)

main 解析 mode + target → 算章节范围 → DAG 调度:

```
main:
  章节范围 = parseTarget(target)  # 复用 $target 逻辑
  for 章 in DAG_order(并发上限 2):
    dispatch general-purpose Agent:
      prompt = "处理第N章 mode=<mode>, 调用 novelist-<skill> skill (mode 子参数), 范围限本章"
      Agent 内: Skill(novelist-<skill>) 执行
  统一 check (若 mode 需要): 派 1 个 Agent 跑 novelist-check 全批
```

**DAG**: 章节间 write-files 不相交 (各章独立文件) → 全可并行, 受并发上限 2 约束。统一 check 串行在末尾。

**Agent prompt 模板** (6 字段自包含):
- 目标: 对第 N 章执行 mode=<mode>
- 已知: 小说根 root, 章节文件路径, Active task 路径
- 工作目录与范围: 仅该章文件
- 输出格式: 评分/报告落 元数据/ 对应路径
- 验收: 该章 mode 完成 + 报告产出
- 失败处理: 标 `需要:` 回传

## 入参解析 (SKILL.md 激活时 main 做)

```python
# 伪码
parts = $ARGUMENTS 分词
mode = parts[0] if parts[0] in MODES else "write"  # write/review/humanize/proofread/polish/rewrite/outline
rest = parts[1:] (去掉 mode) 或 parts (mode 缺省)
workflow_flag = "--workflow" in rest ? "workflow" : "--no-workflow" in rest ? "subagent" : default(mode)
target = rest 去掉 flag 后的剩余 = $target (写到第N章/写N章/缺省下一章)
```

中文别名映射: 评审→review, 去AI味/去AI化→humanize, 校对→proofread, 润色→polish, 重写→rewrite, 大纲/路线图→outline。

## 各 mode 评分/报告产出

| mode | 报告路径 | 评分 |
|---|---|---|
| write | 现有 (检查报告/校对报告/deaigc) | 综合分 (现有) |
| review | 元数据/检查报告/第N章.md + 统一-批.md | 一致性分 |
| humanize | 元数据/校对报告/第N章-deaigc.md | 人味分 |
| proofread | 元数据/校对报告/第N章.md | 文字分 |
| polish | 三报告全产 | 综合分 |
| rewrite | 重写后正文 + 检查报告 | — |
| outline | 情节/第NNN-NNN章路线图.md | — |

## 兼容性

- write 默认行为零回归 (workflow.js write 路径不动)
- 现有 `$target` 解析逻辑保留, mode 作为前缀新增
- 无 Workflow runtime 时: 所有 mode 退化为 subagent (含 write --no-workflow 等效)

## 失败处理

- mode 无法识别 → 默认 write + 提示
- 章节范围解析失败 → AskUserQuestion
- subagent 缺信息标 `需要:` → main 转达
- Workflow mode 分支跑空 phase (如 outline 只路线图) → 正常, 跳过即不调度
