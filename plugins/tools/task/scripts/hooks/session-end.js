#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const sessionId = process.env.SESSION_ID || 'unknown';

const sessionEndEntry = {
  hook: 'SessionEnd',
  session_id: sessionId,
  timestamp: new Date().toISOString()
};

// 保存到hook日志
const logDir = path.join(process.env.HOME, '.claude/logs');
const logPath = path.join(logDir, `task-hooks-${sessionId}.jsonl`);
fs.appendFileSync(logPath, JSON.stringify(sessionEndEntry) + '\n', 'utf8');

console.log(`[Hook:SessionEnd] 会话结束: ${sessionId}`);
