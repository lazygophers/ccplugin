---
name: trellisx-spec
description: 初始化 / 优化 / 重写 .trellis/spec/ 规则文档, 允许破坏式变更 (丢弃旧版本、合并、拆分、推翻原结构), 把描述性条款改为可机器验证的命令式契约 (MUST / 禁 / 严禁)。流程: 诊断 (初始化跳过) → 提案 → AskUserQuestion 强制审批 → 执行 + 同步 task manifest 引用清单。严禁未确认改写。
when_to_use: 用户提及 spec 的 初始化/优化/重写/收紧/refactor, 抱怨 spec 弱/不可执行, 任务收尾沉淀, 或说"记不住/老忘/反复犯错/又踩坑"暗示规则未沉淀。短语 "初始化 spec" "优化 spec" "记不住"。
argument-hint: [scope]
arguments: [范围]
context: fork
agent: trellisx-spec
---

# 立即执行: Spec 破坏式优化

你被启动是为了对 `.trellis/spec/` 执行 spec 优化工作 (init / optimize / sediment 三模式之一)。**现在立即开始**, 不要等待进一步指令。

## 第 1 步: 检测项目环境与模式

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

| 现状 | 模式 | 进入第 2 步分支 |
| --- | --- | --- |
| `.trellis/spec/` 不存在 / 空 / 仅含 index.md | **init** | 2A |
| 有 active task 且任务在 Phase 3 收尾 (用户调用时通常显式说"沉淀"/"任务完成"/"收尾") | **sediment** | 2C |
| 其他 (有 spec 内容, 用户要求优化 / 重写 / 收紧) | **optimize** | 2B |

参数 `$范围` (skill 启动时传入): 限制本次处理范围 (目录 glob / 文件路径 / `all`)。缺省 = `all`。

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

## 第 3 步: 走 AskUserQuestion 审批门

**强制**用 `AskUserQuestion` 工具发起审批, **禁止**纯文本"是否同意"。读 `references/approve.md` 设计问句。

用户未明确批准 → 立即停, 返回 "0 变更, 用户驳回 / 取消"。

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
