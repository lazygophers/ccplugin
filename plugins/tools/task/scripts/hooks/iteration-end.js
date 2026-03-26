#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const taskId = process.env.TASK_ID || 'unknown';
const sessionId = process.env.SESSION_ID || 'unknown';
const iteration = parseInt(process.env.ITERATION || '0');
const phase = process.env.PHASE || 'unknown';
const status = process.env.STATUS || 'unknown';

// 收集迭代指标
const metrics = {
  hook: 'IterationEnd',
  task_id: taskId,
  session_id: sessionId,
  iteration: iteration,
  phase: phase,
  status: status,
  timestamp: new Date().toISOString()
};

// 保存到指标日志
const metricsDir = path.join(process.env.HOME, '.claude/metrics');
if (!fs.existsSync(metricsDir)) {
  fs.mkdirSync(metricsDir, { recursive: true });
}

const metricsPath = path.join(metricsDir, 'task-metrics.jsonl');
fs.appendFileSync(metricsPath, JSON.stringify(metrics) + '\n', 'utf8');

// 保存到hook日志
const logDir = path.join(process.env.HOME, '.claude/logs');
const logPath = path.join(logDir, `task-hooks-${sessionId}.jsonl`);
fs.appendFileSync(logPath, JSON.stringify(metrics) + '\n', 'utf8');

console.log(`[Hook:IterationEnd] 迭代 ${iteration} 完成, 状态: ${status}`);
