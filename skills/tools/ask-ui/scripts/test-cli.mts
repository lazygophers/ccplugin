// CLI 命令面的测试：help / status / complete / cancel / resume / create --no-serve /
// serve 的 idle 收摊，全走真实进程。
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

import { completeAsk, createAsk, submitAnswers } from './store.mjs';
import { ASK_UI_SCRIPT, makeTempRoot } from './test-helpers.mjs';

function runCli(args: string[], options: { cwd?: string; env?: Record<string, string> } = {}) {
  return new Promise<{ code: number | null; stdout: string; stderr: string }>((resolve) => {
    const child = spawn(process.execPath, [ASK_UI_SCRIPT, ...args], {
      cwd: options.cwd,
      env: { ...process.env, ...options.env },
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });
    let stdout = '';
    let stderr = '';
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('close', (code) => resolve({ code, stdout, stderr }));
  });
}

export async function test() {
  const temporaryRoot = await makeTempRoot('cli-commands');
  const dataRoot = path.join(temporaryRoot, 'data');
  try {
    // help：无参数与 --help 都打用法。
    for (const args of [[], ['--help']]) {
      const help = await runCli(args);
      assert.equal(help.code, 0);
      assert.match(help.stdout, /Ask UI/);
    }

    // 未知输入文件：报错退出 1。
    const badInput = await runCli(['ask', '--input', path.join(temporaryRoot, 'nope.json'), '--data-dir', dataRoot, '--no-open']);
    assert.equal(badInput.code, 1);
    assert.match(badInput.stderr, /error/);

    // status：要 --id；查得到时回 bundle。
    const ask = await createAsk({
      title: 'CLI 命令用例',
      questions: [{ id: 'q1', type: 'text', text: '甲' }],
    }, { dataDir: dataRoot, cwd: temporaryRoot });
    const noId = await runCli(['status', '--data-dir', dataRoot]);
    assert.equal(noId.code, 1);
    assert.match(noId.stderr, /--id is required/);
    const status = await runCli(['status', '--id', ask.askId, '--data-dir', dataRoot]);
    assert.equal(status.code, 0);
    assert.equal(JSON.parse(status.stdout).ask.askId, ask.askId);

    // resume：没有已提交的提问时回 waiting；--id 也一样。
    const waiting = await runCli(['resume', '--data-dir', dataRoot]);
    assert.equal(JSON.parse(waiting.stdout).status, 'waiting');
    const waitingById = await runCli(['resume', '--id', ask.askId, '--data-dir', dataRoot]);
    assert.equal(JSON.parse(waitingById.stdout).status, 'waiting');
    const premature = await runCli(['complete', '--id', ask.askId, '--data-dir', dataRoot]);
    assert.equal(premature.code, 1, '未提交时不能读完答案并清理');
    assert.equal(JSON.parse((await runCli(['status', '--id', ask.askId, '--data-dir', dataRoot])).stdout).ask.status, 'waiting_for_user');

    // 提交后 resume 直接带答案；两份已提交且不带 --id 时回 ambiguous。
    await submitAnswers(dataRoot, ask.askId, { answers: [{ questionId: 'q1', customText: '答' }] });
    const resumed = await runCli(['resume', '--data-dir', dataRoot]);
    assert.equal(JSON.parse(resumed.stdout).status, 'submitted');
    assert.equal(JSON.parse(resumed.stdout).answers.answers[0].customText, '答');
    const second = await createAsk({
      title: '第二份',
      questions: [{ id: 'q1', type: 'text', text: '乙' }],
    }, { dataDir: dataRoot, cwd: temporaryRoot });
    await submitAnswers(dataRoot, second.askId, { answers: [{ questionId: 'q1', customText: '乙答' }] });
    const ambiguous = await runCli(['resume', '--data-dir', dataRoot]);
    const parsed = JSON.parse(ambiguous.stdout);
    assert.equal(parsed.status, 'ambiguous');
    assert.equal(parsed.candidates.length, 2);
    // ambiguous 时带 --id 仍然唯一定位。
    const pinned = await runCli(['resume', '--id', ask.askId, '--data-dir', dataRoot]);
    assert.equal(JSON.parse(pinned.stdout).askId, ask.askId);

    // create --no-serve：只落盘不起服务，stdout 带 questionsPath，没有 url。
    const manualFile = path.join(temporaryRoot, 'manual.json');
    await fs.writeFile(manualFile, JSON.stringify({
      title: '手动路径',
      questions: [{ id: 'q1', type: 'text', text: '甲' }],
    }), 'utf8');
    const manual = await runCli(['create', '--input', manualFile, '--data-dir', dataRoot, '--no-serve', '--no-open']);
    assert.equal(manual.code, 0);
    const manualOut = JSON.parse(manual.stdout);
    assert.equal(manualOut.status, 'created');
    assert.equal(manualOut.url, undefined, '--no-serve 不该回 url');

    // stdin 输入：--input - 从管道读。
    const piped = await new Promise<{ code: number | null; stdout: string; stderr: string }>((resolve) => {
      const child = spawn(process.execPath, [ASK_UI_SCRIPT, 'create', '--input', '-', '--data-dir', dataRoot, '--no-serve', '--no-open'], {
        cwd: temporaryRoot, stdio: ['pipe', 'pipe', 'pipe'],
      });
      let stdout = '';
      let stderr = '';
      child.stdout.setEncoding('utf8');
      child.stderr.setEncoding('utf8');
      child.stdout.on('data', (c) => { stdout += c; });
      child.stderr.on('data', (c) => { stderr += c; });
      child.on('close', (code) => resolve({ code, stdout, stderr }));
      child.stdin.end(JSON.stringify({ title: '管道输入', questions: [{ id: 'q1', type: 'text', text: '甲' }] }));
    });
    assert.equal(piped.code, 0);
    assert.equal(JSON.parse(piped.stdout).status, 'created');

    // 缺 --input：报错。
    const noInput = await runCli(['ask', '--data-dir', dataRoot, '--no-open']);
    assert.equal(noInput.code, 1);
    assert.match(noInput.stderr, /--input/);

    // cancel：没人答的表单作废，并顺手停掉常驻服务。
    const cancelTarget = await createAsk({
      title: '作废用例',
      questions: [{ id: 'q1', type: 'text', text: '甲' }],
    }, { dataDir: dataRoot, cwd: temporaryRoot });
    const cancelled = await runCli(['cancel', '--id', cancelTarget.askId, '--data-dir', dataRoot]);
    assert.equal(cancelled.code, 0);
    assert.equal(JSON.parse(cancelled.stdout).status, 'cancelled');
    await assert.rejects(fs.access(path.join(dataRoot, 'asks', cancelTarget.askId)), /ENOENT/);

    // complete：正常收尾。
    const done = await runCli(['complete', '--id', ask.askId, '--data-dir', dataRoot]);
    assert.equal(done.code, 0);
    assert.equal(JSON.parse(done.stdout).status, 'submitted');
    assert.equal(JSON.parse(done.stdout).answers.answers[0].customText, '答');
    await assert.rejects(fs.access(path.join(dataRoot, 'asks', ask.askId)), /ENOENT/);
    assert.equal((await runCli(['resume', '--data-dir', dataRoot])).stdout.includes(ask.askId), false);
    assert.equal(JSON.parse((await runCli(['resume', '--id', second.askId, '--data-dir', dataRoot])).stdout).answers.answers[0].customText, '乙答');
    // 非法终态：store 层报错。
    assert.rejects(() => completeAsk(dataRoot, second.askId, 'bogus' as never), /Invalid final status/);

    // serve：拉起、健康、idle 自动收摊（idle 窗口 0.05 分钟 = 3 秒）。
    const serveRoot = path.join(temporaryRoot, 'serve-data');
    const serve = await new Promise<{ code: number | null; stdout: string; stderr: string; port: number }>((resolve, reject) => {
      const child = spawn(process.execPath, [ASK_UI_SCRIPT, 'serve', '--data-dir', serveRoot],
        { env: { ...process.env, ASK_UI_IDLE_TIMEOUT_MINUTES: '0.05' }, stdio: ['ignore', 'pipe', 'pipe'] });
      let stdout = '';
      let stderr = '';
      child.stdout.setEncoding('utf8');
      child.stderr.setEncoding('utf8');
      child.stdout.on('data', (c) => { stdout += c; });
      child.stderr.on('data', (c) => { stderr += c; });
      const timer = setTimeout(() => reject(new Error(`serve did not exit in time: ${stderr}`)), 15000);
      child.on('close', (code) => {
        clearTimeout(timer);
        try { resolve({ code, stdout, stderr, port: JSON.parse(stdout).port }); }
        catch { resolve({ code, stdout, stderr, port: 0 }); }
      });
    });
    assert.equal(serve.code, 0, `serve 该 idle 退出：${serve.stderr}`);
    assert.ok(serve.port > 0, `serve 启动时 stdout 应带 info JSON：${serve.stdout}`);
    assert.match(serve.stderr, /idle for 0 minutes/);
  } finally {
    await fs.rm(temporaryRoot, { recursive: true, force: true });
  }
}
