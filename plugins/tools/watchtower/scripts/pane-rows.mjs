// pane 行渲染的纯逻辑：输入 recentAgentReturns 的输出 → 面板文本行。
// 放 .mjs 让 node --test 直接测；hooks/views/pane.tsx 只做字符串 → 组件映射。
// 展开态也是这里的纯状态变换：rowsOf(entries, width, expandedId)，点击接线在 register.ts/pane.tsx。

export const MAX_ROWS = 50;

const hhmm = (iso) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '--:--' : d.toTimeString().slice(0, 5);
};

const clip = (s, width) => (s.length <= width ? s : s.slice(0, Math.max(1, width - 1)) + '…');

// 词级软换行（超宽词硬切），跳过空行；width 下限 4，小屏不炸版
export function wrapLines(text, width) {
  const w = Math.max(4, width);
  const out = [];
  for (const para of String(text ?? '').split('\n')) {
    if (para.trim() === '') continue;
    let line = '';
    for (let word of para.trim().split(/\s+/)) {
      while (word.length > w) {
        if (line !== '') {
          out.push(line);
          line = '';
        }
        out.push(word.slice(0, w));
        word = word.slice(w);
      }
      if (line === '') line = word;
      else if (line.length + 1 + word.length <= w) line += ' ' + word;
      else {
        out.push(line);
        line = word;
      }
    }
    if (line !== '') out.push(line);
  }
  return out;
}

// 显示标题：通知的 <summary>（harness 的「Teammate @name finished」形态）优先，
// 再调用时的 description（解析器回查），都无则回退正文第一个非空行
export const titleOf = (entry) =>
  entry.summary ?? entry.title ?? ((entry.text ?? '').split('\n').find((l) => l.trim() !== '') ?? '').trim();

// 收起态：标题行 + 正文预览。预览行数按宽度自适应（≥60 两行，否则一行，小屏至少 1 行）；
// agent 条目标题回退自正文时预览跳过该行，不重复展示；main 条目头部是「主回复」、
// 不含正文，预览从首行起
const isMain = (entry) => entry.kind === 'main';
const headOf = (entry, marker) =>
  isMain(entry) ? `${hhmm(entry.time)}  ◆ 主回复` : `${hhmm(entry.time)}  ${marker} ${titleOf(entry)}`;

export function collapsedRows(entry, width) {
  const w = Math.max(8, width);
  const lines = wrapLines(entry.text, w - 2);
  // 标题回退自正文时预览跳过该行（header 已显示它）；summary/title 在时不跳
  const rest = isMain(entry) || entry.summary !== undefined || entry.title !== undefined ? lines : lines.slice(1);
  const n = w >= 60 ? 2 : 1;
  const shown = rest
    .slice(0, n)
    .map((l, i) => clip(`  ${l}${i === n - 1 && rest.length > n ? '…' : ''}`, w));
  return [clip(headOf(entry, '▸'), w), ...shown];
}

// 展开态：标题行 + 全文按宽度换行（main 保持 ◆ 标记，agent 转为 ▾）+ 末尾收起行。
// 收起行是显式入口：全文一长标题行滚出视野，末尾不给可点的收起就没有入口
export const COLLAPSE_ROW = '⌃ 收起';
export function expandedRows(entry, width) {
  const w = Math.max(8, width);
  return [
    clip(headOf(entry, '▾'), w),
    ...wrapLines(entry.text, w - 2).map((l) => clip(`  ${l}`, w)),
    COLLAPSE_ROW,
  ];
}

export const headerOf = (count) => `Returns — ${count} shown, newest first`;

// band 兜底行（终端 <144 列 unasked 时 pane 不摆放，AbovePrompt 上画这一行）：
// 读失败 / 无记录按 0 条；整行是按钮，⌃ 即提示可点开面板
export function bandRow(count) {
  const n = Number(count);
  return `⌃ 返回值 ${Number.isInteger(n) && n > 0 ? n : 0}`;
}

// entries 为 null（transcript 读不到）或空数组 → 空态一行，不报错。
// errorText 非空（transcript 读不了，如超 4 MiB）→ 只显示那一行错误，区分于空态。
// 解析器已限 50 条，slice 是渲染层兜底：满 50 条时最旧滚出。
// expandedId 命中的条目展开全文（至多一条），其余收起。
export function rowsOf(entries, width = 80, expandedId = null, errorText = null) {
  if (errorText) return [errorText];
  if (!entries || entries.length === 0) return ['No returns in this session yet.'];
  const kept = entries.slice(0, MAX_ROWS);
  return [
    headerOf(kept.length),
    ...kept.flatMap((e) => (e.id === expandedId ? expandedRows(e, width) : collapsedRows(e, width))),
  ];
}
