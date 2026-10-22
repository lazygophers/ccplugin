import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { recentAgentReturns } from './parse-transcript.mjs';

const dir = mkdtempSync(join(tmpdir(), 'watchtower-test-'));
test.after(() => rmSync(dir, { recursive: true, force: true }));

function fixture(lines) {
  const p = join(dir, `f-${Math.random().toString(36).slice(2)}.jsonl`);
  writeFileSync(p, lines.map((l) => JSON.stringify(l)).join('\n') + '\n');
  return p;
}

// helpers：构造 transcript 行
const assistantToolUse = (id, name, ts) => ({
  type: 'assistant',
  timestamp: ts,
  message: { content: [{ type: 'tool_use', id, name, input: { description: 'd' } }] },
});
const bashResult = (id, ts) => ({
  type: 'user',
  timestamp: ts,
  message: { content: [{ type: 'tool_result', tool_use_id: id, content: 'ok' }] },
});
const syncResult = (id, ts, text) => ({
  type: 'user',
  timestamp: ts,
  message: { content: [{ type: 'tool_result', tool_use_id: id, content: [{ type: 'text', text }] }] },
});
const asyncLaunch = (id, ts) => ({
  type: 'user',
  timestamp: ts,
  message: {
    content: [
      { type: 'tool_result', tool_use_id: id, content: [{ type: 'text', text: 'Async agent launched successfully. agentId: x' }] },
    ],
  },
});
const taskNotification = (taskId, id, ts, result) => ({
  type: 'user',
  timestamp: ts,
  message: {
    content: [
      {
        type: 'text',
        text: `<task-notification>\n<task-id>${taskId}</task-id>\n<tool-use-id>${id}</tool-use-id>\n<output-file>/tmp/x</output-file>\n<status>completed</status>\n<summary>Agent "t" finished</summary>\n<result>${result}\n</result>\n</task-notification>`,
      },
    ],
  },
});

test('同步 tool_result 直存正文（Task 与 Agent 名都匹配，Bash 被排除）', () => {
  const p = fixture([
    assistantToolUse('c1', 'Task', '2026-10-22T01:00:00Z'),
    syncResult('c1', '2026-10-22T01:01:00Z', 'sync task result'),
    assistantToolUse('c2', 'Bash', '2026-10-22T02:00:00Z'),
    bashResult('c2', '2026-10-22T02:01:00Z'),
    assistantToolUse('c3', 'Agent', '2026-10-22T03:00:00Z'),
    syncResult('c3', '2026-10-22T03:01:00Z', 'sync agent result'),
  ]);
  assert.deepEqual(recentAgentReturns(p), [
    { time: '2026-10-22T03:01:00Z', taskId: null, text: 'sync agent result' },
    { time: '2026-10-22T01:01:00Z', taskId: null, text: 'sync task result' },
  ]);
});

test('后台 agent：取 task-notification 的 <result> 全文，跳过启动元数据', () => {
  const p = fixture([
    assistantToolUse('c1', 'Agent', '2026-10-22T04:00:00Z'),
    asyncLaunch('c1', '2026-10-22T04:00:01Z'),
    taskNotification('t1', 'c1', '2026-10-22T04:12:13Z', '多行\n正文\n全文'),
  ]);
  assert.deepEqual(recentAgentReturns(p), [
    { time: '2026-10-22T04:12:13Z', taskId: 't1', text: '多行\n正文\n全文\n' },
  ]);
});

test('api-request-blob 重放行被跳过，不重复计数', () => {
  const p = fixture([
    assistantToolUse('c1', 'Agent', '2026-10-22T04:00:00Z'),
    asyncLaunch('c1', '2026-10-22T04:00:01Z'),
    taskNotification('t1', 'c1', '2026-10-22T04:12:13Z', 'real result'),
    // blob 重放：非 user/assistant 的 type，内容是历史 content 的副本
    { type: 'api-request-blob', timestamp: '2026-10-22T05:00:00Z', blob: { messages: [{ content: taskNotification('t1', 'c1', 'replay', 'real result').message.content }] } },
  ]);
  const r = recentAgentReturns(p);
  assert.equal(r.length, 1);
  assert.equal(r[0].time, '2026-10-22T04:12:13Z');
});

test('从尾扫描凑满 10 条停（更早的不返回）', () => {
  const lines = [];
  for (let i = 0; i < 12; i++) {
    const id = `c${i}`;
    lines.push(assistantToolUse(id, 'Agent', `2026-10-22T0${i}:00:00Z`), syncResult(id, `2026-10-22T0${i}:00:30Z`, `result ${i}`));
  }
  const r = recentAgentReturns(fixture(lines));
  assert.equal(r.length, 10);
  assert.equal(r[0].text, 'result 11');
  assert.equal(r[9].text, 'result 2');
});

test('不足 10 条：返回全部', () => {
  const p = fixture([
    assistantToolUse('c1', 'Agent', '2026-10-22T04:00:00Z'),
    syncResult('c1', '2026-10-22T04:00:30Z', 'only one'),
  ]);
  assert.deepEqual(recentAgentReturns(p), [{ time: '2026-10-22T04:00:30Z', taskId: null, text: 'only one' }]);
});

test('同一条 user 行里 task-notification 与 tool_result 混排也能取', () => {
  // 现实中 task-notification 行 content 可能带多个块，正文块以 <task-notification> 开头
  const p = fixture([
    assistantToolUse('c9', 'Agent', '2026-10-22T05:59:00Z'),
    {
      type: 'user',
      timestamp: '2026-10-22T06:00:00Z',
      message: {
        content: [
          { type: 'text', text: '<system-reminder>x</system-reminder>' },
          { type: 'text', text: taskNotification('t9', 'c9', 'unused', 'mixed result').message.content[0].text },
        ],
      },
    },
  ]);
  assert.deepEqual(recentAgentReturns(p), [{ time: '2026-10-22T06:00:00Z', taskId: 't9', text: 'mixed result\n' }]);
});

test('真实形态：content 块是纯字符串；Bash 后台任务的 task-notification 被排除', () => {
  const p = fixture([
    // Bash 后台任务（真实样例：task-id 形如 bzxjf5tal）
    assistantToolUse('cb', 'Bash', '2026-10-22T05:00:00Z'),
    // Agent 后台
    assistantToolUse('ca', 'Agent', '2026-10-22T06:00:00Z'),
    // 字符串块形态的 task-notification（真实 transcript 实测：块是纯字符串）
    {
      type: 'user',
      timestamp: '2026-10-22T07:00:00Z',
      origin: { kind: 'task-notification' },
      message: { content: [' <task-notification>\n<task-id>bx</task-id>\n<tool-use-id>cb</tool-use-id>\n<status>completed</status>\n<result>bash bg output</result>\n</task-notification>', '<task-notification>\n<task-id>ax</task-id>\n<tool-use-id>ca</tool-use-id>\n<status>completed</status>\n<result>agent full result</result>\n</task-notification>'] },
    },
  ]);
  assert.deepEqual(recentAgentReturns(p), [{ time: '2026-10-22T07:00:00Z', taskId: 'ax', text: 'agent full result' }]);
});
