// pane / band 视图：把 pane-rows 的字符串行映射成组件树；每条包 Button，点击切换展开/收起。
// Box/Text/Button 由 register.ts 经 $.ui.resolve 提供；属性用法照 code-modernization 的 views/pane.tsx。
import { MAX_ROWS, headerOf, collapsedRows, expandedRows } from '../../scripts/pane-rows.mjs'

type AnyComponent = (props: Record<string, unknown>) => unknown

export type Kit = { Box: AnyComponent; Text: AnyComponent; Button: AnyComponent }

// 只声明渲染用到的字段；来源 recentReturns 多出的 taskId 不渲染（窄 pane 放不下）
export type Entry = { kind?: 'agent' | 'main'; id: string; time: string; summary?: string; title?: string; text: string }

export function paneView(
  kit: Kit,
  entries: Entry[] | null,
  columns: number,
  expandedId: string | null,
  onToggle: (id: string) => void,
  /** Non-null = the transcript itself is unreadable: one error line, not the empty state. */
  errorText: string | null = null,
): unknown {
  const { Box, Text, Button } = kit
  const shown = (entries ?? []).slice(0, MAX_ROWS)

  return (
    <Box flexDirection="column" paddingRight={1} rowGap={0}>
      {errorText !== null ? (
        <Text>{errorText}</Text>
      ) : shown.length === 0 ? (
        <Text>No returns in this session yet.</Text>
      ) : (
        <>
          <Text bold>{headerOf(shown.length)}</Text>
          {shown.map((e) => {
            const expanded = e.id === expandedId
            const rows = expanded ? expandedRows(e, columns) : collapsedRows(e, columns)
            // Button 的 children 只能是字符串和 Text（Box 会被引擎拒绝，见 ButtonProps）：
            // 标题行是按钮；展开态末尾的收起行也是按钮，其余预览/全文行是 dim Text
            const body = expanded ? rows.slice(1, -1) : rows.slice(1)
            return (
              <Box key={e.id} flexDirection="column">
                <Button key={e.id} onPress={() => onToggle(e.id)}>{rows[0]}</Button>
                {body.map((row, i) => (
                  <Text key={i} wrap="truncate-end" dimColor>{row}</Text>
                ))}
                {expanded ? <Button key="collapse" onPress={() => onToggle(e.id)}>{rows[rows.length - 1]}</Button> : null}
              </Box>
            )
          })}
        </>
      )}
    </Box>
  )
}

// band 视图：pane 未摆放（终端 <144 列 unasked，或 person 关过面板）时，
// AbovePrompt 兜底画的一行——整行一个 Button，点击由 register.ts 开 pane
export function bandView(kit: Kit, label: string, onOpen: () => void): unknown {
  const { Box, Text, Button } = kit
  return (
    <Box>
      <Button key="watchtower-band" onPress={onOpen}>
        <Text wrap="truncate-end">{label}</Text>
      </Button>
    </Box>
  )
}
