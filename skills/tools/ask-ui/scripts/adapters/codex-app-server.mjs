import readline from 'node:readline';

import { spawnCli } from './process-utils.mjs';

export async function wakeCodexAppServer({ binding, prompt }) {
  if (!binding?.sessionRef) {
    throw new Error('Codex auto wake requires a host-provided wake.sessionRef');
  }

  const child = spawnCli('codex', ['app-server', '--listen', 'stdio://'], {
    cwd: binding.cwd || process.cwd(),
    env: process.env,
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  const messages = [];
  let stderr = '';
  let settled = false;
  const pending = new Map();
  const rl = readline.createInterface({ input: child.stdout });

  const send = (message) => {
    child.stdin.write(`${JSON.stringify(message)}\n`);
  };

  const request = (id, method, params) =>
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
      let message;
      try {
        message = JSON.parse(line);
      } catch {
        return;
      }
      messages.push(message);

      if (message.id !== undefined && pending.has(message.id)) {
        const waiter = pending.get(message.id);
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

    child.stderr.on('data', (chunk) => {
      if (stderr.length < 1_000_000) stderr += chunk.toString();
    });
    child.on('error', (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.on('close', (code) => {
      if (!settled) {
        clearTimeout(timer);
        reject(new Error(stderr || `Codex App Server exited with code ${code}`));
      }
    });
  });

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

