// pane 行渲染的纯逻辑：输入 recentAgentReturns 的输出 → 面板文本行。
// 放 .mjs 让 node --test 直接测；hooks/views/pane.tsx 只做字符串 → 组件映射。

export const MAX_ROWS = 10;

const hhmm = (iso) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '--:--' : d.toTimeString().slice(0, 5);
};

// 正文取第一个非空行，拼「时间 + 正文」后按面板宽度截断
export function entryLine(entry, width) {
  const body = ((entry.text ?? '').split('\n').find((l) => l.trim() !== '') ?? '').trim();
  const head = `${hhmm(entry.time)}  ${body}`;
  return head.length <= width ? head : head.slice(0, Math.max(1, width - 1)) + '…';
}

// entries 为 null（transcript 读不到）或空数组 → 空态一行，不报错。
// 解析器已限 10 条，slice 是渲染层兜底：满 10 条时最旧滚出。
export function rowsOf(entries, width = 80) {
  if (!entries || entries.length === 0) return ['No agent returns in this session yet.'];
  const kept = entries.slice(0, MAX_ROWS);
  return [`Agent returns — ${kept.length} shown, newest first`, ...kept.map((e) => entryLine(e, Math.max(20, width)))];
}
