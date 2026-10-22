import test from 'node:test';
import assert from 'node:assert/strict';
import { recentReturns, locateTranscript, projectDirOf } from './parse-transcript.mjs';

// 解析器是纯函数：夹具直接给 transcript 文本，不落盘
function fixture(lines) {
  return lines.map((l) => JSON.stringify(l)).join('\n') + '\n';
}

// helpers：构造 transcript 行
const assistantToolUse = (id, name, ts, input = { description: 'd' }) => ({
  type: 'assistant',
  timestamp: ts,
  message: { content: [{ type: 'tool_use', id, name, input }] },
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
const taskNotification = (taskId, id, ts, result, summary = null) => ({
  type: 'user',
  timestamp: ts,
  message: {
    content: [
      {
        type: 'text',
        text: `<task-notification>\n<task-id>${taskId}</task-id>\n<tool-use-id>${id}</tool-use-id>\n<output-file>/tmp/x</output-file>\n<status>completed</status>\n${summary !== null ? `<summary>${summary}</summary>\n` : ''}<result>${result}\n</result>\n</task-notification>`,
      },
    ],
  },
});
// 主对话 assistant 文本行（uuid 是 main 条目的展开锚点）
const assistantText = (ts, text, uuid = `u-${ts}`) => ({
  type: 'assistant',
  timestamp: ts,
  uuid,
  message: { content: [{ type: 'text', text }] },
});
// 真人 user 输入（轮界）
const humanInput = (ts, text = 'next') => ({ type: 'user', timestamp: ts, message: { content: text } });

test('同步 tool_result 直存正文（Task 与 Agent 名都匹配，Bash 被排除）', () => {
  const p = fixture([
    assistantToolUse('c1', 'Task', '2026-10-22T01:00:00Z'),
    syncResult('c1', '2026-10-22T01:01:00Z', 'sync task result'),
    assistantToolUse('c2', 'Bash', '2026-10-22T02:00:00Z'),
    bashResult('c2', '2026-10-22T02:01:00Z'),
    assistantToolUse('c3', 'Agent', '2026-10-22T03:00:00Z'),
    syncResult('c3', '2026-10-22T03:01:00Z', 'sync agent result'),
  ]);
  assert.deepEqual(recentReturns(p), [
    { kind: 'agent', time: '2026-10-22T03:01:00Z', taskId: null, id: 'c3', title: 'd', text: 'sync agent result' },
    { kind: 'agent', time: '2026-10-22T01:01:00Z', taskId: null, id: 'c1', title: 'd', text: 'sync task result' },
  ]);
});

test('后台 agent：取 task-notification 的 <result> 全文，跳过启动元数据', () => {
  const p = fixture([
    assistantToolUse('c1', 'Agent', '2026-10-22T04:00:00Z'),
    asyncLaunch('c1', '2026-10-22T04:00:01Z'),
    taskNotification('t1', 'c1', '2026-10-22T04:12:13Z', '多行\n正文\n全文'),
  ]);
  assert.deepEqual(recentReturns(p), [
    { kind: 'agent', time: '2026-10-22T04:12:13Z', taskId: 't1', id: 'c1', title: 'd', text: '多行\n正文\n全文\n' },
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
  const r = recentReturns(p);
  assert.equal(r.length, 1);
  assert.equal(r[0].time, '2026-10-22T04:12:13Z');
});

test('凑满 limit 条停（limit 参数生效，更早的不返回）', () => {
  const lines = [];
  for (let i = 0; i < 12; i++) {
    const id = `c${i}`;
    lines.push(assistantToolUse(id, 'Agent', `2026-10-22T0${i}:00:00Z`), syncResult(id, `2026-10-22T0${i}:00:30Z`, `result ${i}`));
  }
  const r = recentReturns(fixture(lines), 10);
  assert.equal(r.length, 10);
  assert.equal(r[0].text, 'result 11');
  assert.equal(r[9].text, 'result 2');
});

test('默认 limit 50：不足返回全部', () => {
  const p = fixture([
    assistantToolUse('c1', 'Agent', '2026-10-22T04:00:00Z'),
    syncResult('c1', '2026-10-22T04:00:30Z', 'only one'),
  ]);
  assert.deepEqual(recentReturns(p), [{ kind: 'agent', time: '2026-10-22T04:00:30Z', taskId: null, id: 'c1', title: 'd', text: 'only one' }]);
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
  assert.deepEqual(recentReturns(p), [{ kind: 'agent', time: '2026-10-22T06:00:00Z', taskId: 't9', id: 'c9', title: 'd', text: 'mixed result\n' }]);
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
  assert.deepEqual(recentReturns(p), [{ kind: 'agent', time: '2026-10-22T07:00:00Z', taskId: 'ax', id: 'ca', title: 'd', text: 'agent full result' }]);
});

test('task-notification 带 <summary>：输出 summary 字段，summary 与 title 缺失时都省略', () => {
  const p = fixture([
    assistantToolUse('c1', 'Agent', '2026-10-22T10:00:00Z', { description: '后台调研' }),
    taskNotification('t1', 'c1', '2026-10-22T10:01:00Z', 'bg result', 'Agent "后台调研" finished'),
    assistantToolUse('c2', 'Task', '2026-10-22T11:00:00Z'),
    taskNotification('t2', 'c2', '2026-10-22T11:01:00Z', 'no summary result'),
  ]);
  assert.deepEqual(recentReturns(p), [
    { kind: 'agent', time: '2026-10-22T11:01:00Z', taskId: 't2', id: 'c2', title: 'd', text: 'no summary result\n' },
    { kind: 'agent', time: '2026-10-22T10:01:00Z', taskId: 't1', id: 'c1', summary: 'Agent "后台调研" finished', title: '后台调研', text: 'bg result\n' },
  ]);
});

test('title 按 tool-use-id 回查 input.description；无 description 时省略 title 字段', () => {
  const p = fixture([
    assistantToolUse('c1', 'Task', '2026-10-22T07:00:00Z', { description: '查依赖版本' }),
    syncResult('c1', '2026-10-22T07:01:00Z', 'result with title'),
    assistantToolUse('c2', 'Agent', '2026-10-22T08:00:00Z', { prompt: 'x' }),
    syncResult('c2', '2026-10-22T08:01:00Z', 'result without title'),
    // 后台通知同样按 tool-use-id 回查 description
    assistantToolUse('c3', 'Agent', '2026-10-22T09:00:00Z', { description: '后台调研' }),
    asyncLaunch('c3', '2026-10-22T09:00:01Z'),
    taskNotification('t3', 'c3', '2026-10-22T09:10:00Z', 'bg result'),
  ]);
  assert.deepEqual(recentReturns(p), [
    { kind: 'agent', time: '2026-10-22T09:10:00Z', taskId: 't3', id: 'c3', title: '后台调研', text: 'bg result\n' },
    { kind: 'agent', time: '2026-10-22T08:01:00Z', taskId: null, id: 'c2', text: 'result without title' },
    { kind: 'agent', time: '2026-10-22T07:01:00Z', taskId: null, id: 'c1', title: '查依赖版本', text: 'result with title' },
  ]);
  assert.ok(!('title' in recentReturns(p)[1]));
});

test('主回复收集：每轮最终 assistant 文本入池，kind main、taskId null、uuid 为锚点', () => {
  const p = fixture([
    assistantText('2026-10-22T01:00:00Z', 'turn one final', 'u1'),
    humanInput('2026-10-22T01:01:00Z'),
    assistantText('2026-10-22T02:00:00Z', 'turn two final', 'u2'),
  ]);
  // 末轮 Stop 回复（其后还没有 user 输入）也入池
  assert.deepEqual(recentReturns(p), [
    { kind: 'main', time: '2026-10-22T02:00:00Z', taskId: null, id: 'u2', text: 'turn two final' },
    { kind: 'main', time: '2026-10-22T01:00:00Z', taskId: null, id: 'u1', text: 'turn one final' },
  ]);
});

test('同轮折叠：一行 text+tool_use+text 取最后一块，跨多条 assistant 行也只留最后一条', () => {
  const p = fixture([
    {
      type: 'assistant',
      timestamp: '2026-10-22T01:00:00Z',
      uuid: 'u1',
      message: { content: [{ type: 'text', text: 'first try' }, { type: 'tool_use', id: 'c1', name: 'Bash', input: {} }, { type: 'text', text: 'mid text' }] },
    },
    assistantText('2026-10-22T01:00:05Z', 'final text', 'u2'),
    humanInput('2026-10-22T01:01:00Z'),
  ]);
  const r = recentReturns(p);
  assert.deepEqual(r, [{ kind: 'main', time: '2026-10-22T01:00:05Z', taskId: null, id: 'u2', text: 'final text' }]);
});

test('tool_result / task-notification / sidechain 输入不开新轮，sidechain assistant 不入池', () => {
  const p = fixture([
    assistantToolUse('c1', 'Agent', '2026-10-22T01:00:00Z'),
    assistantText('2026-10-22T01:00:01Z', 'turn one text', 'u1'),
    syncResult('c1', '2026-10-22T01:00:30Z', 'agent result'), // tool_result 不开轮
    taskNotification('t1', 'c1', '2026-10-22T01:01:00Z', 'bg result'), // 通知不开轮
    { ...humanInput('2026-10-22T01:02:00Z'), isSidechain: true }, // sidechain 输入不开轮
    { ...assistantText('2026-10-22T01:03:00Z', 'sidechain reply', 'u9'), isSidechain: true }, // sidechain 回复不入池
    humanInput('2026-10-22T01:04:00Z'),
  ]);
  const r = recentReturns(p);
  // 2 条 agent（同步 result + 后台通知）+ 1 条 main；sidechain 回复不入池
  assert.deepEqual(r.map((e) => [e.kind, e.text]), [
    ['agent', 'bg result\n'],
    ['agent', 'agent result'],
    ['main', 'turn one text'],
  ]);
});

test('混池时间序：agent 返回与主回复按 transcript 行序从新到旧交错', () => {
  const p = fixture([
    assistantText('2026-10-22T01:00:00Z', 'main one', 'u1'),
    assistantToolUse('c1', 'Agent', '2026-10-22T01:00:30Z'),
    asyncLaunch('c1', '2026-10-22T01:00:31Z'),
    taskNotification('t1', 'c1', '2026-10-22T01:05:00Z', 'agent result'),
    humanInput('2026-10-22T01:06:00Z'),
    assistantText('2026-10-22T02:00:00Z', 'main two', 'u2'),
  ]);
  const r = recentReturns(p);
  assert.deepEqual(r.map((e) => [e.kind, e.text]), [
    ['main', 'main two'],
    ['agent', 'agent result\n'],
    ['main', 'main one'],
  ]);
});

test('默认截断 50 条：60 条输入只保留最新 50 条', () => {
  const lines = [];
  for (let i = 0; i < 60; i++) {
    lines.push(assistantText(`2026-10-22T0${Math.floor(i / 10)}:${String(i % 60).padStart(2, '0')}:00Z`, `reply ${i}`, `u${i}`));
    lines.push(humanInput(`2026-10-22T0${Math.floor(i / 10)}:${String(i % 60).padStart(2, '0')}:10Z`));
  }
  const r = recentReturns(fixture(lines));
  assert.equal(r.length, 50);
  assert.equal(r[0].text, 'reply 59');
  assert.equal(r[49].text, 'reply 10');
});

test('projectDirOf / locateTranscript：纯字符串拼接，HOME 下按 slug 编码（/ 与 . 都 → -，worktree 变体）', () => {
  const home = '/Users/x/home';
  // 普通：/Users/x/proj → -Users-x-proj
  const d1 = `${home}/.claude/projects/-Users-x-proj`;
  assert.equal(projectDirOf('/Users/x/proj', home), d1);
  assert.equal(locateTranscript('/Users/x/proj', 'sess1', home), `${d1}/sess1.jsonl`);

  // worktree：/Users/x/proj/.claude/worktrees/agent-1 → -Users-x-proj--claude-worktrees-agent-1
  const d2 = `${home}/.claude/projects/-Users-x-proj--claude-worktrees-agent-1`;
  assert.equal(projectDirOf('/Users/x/proj/.claude/worktrees/agent-1', home), d2);
  assert.equal(
    locateTranscript('/Users/x/proj/.claude/worktrees/agent-1', 'sess2', home),
    `${d2}/sess2.jsonl`
  );

  // 不存在的 session：路径仍可算出（调用方自行读失败处理）
  assert.equal(locateTranscript('/Users/x/proj', 'nope', home), `${d1}/nope.jsonl`);
});
