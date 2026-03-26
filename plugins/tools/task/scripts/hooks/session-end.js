#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const sessionId = process.env.SESSION_ID || 'unknown';
const PLUGIN_NAME = 'task';
const PROJECT_DIR = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const HOME = process.env.HOME || require('os').homedir();

// ─── 日志（与 lib/logging 规范一致）────────────────────────────────────────────────
// 日志目录: <project>/.lazygophers/ccplugin/log/
// 文件命名: YYYYMMDDHH.log（按小时轮转）
// 软连接: log.log → 当前小时文件
// 格式: <app_name> [LEVEL] [HH:MM:SS] [filename:lineno] message

function resolveLogDir() {
  const lazygophersPath = path.join(PROJECT_DIR, '.lazygophers');
  try {
    if (fs.existsSync(lazygophersPath) && !fs.statSync(lazygophersPath).isDirectory()) {
      return path.join(HOME, '.lazygophers', 'ccplugin', 'log');
    }
  } catch { /* ignore */ }
  return path.join(PROJECT_DIR, '.lazygophers', 'ccplugin', 'log');
}

function getCurrentHour() {
  const now = new Date();
  return now.getFullYear().toString() +
    String(now.getMonth() + 1).padStart(2, '0') +
    String(now.getDate()).padStart(2, '0') +
    String(now.getHours()).padStart(2, '0');
}

function getTimestamp() {
  const now = new Date();
  return String(now.getHours()).padStart(2, '0') + ':' +
    String(now.getMinutes()).padStart(2, '0') + ':' +
    String(now.getSeconds()).padStart(2, '0');
}

function logToFile(level, msg) {
  try {
    const logDir = resolveLogDir();
    fs.mkdirSync(logDir, { recursive: true });
    const hour = getCurrentHour();
    const logFile = `${hour}.log`;
    const logPath = path.join(logDir, logFile);
    const ts = getTimestamp();
    const line = `${PLUGIN_NAME} [${level}] [${ts}] [session-end.js:0] ${msg}\n`;
    fs.appendFileSync(logPath, line, 'utf-8');

    // 清理旧日志
    for (const f of fs.readdirSync(logDir)) {
      if (f === 'log.log' || f === logFile) continue;
      if (f.endsWith('.log')) {
        try { fs.unlinkSync(path.join(logDir, f)); } catch { /* ignore */ }
      }
    }

    // 更新软连接
    const symlinkPath = path.join(logDir, 'log.log');
    try { fs.unlinkSync(symlinkPath); } catch { /* ignore */ }
    try { fs.symlinkSync(logFile, symlinkPath); } catch { /* ignore */ }
  } catch { /* ignore file logging errors */ }
}

// 记录会话结束事件
logToFile('INFO', `会话结束: ${sessionId}`);
process.stderr.write(`[${PLUGIN_NAME}][INFO] 会话结束: ${sessionId}\n`);
