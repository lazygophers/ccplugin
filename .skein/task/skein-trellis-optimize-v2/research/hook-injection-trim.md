# C 方向勘察: hook 注入瘦身 (skein v2)

token 估算方法: 字符数 // 4 (与 hooklib.CHARS_PER_TOKEN=4 一致, memory.py/skein.py budget_guard 同常数, 中英混排偏保守高估)。所有实测数字来自 `python3 -c` 读实际 spec 内容 + 量注入 ctx 字符串。

## 一、hook 注入清单 (skein 自有, plugin.json hooks 段)

| event | 触发时机 | 注入什么 | 实测 token | 频次 | 脚本 file:line |
|---|---|---|---|---|---|
| SessionStart (memory) | startup/resume/clear/compact | core 规则**索引** (仅 `[类目] title`, 10 条) | **71** (285 chars) | 每 session + 每次 compact | memory.py:118-126 (`session_start`) |
| SessionStart (skein) | 同 | 未初始化: setup 提示; 已初始化: active task 列表 (id/status/worktree/PRD 指针, 不含正文) | ≤400 (硬预算) | 同 | skein.py:1106-1127 (`session_context`) |
| UserPromptSubmit (skein) | **每 prompt** | task 判定骨架 (脚本预筹 3 档 + 判定行格式 + flow/豁免边界 + 查重句) | **113** (452 chars) | **每 prompt (最高频)** | skein.py:1184-1209 (`user_prompt`) |
| SubagentStart (memory) | 每 subagent 派发 | core 规则**全文** + spec 纪律 head | **预截断 4118 → 硬截断 2005** | 每 subagent | memory.py:128-141 (`subagent_start`) |
| PreToolUse guard | Edit/Write/Read/MultiEdit | 无注入, 命中阻断 exit 2 | 0 | 每受限工具调用 | hooks.py:77-104 |
| PermissionRequest/Denied | Bash/Edit/Write/Read | 无注入, allow JSON | 0 | 每权限事件 | hooks.py:44-62 |
| PostToolUse fmt | 写 prd.md 后 | 无注入, 跑 skein fmt | 0 | 写 prd.md | hooks.py:148-165 |
| PostToolUse spec-meta | 写 spec/**/*.md 后 | warning (仅异常时) | ~0 命中即注入 | 写 spec | hooks.py:191-227 |
| PostToolBatch | ≥2 状态写并发 | 阻断 reason (仅命中) | ~0 命中即注入 | 并发写 | hooks.py:113-125 |
| PostToolUseFailure report | Bash 失败且是本插件命令 | 错误上下文 + issue 引导 (仅命中, err 截 800 字符) | ~0-220 命中即注入 | 失败 | hooks.py:129-141 |

**关键纠正 (vs 任务假设)**:
- **UserPromptSubmit 注 113 token, 非 300-400**。假设的 300-400 是 SESSION_CTX_BUDGET_TOKENS 硬预算 (skein.py:42), 实测 ctx 仅 452 字符 = 113 token, 远未触预算。瘦身空间小 (内容已是判定骨架, 删则破闭环)。
- **SessionStart 注的是 core 规则索引 (71 token), 非 core 全文**。全文只在 SubagentStart 注。SessionStart 已是「按需」设计 (索引常驻, 全文 inject-core 拉取)。
- **SubagentStart 注 core 全文属实, 且超预算**: 10 条 core 规则 16238 字符 (4059 token) > SUBAGENT_BUDGET_TOKENS=2000, budget_guard 硬截断到 8000 字符 (memory.py:35)。**这是最大瘦身点** — 已截断 = 注入了一半 core 规则且不完整 (最后规则被 `… (超预算已截断)` 切断)。

## 二、瘦身机会

### 机会 1: SubagentStart core 全文硬截断 — 最大, 已病态 (强)
- 位置: memory.py:128-141 (`subagent_start`) + memory.py:35 (`SUBAGENT_BUDGET_TOKENS=2000`)
- 当前: head (213 chars / 53 token) + core 全文 (16238 chars / 4059 token) = 16472 chars / 4118 token → 截断到 8022 chars / 2005 token
- 问题: ① 已超预算被硬截断, 注入的 core 规则不完整 (截断点在 Hook 链规范中间, 后续规则全丢); ② subagent 多为短命执行器 (skein-executor), 不一定需要全部 10 类 core 规则; ③ 现状等于「注了一半, 半失效」— 病态。
- 建议 (三选一, 不拍板):
  - (a) **按 subagent 任务类目过滤**: dispatch prompt 已含「目标/范围」, hook 读不到 dispatch prompt (SubagentStart stdin 无 task 描述), 故需 main 派发时经环境变量/参数传类目 hint, subagent_start 只注该类目 core 规则 — 省 ~3000 token/subagent。
  - (b) **只注索引 (同 SessionStart) + 纪律 head, 全文改 subagent 自跑 `memory.py recall <关键词>`**: 省 ~3900 token/subagent, 但短命 subagent 不一定记得 recall, 风险是规则不进上下文。
  - (c) **扩 SUBAGENT_BUDGET_TOKENS + 拆 core 到 recall**: 治本但要 sediment 判定, 改动大。
- 预估省: 选 (a)/(b) **~3000-3900 token / subagent** (每 subagent 一次)。

### 机会 2: core 规则总量超 CORE_BUDGET 软预算 (强, 关联机会 1)
- 位置: memory.py:33 (`CORE_BUDGET=8000`) + memory.py:96-103 (`_core_text` 超预算告警)
- 当前: core 正文 16238 字符 > 8000 软预算, 每次跑 _core_text stderr 告警「常驻注入过重, 考虑降级部分到 recall」
- 问题: 10 条 core 规则已超 skein 自己设的软预算, 说明 core 层囤积过多。插件自身 dogfood 踩了自己的红线。
- 建议: 经 skein-memory sediment 判定门, 把低频/类目特定的 core 规则降级 recall (如 PEP 563 / git worktree 这类非每次任务命中的)。**这是 A 方向 (单一真值源+死代码) 的姊妹项, 归 memory skill 沉淀, 非 hook 改动**。
- 预估省: 治本解, 配合机会 1 (b) 可让 subagent 全文注入回到预算内。

### 机会 3: UserPromptSubmit 每 prompt 注入 — 低, 边界紧 (弱)
- 位置: skein.py:1184-1209 (`user_prompt`)
- 当前: 113 token / 每 prompt。最高频 (每 prompt 一次, 长会话累计上千次)。
- 问题: 假设的 300-400 不属实, 实际 113 token 内容是 task 闭环判定骨架 (脚本预筹 verdict + 判定行格式 + flow/豁免边界), 删任一段破闭环。可瘦身仅 ~10-20 token (如压缩查重句)。
- 建议: **基本不可瘦**, 是 skein dogfood 核心 (task 闭环靠这行强制判定)。仅可微调措辞, 省 <20 token/prompt。
- 预估省: <20 token / prompt (边际)。

### 机会 4: 非本插件干扰 — ponytail / notify SessionStart:compact 注入 (评估, 非 skein 可控)
- 位置: ~/.claude/plugins/cache/ponytail/ponytail/4.8.4/ (非本仓)
- 现状: ponytail SubagentStart 注 SKILL.md body **1438 token** (5749 chars) + SessionStart 注同量; UserPromptSubmit 注 mode-tracker (轻)。本次调研即被 ponytail 注入 ~1400 token (见 SubagentStart additional context)。
- 问题: 与 skein subagent-start core 全文**叠加** (skein 2005 + ponytail 1438 = ~3440 token/subagent), 挤占 subagent 上下文。但非 skein 可控。
- 建议: 仅在评估 subagent 总注入负担时计入, 不改 ponytail (第三方插件)。
- 预估省: 0 (边界外, 记录干扰)。

## 三、风险与不变量

- **skein 不变量 (不能破)**: core 规则常驻是两层记忆基础 (memory.py:5「core 每 session 常驻注入」+ skein-memory SKILL.md:18「core 硬约束」)。但**现状已是「索引常驻 + 全文按需」**(session_start 注索引, inject-core 按需拉全文) — SessionStart 全文注入假设不成立, 此不变量已满足, 非瘦身障碍。
- **SubagentStart 全文注入是设计选择非不变量**: memory.py:128 注释「给短命执行 agent 直接注入 core 全文 + spec 纪律」。理由是短命 subagent 无 session 记忆, 需全文兜底。但已被 budget_guard 截断失效 — 缩减反而消除病态。
- **task 闭环靠 UserPromptSubmit + PreToolUse guard 强制**, 非 SessionStart 全文: 判定行 (user_prompt) + guard 阻断 (hooks.py:77) 是闭环硬核, 这两处不能动。
- **失败模式 a... agentId 泄露**: 与注入无关, 是 task 通知输出 bug, 不在本方向。

## 四、规模评估

- **可瘦身注入点**: 主要 1 个 (SubagentStart core 全文, 机会 1), 关联 1 个 (core 总量降级 recall, 机会 2)。UserPromptSubmit (机会 3) 边际。
- **预估总省 token**:
  - 每 subagent: **~3000-3900 token** (机会 1 a/b) — 这是主战场。
  - 每 prompt: <20 token (机会 3, 边际)。
  - 每 session: 0 (SessionStart 索引已极简 71 token, 无瘦空间)。
- **改动文件数 + 行数**:
  - 机会 1: memory.py subagent_start + SUBAGENT_BUDGET_TOKENS (~15 行改); 若选 (a) 还需 main 派发处传类目 hint + plugin.json 无改。
  - 机会 2: 经 skein-memory sediment 判定门降级 (非代码改, 是 spec 沉淀操作)。
  - 机会 3: skein.py user_prompt 措辞微调 (~3 行)。
- **风险点**: 机会 1 (b) 风险最高 — subagent 不 recall 则规则不进上下文, 短命执行器可能违规; 机会 1 (a) 需改 dispatch 链路 (main → subagent-start hook 传 hint), 跨改动; 机会 1 (c) 治本但依赖 sediment 判定。
