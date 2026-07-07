export const meta = {
  name: 'trellisx-apply',
  description: 'trellisx-apply 注入编排: 一次调用并行规划 (mode=plan) 或并行写盘自验 (mode=write) 注入 .trellis。审批门 (AskUserQuestion) 由 main 在两次调用之间做, 不在脚本内。',
  phases: [
    { title: 'Plan', detail: '并行: 诊断 + 3 维规划 (read-only, 返回 diff)' },
    { title: 'Write', detail: '备份 → 并行 3 维写盘+自验 → 失败回滚' },
  ],
}

// 注入维度: spec / hook / finishcmd。reference 路径相对 skill 根。
const DIMS = [
  { key: 'spec', ref: 'references/spec-injection.md',
    files: '.trellis/spec/guides/trellisx-worktree.md',
    desc: 'spec worktree 约定 (仅不存在才新增, 已存在跳过)' },
  { key: 'hook', ref: 'references/hook-injection.md',
    files: '.trellis/scripts/{trellisx_wt,trellisx-worktree,trellisx-taskmd,trellisx-finish,trellisx-packages}.py + .trellis/config.yaml (hooks + session_auto_commit:true + packages:) + <git根>/.gitignore',
    desc: '复制五脚本 + config.yaml 生命周期 hook + session_auto_commit + packages 发现 + gitignore' },
  { key: 'finishcmd', ref: 'references/finishcmd-injection.md',
    files: '.claude/commands/trellis/finish-work.md',
    desc: 'finish-work.md 全链注入 (先跑 trellisx-finish.py 再 journal); 无文件则跳过' },
]

const PLAN_SCHEMA = {
  type: 'object',
  required: ['key', 'status', 'diff'],
  properties: {
    key: { type: 'string' },
    status: { type: 'string', enum: ['plan', 'skip'] },
    diff: { type: 'string', description: '注入 diff / plan 文本 (审批用); skip 时说明原因' },
    notes: { type: 'string' },
  },
}

const WRITE_SCHEMA = {
  type: 'object',
  required: ['key', 'ok', 'verified'],
  properties: {
    key: { type: 'string' },
    ok: { type: 'boolean', description: '写盘是否成功' },
    verified: { type: 'boolean', description: '本维度自验 (语法/marker 配对/行为) 是否通过' },
    changed: { type: 'array', items: { type: 'string' }, description: '改动文件清单' },
    problem: { type: 'string', description: 'ok=false 或 verified=false 时的精确定位' },
  },
}

const lang = (args && args.lang) || '目标语言 (综合 $LANG + 项目 CLAUDE.md/README + 会话语言, 默认 zh)'
const mode = (args && args.mode) || 'plan'
const skillDir = (args && args.skillDir) || '<trellisx-apply skill 根目录, 由 main 传入绝对路径>'
const target = (args && args.target) || '<目标 trellis 项目根, 由 main 传入绝对路径>'

const fields = (goal, scope, out, accept, fail) =>
  `目标: ${goal}\n已知: 目标语言=${lang}; reference 绝对路径前缀=${skillDir}/ (如 ${skillDir}/references/hook-injection.md); 目标项目根=${target} (所有 .trellis/** 落点相对此根)\n工作目录与范围: 目标项目根=${target}; ${scope}\n输出格式: ${out}\n验收标准: ${accept}\n失败处理: ${fail}`

if (mode === 'plan') {
  phase('Plan')
  // diagnose 先定语言/模式, 但各 plan agent 不阻塞等它 (自诊断本维度)。
  const planners = [
    () => agent(fields(
      '诊断 .trellis 现状: 首次/更新模式 (config.yaml 是否已含 trellisx hook) + 已有 trellisx marker + gitignore 状态 + 确定目标语言 (传给写盘)。read-only。',
      '只读 .trellis/**; 禁写盘',
      'StructuredOutput: 复用 PLAN_SCHEMA, key=diagnose, diff 字段填诊断结论 (模式/语言)',
      '诊断结论可指导写盘', '读不到目标 → status=skip 说明'),
      { label: 'plan:diagnose', phase: 'Plan', schema: PLAN_SCHEMA }),
    ...DIMS.map(d => () => agent(fields(
      `按 ${skillDir}/${d.ref} 算「${d.desc}」的注入 diff (目标语言), 不写盘。`,
      `只读相关文件 (本维度落点: ${d.files}); 禁写盘`,
      `StructuredOutput PLAN_SCHEMA: key=${d.key}; diff=注入 diff/plan 文本; 维度不适用则 status=skip`,
      'diff 完整可审, marker 幂等设计', '读不到目标 → status=skip 标注原因'),
      { label: `plan:${d.key}`, phase: 'Plan', schema: PLAN_SCHEMA })),
  ]
  const plans = (await parallel(planners)).filter(Boolean)
  return { mode: 'plan', plans }
}

if (mode === 'write') {
  phase('Write')
  const plans = (args && args.plans) || {} // {key: diffText} 由 main 审批后回传
  // 1) 备份 (串行单 agent, git stash, 不可并发撕裂 index)
  const backup = await agent(fields(
    '审批已过。git stash push -- .trellis/ 备份当前 .trellis (写盘前)。',
    '仅 git stash, 不写注入内容',
    '报 stash 是否成功 + stash ref', '备份成功才放行写盘', 'stash 失败 → 报错, 不进写盘'),
    { label: 'prep-backup', phase: 'Write' })

  // 2) 并行写盘 + 自验 (合并原 Phase B/C, 每 writer 自验本维度, 无独立 verify barrier)
  const results = (await parallel(DIMS.map(d => () => agent(fields(
    `按 ${d.ref} + 审批 plan 写盘「${d.desc}」, 写完**自验本维度** (语法 ast.parse / marker 起止配对 / 行为闭环 / i18n 语言一致)。\n审批 plan:\n${plans[d.key] || '(无明确 plan, 按 reference 默认注入)'}`,
    `独占文件集 (sole owner, 禁碰他维文件): ${d.files}`,
    `StructuredOutput WRITE_SCHEMA: key=${d.key}; ok/verified/changed/problem`,
    '文件落盘 + marker 幂等不堆叠 + 自验全过', 'ok=false/verified=false → problem 给精确定位, 禁留半截'),
    { label: `write:${d.key}`, phase: 'Write', schema: WRITE_SCHEMA })))).filter(Boolean)

  const failed = results.filter(r => !r.ok || !r.verified)
  if (failed.length) {
    // 3) 任一失败 → 回滚 (串行单 agent)
    await agent(fields(
      `写盘/自验失败 (${failed.map(f => f.key).join(',')})。git stash pop 回滚全部 .trellis 改动。`,
      '仅 git stash pop 恢复 backup', '报回滚结果', '恢复到写盘前', 'pop 冲突 → 报脏文件清单'),
      { label: 'rollback', phase: 'Write' })
    return { mode: 'write', ok: false, failed, results, rolledBack: true }
  }
  return { mode: 'write', ok: true, results }
}

throw new Error(`未知 mode: ${mode} (应为 plan | write)`)
