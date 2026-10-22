// pane 视图：把 pane-rows 的字符串行映射成组件树。
// Box/Text 由 register.ts 经 $.ui.resolve 提供；属性用法照 code-modernization 的 views/pane.tsx。
import { rowsOf } from '../../scripts/pane-rows.mjs'

type AnyComponent = (props: Record<string, unknown>) => unknown

export type Kit = { Box: AnyComponent; Text: AnyComponent }

export type Entry = { time: string; taskId: string | null; text: string }

export function paneView(kit: Kit, entries: Entry[] | null, columns: number): unknown {
  const { Box, Text } = kit

  return (
    <Box flexDirection="column" paddingRight={1} rowGap={0}>
      {rowsOf(entries, columns).map((row, i) => (
        <Text key={i} wrap="truncate-end" bold={i === 0}>{row}</Text>
      ))}
    </Box>
  )
}
