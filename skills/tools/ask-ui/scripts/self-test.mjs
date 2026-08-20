#!/usr/bin/env node

import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  completeSession,
  createRound,
  hasPendingRound,
  loadSessionBundle,
  resumeRound,
  startHttpServer,
} from './ask-ui.mjs';

const ASK_UI_SCRIPT = fileURLToPath(new URL('./ask-ui.mjs', import.meta.url));

async function runDirectAsk({ questionSet, answers, dataRoot, cwd, testDuplicate = false }) {
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
  const sessionId = decodeURIComponent(parsedUrl.pathname.split('/').at(-1));
  const token = parsedUrl.searchParams.get('token');
  const bundle = await (await fetch(
    `${parsedUrl.origin}/api/sessions/${encodeURIComponent(sessionId)}`,
    { headers: { Authorization: `Bearer ${token}` } },
  )).json();
  const roundNumber = bundle.session.currentRound;
  const endpoint = `${parsedUrl.origin}/api/sessions/${encodeURIComponent(sessionId)}/rounds/${roundNumber}/answers`;
  const request = {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ submissionId: `direct-${roundNumber}`, answers }),
  };
  const submitted = await fetch(endpoint, request);
  assert.equal(submitted.status, 200);
  assert.equal((await submitted.json()).duplicate, false);

  const answersPath = path.join(
    dataRoot,
    'sessions',
    sessionId,
    'rounds',
    String(roundNumber).padStart(3, '0'),
    'answers.json',
  );
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

async function stopDetachedServer(serverDataRoot) {
  if (!serverDataRoot) return;
  try {
    const info = JSON.parse(await fs.readFile(path.join(serverDataRoot, 'server.json'), 'utf8'));
    if (Number.isInteger(info.pid)) process.kill(info.pid, 'SIGTERM');
    await new Promise((resolve) => setTimeout(resolve, 200));
  } catch (error) {
    if (!['ENOENT', 'ESRCH'].includes(error.code)) throw error;
  }
}

const temporaryRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'ask-ui-test-'));
const dataRoot = path.join(temporaryRoot, 'data');
let server;
let directDataRoot;

try {
  // 经 symlink 调用时 CLI 必须照常执行。skills add 默认以 symlink 安装到 agent 目录，
  // 早前的 main 判定拿 argv[1] 字面路径比 realpath 过的 import.meta.url，导致静默退出 0。
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

  const first = await createRound({
    sessionTitle: '个人工作台需求确认收集',
    title: '第一轮：目标确认',
    questions: [
      {
        id: 'scope',
        type: 'single',
        title: '优先范围',
        options: [
          { id: 'personal', label: '个人工作台' },
          { id: 'team', label: '团队工作台' },
        ],
        recommendedOptionIds: ['personal'],
      },
      {
        id: 'modules',
        type: 'multiple',
        title: '首批模块',
        options: [
          { id: 'tasks', label: '任务' },
          { id: 'notes', label: '笔记' },
          { id: 'calendar', label: '日历' },
        ],
        recommendedOptionIds: ['tasks', 'notes'],
      },
      {
        id: 'context',
        type: 'text',
        title: '补充背景',
        required: false,
        recommendedDraft: '先做本地 Demo。',
      },
      {
        id: 'channel',
        type: 'single',
        title: '提醒渠道',
        options: [
          { id: 'email', label: '邮件' },
          { id: 'chat', label: '即时消息' },
        ],
      },
    ],
  }, { dataDir: dataRoot, cwd: temporaryRoot });

  const invalidOther = await createRound({
    sessionTitle: '非法选项验证',
    title: '第一轮',
    questions: [
      {
        id: 'restricted',
        type: 'single',
        title: '固定选项',
        options: [
          { id: 'one', label: '选项一' },
          { id: 'two', label: '选项二' },
        ],
      },
    ],
  }, { dataDir: dataRoot, cwd: temporaryRoot });

  const supplementOnly = await createRound({
    sessionTitle: '仅补充说明也算作答',
    title: '第一轮',
    questions: [
      {
        id: 'must-pick',
        type: 'multiple',
        title: '必填多选',
        required: true,
        minSelections: 2,
        options: [
          { id: 'alpha', label: '甲' },
          { id: 'beta', label: '乙' },
          { id: 'gamma', label: '丙' },
        ],
      },
    ],
  }, { dataDir: dataRoot, cwd: temporaryRoot });

  const belowMinimum = await createRound({
    sessionTitle: '选了就要满足下限',
    title: '第一轮',
    questions: [
      {
        id: 'must-pick',
        type: 'multiple',
        title: '必填多选',
        required: true,
        minSelections: 2,
        options: [
          { id: 'alpha', label: '甲' },
          { id: 'beta', label: '乙' },
          { id: 'gamma', label: '丙' },
        ],
      },
    ],
  }, { dataDir: dataRoot, cwd: temporaryRoot });

  const started = await startHttpServer({
    dataRoot,
    token: 'self-test-token',
    persistServerInfo: false,
  });
  server = started.server;
  const base = `http://127.0.0.1:${started.info.port}`;
  const headers = {
    Authorization: 'Bearer self-test-token',
    'Content-Type': 'application/json',
  };

  // 常驻服务必须有终点：还有人没答完就继续跑，最后一个会话结束就收摊。
  {
    const idleRoot = path.join(temporaryRoot, 'idle-data');
    const first = await createRound({
      sessionTitle: '甲会话',
      title: '第一轮',
      questions: [{ id: 'q1', type: 'text', title: '甲' }],
    }, { dataDir: idleRoot, cwd: temporaryRoot });
    const second = await createRound({
      sessionTitle: '乙会话',
      title: '第一轮',
      questions: [{ id: 'q1', type: 'text', title: '乙' }],
    }, { dataDir: idleRoot, cwd: temporaryRoot });

    assert.equal(await hasPendingRound(idleRoot), true, '两个会话都在等答，应判定为有人未答');

    await completeSession(idleRoot, first.sessionId, 'completed');
    assert.equal(await hasPendingRound(idleRoot), true, '乙会话还在等，服务不该收摊');

    await completeSession(idleRoot, second.sessionId, 'completed');
    assert.equal(await hasPendingRound(idleRoot), false, '会话都结束了，服务该收摊');
  }

  // q1、mr 这类短 id 只是 JSON 内部的引用键，不进文件路径，必须放行。
  const shortIds = await createRound({
    sessionTitle: '短 id 合法',
    title: '第一轮',
    questions: [
      {
        id: 'q1',
        type: 'single',
        title: '交付到哪一步',
        required: true,
        options: [{ id: 'mr', label: '开 MR' }, { id: 'commit', label: '只 commit' }],
      },
    ],
  }, { dataDir: dataRoot, cwd: temporaryRoot });
  assert.equal(shortIds.roundNumber, 1);

  // 非法 id 必须一次报全：逐个报会让调用方每修一处就重跑一次。
  await assert.rejects(
    () => createRound({
      sessionTitle: '非法 id 一次报全',
      title: '第一轮',
      questions: [
        { id: 'q/1', type: 'single', title: '甲', options: [{ id: 'ok-1', label: 'x' }, { id: 'bad opt', label: 'y' }] },
        { id: '..', type: 'single', title: '乙', options: [{ id: 'a/b', label: 'x' }, { id: 'c d', label: 'y' }] },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    (error) => {
      const reported = error.message.split('；');
      assert.equal(reported.length, 5, `期望一次报 5 处，实际 ${reported.length}：${error.message}`);
      for (const bad of ['q/1', 'bad opt', '..', 'a/b', 'c d']) {
        assert.ok(error.message.includes(bad), `缺少对 ${bad} 的报错`);
      }
      return true;
    },
  );

  // sessionId 会拼进文件路径，路径穿越必须继续挡住。
  await assert.rejects(
    () => createRound({
      sessionId: '../escape',
      sessionTitle: '路径穿越',
      title: '第一轮',
      questions: [{ id: 'q1', type: 'text', title: '甲' }],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    /sessionId must contain 3-128 safe characters/,
  );

  // 图表组件命中缓存时必须直接回文件，绝不联网：这是离线可用的前提。
  const vendorDir = path.join(temporaryRoot, 'vendor');
  await fs.mkdir(vendorDir, { recursive: true });
  await fs.writeFile(path.join(vendorDir, 'mermaid-11.16.1.min.js'), 'globalThis.mermaid = "cached";');
  process.env.ASK_UI_VENDOR_DIR = vendorDir;
  const mermaidResponse = await fetch(`${base}/vendor/mermaid.min.js`);
  assert.equal(mermaidResponse.status, 200);
  assert.equal(mermaidResponse.headers.get('content-type'), 'text/javascript; charset=utf-8');
  assert.equal(await mermaidResponse.text(), 'globalThis.mermaid = "cached";');
  delete process.env.ASK_UI_VENDOR_DIR;

  // 必填多选：一个选项都不选，只写补充说明，也应当通过，且不触发 minSelections。
  const supplementOnlyResponse = await fetch(
    `${base}/api/sessions/${supplementOnly.sessionId}/rounds/1/answers`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({
        answers: [
          {
            questionId: 'must-pick',
            selectedOptionIds: [],
            customText: '',
            supplementaryText: '三个都不合适，我想要按项目分组。',
          },
        ],
      }),
    },
  );
  assert.equal(supplementOnlyResponse.status, 200);

  // 但只要选了，数量仍须满足 minSelections。
  const belowMinimumResponse = await fetch(
    `${base}/api/sessions/${belowMinimum.sessionId}/rounds/1/answers`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({
        submissionId: 'below-minimum',
        answers: [
          {
            questionId: 'must-pick',
            selectedOptionIds: ['alpha'],
            customText: '',
            supplementaryText: '只选一个',
          },
        ],
      }),
    },
  );
  assert.equal(belowMinimumResponse.status, 422);

  const bundleResponse = await fetch(`${base}/api/sessions/${first.sessionId}`, { headers });
  assert.equal(bundleResponse.status, 200);
  const bundle = await bundleResponse.json();
  assert.equal(bundle.rounds.length, 1);
  assert.equal(bundle.rounds[0].questions.questions.length, 4);

  const rejectedOtherResponse = await fetch(
    `${base}/api/sessions/${invalidOther.sessionId}/rounds/1/answers`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({
        answers: [
          {
            questionId: 'restricted',
            selectedOptionIds: ['nope'],
            customText: '',
          },
        ],
      }),
    },
  );
  assert.equal(rejectedOtherResponse.status, 422);

  const rejectedCustomTextResponse = await fetch(
    `${base}/api/sessions/${invalidOther.sessionId}/rounds/1/answers`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({
        answers: [
          {
            questionId: 'restricted',
            selectedOptionIds: ['one'],
            customText: '选项之外的答案',
          },
        ],
      }),
    },
  );
  assert.equal(rejectedCustomTextResponse.status, 422);

  const rejectedSupplementResponse = await fetch(
    `${base}/api/sessions/${invalidOther.sessionId}/rounds/1/answers`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({
        answers: [
          {
            questionId: 'restricted',
            selectedOptionIds: ['one'],
            customText: '',
            supplementaryText: 'x'.repeat(2001),
          },
        ],
      }),
    },
  );
  assert.equal(rejectedSupplementResponse.status, 422);

  const answers = [
    {
      questionId: 'scope',
      selectedOptionIds: ['personal'],
      customText: '',
      supplementaryText: '先覆盖个人高频场景。',
    },
    { questionId: 'modules', selectedOptionIds: ['tasks', 'notes'], customText: '' },
    { questionId: 'context', selectedOptionIds: [], customText: '先做本地 Demo。' },
    { questionId: 'channel', selectedOptionIds: ['email'], customText: '', supplementaryText: '工作日才提醒。' },
  ];
  // 草稿自动保存已移除：答案只在用户点提交时落盘，draft 端点必须不复存在。
  const draftResponse = await fetch(
    `${base}/api/sessions/${first.sessionId}/rounds/1/draft`,
    { method: 'POST', headers, body: JSON.stringify({ answers }) },
  );
  assert.equal(draftResponse.status, 404);

  const submitResponse = await fetch(
    `${base}/api/sessions/${first.sessionId}/rounds/1/answers`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({ submissionId: 'self-test-submit', answers }),
    },
  );
  assert.equal(submitResponse.status, 200);
  assert.equal((await submitResponse.json()).duplicate, false);

  const resumed = await resumeRound(dataRoot, first.sessionId);
  assert.equal(resumed.status, 'submitted');
  assert.equal(resumed.roundNumber, 1);
  assert.equal(resumed.answers.answers[0].supplementaryText, '先覆盖个人高频场景。');

  await createRound({
    sessionId: first.sessionId,
    sessionTitle: '个人工作台需求确认收集',
    title: '第二轮：细节确认',
    basedOnRound: 1,
    questions: [
      {
        id: 'layout',
        type: 'single',
        title: '布局方式',
        options: [
          { id: 'tabs', label: 'Tab 切换' },
          { id: 'board', label: '看板' },
        ],
        recommendedOptionIds: ['tabs'],
      },
    ],
  }, { dataDir: dataRoot, cwd: temporaryRoot });

  const afterSecondRound = await loadSessionBundle(dataRoot, first.sessionId);
  assert.equal(afterSecondRound.rounds[0].status, 'processed');
  assert.equal(afterSecondRound.rounds[1].status, 'waiting_for_user');

  const completed = await completeSession(dataRoot, first.sessionId);
  assert.equal(completed.status, 'completed');

  directDataRoot = path.join(temporaryRoot, 'direct-data');
  const directFirst = await runDirectAsk({
    cwd: temporaryRoot,
    dataRoot: directDataRoot,
    testDuplicate: true,
    questionSet: {
      sessionTitle: '直接返回链路验证',
      title: '第一轮',
      wake: {
        mode: 'auto',
        provider: 'codex-app-server',
        sessionRef: 'must-not-be-called',
      },
      questions: [
        {
          id: 'scope',
          type: 'single',
          title: '范围',
          options: [{ id: 'opt-a', label: 'A' }, { id: 'opt-b', label: 'B' }],
          recommendedOptionIds: ['opt-a'],
        },
        {
          id: 'detail',
          type: 'text',
          title: '补充',
          required: false,
        },
      ],
    },
    answers: [
      { questionId: 'scope', selectedOptionIds: ['opt-a'], customText: '' },
      { questionId: 'detail', selectedOptionIds: [], customText: '第一轮完成' },
    ],
  });
  assert.equal(directFirst.status, 'submitted');
  assert.equal(directFirst.roundNumber, 1);

  const directSecond = await runDirectAsk({
    cwd: temporaryRoot,
    dataRoot: directDataRoot,
    questionSet: {
      sessionId: directFirst.sessionId,
      sessionTitle: '直接返回链路验证',
      title: '第二轮',
      basedOnRound: 1,
      questions: [
        {
          id: 'confirm',
          type: 'single',
          title: '确认结果',
          options: [{ id: 'yes', label: '确认' }, { id: 'adjust', label: '调整' }],
          recommendedOptionIds: ['yes'],
        },
        {
          id: 'note',
          type: 'text',
          title: '备注',
          required: false,
        },
      ],
    },
    answers: [
      { questionId: 'confirm', selectedOptionIds: ['yes'], customText: '' },
      { questionId: 'note', selectedOptionIds: [], customText: '第二轮完成' },
    ],
  });
  assert.equal(directSecond.roundNumber, 2);
  assert.equal(directSecond.testReadyUrl, directFirst.testReadyUrl);
  const directBundle = await loadSessionBundle(directDataRoot, directFirst.sessionId);
  assert.equal(directBundle.rounds[0].status, 'processed');
  assert.equal(directBundle.rounds[0].deliveryMode, 'direct');
  assert.equal(directBundle.rounds[1].status, 'submitted');
  assert.equal(directBundle.session.wakeState, undefined);
  process.stdout.write('ask-ui self-test passed\n');
} finally {
  if (server) await new Promise((resolve) => server.close(resolve));
  await stopDetachedServer(directDataRoot);
  await fs.rm(temporaryRoot, { recursive: true, force: true });
}
