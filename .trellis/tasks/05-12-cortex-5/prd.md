# PRD — cortex 记忆系统强化 (6 需求合并)

## 6 用户需求 (合并实施)

| # | 需求 | 类型 |
|---|------|------|
| 1 | 每次更改必须**整个插件全局考虑** | 元约束 (本任务执行原则) |
| 2 | 注入提示词: 用户说"记住"等关键词, AI **主动写入记忆** | session_start 行为契约增条目 |
| 3 | 记忆 cron/skill: **重复出现 → 作为记忆, 注意级别** | promote 算法细化 + 级别判定 |
| 4 | 每记忆级别要 **边界 / 审判 / 审核标准** | memory-policy.yaml 大幅细化 |
| 5 | `plugins/tools/cortex/scripts/` 缺**记忆相关 bash** | 加 memory/recall/promote/consolidate wrapper |
| 6 | **stop hook 报错** — settings.json 引 `${CLAUDE_PLUGIN_ROOT}` 不展开 | doctor.sh 检测 + 提示用户清理 |

## 1. 全局影响面

| 区域 | 改动 |
|------|------|
| hooks/session_start.sh + locales | 加"记住"触发指令 |
| _meta/memory-policy.yaml | 各 level 边界/审判/审核标准 (5 倍内容) |
| presets/seed/_meta/memory-policy.yaml | 同步源 |
| scripts/cron/memory-promote.sh | 重复检测算法明确 |
| scripts/install_wrappers.sh | 加 memory.sh / recall.sh / promote.sh / consolidate.sh |
| skills/cortex-memory/SKILL.md | 写入触发 "记住" 关键词时调用 |
| skills/cortex-promote/SKILL.md | 级别判定明确 |
| 测试 | hooks v2 测试 + policy schema 测试 |

## 2. 设计

### 2.1 需求 2 — "记住"自动写记忆

`locales/{zh-CN,en,ja}.yml` behavior_contract 加新条目:

```
3. **用户显式记忆指令**:
   - 用户说"记住 X" / "你要记得 X" / "remember X" / "please remember"
     → 立即调 cortex_memory_write
   - 判定 level:
     · "永远记住" / "硬性" / "绝对" → 建议 L0 候选 (写 candidates, 不自动落)
     · "记住" / "remember" 一般语气 → L1 (weight=0.85)
     · "短期记一下" / "暂时" → L2 (weight=0.6)
   - 写入后回复: "✓ 已记录到 L<N>: <brief>"
   - 用户说"忘了 X" / "forget X" → cortex_memory_forget
```

补 zh-CN 触发词清单加:
```yaml
default_triggers:
  - 记忆指令: 记住, 要记得, remember, please remember, 别忘了, don't forget
```

### 2.2 需求 3 — 重复出现晋级

`memory-promote.sh` prompt 细化重复检测算法:

```
扫 L4 ledger 上 7 天:
  - 统计 (实体, 主题, 上下文) 三元组出现频率
  - freq ≥ 3 → 创建 L3 episodic 候选 (auto promote)
  - freq ≥ 5 + 跨 ≥3 天 → L3 → L2 候选 (写 candidates, 不自动)
  - freq ≥ 10 + 跨 ≥30 天 → L2 → L1 候选

扫 L3 episodic 上 30 天:
  - 同主题 ≥ 5 次 + last_recalled 增长 → L2 候选

扫 L2 semantic 上 365 天:
  - recall_count ≥ 20 + stable (90 天无 weight 大改) → L1 候选

L0 永不自动 (用户审批)。

输出: views/candidates.md 含
  | 候选 | 来源 level | 目标 level | freq | timespan | weight | 建议理由 |
```

### 2.3 需求 4 — 各级别边界/审判/审核

`_meta/memory-policy.yaml` 重写, 每 level 加 3 子段:

```yaml
L0:
  boundary:    # 什么属于 L0 (准入条件)
    - 类型: identity / values / habits / hard_constraints
    - 触发: 用户明确"永久"/"硬性"/"绝对" + 用户审批
    - 不可逆: 一旦入 L0, 仅用户能改/删
    - 体积: 单条 ≤ 1500 chars (brief), full 可大
  judgment:    # 谁审 + 怎么审
    - 写入: needs_user_confirm=true
    - 审批者: 仅 user (AI 提候选, 不执行)
    - 工具: cortex_memory_write 要求 user_signature 字段
    - 拒入: AI 单方提议 → 写到 views/candidates.md, 不直落
  review:      # 周期复审标准
    - 频率: monthly
    - 检测: hash 变化 / git tag missing → memory-warden 告警
    - 用户决策: 保留 / 修订 / 删除
    - 冲突: 若 L0 多条相互矛盾 → 强制用户裁决

L1:
  boundary:
    - 类型: procedural (技能/流程) + semantic-stable (稳定语义)
    - 准入: recall_count ≥ 20 + 跨 ≥90 天 + weight ≥ 0.8
    - 触发: AI 自动提议 (memory-promote 写 candidates) 或 用户显式"记住"
    - 体积: 单条 ≤ 5000 chars
  judgment:
    - 写入: AI 自动可写 (无需 user confirm), weight 必 ≥ 0.8
    - 审批者: AI (按 promote_criteria) + 用户随时 override
    - 工具: cortex_memory_write level=L1
    - 拒入: weight 不达标 → 退回 L2
  review:
    - 频率: monthly
    - 检测: 同 topic 矛盾 / 时效失效 (expires < now) / recall_count 衰减
    - 行动: 矛盾 → warden 报警; 时效失效 → 提议降级 L2
    - 用户可手动晋升到 L0

L2:
  boundary:
    - 类型: semantic (抽象事实, 可演化)
    - 准入: recall_count ≥ 5 + 跨 ≥ 7 天 (一周) + weight ≥ 0.5
    - 触发: L3 promote 或 AI ingest 时直接判定
    - 体积: 单条 ≤ 3000 chars; 时效 365 天
  judgment:
    - 写入: AI 自动 (dedupe 必开)
    - dedupe: 同 topic uri 合并; 矛盾保新弃旧 (但写入 ledger 留痕)
    - 工具: cortex_memory_write level=L2
  review:
    - 频率: monthly
    - 检测: 365 天未召回 + recall_count < 5 → archive_pending
    - 衰减: weight 每月 -0.05 (除非 recalled)

L3:
  boundary:
    - 类型: episodic (具体经历, 时间戳)
    - 准入: L4 模式 ≥ 3 次 / 用户显式 / AI 检测 "important moment"
    - 体积: 单条 ≤ 2000 chars; 时效 90 天
  judgment:
    - 写入: AI 自动 (无 dedupe, 因情节本独立)
    - 工具: cortex_memory_write level=L3
  review:
    - 频率: weekly (memory-consolidate)
    - 检测: 90 天未召回 + recall_count < 3 → archive_pending
    - 模式聚合: 同事件类型 ≥ 5 → 抽象为 L2

L4:
  boundary:
    - 类型: ledger (raw event 流) + sessions (claude code transcript)
    - 准入: 全部接收 (immutable append-only)
    - 体积: 不限单条, 总按日期分文件
  judgment:
    - 写入: 系统自动 (Stop hook / PostCompact hook / ingest)
    - 不审: append only, 不允许改
    - 工具: cortex_ledger_append / cortex_session_import
  review:
    - 频率: weekly
    - 行动: 30 天后 gzip 压缩; 60 天后归档
    - 模式提炼: memory-consolidate 跑跨域统计
```

### 2.4 需求 5 — 记忆 bash wrapper

`scripts/install_wrappers.sh` 加 4 新 wrapper (生成到 ~/.cortex/scripts/):

| wrapper | 调用 | 用途 |
|---------|------|------|
| `memory.sh <verb> [args]` | cortex-memory SKILL | `read/write/forget/update <uri>` CRUD |
| `recall.sh <query>` | cortex-recall SKILL | 渐进披露召回 query 相关记忆 |
| `promote.sh [--dry-run]` | cortex-promote SKILL | 跑晋级候选检测 (扫 candidates.md + 执行 L4→L3, L3→L2 auto; L2→L1, L1→L0 仅候选) |
| `consolidate.sh [--week N]` | cortex-consolidate SKILL | 跑 ledger → views 巩固 + 反思生成 |

每个 wrapper 风格同 init.sh:
- 检 ~/.cortex/config.json
- jq 解析 vault
- claude --bare AUTO_MODE 调对应 SKILL
- --max-budget-usd 0.30 限额

新增后 wrapper 总数 12 → 16:
config, dashboard, doctor, fold, ingest, init, install_cron, lint, refactor, save, search, update, **memory, recall, promote, consolidate**.

### 2.6 需求 6 — stop hook 脏配置检测

**问题**:
- `~/.claude/settings.json` 用户手动添加了
  - `${CLAUDE_PLUGIN_ROOT}/hooks/stop.sh`
  - `${CLAUDE_PLUGIN_ROOT}/scripts/on-stop.sh`
- 但 `${CLAUDE_PLUGIN_ROOT}` 仅在 plugin 的 `hooks.json`/`plugin.json` 上下文展开, **在 settings.json 不展开** → Claude 报 `Hook command references ${CLAUDE_PLUGIN_ROOT}...`
- plugin 自己的 `.claude-plugin/plugin.json` 用绝对路径 `~/.claude/plugins/...`, 正常工作

**修复策略**:
- 不自动改用户 `settings.json` (用户私有, plugin 无权)
- doctor.sh 加检测: 扫 `~/.claude/settings.json` + `~/.claude/settings.local.json`, 找含 `${CLAUDE_PLUGIN_ROOT}` 的 hook command, 报警
- install.sh 跑完后调一次 doctor 检测
- 输出详细修复步骤 (给用户复制粘贴的 jq 命令)

**doctor 检测逻辑**:
```bash
for f in ~/.claude/settings.json ~/.claude/settings.local.json; do
  [ -f "$f" ] || continue
  bad=$(jq -r '.. | objects | .command? // empty | select(contains("${CLAUDE_PLUGIN_ROOT}"))' "$f" 2>/dev/null)
  if [ -n "$bad" ]; then
    echo "⚠ $f 含无效引用:"
    echo "$bad"
    echo "  修复: 删除这些 hook 条目 (plugin 自己已注册, 重复)"
  fi
done
```

doctor.sh wrapper 加这段。

### 2.5 需求 1 — 全局一致性

本 PRD 跨多文件改动, 强制清单 (子任务结束前对照):
- [ ] memory-policy.yaml 改完 → presets/seed/_meta/memory-policy.yaml 同步
- [ ] locales 改 → 3 lang (zh-CN/en/ja) 同步
- [ ] install SKILL 改 → 反映新 wrapper 数量 (16)
- [ ] hook session_start 改 → 测试 v2 套件更新
- [ ] templates/triggers.yaml 同步加 "记忆指令" 分类
- [ ] memory-promote.sh prompt 改 → 反映重复检测算法
- [ ] 所有 SKILL.md (memory/recall/promote/consolidate/forget) 反映各 level 边界 (与 policy 一致)
- [ ] cortex-install SKILL 流程 §4 加 4 个新 wrapper 生成项

## 3. 实施步骤

### Step 1: memory-policy.yaml 重写 (核心源)
改 `plugins/tools/cortex/presets/seed/_meta/memory-policy.yaml`, 加 L0-L4 各 3 子段 (boundary/judgment/review)。保留 cron jobs / recall 段。

### Step 2: locales 加"记忆指令"
3 文件加 default_triggers 中"记忆指令" + behavior_contract 第 3 条 (记住/忘掉指令)。

### Step 3: templates/triggers.yaml 加分类
加 `memory_instruction: [记住, 要记得, remember, ...]` 分类。

### Step 4: memory-promote.sh prompt 细化
改 prompt 反映 §2.2 三层重复检测算法。

### Step 5: install_wrappers.sh 加 4 wrapper
heredoc 生成 memory/recall/promote/consolidate.sh, 风格同 init.sh。

### Step 6: install SKILL 更新
反映 16 wrapper (从 12) + 4 新 wrapper 名称提示。

### Step 7: SKILL 更新 (5 个)
cortex-memory/recall/promote/consolidate/forget SKILL.md 反映各 level 边界 (从 policy 同步关键描述)。

### Step 8: doctor 加 stop hook 检测
改 `plugins/tools/cortex/scripts/install_wrappers.sh` 生成的 doctor.sh, 加 §2.6 检测段。

### Step 9: 测试
新增 `test_memory_policy_schema.py` (policy 含 boundary/judgment/review) + 已有 session_start v2 测试不回归。

## 4. 验收

- [ ] memory-policy.yaml 含 L0-L4 各 boundary/judgment/review 3 段
- [ ] vault 安装后 _meta/memory-policy.yaml 与 plugin 同步
- [ ] locales 3 文件含 default_triggers "记忆指令" 分类 + behavior_contract 新条目
- [ ] templates/triggers.yaml 含 memory_instruction
- [ ] install_wrappers.sh 跑后生成 16 wrapper (12 + 4)
- [ ] 4 新 wrapper 含 [AUTO_MODE] + claude --bare + budget 限额
- [ ] memory-promote.sh prompt 含"freq ≥ 3 / 5 / 10"三层
- [ ] cortex-install SKILL 反映 16 wrapper 数
- [ ] 5 个 memory SKILL.md 反映各 level 边界
- [ ] 测试 PASS (≥ 227 现有 + 新增至少 3)

## 5. 风险

| 风险 | 缓解 |
|------|------|
| memory-policy.yaml schema 大改, lint 不识别 | policy 当前未被 lint 强解析, 仅 cron prompt 读; 内容变化 OK |
| "记住" 误触发 (用户随口说) | 加 weight 阈值 + 写入后即时回报 ("✓ 已记 L<N>"), 用户可立刻 "忘了" |
| wrapper 数量爆炸 (16) | 加分组提示 ("基础 / cron / 记忆 / vault" 4 组) 到 install 输出 |
| L0 写入自动化风险 | 严格保留 needs_user_confirm + git tag, AI 仅写候选 |

## 6. 子任务拆分

9 步骤拆 2 wave 并行 (≤2 agent):

**Wave A** (核心数据 + wrapper)
- Agent A1: Step 1 + 2 + 3 (memory-policy + locales + triggers)
- Agent A2: Step 5 + 6 + 8 (install_wrappers 加 4 memory wrapper + doctor 加检测 + cortex-install SKILL)

**Wave B** (prompt + SKILL + 测试)
- Agent B1: Step 4 + 7 (memory-promote.sh + 5 SKILL)
- Agent B2: Step 9 (测试)

预估: A 0.5d + B 0.5d ≈ 1d。
