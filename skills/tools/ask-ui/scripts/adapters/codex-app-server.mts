import process from 'node:process';
import readline from 'node:readline';
import { spawnCli } from './process-utils.mjs';
import type { WakeRequest } from './claude-code.mjs';

interface JsonRpcMessage {
  id?: number | string;
  method?: string;
  params?: unknown;
  result?: unknown;
  error?: unknown;
  [key: string]: unknown;
}

export async function wakeCodexAppServer({ binding, prompt }: WakeRequest) {
  if (!binding?.sessionRef) {
    throw new Error('Codex auto wake requires a host-provided wake.sessionRef');
  }

  const child = spawnCli('codex', ['app-server', '--listen', 'stdio://'], {
    cwd: binding.cwd || process.cwd(),
    env: process.env,
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  const messages: JsonRpcMessage[] = [];
  let stderr = '';
  let settled = false;
  const pending = new Map<number | string, { resolve: (value: unknown) => void; reject: (reason: unknown) => void }>();
  const rl = readline.createInterface({ input: child.stdout! });

  const send = (message: unknown) => {
    child.stdin!.write(`${JSON.stringify(message)}\n`);
  };

  const request = (id: number | string, method: string, params: unknown) =>
    new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      send({ id, method, params });
    });

  const completion = new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      if (!settled) reject(new Error('Codex App Server wake timed out'));
      child.kill();
    }, 600_000);

    rl.on('line', (line) => {
      let message: JsonRpcMessage;
      try {
        message = JSON.parse(line);
      } catch {
        return;
      }
      messages.push(message);

      if (message.id !== undefined && pending.has(message.id)) {
        const waiter = pending.get(message.id)!;
        pending.delete(message.id);
        if (message.error) waiter.reject(new Error(JSON.stringify(message.error)));
        else waiter.resolve(message.result);
      }

      if (message.method === 'turn/completed') {
        settled = true;
        clearTimeout(timer);
        resolve(message.params);
        child.kill();
      }
    });

    child.stderr!.on('data', (chunk) => {
      if (stderr.length < 1_000_000) stderr += chunk.toString();
    });
    // 子进程早死（握手都没完成）时，挂起的 request 也得跟着失败，否则永远悬空；
    // completion 的 rejection 若无人 await 还会变成 unhandled rejection 崩掉宿主。
    const failPending = (error: Error) => {
      for (const [, waiter] of pending) waiter.reject(error);
      pending.clear();
    };
    child.on('error', (error) => {
      clearTimeout(timer);
      failPending(error);
      reject(error);
    });
    child.on('close', (code) => {
      if (!settled) {
        clearTimeout(timer);
        const error = new Error(stderr || `Codex App Server exited with code ${code}`);
        failPending(error);
        reject(error);
      }
    });
  });

  // completion 在到达 await 前就 reject 时（握手阶段子进程死掉），失败已经由
  // failPending 传导给挂起的 request，这里只防 unhandled rejection。
  completion.catch(() => {});
  await request(1, 'initialize', {
    clientInfo: { name: 'ask-ui', title: 'Ask UI', version: '1.0.0' },
  });
  send({ method: 'initialized', params: {} });
  await request(2, 'thread/resume', { threadId: binding.sessionRef });
  await request(3, 'turn/start', {
    threadId: binding.sessionRef,
    input: [{ type: 'text', text: prompt }],
    cwd: binding.cwd || process.cwd(),
  });
  const completed = await completion;

  return { provider: 'codex-app-server', completed, messages, stderr };
}
