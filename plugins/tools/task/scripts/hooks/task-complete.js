#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const taskId = process.env.TASK_ID || 'unknown';
const sessionId = process.env.SESSION_ID || 'unknown';
const totalIterations = parseInt(process.env.TOTAL_ITERATIONS || '0');
const success = process.env.SUCCESS === 'true';

const completionEntry = {
  hook: 'TaskComplete',
  task_id: taskId,
  session_id: sessionId,
  total_iterations: totalIterations,
  success: success,
  timestamp: new Date().toISOString()
};

// 保存到hook日志
const logDir = path.join(process.env.HOME, '.claude/logs');
const logPath = path.join(logDir, `task-hooks-${sessionId}.jsonl`);
fs.appendFileSync(logPath, JSON.stringify(completionEntry) + '\n', 'utf8');

// 保存到完成记录
const completeDir = path.join(process.env.HOME, '.claude/task-history');
if (!fs.existsSync(completeDir)) {
  fs.mkdirSync(completeDir, { recursive: true });
}

const completePath = path.join(completeDir, `${taskId}.json`);
fs.writeFileSync(completePath, JSON.stringify(completionEntry, null, 2), 'utf8');

console.log(`[Hook:TaskComplete] 任务完成: ${taskId}, 迭代次数: ${totalIterations}, 成功: ${success}`);
