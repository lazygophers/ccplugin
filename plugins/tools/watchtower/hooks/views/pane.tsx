// pane 视图：把 pane-rows 的字符串行映射成组件树；每条包 Button，点击切换展开/收起。
// Box/Text/Button 由 register.ts 经 $.ui.resolve 提供；属性用法照 code-modernization 的 views/pane.tsx。
import { MAX_ROWS, headerOf, collapsedRows, expandedRows } from '../../scripts/pane-rows.mjs'

type AnyComponent = (props: Record<string, unknown>) => unknown

export type Kit = { Box: AnyComponent; Text: AnyComponent; Button: AnyComponent }

// 只声明渲染用到的字段；来源 recentAgentReturns 多出的 taskId 不渲染（窄 pane 放不下）
export type Entry = { id: string; time: string; title?: string; text: string }

export function paneView(
  kit: Kit,
  entries: Entry[] | null,
  columns: number,
  expandedId: string | null,
  onToggle: (id: string) => void,
): unknown {
  const { Box, Text, Button } = kit
  const shown = (entries ?? []).slice(0, MAX_ROWS)

  return (
    <Box flexDirection="column" paddingRight={1} rowGap={0}>
      {shown.length === 0 ? (
        <Text>No agent returns in this session yet.</Text>
      ) : (
        <>
          <Text bold>{headerOf(shown.length)}</Text>
          {shown.map((e) => {
            const rows = e.id === expandedId ? expandedRows(e, columns) : collapsedRows(e, columns)
            return (
              <Button key={e.id} onPress={() => onToggle(e.id)}>
                <Box flexDirection="column">
                  {rows.map((row, i) => (
                    <Text key={i} wrap="truncate-end" dimColor={i > 0}>{row}</Text>
                  ))}
                </Box>
              </Button>
            )
          })}
        </>
      )}
    </Box>
  )
}
