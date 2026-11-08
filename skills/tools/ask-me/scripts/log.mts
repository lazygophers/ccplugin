// 运行日志：posix 固定 /tmp/ask-me.log（win32 退回 os.tmpdir()），一行一条 JSON
// （t / pid / event + 字段）。只留最近 3 小时：写日志时节流清理旧行。多进程同时
// 追加是常态（前台 ask、常驻 serve、resume 会在同一台机器上并发），appendFile 的
// 原子追加足以保证行不交错；清理撞车只可能丢旧行，失败一律吞掉——日志永远不许
// 把主流程搞挂，也不记录答案内容。
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';

export const RETENTION_MS = 3 * 60 * 60 * 1000;
const PRUNE_EVERY_MS = 5 * 60 * 1000;
let lastPrune = 0;

// 每次调用时解析。$ASK_ME_LOG 只给测试重定向用（posix 路径固定后 TEMP 不再生效）。
export function logPath(): string {
  if (process.env.ASK_ME_LOG) return process.env.ASK_ME_LOG;
  return path.join(process.platform === 'win32' ? os.tmpdir() : '/tmp', 'ask-me.log');
}

// 日志按时间顺序追加，首行最老：首行没过期就整个跳过，不读全文件。
// shortcut: 读完到 rename 之间别的进程追加的行会丢，窗口毫秒级，rename 前复核大小压缩窗口；要零丢失得加文件锁。
export async function prune(now = Date.now()): Promise<void> {
  const file = logPath();
  try {
    const text = await fs.readFile(file, 'utf8');
    const cutoff = now - RETENTION_MS;
    const lines = text.split('\n').filter(Boolean);
    const fresh = lines.filter((line) => {
      try { return Date.parse(JSON.parse(line).t) >= cutoff; } catch { return false; }
    });
    if (fresh.length === lines.length) return;
    const size = (await fs.stat(file)).size;
    if (size !== Buffer.byteLength(text)) return; // 读完又有人追加：本轮放弃，下轮再清
    const temporary = `${file}.${process.pid}.tmp`;
    await fs.writeFile(temporary, fresh.map((line) => `${line}\n`).join(''), 'utf8');
    await fs.rename(temporary, file);
  } catch {
    // 没有日志文件，或清理撞车：什么都不做。
  }
}

export async function log(event: string, fields: Record<string, unknown> = {}): Promise<void> {
  try {
    if (Date.now() - lastPrune > PRUNE_EVERY_MS) {
      lastPrune = Date.now();
      await prune();
    }
    const line = JSON.stringify({ t: new Date().toISOString(), pid: process.pid, event, ...fields });
    await fs.appendFile(logPath(), `${line}\n`, 'utf8');
  } catch {
    // 日志写不进去（目录只读、磁盘满）不是停掉提问的理由。
  }
}

// 错误统一记成 event=error：where 标出处，message / stack 供事后修复。
export function logError(where: string, error: unknown): Promise<void> {
  const e = error instanceof Error ? error : new Error(String(error));
  return log('error', { where, message: e.message, stack: e.stack });
}
