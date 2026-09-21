#!/usr/bin/env node

// CLI 入口：参数解析与命令分发。业务全在 questionset / answers / store /
// http-server / wake / browser / vendor 这七个 module 里。
import process from 'node:process';
import path from 'node:path';
import { randomBytes } from 'node:crypto';
import { realpathSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

import {
  completeAsk,
  createAsk,
  ensureDataRoot,
  loadAskBundle,
  readAsk,
  readJson,
  resumeAsk,
  submittedAskResult,
} from './store.mjs';
import { ensureServer, startHttpServer, stopIdleServer, watchForIdle } from './http-server.mjs';
import { openBrowser } from './browser.mjs';
import { log } from './log.mjs';

// 太短会在多轮提问之间反复重启服务、换掉用户手上的链接；答完的表单也要能隔天回去翻。
const DEFAULT_IDLE_TIMEOUT_MS = 24 * 60 * 60 * 1000;

function idleTimeoutMs(value) {
  const minutes = Number(value ?? process.env.ASK_UI_IDLE_TIMEOUT_MINUTES);
  if (!Number.isFinite(minutes) || minutes <= 0) return DEFAULT_IDLE_TIMEOUT_MS;
  return minutes * 60 * 1000;
}

function parseArgs(argv) {
  const result = { _: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (!value.startsWith('--')) {
      result._.push(value);
      continue;
    }

    const key = value.slice(2);
    const next = argv[index + 1];
    if (next !== undefined && !next.startsWith('--')) {
      result[key] = next;
      index += 1;
    } else {
      result[key] = true;
    }
  }
  return result;
}

async function waitForSubmission(dataRoot, askId, signal) {
  while (!signal.aborted) {
    const ask = await readAsk(dataRoot, askId);
    if (ask.status === 'submitted') return ask;
    if (ask.status !== 'waiting_for_user') throw new Error(`Ask UI form is ${ask.status}`);
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw signal.reason || new Error('Ask UI wait interrupted');
}

async function readInput(inputFile) {
  if (!inputFile) throw new Error('--input <questions.json> is required');
  if (inputFile !== '-') return readJson(path.resolve(inputFile));
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}

function print(value) {
  process.stdout.write(`${JSON.stringify(value)}\n`);
}

function help() {
  process.stdout.write(`Ask UI\n\n`);
  process.stdout.write(`  ask --input <file> [--data-dir <dir>] [--port <number>] [--no-open]\n`);
  process.stdout.write(`  create --input <file> [--data-dir <dir>] [--no-open] [--no-serve]\n`);
  process.stdout.write(`  serve [--data-dir <dir>] [--port <number>] [--token <token>]\n`);
  process.stdout.write(`  resume [--id <askId>] [--data-dir <dir>]\n`);
  process.stdout.write(`  status --id <askId> [--data-dir <dir>]\n`);
  process.stdout.write(`  complete --id <askId> [--data-dir <dir>]\n`);
  process.stdout.write(`  cancel --id <askId> [--data-dir <dir>]\n`);
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const command = args._[0] || 'help';
  log('cli-start', { command });
  const dataRoot = await ensureDataRoot(args['data-dir']);

  if (command === 'ask') {
    const created = await createAsk(await readInput(args.input), {
      dataDir: dataRoot,
      cwd: process.cwd(),
      deliveryMode: 'direct',
    });
    const server = await ensureServer(dataRoot, { port: Number(args.port) || 0 });
    const url = `http://127.0.0.1:${server.port}/ask/${encodeURIComponent(created.askId)}?token=${encodeURIComponent(server.token)}`;
    const abortController = new AbortController();
    const interrupt = (signal) => abortController.abort(
      new Error(`Ask UI wait interrupted by ${signal}; saved data was preserved`),
    );
    const onSigint = () => { log('ask-interrupted', { askId: created.askId, signal: 'SIGINT' }); interrupt('SIGINT'); };
    const onSigterm = () => { log('ask-interrupted', { askId: created.askId, signal: 'SIGTERM' }); interrupt('SIGTERM'); };
    process.once('SIGINT', onSigint);
    process.once('SIGTERM', onSigterm);
    process.stderr.write(`Ask UI ready at ${url}\n`);
    process.stderr.write(`ask-ui-id: ${created.askId}\n`);
    process.stderr.write(`Waiting for submission; data is saved under ${dataRoot}\n`);
    // 这条命令会阻塞到用户提交为止，很容易被 harness 转到后台。一旦转后台，
    // 任务输出里 stdout 和 stderr 是混在一起的，直接 JSON.parse 必然失败。
    process.stderr.write(`If this command is backgrounded or interrupted, do not parse the task output; run: ask-ui.mjs resume --id ${created.askId}\n`);
    log('ask-created', { askId: created.askId, deliveryMode: 'direct' });
    if (!args['no-open']) openBrowser(url);
    try {
      await waitForSubmission(dataRoot, created.askId, abortController.signal);
      // 转后台时 stdout 会和 stderr 混在一起，这行是「结果已就绪」的唯一可靠信号。
      process.stderr.write(`ask-ui-submitted: ${created.askId}\n`);
      print(await submittedAskResult(dataRoot, created.askId));
    } finally {
      process.removeListener('SIGINT', onSigint);
      process.removeListener('SIGTERM', onSigterm);
    }
    return;
  }

  if (command === 'create') {
    const created = await createAsk(await readInput(args.input), {
      dataDir: dataRoot,
      cwd: process.cwd(),
      deliveryMode: 'manual',
    });
    log('ask-created', { askId: created.askId, deliveryMode: 'manual' });
    if (args['no-serve']) {
      print({ ...created, ask: undefined });
      return;
    }
    const server = await ensureServer(dataRoot);
    const url = `http://127.0.0.1:${server.port}/ask/${encodeURIComponent(created.askId)}?token=${encodeURIComponent(server.token)}`;
    if (!args['no-open']) openBrowser(url);
    print({
      status: 'created',
      askId: created.askId,
      dataRoot,
      questionsPath: created.questionsPath,
      url,
      marker: `ask-ui-id: ${created.askId}`,
    });
    return;
  }

  if (command === 'serve') {
    const started = await startHttpServer({
      dataRoot,
      port: Number(args.port) || 0,
      token: args.token || randomBytes(24).toString('hex'),
      shutdownAfterSubmit: true,
    });
    print(started.info);
    const idleMs = idleTimeoutMs(args['idle-timeout']);
    process.stderr.write(
      `[${new Date().toISOString()}] serve started pid=${process.pid} port=${started.info.port} idleMs=${idleMs}\n`,
    );
    log('serve-start', { port: started.info.port, idleMs });
    for (const signal of ['SIGTERM', 'SIGINT']) {
      process.once(signal, () => {
        process.stderr.write(`[${new Date().toISOString()}] serve exiting: received ${signal}\n`);
        log('serve-exit', { reason: `signal ${signal}` });
        process.exit(0);
      });
    }
    return new Promise((resolve) => {
      watchForIdle(started.server, dataRoot, {
        idleMs,
        onExit: (reason) => {
          process.stderr.write(`[${new Date().toISOString()}] serve exiting: ${reason}\n`);
          log('serve-exit', { reason });
          started.server.close(() => resolve());
          // 已建立的 keep-alive 连接会拖住 close，直接断掉。
          started.server.closeAllConnections?.();
        },
      });
    });
  }

  if (command === 'resume') {
    print(await resumeAsk(dataRoot, args.id || null));
    return;
  }

  if (command === 'status') {
    if (!args.id) throw new Error('--id is required');
    print(await loadAskBundle(dataRoot, args.id));
    return;
  }

  if (command === 'complete' || command === 'cancel') {
    if (!args.id) throw new Error('--id is required');
    const completed = await completeAsk(
      dataRoot,
      args.id,
      command === 'cancel' ? 'cancelled' : 'completed',
    );
    log(command === 'cancel' ? 'ask-cancelled' : 'ask-completed', { askId: args.id });
    // 收尾时顺手关掉常驻服务，不必等它自己 idle 超时。
    print({ ...completed, serverStopped: await stopIdleServer(dataRoot) });
    return;
  }

  help();
}

// argv[1] 是命令行里的字面路径，import.meta.url 是 Node 解析入口后 realpath 过的 URL。
// 经 symlink（skills add 的默认安装方式）或 /tmp 调用时两者不等，必须都归一到真实路径再比。
const isMain = process.argv[1]
  && pathToFileURL(realpathSync(path.resolve(process.argv[1]))).href === import.meta.url;
if (isMain) {
  main().catch((error) => {
    process.stderr.write(`${JSON.stringify({ error: error.message })}\n`);
    log('cli-error', { error: error.message });
    process.exitCode = 1;
  });
}
