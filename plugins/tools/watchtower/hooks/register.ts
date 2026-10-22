import type { On, PluginOptions } from 'claude-code'
import { locateTranscript, projectDirOf, recentReturns } from '../scripts/parse-transcript.mjs'
import { bandRow } from '../scripts/pane-rows.mjs'
import { bandView, paneView } from './views/pane'
import type { Entry, Kit } from './views/pane'

/**
 * The watchtower pane: the latest 50 entries of this session (agent return
 * values + main-conversation final replies, newest first),
 * read straight from the transcript on every draw (zero storage of its own).
 * Structure follows the official code-modernization plugin: `session.start`
 * opens the pane, `clock.every` keeps it fresh, `ui.render` redraws,
 * `ui.close` takes it down. The engine `$` is never stored or passed: it is
 * only spelled `$.noun.event(...)` inside the handler the engine gave it to.
 */
export const PANE_ID = 'watchtower'
const REFRESH_MS = 2000

type Pane = { isOpen: boolean; isClosedByPerson: boolean }
type State = {
  cwd: string
  sessionId: string
  /** The home dir as `$.env.get('HOME')` gave it; transcript paths live under it. */
  home: string
  pane: Pane
  timer: { cancel(): void } | null
  /** The tool-use id of the one expanded entry; null = all collapsed. Survives the 2s refresh. */
  expandedId: string | null
}

const state: State = {
  cwd: '',
  sessionId: '',
  home: '',
  pane: { isOpen: false, isClosedByPerson: false },
  timer: null,
  expandedId: null,
}

/** A cell count as the engine reports it, made safe for layout arithmetic. */
const wholeOf = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) ? Math.max(0, Math.floor(value)) : 0

type DirEntry = { name: string; kind: string; mtimeMs: number }

/** The newest .jsonl of the project dir (research report §7 fallback); null if none. */
function newestTranscriptOf(entries: DirEntry[]): string | null {
  let newest: DirEntry | null = null
  for (const entry of entries) {
    if (entry.kind !== 'file' || !entry.name.endsWith('.jsonl')) continue
    // a list entry already carries a regular file's own mtimeMs
    if (newest === null || entry.mtimeMs > newest.mtimeMs) newest = entry
  }
  return newest?.name ?? null
}

export function register(on: On, _raw: PluginOptions) {
  on('session.start', async ($, e, next) => {
    state.cwd = e.cwd
    state.home = (await $.env.get('HOME')) ?? ''
    state.sessionId =
      typeof (e as { sessionId?: unknown }).sessionId === 'string'
        ? (e as { sessionId: string }).sessionId
        : ''

    state.timer?.cancel()

    if (!state.pane.isClosedByPerson) {
      try {
        // opened unasked on a terminal too narrow to dock a pane, the engine holds it undrawn
        const result = await $.ui.open({ id: PANE_ID, title: 'Agent returns' })
        state.pane.isOpen = result === undefined || result.isPlaced !== false
      } catch {
        // a build without panes: the pane is simply not there
      }
    }

    state.timer = $.clock.every(REFRESH_MS, () => {
      if (state.pane.isOpen) $.ui.invalidate('ui.render')
    })

    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    // pane 已摆放（宽终端，或按钮/命令开过）时 band 让位；非终端 surface 没有 band
    if (e.surface !== 'terminal' || state.pane.isOpen) {
      return next(e)
    }

    // band 渲染时顺手读一次 transcript 记条数（读失败按 0 条）；
    // 不为 band 起新 timer，跟引擎自己的 AbovePrompt 重绘走
    const table = $.ui.resolve(e)
    let count = 0
    try {
      const dir = projectDirOf(state.cwd, state.home)
      const path =
        state.sessionId !== ''
          ? locateTranscript(state.cwd, state.sessionId, state.home)
          : `${dir}/${newestTranscriptOf(await $.fs.list(dir))}`
      count = recentReturns(await $.fs.read(path)).length
    } catch {
      // transcript 读不到（缺失、无记录、超 4 MiB）：按 0 条画 band，不报错
    }

    return bandView(
      { Box: table.Box, Text: table.Text, Button: table.Button } as Kit,
      bandRow(count),
      () => {
        // 引擎调用内联在 handler 里（不存 $）：点击是 asked open，110 列起摆放
        void (async () => {
          try {
            const result = await $.ui.open({ id: PANE_ID, title: 'Agent returns' })
            if (result === undefined || result.isPlaced !== false) {
              state.pane.isOpen = true
              $.ui.invalidate('ui.render')
            } else {
              $.ui.toast(`The pane could not be shown: ${result.reason}`, { timeoutMs: 8000 })
            }
          } catch {
            // a build without panes: nothing to open
          }
        })()
      },
    )
  })

  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if (e.requestId !== PANE_ID) {
      return next(e)
    }

    const table = $.ui.resolve(e)
    const kit: Kit = { Box: table.Box, Text: table.Text, Button: table.Button }
    const columns = Math.max(40, wholeOf(e.props.bodyColumns))

    state.pane.isOpen = true

    let entries: Entry[] | null = null
    let errorText: string | null = null
    try {
      // the transcript, read through the engine (a hooks module cannot touch node:fs):
      // by session id when the engine gave one, else the newest .jsonl of the project dir
      const dir = projectDirOf(state.cwd, state.home)
      let path: string
      if (state.sessionId !== '') path = locateTranscript(state.cwd, state.sessionId, state.home)
      else {
        const newest = newestTranscriptOf(await $.fs.list(dir))
        if (newest === null) throw new Error(`no transcript in ${dir}`)
        path = `${dir}/${newest}`
      }
      entries = recentReturns(await $.fs.read(path))
    } catch (err) {
      // unreadable (missing, or over the engine's 4 MiB read cap): one error
      // line, distinct from "no agent returns yet"
      errorText = `Cannot read transcript: ${err instanceof Error ? err.message : String(err)}`
    }

    // the refresh keeps the expanded entry expanded while it is still among the latest 50
    if (state.expandedId !== null && entries !== null && !entries.some((entry) => entry.id === state.expandedId)) {
      state.expandedId = null
    }

    return paneView(
      kit,
      entries,
      columns,
      state.expandedId,
      (id) => {
        state.expandedId = state.expandedId === id ? null : id
        $.ui.invalidate('ui.render')
      },
      errorText,
    )
  })

  on('ui.close', async ($, e, next) => {
    const result = await next(e)

    if (e.id === PANE_ID && result.deny === undefined) {
      state.pane.isOpen = false
      state.pane.isClosedByPerson = e.origin.kind === 'person' || state.pane.isClosedByPerson
    }

    return result
  })
}
