#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const taskId = process.env.TASK_ID || 'unknown';
const sessionId = process.env.SESSION_ID || 'unknown';
const checkpointPath = process.env.CHECKPOINT_PATH || '';

const checkpointEntry = {
  hook: 'CheckpointSave',
  task_id: taskId,
  session_id: sessionId,
  checkpoint_path: checkpointPath,
  timestamp: new Date().toISOString()
};

// 保存到hook日志
const logDir = path.join(process.env.HOME, '.claude/logs');
const logPath = path.join(logDir, `task-hooks-${sessionId}.jsonl`);
fs.appendFileSync(logPath, JSON.stringify(checkpointEntry) + '\n', 'utf8');

console.log(`[Hook:CheckpointSave] 检查点保存: ${checkpointPath}`);
