---
name: trellisx-spec
description: '初始化 / 优化 / 重写 .trellis/spec/ 规则文档, 允许破坏式变更 (丢弃旧版本、合并、拆分、推翻原结构), 把描述性条款改为可机器验证的命令式契约 (MUST / 禁 / 严禁)。流程: 诊断 (初始化跳过) → 提案 → AskUserQuestion 强制审批 → 执行 + 同步 task manifest 引用清单。严禁未确认改写。sediment 模式 = finish 前自动判定触发 (有增量才沉淀, 软约束); planning 时 spec 自动加载 (交叉引用 trellisx-flow/orchestrate)'
when_to_use: '提及 spec 的初始化/优化/重写/收紧/refactor, 或抱怨 spec 弱/不可执行。sediment 由 flow finish 步自动判触发。短语 "优化 spec"'
argument-hint: '[scope]'
arguments: '[范围]'
---

# 立即执行: Spec 破坏式优化

本 skill 触发后, **main 直接按以下 5 步流程执行**, 不要 fork 到 sub-agent (sub-agent 无法走 AskUserQuestion 审批门)。立即开始, 无需等待进一步指令。

## 第 1 步: 检测项目环境与模式

> **推荐配套**: optimize/sediment 模式做破坏式重构前, 可先 `/trellisx-grill` 对现有 spec 审一轮 (轴 C 验证可执行性 / H 触发准确性 / I token / J 自举矛盾 / K 诚实边界), grill 出的弱点喂给下方诊断, 避免重构时丢关键约束。grill 可在任意阶段调用 (非仅前置)。

```bash
# 1.1 确认 .trellis/ 存在
ls -la .trellis/ 2>/dev/null
# 不存在则报错退出: "当前目录非 trellis 项目, 终止"

# 1.2 列 .trellis/spec/ 内容
find .trellis/spec -type f 2>/dev/null

# 1.3 查当前 active task (用于 sediment 模式判定)
python3 ./.trellis/scripts/task.py current 2>/dev/null || true
```

**模式自动判定** (按 1.2 / 1.3 结果):

| 现状 (按行从上往下匹配, 命中即停) | 模式 | 进入第 2 步分支 |
| --- | --- | --- |
| `.trellis/spec/` 不存在 / 空 / 仅含 index.md (`find .trellis/spec -type f` 仅 0 或 1 行且为 index.md) | **init** | 2A |
| `task.py current` 非空, 且满足任一: 用户输入含触发词 `沉淀` / `任务完成` / `收尾` / `学习沉淀` ; 或 task 已在 Phase 3 ; 或 **finish 前自动判定有 spec 增量** (trellisx-flow finish 步触发) | **sediment** | 2C |
| 以上均不命中 (有 spec 内容, 用户要求优化 / 重写 / 收紧) | **optimize** | 2B |

参数 `$范围` (skill 启动时传入): 限制本次处理范围 (目录 glob / 文件路径 / `all`)。缺省 = `all`。

> 📄 **spec 主动化 (软约束, 两端自动)**:
> - **planning 自动加载**: trellisx-flow / trellisx-orchestrate 在 planning 开始时主动 grep `.trellis/spec/` 按主题加载相关 guide 注入 PRD 上下文 (有相关 spec 才加载, 无则跳过)。本 skill 不负责加载, 仅提供 spec 内容供加载。
> - **finish 前 sediment 自动判定**: trellisx-flow finish 步主动判本 task 有无 spec 增量 (非平凡契约 / 踩坑 / 反复犯错), 有则触发本 skill sediment 模式 (提案→审批→写盘), 无则跳过。**非用户主动调**, 是流程自动判定 ("如需" = AI 判)。
> - **sediment ≠ cortex**: sediment 是 spec 自身增量沉淀 (命令式契约), 非 cortex 知识库归档。两者并存, 各管各的。

## 第 2 步: 按模式读 references + 准备提案

### 分支 2A (init 模式)

读 `references/init-mode.md` + `references/rewrite-style.md` + `references/propose.md`。

按 `init-mode.md` 模板生成首版提案 (NEW 类型变更), 输出到主会话:

```
spec init 模式首版提案 (共 N 项 NEW)
─────────────────────────────────
#1 NEW .trellis/spec/index.md
#2 NEW .trellis/spec/guides/<file>.md
...
```

跳到第 3 步。

### 分支 2B (optimize 模式)

读 `references/diagnose.md` 跑体检, 输出体检报告到主会话 (不写盘):

```
spec 体检报告
─────────────
文件清单 + 行数
命令式比例: X% (达标 ≥ 60%)
描述式残留: Y 处
死链: Z 处
建议提案: ...
```

读 `references/propose.md` + `references/rewrite-style.md`, 按诊断结果生成提案 (DELETE / REWRITE / MERGE / SPLIT / EXTRACT / PATCH 类型)。

跳到第 3 步。

### 分支 2C (sediment 模式)

读 `references/sediment-mode.md` + `references/propose.md`。

读 active task 的 `prd.md` / `design.md` / `implement.md` / `journal-*.md`, 提炼"本任务非平凡发现" (踩坑 / 教训 / 反复犯错 / 跨任务可复用契约), 按 `sediment-mode.md` 模板生成提案 (PATCH / NEW 为主)。

跳到第 3 步。

## 第 3 步: 🔴 直接调 AskUserQuestion 审批 (🛑 STOP)

> 🔴 **CHECKPOINT · 🛑 STOP**: 写盘前**硬性停在此**。**立即调用 `AskUserQuestion` 工具**弹选项, 禁在文本里写"是否同意?"等回复。未经工具明确批准 → 0 写盘。

读 `references/approve.md` 设计问句结构 (单一批准 / 选择性多选 / 高风险二次确认)。

用户在工具内选 "取消" / 未明确批准 → 立即停, 返回 "0 变更, 用户驳回"。
用户选 "全部批准" 或 "按编号选择 (选中项)" → 进入第 4 步。

**禁止**:
- 用文本提问代替工具调用 (用户无法用工具 UI 选择 = 失去审批门设计)
- 等待用户在对话里打字回复 (走文本回复 = 拖慢 + 易误解)

## 第 4 步: 一次性写盘 + 同步

用户批准后, 读 `references/execute.md` 执行:

- 一次写盘 (避免中间状态)
- 每文件附 frontmatter (`updated` / `rewrite-version` / `supersedes` / `authored-by: trellisx-spec` / `mode`)
- 同步 index / 锚点 / 导航
- grep 受影响 task manifest (`implement.jsonl` / `check.jsonl`), 列引用清单 (本 skill 不动 manifest)

## 第 5 步: 自检 + 返回报告

读 `references/selfcheck.md` 跑自检 (命令式比例 / 描述式残留 / 死链 / 首段说明 / frontmatter / index 锚点对齐)。

返回主会话最终报告:

```
spec 变更执行报告
═════════════════
模式: <init | optimize | sediment>
范围: <$范围>
批准 N 项, 执行 M 项
新增 / 修改 / 删除文件清单
受影响 task manifest: <count>
自检结果: <达标 / 未达标项>
```

## 边界硬规

- 仅读写 `.trellis/spec/**`; **禁**触碰 `.trellis/tasks/**` / `.trellis/workspace/**` / 源码
- 仅 grep `implement.jsonl` / `check.jsonl` (只读), 列引用清单给用户, **禁**直接编辑 task manifest
- AskUserQuestion 不可跳过, 不接受纯文本批准
- 多文件写盘中途失败 → 全部回滚 (git checkout 或 backup)

## ⛔ 反例黑名单 (禁做 → 改为)

命中任一条即停, 按"改为"修正后再继续。**只写应做、不列禁做即视为流程缺陷。**

| ⛔ 禁做 | ✅ 改为 | 为什么 |
| --- | --- | --- |
| 破坏式重写 spec, 丢掉原版关键约束 (MUST / 禁项 / 阈值) | REWRITE 前先抽原文全部命令式条款列表, diff 核对新版逐条覆盖, 缺失项显式标注 (合并 / 故意删 / 漏) | 破坏式 ≠ 失忆, 静默丢约束 = 引入回归 |
| 增量小改 (补 1 条规则 / 改 1 个阈值) 也走破坏式 REWRITE | 增量捕获走 trellis 原生 `trellis-update-spec`; 本 skill 只接 init / 整体优化 / 收尾沉淀 | 杀鸡用牛刀, 整文件重写放大 diff 与审批成本 |
| 未经 AskUserQuestion 工具批准直接写盘 (含"看起来无害"的小改) | 第 3 步硬停, 必须经 AskUserQuestion 工具选项批准; 纯文本"是否同意"不算批准 | 失去审批门 = 破坏式变更失控, 用户无法逐项否决 |
| 改完 spec 不管引用它的 task manifest | 写盘后 grep `implement.jsonl` / `check.jsonl`, 列受影响引用清单交用户 (本 skill 不改 manifest) | 锚点 / 路径漂移后 manifest 引用变死链, 静默失效 |
| 凭主观臆测写需求 / 约束进 spec ("应该是这样") | 每条契约据源 (源码行 / 既有 spec / 任务 journal 实证); 无据则标 `推测:` 或不写 | spec 是机器可验证契约, 臆测条款误导后续所有任务 |
| 把"建议 / 通常 / 可以考虑"等描述式软话写成 spec 条款 | 改写为命令式 (MUST / MUST NOT / 禁 / 必), 且尽量 lint/grep/test 可验 | 描述式条款无法机器验证, 等于没立规则 |
| 多文件写盘中途失败后留半截状态 | 立即全部回滚 (git checkout / backup 还原), 返回失败原因, 禁留部分写入 | 半截 spec 比旧 spec 更危险 (新旧条款并存自相矛盾) |

## 立场 (写 spec 条款时遵守)

| 立场 | 说明 |
| --- | --- |
| 允许破坏 | 推翻原结构、删冗余、改命名、不保持向后兼容 |
| 拒绝静默写 | 每次破坏前必须展示 plan + 影响面, 经用户批准后才动盘 |
| 命令式优于描述式 | "MUST/MUST NOT/禁/必" 替代 "建议/通常/可以考虑" |
| 可机器验证 > 可读 | 优先 lint/test/grep 可验证条目, 而非空泛文字 |
| 引证而非复述 | 外部已有规则用相对路径 + 锚点引用, 不抄过来制造漂移 |

## 失败处理

- 工具瞬时错误 → 重试 1 次
- 用户驳回审批 → 立即停, 返回 "0 变更, 用户驳回"
- 阶段 1 诊断无问题 (健康度全达标) → 跳到结束, 返回 "spec 健康, 无变更建议"
- 多文件写盘中途失败 → 回滚已写文件, 返回失败原因
- 当前目录非 trellis 项目 → 立即停, 返回 "非 trellis 项目, 终止"

## References 索引 (按需读)

| 文件 | 用途 |
| --- | --- |
| `references/diagnose.md` | optimize 模式体检 |
| `references/propose.md` | 提案分类 + 影响面计算 |
| `references/approve.md` | AskUserQuestion 问句设计 |
| `references/execute.md` | 写盘 + frontmatter + manifest 同步 |
| `references/rewrite-style.md` | 命令式重写范本 (旧 → 新对照) |
| `references/init-mode.md` | init 模式首版模板 |
| `references/sediment-mode.md` | sediment 模式任务学习提炼 |
| `references/selfcheck.md` | 执行后自检命令 |
