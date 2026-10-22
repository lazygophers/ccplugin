import test from 'node:test';
import assert from 'node:assert/strict';
import { rowsOf, entryLine } from './pane-rows.mjs';

const entry = (time, text) => ({ time, taskId: null, text });

test('空态：null 与空数组都返回一行空态文案', () => {
  assert.deepEqual(rowsOf(null), ['No agent returns in this session yet.']);
  assert.deepEqual(rowsOf([]), ['No agent returns in this session yet.']);
});

test('渲染输入→输出：表头 + 每条一行，时间在前正文在后', () => {
  const rows = rowsOf([entry('2026-10-22T04:12:13Z', 'first result'), entry('2026-10-22T03:00:00Z', 'second result')]);
  assert.equal(rows.length, 3);
  assert.match(rows[0], /^Agent returns — 2 shown, newest first$/);
  assert.match(rows[1], /^\d{2}:\d{2}  first result$/);
  assert.match(rows[2], /^\d{2}:\d{2}  second result$/);
});

test('截断到 10 条：12 条输入只保留最新 10 条，最旧滚出', () => {
  const entries = Array.from({ length: 12 }, (_, i) => entry(`2026-10-22T0${i}:00:00Z`, `result ${i}`)); // 新→旧
  const rows = rowsOf(entries);
  assert.equal(rows.length, 11); // 表头 + 10 行
  assert.ok(rows[1].includes('result 0')); // 最新保留
  assert.ok(!rows.some((r) => r.includes('result 10') || r.includes('result 11'))); // 最旧滚出
});

test('超宽截断：行宽不超过 width，结尾是 …', () => {
  const line = entryLine(entry('2026-10-22T04:12:13Z', 'x'.repeat(100)), 30);
  assert.ok(line.length <= 30);
  assert.ok(line.endsWith('…'));
});

test('多行正文只取第一个非空行；坏时间戳不抛错', () => {
  assert.equal(entryLine(entry('2026-10-22T04:12:13Z', '\n\nline1\nline2'), 80).includes('line1'), true);
  assert.match(entryLine(entry('garbage', 'ok'), 80), /^--:--  ok$/);
});
