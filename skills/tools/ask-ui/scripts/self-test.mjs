#!/usr/bin/env node

// 聚合入口：按 module 顺序跑各 test-*.mjs，最后过一遍 CLI 端到端（symlink 调用、
// 直连 ask 全流程、answers.json 契约）与日志轮转。pre-commit 钩子只认这个文件。
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { validateAgainstSchema, formatSchemaErrors } from './schema-validator.mjs';
import { loadAskBundle } from './store.mjs';
import { makeTempRoot, runDirectAsk, stopDetachedServer } from './test-helpers.mjs';

import { test as testQuestionset } from './test-questionset.mjs';
import { test as testAnswers } from './test-answers.mjs';
import { test as testStore } from './test-store.mjs';
import { test as testHttpServer } from './test-http-server.mjs';
import { test as testVendor } from './test-vendor.mjs';
import { test as testWake } from './test-wake.mjs';

const answerSetSchema = JSON.parse(
  await fs.readFile(fileURLToPath(new URL('../references/answerset.schema.json', import.meta.url)), 'utf8'),
);

for (const [name, run] of [
  ['questionset', testQuestionset],
  ['answers', testAnswers],
  ['store', testStore],
  ['http-server', testHttpServer],
  ['vendor', testVendor],
  ['wake', testWake],
]) {
  await run();
  process.stdout.write(`ask-ui ${name} ok\n`);
}

// ---- CLI：经 symlink 调用必须照常执行 ----
//
// skills add 默认以 symlink 安装到 agent 目录，早前的 main 判定拿 argv[1] 字面路径比
// realpath 过的 import.meta.url，导致静默退出 0。
const temporaryRoot = await makeTempRoot('cli');
let directDataRoot;
try {
  const skillLink = path.join(temporaryRoot, 'linked-skill');
  await fs.symlink(path.dirname(path.dirname(fileURLToPath(import.meta.url))), skillLink);
  const linkedHelp = await new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [path.join(skillLink, 'scripts', 'ask-ui.mjs'), '--help'], {
      stdio: ['ignore', 'pipe', 'ignore'],
    });
    let output = '';
    child.stdout.on('data', (chunk) => { output += chunk; });
    child.on('error', reject);
    child.on('close', () => resolve(output));
  });
  assert.match(linkedHelp, /Ask UI/);

  // ---- CLI：直连 ask 全流程（真实进程、真实端口）----
  directDataRoot = path.join(temporaryRoot, 'direct-data');
  const directFirst = await runDirectAsk({
    cwd: temporaryRoot,
    dataRoot: directDataRoot,
    testDuplicate: true,
    questionSet: {
      title: '直接返回链路验证',
      wake: {
        mode: 'auto',
        provider: 'codex-app-server',
        sessionRef: 'must-not-be-called',
      },
      questions: [
        {
          id: 'scope',
          type: 'single',
          text: '范围',
          options: [{ id: 'opt-a', text: 'A', recommended: true, reason: '先做小的。' }, { id: 'opt-b', text: 'B' }],
        },
        {
          id: 'detail',
          type: 'text',
          text: '补充',
          required: false,
        },
      ],
    },
    answers: [
      { questionId: 'scope', selectedOptionIds: ['opt-a'], customText: '' },
      { questionId: 'detail', selectedOptionIds: [], customText: '第一次提问完成' },
    ],
  });
  assert.equal(directFirst.status, 'submitted');

  const directSecond = await runDirectAsk({
    cwd: temporaryRoot,
    dataRoot: directDataRoot,
    questionSet: {
      title: '直接返回链路追问',
      questions: [
        {
          id: 'confirm',
          type: 'single',
          text: '确认结果',
          options: [{ id: 'yes', text: '确认', recommended: true, reason: '默认继续。' }, { id: 'adjust', text: '调整' }],
        },
        {
          id: 'note',
          type: 'text',
          text: '备注',
          required: false,
        },
      ],
    },
    answers: [
      { questionId: 'confirm', selectedOptionIds: ['yes'], customText: '' },
      { questionId: 'note', selectedOptionIds: [], customText: '追问完成' },
    ],
  });
  assert.equal(directSecond.status, 'submitted');
  // 追问是独立的一次 ask，但常驻服务被复用：同一个 origin。
  assert.equal(new URL(directSecond.testReadyUrl).origin, new URL(directFirst.testReadyUrl).origin);
  assert.notEqual(new URL(directSecond.testReadyUrl).pathname, new URL(directFirst.testReadyUrl).pathname);
  const firstBundle = await loadAskBundle(directDataRoot, directFirst.askId);
  assert.equal(firstBundle.ask.status, 'submitted');
  assert.equal(firstBundle.ask.deliveryMode, 'direct');
  assert.equal(firstBundle.ask.wakeState, undefined, 'direct 模式不走唤醒，wakeState 不该出现');

  // 真跑出来的 answers.json 必须符合 references/answerset.schema.json——Agent 是照那份
  // 契约读答案的，落盘结构一旦偏离，读答案的一侧会静默拿错字段。
  for (const bundle of [firstBundle, await loadAskBundle(directDataRoot, directSecond.askId)]) {
    if (!bundle.answers) continue;
    const verdict = validateAgainstSchema(bundle.answers, answerSetSchema);
    assert.ok(verdict.valid, `${bundle.ask.askId} 的 answers.json 不符合 AnswerSet schema：\n${formatSchemaErrors(verdict.errors)}`);
  }

  // ---- 日志轮转 ----
  // $TEMP/ask-ui.log 满 10MB 轮转，备份最多 3 份。TEMP 在 import log.mjs
  // 之前指到临时目录，避免污染真实的 $TEMP。
  {
    process.env.TEMP = path.join(temporaryRoot, 'log-test');
    await fs.mkdir(process.env.TEMP, { recursive: true });
    const { log, logPath } = await import('./log.mjs');
    const overflow = 'x'.repeat(10 * 1024 * 1024 + 1024);
    await fs.appendFile(logPath(), overflow, 'utf8');
    await log('rotation-probe');
    assert.ok(existsSync(`${logPath()}.1`), '满 10MB 应转出 .1 备份');
    assert.match(await fs.readFile(logPath(), 'utf8'), /rotation-probe/, '转档后当前文件应从新行开始');
    for (let round = 2; round <= 4; round += 1) {
      await fs.appendFile(logPath(), overflow, 'utf8');
      await log(`rotation-probe-${round}`);
    }
    assert.ok(existsSync(`${logPath()}.3`), '第三份备份存在');
    assert.ok(!existsSync(`${logPath()}.4`), '第四份备份不该存在');
  }

  process.stdout.write('ask-ui self-test passed\n');
} finally {
  await stopDetachedServer(directDataRoot);
  await fs.rm(temporaryRoot, { recursive: true, force: true });
}
