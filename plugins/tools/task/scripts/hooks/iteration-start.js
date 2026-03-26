#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const taskId = process.env.TASK_ID || 'unknown';
const sessionId = process.env.SESSION_ID || 'unknown';
const iteration = parseInt(process.env.ITERATION || '0');
const phase = process.env.PHASE || 'unknown';

const logEntry = {
  hook: 'IterationStart',
  task_id: taskId,
  session_id: sessionId,
  iteration: iteration,
  phase: phase,
  timestamp: new Date().toISOString()
};

const logDir = path.join(process.env.HOME, '.claude/logs');
const logPath = path.join(logDir, `task-hooks-${sessionId}.jsonl`);
fs.appendFileSync(logPath, JSON.stringify(logEntry) + '\n', 'utf8');

console.log(`[Hook:IterationStart] 迭代 ${iteration} 开始, 阶段: ${phase}`);
