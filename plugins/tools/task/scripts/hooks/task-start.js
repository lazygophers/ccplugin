#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

// 从环境变量获取上下文
const taskId = process.env.TASK_ID || 'unknown';
const sessionId = process.env.SESSION_ID || 'unknown';
const userTask = process.env.USER_TASK || '';

// 记录任务启动
const logDir = path.join(process.env.HOME, '.claude/logs');
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

const logEntry = {
  hook: 'TaskStart',
  task_id: taskId,
  session_id: sessionId,
  user_task: userTask,
  timestamp: new Date().toISOString()
};

const logPath = path.join(logDir, `task-hooks-${sessionId}.jsonl`);
fs.appendFileSync(logPath, JSON.stringify(logEntry) + '\n', 'utf8');

console.log(`[Hook:TaskStart] 任务启动: ${taskId}`);
