// 运行日志：$TEMP/ask-ui.log，一行一条 JSON（t / pid / event + 字段）。
// 10MB 轮转，最多留 3 个备份（ask-ui.log.1 .. .3）。多进程同时追加是常态
// （前台 ask、常驻 serve、resume 会在同一台机器上并发），appendFile 的原子
// 追加足以保证行不交错；轮转撞车由「写失败就吞掉」兜住——日志永远不许
// 把主流程搞挂，也不记录答案内容。
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';

const MAX_BYTES = 10 * 1024 * 1024;
const BACKUPS = 3;

// 每次调用时解析：$TEMP 优先（Windows 惯例），其次 $TMPDIR（macOS），
// 最后 os.tmpdir() 兜底。测试可以在 import 后改 env 重定向。
export function logPath() {
  const base = process.env.TEMP || process.env.TMPDIR || os.tmpdir();
  return path.join(base, 'ask-ui.log');
}

async function rotate() {
  const file = logPath();
  try {
    const stat = await fs.stat(file);
    if (stat.size < MAX_BYTES) return;
    await fs.rm(`${file}.${BACKUPS}`, { force: true });
    for (let i = BACKUPS - 1; i > 0; i -= 1) {
      await fs.rename(`${file}.${i}`, `${file}.${i + 1}`).catch(() => {});
    }
    await fs.rename(file, `${file}.1`);
  } catch {
    // 没有日志文件，或轮转撞车：什么都不做，接着往当前文件追加。
  }
}

export async function log(event, fields = {}) {
  try {
    await rotate();
    const line = JSON.stringify({ t: new Date().toISOString(), pid: process.pid, event, ...fields });
    await fs.appendFile(logPath(), `${line}\n`, 'utf8');
  } catch {
    // 日志写不进去（目录只读、磁盘满）不是停掉提问的理由。
  }
}
