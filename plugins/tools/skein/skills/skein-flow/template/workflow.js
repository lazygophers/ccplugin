/**
 * skein-flow workflow — SKEIN 四阶段闭环编排器 (动态工作流版)
 *
 * 持续轮询 claim exec 取 subtask, 异步派出 executor 执行, 全 done 的 task 自动 check→finish。
 * 连续 10 分钟 (无 agent 执行 + 无 subtask 可调度) 则退出。
 *
 * 用法:
 *   /skein-flow <task-id> [task-id ...]   — 只处理指定 task
 *   /skein-flow                            — 全空 = 全局 claim exec
 *
 * 依赖:
 *   - skein CLI (alias 或 python3 $CLAUDE_PLUGIN_ROOT/scripts/skein.py)
 *   - task 已过 plan 阶段 (就绪/进行中态)
 *   - skein 插件具名 agent 已注册 (skein:skein-executor / checker / finisher)
 *
 * API: agent(prompt, { schema, label, subagent_type, run_in_background }) / pipeline() / export const meta
 * 约束: 脚本无直接 shell/fs 访问, skein CLI 调用经 agent 间接完成
 */
export const meta = {
  name: 'skein-flow',
  description: 'SKEIN task 闭环编排器: exec→check→finish 持续调度',
}

// ── 配置 ───────────────────────────────────────────────────────

const IDLE_TIMEOUT_MS = 10 * 60 * 1000 // 连续空闲上限: 10 分钟
const POLL_INTERVAL_MS = 5000 // claim exec 返回空时的轮询间隔

// ── agent 模板 ─────────────────────────────────────────────────

/** 跑 skein CLI 命令的通用 agent (同步等结果) */
const cliAgent = (cmd, label = 'skein-cli') =>
  agent(
    `运行以下 shell 命令, 仅返回 stdout。失败则返回错误信息。\n\n${cmd}`,
    { label, schema: { type: 'string' } },
  )

/** exec: 异步派 skein:skein-executor (不阻塞主循环) */
const execAgent = (tid, sid, workdir) =>
  agent(
    JSON.stringify({ tid, sid, workdir }),
    { label: `exec ${tid}/${sid}`, subagent_type: 'skein:skein-executor', run_in_background: true },
  )

/** check: 同步派 skein:skein-checker */
const checkAgent = (tid, workdir) =>
  agent(
    JSON.stringify({ tid, workdir }),
    {
      label: `check ${tid}`,
      subagent_type: 'skein:skein-checker',
      schema: {
        type: 'object',
        required: ['verdict'],
        properties: {
          verdict: { type: 'string', enum: ['PASS', 'FAIL'] },
          failures: { type: 'array', items: { type: 'string' } },
          conflicts: { type: 'array', items: { type: 'string' } },
        },
      },
    },
  )

/** finish: 同步派 skein:skein-finisher */
const finishAgent = (tid, workdir) =>
  agent(
    JSON.stringify({ tid, workdir }),
    {
      label: `finish ${tid}`,
      subagent_type: 'skein:skein-finisher',
      schema: {
        type: 'object',
        required: ['verdict'],
        properties: {
          verdict: { type: 'string' },
          details: { type: 'string' },
          issues: { type: 'array', items: { type: 'string' } },
        },
      },
    },
  )

// ── 辅助 ───────────────────────────────────────────────────────

function parseClaimResult(raw) {
  if (!raw || typeof raw !== 'string') return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

async function getWorktree(tid) {
  const result = await cliAgent(
    `skein list --status open --json 2>/dev/null | jq -r '.[] | select(.id=="${tid}") | .worktree // empty'`,
    `worktree ${tid}`,
  )
  const wt = typeof result === 'string' ? result.trim() : ''
  return wt || '.'
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// ── 主循环 ─────────────────────────────────────────────────────

const summaries = []
const pendingAgents = [] // 异步 agent 句柄队列
let idleStart = null

while (true) {
  // 1. 回收已完成的异步 agent
  for (let i = pendingAgents.length - 1; i >= 0; i--) {
    const status = pendingAgents[i].status
    if (status === 'completed' || status === 'failed') {
      pendingAgents.splice(i, 1)
    }
  }

  // 2. claim exec 取就绪 subtask
  const claimRaw = await cliAgent(
    `skein claim exec --json 2>/dev/null || skein claim exec 2>/dev/null`,
    'claim exec',
  )
  const claimed = parseClaimResult(claimRaw)

  // 按需筛 task (args 指定时)
  const filter = (args && Array.isArray(args) && args.length > 0)
    ? new Set(args.map(String))
    : null
  const batch = filter
    ? claimed.filter((c) => filter.has(c.tid || c.task_id))
    : claimed

  // 3. 有 subtask 可派 — 异步派出, 不等回
  if (batch.length > 0) {
    idleStart = null
    for (const item of batch) {
      const tid = item.tid || item.task_id
      const sid = item.sid || item.subtask_id
      const workdir = await getWorktree(tid)
      const handle = await execAgent(tid, sid, workdir)
      pendingAgents.push(handle)
    }
    continue // 立即回循环头, 不等 agent 完成
  }

  // 4. 无 subtask 可派 — 尝试推进全 done 的 task 走 check→finish
  const advanced = await advanceTasks()
  if (advanced) {
    idleStart = null
    continue
  }

  // 5. 无 subtask + 无 task 可推进 — 判空闲
  const hasRunning = pendingAgents.length > 0

  if (hasRunning) {
    // 有 agent 在跑, 不算空闲, 等
    idleStart = null
    await sleep(POLL_INTERVAL_MS)
    continue
  }

  // 真正空闲: 无 agent 执行 + 无 subtask 可调度
  if (idleStart === null) idleStart = Date.now()
  if (Date.now() - idleStart >= IDLE_TIMEOUT_MS) break
  await sleep(POLL_INTERVAL_MS)
}

/**
 * 扫描进行中 task, 全 subtask done 的走 check→finish。
 * @returns {Promise<boolean>} 有 task 被推进则 true
 */
async function advanceTasks() {
  const raw = await cliAgent(
    `skein list --status open --json 2>/dev/null`,
    'scan tasks',
  )
  const tasks = typeof raw === 'string' ? JSON.parse(raw || '[]') : []
  let advanced = false

  for (const t of tasks) {
    if (t.status !== '进行中') continue
    const subs = t.subs || {}
    const allDone = (subs.run || 0) === 0 && (subs.pend || 0) === 0
      && (subs.fail || 0) === 0 && (subs.done || 0) > 0
    if (!allDone) continue

    const workdir = t.worktree || '.'
    const tid = t.id

    // ── check ──
    const checkResult = await checkAgent(tid, workdir)

    if (checkResult.verdict === 'FAIL') {
      summaries.push({ tid, verdict: 'CHECK_FAILED', failures: checkResult.failures, conflicts: checkResult.conflicts })
      continue
    }

    // ── finish ── (check 全绿)
    const finishResult = await finishAgent(tid, workdir)
    summaries.push({ tid, verdict: finishResult.verdict, details: finishResult.details, issues: finishResult.issues })
    advanced = true
  }

  return advanced
}

return summaries
