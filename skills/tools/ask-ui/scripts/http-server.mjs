// HTTP module：seam 只做三件事——鉴权、按路径分发、错误出口。提交后的生命周期
// （回调、唤醒、收摊）全部经 afterSubmitted 一个出口驱动，不散落在路由分支里。
import {
  closeSync,
  createReadStream,
  existsSync,
  openSync,
  statSync,
} from 'node:fs';
import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import process from 'node:process';
import { randomBytes } from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

import {
  assertSafeId,
  hasPendingAsk,
  loadAskBundle,
  readAsk,
  readJson,
  saveDraft,
  submitAnswers,
} from './store.mjs';
import { closeBrowserTab, openInBrowser } from './browser.mjs';
import { ensureVendor, VENDOR } from './vendor.mjs';
import { triggerWake } from './wake.mjs';
import { log } from './log.mjs';

const SCRIPT_FILE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), 'ask-ui.mjs');
const SKILL_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const APP_ROOT = path.join(SKILL_ROOT, 'assets', 'app');
const MAX_BODY_BYTES = 1_048_576;

// 提交后等这么久再关页、关进程：留一眼看「已提交」那张卡的时间。
const SUBMIT_TEARDOWN_MS = Number(process.env.ASK_UI_CLOSE_DELAY_MS) || 3000;

// 交给默认浏览器打开的白名单。兜底路径上的 `open` 会执行 `.app` / `.sh` / `.command`，
// 所以这里只放行文档和图片——正文里的链接不该有本事启动程序。
const OPENABLE = /\.(html?|md|markdown|txt|log|json|ya?ml|csv|pdf|png|jpe?g|gif|webp|svg)$/i;

function contentType(file) {
  if (file.endsWith('.html')) return 'text/html; charset=utf-8';
  if (file.endsWith('.js')) return 'text/javascript; charset=utf-8';
  if (file.endsWith('.css')) return 'text/css; charset=utf-8';
  return 'application/octet-stream';
}

function addSecurityHeaders(response) {
  response.setHeader('X-Content-Type-Options', 'nosniff');
  response.setHeader('X-Frame-Options', 'DENY');
  response.setHeader('Referrer-Policy', 'no-referrer');
  response.setHeader(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self' https://cdn.bootcdn.net 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'",
  );
}

function sendJson(response, statusCode, value) {
  addSecurityHeaders(response);
  response.writeHead(statusCode, { 'Content-Type': 'application/json; charset=utf-8' });
  response.end(`${JSON.stringify(value)}\n`);
}

function sendFile(response, file) {
  const stream = createReadStream(file);
  // 读文件的错误是异步从流里冒出来的，路由里的 try/catch 接不住。不挂这个监听，
  // 一个权限不对的组件文件就会让整个服务连同全部活跃会话一起退出。
  stream.on('error', (error) => {
    if (response.headersSent) {
      response.destroy();
      return;
    }
    sendJson(response, 500, { error: error.message });
  });
  // 头留到确认打得开文件之后再发，否则失败时已经发出去 200，改不回错误状态码。
  stream.on('open', () => {
    addSecurityHeaders(response);
    response.writeHead(200, { 'Content-Type': contentType(file) });
    stream.pipe(response);
  });
}

async function readRequestJson(request) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > MAX_BODY_BYTES) {
      const error = new Error('Request body is too large');
      error.statusCode = 413;
      throw error;
    }
    chunks.push(chunk);
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}');
  } catch {
    const error = new Error('Request body must be valid JSON');
    error.statusCode = 400;
    throw error;
  }
}

// 正文里的本地文件链接点下去走这里：交给默认浏览器开新标签页，地址栏里看到的
// 就是真的 file:// 地址。不能让页面自己跳——Chrome 禁止 http:// 页面导航到
// file://，`window.open('file://…')` 直接返回 null，点了静默失败。
// 鉴权在路由层：服务只绑 127.0.0.1，能拿到 token 的就是本机用户自己。
async function openLocalFile(response, requestUrl, dataRoot) {
  const requested = requestUrl.searchParams.get('path') || '';
  const hash = requestUrl.searchParams.get('hash') || '';
  if (!requested) {
    sendJson(response, 400, { error: 'path is required' });
    return;
  }
  // 相对路径按工作区解析：dataRoot 是 <workspace>/.ask-ui。
  const target = path.resolve(path.dirname(dataRoot), requested.replace(/^file:\/\//, ''));
  if (!existsSync(target)) {
    sendJson(response, 404, { error: `文件不存在：${target}` });
    return;
  }
  if (!OPENABLE.test(target)) {
    sendJson(response, 403, { error: `只放行文档和图片，不给开这种文件：${path.basename(target)}` });
    return;
  }
  const url = `${pathToFileURL(target).href}${hash}`;
  if (!process.env.ASK_UI_OPENER && await openInBrowser(url)) {
    sendJson(response, 200, { opened: target });
    return;
  }
  // Windows 的 start 是 cmd 内建、不是可执行文件，必须由 cmd 转一手；它后面那个
  // 空字符串是窗口标题，省掉的话带引号的路径会被当成标题，文件反而不开。
  const [opener, openerArgs] = process.env.ASK_UI_OPENER
    ? [process.env.ASK_UI_OPENER, []]
    : {
      darwin: ['open', []],
      win32: ['cmd', ['/c', 'start', '']],
    }[process.platform] || ['xdg-open', []];
  // Windows 的 start 和 Linux 的 xdg-open 把 file:// URL 整条转交给默认处理器，
  // `#锚点` 留得住；macOS 只有上面那条 AppleScript 路留得住，这里是它的兜底。
  spawn(opener, [...openerArgs, url], {
    detached: true,
    stdio: 'ignore',
    windowsHide: true,
  }).unref();
  sendJson(response, 200, { opened: target });
}

async function handleAskApi(response, requestUrl, request, dataRoot, lifecycle) {
  const apiMatch = requestUrl.pathname.match(
    /^\/api\/asks\/([^/]+)(?:\/(answers|status|draft))?$/,
  );
  if (!apiMatch) {
    sendJson(response, 404, { error: 'Not found' });
    return;
  }
  const askId = assertSafeId(decodeURIComponent(apiMatch[1]), 'askId');
  const operation = apiMatch[2] || null;

  if (request.method === 'GET' && operation === 'status') {
    const ask = await readAsk(dataRoot, askId);
    sendJson(response, 200, { ask });
    return;
  }
  if (request.method === 'GET' && operation === null) {
    sendJson(response, 200, await loadAskBundle(dataRoot, askId));
    return;
  }
  // PUT 是正常路径；关标签页那一下只能靠 sendBeacon，而它只发 POST。
  if ((request.method === 'PUT' || request.method === 'POST') && operation === 'draft') {
    sendJson(response, 200, await saveDraft(dataRoot, askId, await readRequestJson(request)));
    return;
  }
  if (request.method === 'POST' && operation === 'answers') {
    const result = await submitAnswers(
      dataRoot,
      askId,
      await readRequestJson(request),
    );
    sendJson(response, 200, result);
    if (!result.duplicate) afterSubmitted({ askId, result, ...lifecycle });
    return;
  }
  sendJson(response, 405, { error: 'Method not allowed' });
}

// 提交后的全部副作用集中在这一个出口：日志、调用方回调、唤醒、收摊。
// wake 与 teardown 由同一个生命周期点驱动，路由层只管转发。
function afterSubmitted({ askId, result, dataRoot, server, onSubmitted, enableWake, shutdownAfterSubmit, persistServerInfo }) {
  log('ask-submitted', { askId });
  if (onSubmitted) {
    setTimeout(() => {
      try {
        onSubmitted({ askId, result });
      } catch {
        // Submission is already durable; observer failures must not alter it.
      }
    }, 0);
  }
  if (enableWake && result.ask.deliveryMode !== 'direct') {
    setTimeout(() => {
      triggerWake(dataRoot, askId).catch(() => {});
    }, 0);
  }
  // 答完就收摊：关掉那一页，没有别的提问还等着人答就连进程一起退。
  // 手动路径除外——它没有等待方，收摊会把「回会话说已提交」的指引一起掐死。
  if (shutdownAfterSubmit && result.ask.deliveryMode === 'direct') {
    setTimeout(() => {
      teardownAfterSubmit({ server, dataRoot, askId, persistServerInfo });
    }, SUBMIT_TEARDOWN_MS);
  }
}

// 答完收摊：关浏览器页、清 server.json、按条件退出进程。
async function teardownAfterSubmit({ server, dataRoot, askId, persistServerInfo }) {
  await closeBrowserTab(askId).catch(() => false);
  if (await hasPendingAsk(dataRoot)) return;
  process.stderr.write(`[${new Date().toISOString()}] serve exiting: ${askId} submitted\n`);
  if (persistServerInfo) {
    await fs.rm(path.join(dataRoot, 'server.json'), { force: true });
  }
  server.close(() => process.exit(0));
  // keep-alive 连接会拖住 close，直接断掉；再兜一层超时，绝不留下僵尸进程。
  server.closeAllConnections?.();
  setTimeout(() => process.exit(0), 1000).unref();
}

export async function startHttpServer({
  dataRoot,
  token = randomBytes(24).toString('hex'),
  port = 0,
  persistServerInfo = true,
  enableWake = true,
  onSubmitted = null,
  shutdownAfterSubmit = false,
} = {}) {
  if (!dataRoot) throw new Error('dataRoot is required');
  await fs.mkdir(dataRoot, { recursive: true });

  const server = http.createServer(async (request, response) => {
    const requestUrl = new URL(request.url, 'http://127.0.0.1');
    if (request.method === 'GET' && requestUrl.pathname === '/app.js') {
      sendFile(response, path.join(APP_ROOT, 'app.js'));
      return;
    }
    if (request.method === 'GET' && requestUrl.pathname === '/conditions.js') {
      sendFile(response, path.join(APP_ROOT, 'conditions.js'));
      return;
    }
    if (request.method === 'GET' && requestUrl.pathname === '/view-state.js') {
      sendFile(response, path.join(APP_ROOT, 'view-state.js'));
      return;
    }
    if (request.method === 'GET' && requestUrl.pathname === '/fallback.css') {
      sendFile(response, path.join(APP_ROOT, 'fallback.css'));
      return;
    }
    const vendorMatch = requestUrl.pathname.match(/^\/vendor\/([a-z]+)\.min\.js$/);
    if (request.method === 'GET' && vendorMatch && VENDOR[vendorMatch[1]]) {
      // 只在页面真的用到该组件时才被请求，下载成本不会落到用不上的轮次上。
      try {
        sendFile(response, await ensureVendor(vendorMatch[1]));
      } catch (error) {
        sendJson(response, 502, { error: error.message });
      }
      return;
    }

    const bearer = request.headers.authorization?.replace(/^Bearer\s+/i, '');
    const suppliedToken = bearer || requestUrl.searchParams.get('token');

    if (suppliedToken !== token) {
      sendJson(response, 401, { error: 'Unauthorized' });
      return;
    }

    try {
      if (request.method === 'GET' && requestUrl.pathname === '/local') {
        await openLocalFile(response, requestUrl, dataRoot);
        return;
      }
      if (requestUrl.pathname === '/health') {
        sendJson(response, 200, { ok: true, pid: process.pid });
        return;
      }
      if (
        request.method === 'GET'
        && (requestUrl.pathname === '/' || requestUrl.pathname.startsWith('/ask/'))
      ) {
        sendFile(response, path.join(APP_ROOT, 'index.html'));
        return;
      }
      await handleAskApi(response, requestUrl, request, dataRoot, {
        dataRoot,
        server,
        onSubmitted,
        enableWake,
        shutdownAfterSubmit,
        persistServerInfo,
      });
    } catch (error) {
      sendJson(response, error.statusCode || 500, { error: error.message });
    }
  });

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(Number(port) || 0, '127.0.0.1', resolve);
  });
  const address = server.address();
  const info = {
    pid: process.pid,
    host: '127.0.0.1',
    port: address.port,
    token,
    dataRoot,
    startedAt: new Date().toISOString(),
    codeVersion: codeVersion(),
  };
  if (persistServerInfo) await fs.writeFile(
    path.join(dataRoot, 'server.json'),
    `${JSON.stringify(info)}\n`,
    'utf8',
  );
  return { server, info };
}

export function watchForIdle(server, dataRoot, { idleMs, onExit }) {
  let lastRequestAt = Date.now();
  server.on('request', () => { lastRequestAt = Date.now(); });

  const timer = setInterval(async () => {
    // 数据目录被删掉，服务再挂着也没有意义——测试和临时会话都是这样留下垃圾进程的。
    if (!existsSync(dataRoot)) {
      onExit('data directory is gone');
      return;
    }
    if (Date.now() - lastRequestAt < idleMs) return;
    if (await hasPendingAsk(dataRoot)) return;
    onExit(`idle for ${Math.round(idleMs / 60000)} minutes with no unanswered form`);
  }, Math.min(idleMs, 30_000));
  timer.unref();
  return timer;
}

// 只在没有任何一次提问还等着人回答时才停，且只按 server.json 里记的 pid 精确停。
export async function stopIdleServer(dataRoot) {
  if (await hasPendingAsk(dataRoot)) return false;
  const info = await readJson(path.join(dataRoot, 'server.json'), null);
  if (!info?.pid || !await serverIsAlive(info)) return false;
  process.kill(info.pid, 'SIGTERM');
  await fs.rm(path.join(dataRoot, 'server.json'), { force: true });
  return true;
}

async function serverIsAlive(info) {
  if (!info?.port || !info?.token) return false;
  try {
    const response = await fetch(
      `http://127.0.0.1:${info.port}/health?token=${encodeURIComponent(info.token)}`,
      { signal: AbortSignal.timeout(800) },
    );
    return response.ok;
  } catch {
    return false;
  }
}

// 常驻服务把代码读进内存就不再看磁盘了，所以改完 skill 必须换掉旧进程，
// 否则页面拿的是新前端、服务端还是旧逻辑，新加的路由一律 404。
function codeVersion() {
  return statSync(SCRIPT_FILE).mtimeMs;
}

export async function ensureServer(dataRoot, { port = 0 } = {}) {
  const serverFile = path.join(dataRoot, 'server.json');
  const existing = await readJson(serverFile, null);
  const alive = await serverIsAlive(existing);
  if (alive && existing.codeVersion === codeVersion()) return existing;
  // 旧进程照样得换：页面是每次从磁盘现读的新前端，配上内存里的旧服务端，新加的
  // 路由一律 404（本地文件链接就是这么点不开的）。有人正在答题也照换，只是端口和
  // token 原样留着——答案本来就在磁盘上，那一页几秒后重新轮询就接上了。
  let reuse = null;
  if (alive) {
    if (await hasPendingAsk(dataRoot)) {
      reuse = { port: existing.port, token: existing.token };
      process.stderr.write(
        `ask-ui: 服务跑的是旧代码（pid ${existing.pid}），换成新代码，端口 ${existing.port} 和链接不变。\n`,
      );
      log('server-restarted', { oldPid: existing.pid, port: existing.port });
    }
    process.kill(existing.pid);
    await fs.rm(serverFile, { force: true });
  }

  const token = reuse?.token || randomBytes(24).toString('hex');
  if (reuse?.port) port = reuse.port;
  await fs.mkdir(dataRoot, { recursive: true });
  // stdio 全丢弃时，服务为什么退出就永远查不到了：退出原因和崩溃栈都走 stderr。
  const logFd = openSync(path.join(dataRoot, 'server.log'), 'a');
  const child = spawn(
    process.execPath,
    [SCRIPT_FILE, 'serve', '--data-dir', dataRoot, '--port', String(Number(port) || 0), '--token', token],
    { detached: true, stdio: ['ignore', logFd, logFd], windowsHide: true },
  );
  closeSync(logFd);
  child.unref();

  const deadline = Date.now() + 8000;
  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    const info = await readJson(serverFile, null);
    if (info?.token === token && await serverIsAlive(info)) return info;
  }
  throw new Error('Ask UI server did not start');
}
