#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const taskId = process.env.TASK_ID || 'unknown';
const sessionId = process.env.SESSION_ID || 'unknown';
const iteration = parseInt(process.env.ITERATION || '0');
const errorMessage = process.env.ERROR_MESSAGE || '';

const failureEntry = {
  hook: 'TaskFailed',
  task_id: taskId,
  session_id: sessionId,
  iteration: iteration,
  error_message: errorMessage,
  timestamp: new Date().toISOString()
};

// 保存到hook日志
const logDir = path.join(process.env.HOME, '.claude/logs');
const logPath = path.join(logDir, `task-hooks-${sessionId}.jsonl`);
fs.appendFileSync(logPath, JSON.stringify(failureEntry) + '\n', 'utf8');

// 保存到失败记录
const failureDir = path.join(process.env.HOME, '.claude/task-failures');
if (!fs.existsSync(failureDir)) {
  fs.mkdirSync(failureDir, { recursive: true });
}

const failurePath = path.join(failureDir, `${taskId}-${iteration}.json`);
fs.writeFileSync(failurePath, JSON.stringify(failureEntry, null, 2), 'utf8');

console.log(`[Hook:TaskFailed] 任务失败: ${taskId}, 迭代: ${iteration}`);
