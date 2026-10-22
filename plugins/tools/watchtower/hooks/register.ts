import type { EngineInterface, On, PluginOptions } from 'claude-code'
import { locateTranscript, projectDirOf, recentAgentReturns } from '../scripts/parse-transcript.mjs'
import { paneView } from './views/pane'
import type { Entry, Kit } from './views/pane'

/**
 * The watchtower pane: the latest 10 agent return values of this session,
 * read straight from the transcript on every draw (zero storage of its own).
 * Structure follows the official code-modernization plugin: `session.start`
 * binds the engine and opens the pane, `clock.every` keeps it fresh,
 * `ui.render` redraws, `ui.close` takes it down.
 */
export const PANE_ID = 'watchtower'
const REFRESH_MS = 2000

type Pane = { isOpen: boolean; isClosedByPerson: boolean }
type State = {
  $: EngineInterface | null
  cwd: string
  sessionId: string
  pane: Pane
  timer: { cancel(): void } | null
}

const state: State = {
  $: null,
  cwd: '',
  sessionId: '',
  pane: { isOpen: false, isClosedByPerson: false },
  timer: null,
}

/** A cell count as the engine reports it, made safe for layout arithmetic. */
const wholeOf = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) ? Math.max(0, Math.floor(value)) : 0

/** The transcript of the current session: by session id when the engine gave
 *  one, else the newest .jsonl of the project dir (research report §7 fallback). */
async function transcriptOf(): Promise<string> {
  const $ = state.$
  if ($ === null) throw new Error('engine not bound')
  if (state.sessionId !== '') return locateTranscript(state.cwd, state.sessionId)
  const dir = projectDirOf(state.cwd)
  let newest: { path: string; mtimeMs: number } | null = null
  for (const entry of await $.fs.list(dir)) {
    if (entry.kind !== 'file' || !entry.name.endsWith('.jsonl')) continue
    const mtimeMs = (await $.fs.stat(`${dir}/${entry.name}`)).mtimeMs
    if (newest === null || mtimeMs > newest.mtimeMs) newest = { path: `${dir}/${entry.name}`, mtimeMs }
  }
  if (newest === null) throw new Error(`no transcript in ${dir}`)
  return newest.path
}

export function register(on: On, _raw: PluginOptions) {
  on('session.start', async ($, e, next) => {
    state.$ = $
    state.cwd = e.cwd
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

  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if (state.$ === null || e.requestId !== PANE_ID) {
      return next(e)
    }

    const table = $.ui.resolve(e)
    const kit: Kit = { Box: table.Box, Text: table.Text }
    const columns = Math.max(40, wholeOf(e.props.bodyColumns))

    state.pane.isOpen = true

    let entries: Entry[] | null = null
    try {
      entries = recentAgentReturns(await transcriptOf())
    } catch {
      // no transcript yet, or not readable: the empty state, not an error
    }

    return paneView(kit, entries, columns)
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
