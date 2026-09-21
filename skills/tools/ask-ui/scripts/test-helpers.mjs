// 各 test-*.mjs 共用的工具：临时目录、直连 ask 的端到端流程、常驻服务的收尾。
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

export const ASK_UI_SCRIPT = fileURLToPath(new URL('./ask-ui.mjs', import.meta.url));

export async function makeTempRoot(label) {
  return fs.mkdtemp(path.join(os.tmpdir(), `ask-ui-${label}-`));
}

// 经 CLI 的直连 ask 全流程：起 ask → 从 stderr 抓 URL → 直接 POST 答案 → 等 CLI 退出。
export async function runDirectAsk({ questionSet, answers, dataRoot, cwd, testDuplicate = false }) {
  const inputFile = path.join(cwd, `direct-${Date.now()}-${Math.random()}.json`);
  await fs.writeFile(inputFile, JSON.stringify(questionSet), 'utf8');
  const child = spawn(
    process.execPath,
    [ASK_UI_SCRIPT, 'ask', '--input', inputFile, '--data-dir', dataRoot, '--no-open'],
    { cwd, stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true },
  );
  let stdout = '';
  let stderr = '';
  child.stdout.setEncoding('utf8');
  child.stderr.setEncoding('utf8');
  child.stdout.on('data', (chunk) => { stdout += chunk; });
  const exitPromise = new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('exit', resolve);
  });

  const readyUrl = await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error(`ask readiness timeout: ${stderr}`)), 8000);
    child.stderr.on('data', (chunk) => {
      stderr += chunk;
      const match = stderr.match(/Ask UI ready at (http:\/\/127\.0\.0\.1:\d+\/\S+)/);
      if (match) {
        clearTimeout(timeout);
        resolve(match[1]);
      }
    });
    child.once('error', (error) => {
      clearTimeout(timeout);
      reject(error);
    });
    child.once('exit', (code) => {
      clearTimeout(timeout);
      reject(new Error(`ask exited before readiness (${code}): ${stderr}`));
    });
  });

  const parsedUrl = new URL(readyUrl);
  const askId = decodeURIComponent(parsedUrl.pathname.split('/').at(-1));
  const token = parsedUrl.searchParams.get('token');
  const bundle = await (await fetch(
    `${parsedUrl.origin}/api/asks/${encodeURIComponent(askId)}`,
    { headers: { Authorization: `Bearer ${token}` } },
  )).json();
  const endpoint = `${parsedUrl.origin}/api/asks/${encodeURIComponent(askId)}/answers`;
  const request = {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ submissionId: `direct-${askId}`, answers }),
  };
  const submitted = await fetch(endpoint, request);
  assert.equal(submitted.status, 200);
  assert.equal((await submitted.json()).duplicate, false);

  const answersPath = path.join(dataRoot, 'asks', askId, 'answers.json');
  assert.ok(JSON.parse(await fs.readFile(answersPath, 'utf8')).submittedAt);

  if (testDuplicate) {
    const duplicate = await fetch(endpoint, request);
    assert.equal(duplicate.status, 200);
    assert.equal((await duplicate.json()).duplicate, true);
  }

  const exitCode = await exitPromise;
  assert.equal(exitCode, 0, stderr);
  return { ...JSON.parse(stdout), testReadyUrl: readyUrl };
}

export async function stopDetachedServer(serverDataRoot) {
  if (!serverDataRoot) return;
  try {
    const info = JSON.parse(await fs.readFile(path.join(serverDataRoot, 'server.json'), 'utf8'));
    if (Number.isInteger(info.pid)) process.kill(info.pid, 'SIGTERM');
    await new Promise((resolve) => setTimeout(resolve, 200));
  } catch (error) {
    if (!['ENOENT', 'ESRCH'].includes(error.code)) throw error;
  }
}

// signal 0 不发信号，只问「这个 pid 还在不在」。
export function serverPidAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}
