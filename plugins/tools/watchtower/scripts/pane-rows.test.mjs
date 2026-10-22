import test from 'node:test';
import assert from 'node:assert/strict';
import { rowsOf, collapsedRows, expandedRows, wrapLines, titleOf, bandRow } from './pane-rows.mjs';

const entry = (over = {}) => ({ id: 'e1', time: '2026-10-22T04:12:13Z', taskId: null, text: 'first result', ...over });

test('空态：null 与空数组都返回一行空态文案', () => {
  assert.deepEqual(rowsOf(null), ['No returns in this session yet.']);
  assert.deepEqual(rowsOf([]), ['No returns in this session yet.']);
});

test('读失败态：errorText 只渲染一行错误，区分于空态，有记录也不渲染', () => {
  const tooBig = 'Cannot read transcript: file is over the 4 MiB read cap';
  assert.deepEqual(rowsOf(null, 80, null, tooBig), [tooBig]);
  assert.deepEqual(rowsOf([entry()], 80, null, 'Cannot read transcript: not found'), [
    'Cannot read transcript: not found',
  ]);
});

test('收起态：表头 + 每条标题行（无 title 回退正文首行，单行正文不再重复出预览）', () => {
  const rows = rowsOf([entry(), entry({ id: 'e2', time: '2026-10-22T03:00:00Z', text: 'second result' })]);
  assert.equal(rows.length, 3);
  assert.match(rows[0], /^Returns — 2 shown, newest first$/);
  assert.match(rows[1], /^\d{2}:\d{2}  ▸ first result$/);
  assert.match(rows[2], /^\d{2}:\d{2}  ▸ second result$/);
});

test('有 title 用 title，预览显示正文前两行（≥60 宽），截断尾带 …', () => {
  const rows = collapsedRows(entry({ title: '查依赖版本', text: 'line1\nline2\nline3' }), 80);
  assert.match(rows[0], /^\d{2}:\d{2}  ▸ 查依赖版本$/);
  assert.deepEqual(rows.slice(1), ['  line1', '  line2…']);
});

test('截断到 50 条：60 条输入只保留最新 50 条，最旧滚出', () => {
  const entries = Array.from({ length: 60 }, (_, i) => entry({ id: `e${i}`, time: `2026-10-22T0${Math.floor(i / 10)}:${String(i).padStart(2, '0')}:00Z`, text: `result ${i}` })); // 新→旧
  const rows = rowsOf(entries);
  assert.ok(rows[1].includes('result 0')); // 最新保留
  assert.ok(!rows.some((r) => r.includes('result 50') || r.includes('result 59'))); // 最旧滚出
});

test('main 条目：头部 ◆ 主回复，预览从正文首行起（不因头部吞首行）', () => {
  const rows = collapsedRows(entry({ kind: 'main', text: 'line1\nline2\nline3' }), 80);
  assert.match(rows[0], /^\d{2}:\d{2}  ◆ 主回复$/);
  assert.deepEqual(rows.slice(1), ['  line1', '  line2…']);
  // 展开态也保持 ◆ 标记，末尾带收起行
  const expanded = expandedRows(entry({ kind: 'main', text: '第一行\n第二行' }), 80);
  assert.match(expanded[0], /^\d{2}:\d{2}  ◆ 主回复$/);
  assert.deepEqual(expanded.slice(1), ['  第一行', '  第二行', '⌃ 收起']);
});

test('混池渲染：同一批里 ◆ 与 ▸ 两种头部并存，agent 条目维持 title 头部', () => {
  const rows = rowsOf([
    entry({ kind: 'main', text: 'main reply body' }),
    entry({ kind: 'agent', title: '查依赖', text: 'agent body' }),
  ]);
  assert.ok(rows.some((r) => /◆ 主回复/.test(r)));
  assert.ok(rows.some((r) => /▸ 查依赖/.test(r)));
});

test('展开态：expandedId 命中条目显示全文换行，其余条目收起', () => {
  const entries = [
    entry({ id: 'a', title: '查依赖', text: '第一行\n第二行\n第三行' }),
    entry({ id: 'b', text: 'short result' }),
  ];
  const collapsed = rowsOf(entries, 80, null);
  assert.ok(!collapsed.some((r) => r.includes('第三行'))); // 收起只见预览两行
  const rows = rowsOf(entries, 80, 'a');
  assert.ok(rows.some((r) => r.includes('第三行')));
  assert.ok(rows.some((r) => r.includes('▾ 查依赖')));
  assert.ok(rows.some((r) => r.includes('▸ short result'))); // 其余仍收起
  assert.ok(rows.includes('⌃ 收起')); // 展开块末尾有显式收起入口
  assert.ok(!rowsOf(entries, 80, null).includes('⌃ 收起')); // 收起态不出现
});

test('小屏（width 20）：预览只 1 行、所有行不超宽、超长词硬切不炸版', () => {
  const rows = collapsedRows(entry({ text: 'word '.repeat(3) + 'x'.repeat(60) }), 20);
  assert.equal(rows.length, 2); // 标题 + 1 行预览
  assert.ok(rows.every((r) => r.length <= 20));
});

test('wrapLines：软换行、超宽词硬切、跳过空行', () => {
  assert.deepEqual(wrapLines('aaa bb cc', 5), ['aaa', 'bb cc']);
  assert.deepEqual(wrapLines('abcdefghij', 4), ['abcd', 'efgh', 'ij']); // 超长词硬切不丢字符
  assert.deepEqual(wrapLines('\n\n x \n\n  y', 10), ['x', 'y']); // 只留非空行
  assert.deepEqual(wrapLines(undefined, 10), []); // 坏输入不抛错
});

test('titleOf：summary 优先于 title，缺失时逐级回退；summary 在时预览不吞正文首行', () => {
  assert.equal(titleOf(entry({ summary: 'Agent "调研" finished', title: '查依赖版本' })), 'Agent "调研" finished');
  assert.equal(titleOf(entry({ title: '查依赖版本' })), '查依赖版本');
  assert.equal(titleOf(entry({ text: '\n\n t1\nrest' })), 't1');
  const rows = collapsedRows(entry({ summary: 'Agent "调研" finished', text: 'line1\nline2' }), 80);
  assert.match(rows[0], /▸ Agent "调研" finished$/);
  assert.deepEqual(rows.slice(1), ['  line1', '  line2']); // 首行不被跳过
});

test('bandRow：一行短文案，0 / null / 非数都回退 0，不炸', () => {
  assert.equal(bandRow(3), '⌃ 返回值 3');
  assert.equal(bandRow(0), '⌃ 返回值 0'); // 0 不画 band，此值只保底
  assert.equal(bandRow(null), '⌃ 返回值 0');
  assert.equal(bandRow('garbage'), '⌃ 返回值 0');
  assert.ok(bandRow(999999).length <= 20); // 100 列终端一行放得下
});

test('坏时间戳不抛错，titleOf 回退正文第一个非空行', () => {
  assert.match(collapsedRows(entry({ time: 'garbage' }), 80)[0], /^--:--  ▸ /);
  assert.equal(titleOf(entry({ text: '\n\n t1\nrest' })), 't1');
  assert.equal(titleOf(entry({ title: 'd', text: 'x' })), 'd');
});
