# Implement — cortex 后台 worker agents

## Phase A — 并行 (S1 // S2)

- [ ] **[L3] S1** dispatch trellis-implement: 建 5 worker agent (agents/cortex-{lint,history,evolve,extract,ingest}-worker.md) 按 design.md 模板 + model 表
- [ ] **[L3] S2** dispatch trellis-implement: 5 skill SKILL.md 加 context:fork + agent 绑定 + 正文分段 (scan→plan 段 / 主会话 ask+apply 段)

## Phase B — wire (S3, 依赖 S1)

- [ ] **[L1] S3** main: plugin.json agents 数组 1→6 + README/llms 提 worker

## Phase C — 验证 (S4)

- [ ] **[L1] S4** main: worker frontmatter 体检 + skill 绑定校验 + plugin.json JSON + 既有脚本 smoke + 暂存

## Phase D — 收尾

- [ ] commit + push (PR #9 更新) + archive + journal

## S4 验证命令

```bash
# worker
for w in lint history evolve extract ingest; do
  f=plugins/tools/cortex/agents/cortex-$w-worker.md
  test -f $f || echo "MISS $w"
  python3 -c "
import yaml
fm=yaml.safe_load(open('$f').read().split('---')[1])
assert fm['name']=='cortex-$w-worker', fm['name']
assert fm.get('background') is True
assert fm.get('description')
t=fm.get('tools','')
assert 'Agent' not in str(t) and 'Write' not in str(t)
print('$w worker OK model=%s'%fm.get('model'))
"
done
# skill 绑定
for s in cortex-lint cortex-history-digest cortex-evolve cortex-extract cortex-ingest; do
  python3 -c "
import yaml
fm=yaml.safe_load(open('plugins/tools/cortex/skills/$s/SKILL.md').read().split('---')[1])
assert fm.get('context')=='fork', fm.get('context')
assert fm.get('agent','').startswith('cortex-') and fm.get('agent','').endswith('-worker'), fm.get('agent')
print('$s -> %s'%fm['agent'])
"
done
# plugin.json
python3 -c "import json; d=json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json')); assert len(d['agents'])==6, d['agents']; print('agents 6 OK')"
# 既有脚本 smoke
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/layout-ok/ >/dev/null; echo "validate $?"
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/ >/dev/null 2>&1; echo "lint $?"
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target plugins/tools/cortex/tests/fixtures/extract/ >/dev/null 2>&1; echo "extract $?"
```

## S1 Dispatch Prompt

```
Active task: .trellis/tasks/06-10-cortex-worker-agents

## 目标
建 5 个后台 worker subagent: agents/cortex-{lint,history,evolve,extract,ingest}-worker.md. 按 design.md "worker frontmatter 模板" + "worker 正文结构" + model 表.

## 已知 (硬限)
- subagent 禁 AskUserQuestion / 禁 spawn subagent / 本任务 worker 禁 Write/Edit (只读+脚本, 只回 plan)
- frontmatter: name=cortex-<x>-worker, description (何时委托, 前置), tools=Read,Glob,Grep,Bash (ingest 加 WebFetch), model (lint=haiku; history/evolve/extract/ingest=inherit), background: true
- 正文 ≤ 80 行: 职责 / 输入契约 (自包含, 不依赖主会话历史) / plan 输出格式 / 边界 (禁 ask 禁 apply, needs_ask 标记留主会话)
- 各 worker 对应 skill 的 scan→plan 职责: lint=7规则check报告; history=扫~/.claude/projects学习增量; evolve=三轴升降级plan; extract=L4-inbox三轴路由plan; ingest=gh/WebFetch抓取+入库plan
- 路径/级别/三轴权威: worker 读 cortex-schema/references + cortex-extract/cortex-evolve references (不复制)

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/agents/cortex-*-worker.md (新建 5)
禁改: agents/cortex.md (现有主 agent) / skill / plugin.json / scripts

## 验收
跑 implement.md S4 验证命令的 worker 段, 5 worker 全过.

## Sub-agent 自防护
trellis-implement, 不再 spawn.
回报: 5 文件 + 行数 + model + 验证退出码.
```

## S2 Dispatch Prompt

```
Active task: .trellis/tasks/06-10-cortex-worker-agents

## 目标
5 skill SKILL.md 加 context:fork + agent 绑定, 正文分段. 目标 skill: cortex-lint, cortex-history-digest, cortex-evolve, cortex-extract, cortex-ingest.

## 操作 (每个 skill)
1. frontmatter 末尾 (--- 前) 加两行:
   context: fork
   agent: cortex-<x>-worker
   (x: lint→lint, history-digest→history, evolve→evolve, extract→extract, ingest→ingest)
2. 正文重构为两段 (不删原有规则内容, 重组):
   ## 后台扫描段 (cortex-<x>-worker 执行)
   <原 scan/plan 相关内容; 强调 dry-run/check 出 plan>
   ## 主会话段 (worker 返回 plan 后)
   <审 plan → ask (L0/L1 确认) → --apply/--fix 落盘; 明示这段在主会话, 不在 worker>
3. 不破坏既有 frontmatter 字段 (name/description/when_to_use/argument-hint/arguments/user-invocable/disable-model-invocation)

## 已知
- worker 只 scan→plan, 不 ask 不 apply (subagent 禁 AskUserQuestion)
- 既有正文里的 ask/apply 内容移到 "主会话段"

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: skills/cortex-{lint,history-digest,evolve,extract,ingest}/SKILL.md
禁改: agents / plugin.json / references / 其他 skill (recall/schema/context-digest 不动)

## 验收
跑 implement.md S4 验证命令的 skill 绑定段, 5 skill 全过 (context==fork, agent==cortex-*-worker). frontmatter 仍合规 (desc ≤ 512 / wtu ≤ 128).

## Sub-agent 自防护
trellis-implement, 不再 spawn.
回报: 5 skill 改动 + 验证退出码.
```
