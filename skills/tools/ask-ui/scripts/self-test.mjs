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
  normalizeQuestionSet,
  resumeRound,
  startHttpServer,
} from './ask-ui.mjs';
import { formatSchemaErrors, validateAgainstSchema } from './schema-validator.mjs';
import { visibleQuestionIds } from '../assets/app/conditions.js';
import * as viewState from '../assets/app/view-state.js';

const ASK_UI_SCRIPT = fileURLToPath(new URL('./ask-ui.mjs', import.meta.url));

const questionSetSchema = JSON.parse(
  await fs.readFile(fileURLToPath(new URL('../references/questionset.schema.json', import.meta.url)), 'utf8'),
);
const answerSetSchema = JSON.parse(
  await fs.readFile(fileURLToPath(new URL('../references/answerset.schema.json', import.meta.url)), 'utf8'),
);

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

  // ---- references/*.schema.json 与手写校验的对齐 ----
  //
  // schema 是写给人和 Agent 看的 DSL 定义，运行时把关的仍是 ask-ui.mjs 里的中文校验。
  // 两边必须说同一件事，否则 Agent 照 schema 写出来的 JSON 会在运行时被拒。断言的
  // 关系有两条：schema 判合法的必须能通过 normalizeQuestionSet（schema ⊆ 校验器），
  // 且下面列出的每种典型错误两边都要拒。
  const runtimeVerdict = (doc) => {
    try {
      normalizeQuestionSet(doc, { cwd: temporaryRoot });
      return { valid: true, message: '' };
    } catch (error) {
      return { valid: false, message: error.message };
    }
  };

  const exampleQuestionSet = JSON.parse(
    await fs.readFile(fileURLToPath(new URL('../references/example-question-set.json', import.meta.url)), 'utf8'),
  );
  const baseQuestion = { id: 'q1', type: 'single', text: '选一个', options: [{ text: '甲' }, { text: '乙' }] };
  const wrap = (...questions) => ({ sessionTitle: '对齐用例', questions });

  const schemaValidCases = [
    ['references 里的起手模板', exampleQuestionSet],
    ['三种题型齐全', wrap(
      baseQuestion,
      { id: 'q2', type: 'multiple', text: '选多个', minSelections: 1, maxSelections: 2, options: [{ text: '甲', recommended: true, reason: '默认项' }, { text: '乙' }] },
      { id: 'q3', type: 'text', text: '补充', required: false, multiline: true, maxLength: 200 },
    )],
    ['四种 showWhen 匹配方式', wrap(
      baseQuestion,
      { id: 'q2', type: 'text', text: '细节', showWhen: { questionId: 'q1', optionIds: ['option-1'] } },
      { id: 'q3', type: 'text', text: '再问', showWhen: { questionId: 'q2', answered: true } },
      { id: 'q4', type: 'text', text: '关键词', showWhen: { questionId: 'q2', contains: ['超时'] } },
      { id: 'q5', type: 'text', text: '正则', showWhen: { questionId: 'q2', matches: '^ERR-\\d+$' } },
    )],
  ];

  for (const [name, doc] of schemaValidCases) {
    const bySchema = validateAgainstSchema(doc, questionSetSchema);
    assert.ok(bySchema.valid, `${name} 应通过 schema：\n${formatSchemaErrors(bySchema.errors)}`);
    const byRuntime = runtimeVerdict(doc);
    assert.ok(byRuntime.valid, `${name} 通过了 schema 却被运行时校验拒收：${byRuntime.message}`);
  }

  // 两边都必须拒的典型写错。左边是 schema 能表达的结构错误。
  const rejectedByBoth = [
    ['漏写 type', wrap({ id: 'q1', text: '选一个', options: [{ text: '甲' }, { text: '乙' }] })],
    ['选项写成字符串', wrap({ id: 'q1', type: 'single', text: '选一个', options: ['甲', '乙'] })],
    ['选择题只有一个选项', wrap({ id: 'q1', type: 'single', text: '选一个', options: [{ text: '甲' }] })],
    ['reason 没配 recommended', wrap({ id: 'q1', type: 'single', text: '选一个', options: [{ text: '甲', reason: '就它' }, { text: '乙' }] })],
    ['text 为空', wrap({ id: 'q1', type: 'single', text: '', options: [{ text: '甲' }, { text: '乙' }] })],
    ['题级 recommendedOptionIds', wrap({ ...baseQuestion, recommendedOptionIds: ['option-1'] })],
    ['showWhen 同时写两种匹配', wrap(
      baseQuestion,
      { id: 'q2', type: 'text', text: '细节', showWhen: { questionId: 'q1', optionIds: ['option-1'], answered: true } },
    )],
    ['questions 为空', { sessionTitle: '空', questions: [] }],
  ];

  for (const [name, doc] of rejectedByBoth) {
    assert.ok(!validateAgainstSchema(doc, questionSetSchema).valid, `${name} 应被 schema 拒收`);
    assert.ok(!runtimeVerdict(doc).valid, `${name} 应被运行时校验拒收`);
  }

  // 跨字段规则 JSON Schema 表达不了，schema.md 里已写明由运行时把关。这里钉住这个分工：
  // 一旦哪天 schema 也能拦，说明分工变了，得回去更新文档。
  const runtimeOnly = [
    ['showWhen 指向排在后面的题', wrap(
      { id: 'q1', type: 'text', text: '先问', showWhen: { questionId: 'q2', optionIds: ['option-1'] } },
      { id: 'q2', type: 'single', text: '选一个', options: [{ text: '甲' }, { text: '乙' }] },
    )],
    ['showWhen 引用不存在的选项', wrap(
      baseQuestion,
      { id: 'q2', type: 'text', text: '细节', showWhen: { questionId: 'q1', optionIds: ['option-9'] } },
    )],
    ['文本题却用 optionIds 匹配', wrap(
      { id: 'q1', type: 'text', text: '先问' },
      { id: 'q2', type: 'text', text: '细节', showWhen: { questionId: 'q1', optionIds: ['option-1'] } },
    )],
  ];

  for (const [name, doc] of runtimeOnly) {
    assert.ok(validateAgainstSchema(doc, questionSetSchema).valid, `${name} 属跨字段规则，schema 不该拦`);
    assert.ok(!runtimeVerdict(doc).valid, `${name} 应被运行时校验拒收`);
  }

  // ---- 视图状态模块（assets/app/view-state.js）----
  //
  // 页面「第几题该高亮、已答几道、下一道待答题是谁」从 app.js 搬进这个不碰 DOM 的模块，
  // 这里直接喂问题集与答案断言返回值。可见题序列还要和 conditions.js 判定逐条对齐：
  // 两边一旦漂移，用户屏幕上看到的题和服务端校验的题就不是同一批。
  const viewSet = normalizeQuestionSet({
    sessionTitle: '视图状态用例',
    questions: [
      { id: 'entry', type: 'single', text: '选一个方向', options: [{ text: '迁移' }, { text: '回滚' }] },
      { id: 'background', type: 'text', text: '背景说明' },
      { id: 'window', type: 'text', text: '迁移窗口', showWhen: { questionId: 'entry', optionIds: ['option-1'] } },
      { id: 'plan', type: 'text', text: '迁移方案', showWhen: { questionId: 'window', answered: true } },
      { id: 'owner', type: 'text', text: '负责人' },
      { id: 'rollback', type: 'text', text: '回滚原因', showWhen: { questionId: 'entry', optionIds: ['option-2'] } },
    ],
  }, { cwd: temporaryRoot });
  const viewRound = { roundNumber: 1, questions: viewSet, answers: null };
  const draft = viewState.answersForRound(viewRound);
  const draftOf = (id) => draft.find((answer) => answer.questionId === id);
  const visibleIdsNow = () => {
    const sequence = viewState.visibleQuestionsOf(viewRound, true, draft).map((question) => question.id);
    assert.deepEqual(
      sequence,
      [...visibleQuestionIds(viewSet.questions, draft)],
      '视图状态模块与 conditions.js 对同一份答案给出的可见题必须一致',
    );
    return sequence;
  };

  const untouched = viewState.visibleQuestionsOf(viewRound, true, draft);
  assert.deepEqual(visibleIdsNow(), ['entry', 'background', 'owner']);

  draftOf('entry').selectedOptionIds = ['option-1'];
  const migrating = viewState.visibleQuestionsOf(viewRound, true, draft);
  assert.deepEqual(visibleIdsNow(), ['entry', 'background', 'window', 'owner']);

  draftOf('window').customText = '周六 02:00-04:00';
  const withPlan = viewState.visibleQuestionsOf(viewRound, true, draft);
  assert.deepEqual(visibleIdsNow(), ['entry', 'background', 'window', 'plan', 'owner']);

  draftOf('entry').selectedOptionIds = ['option-2'];
  const rollingBack = viewState.visibleQuestionsOf(viewRound, true, draft);
  assert.deepEqual(visibleIdsNow(), ['entry', 'background', 'owner', 'rollback']);

  // 新增多题：序号按变化后的可见顺序算。
  const grown = viewState.visibilityDiff(untouched, withPlan);
  assert.deepEqual(grown.added, [
    { id: 'window', title: '迁移窗口', position: 3 },
    { id: 'plan', title: '迁移方案', position: 4 },
  ]);
  assert.deepEqual(grown.removed, []);
  assert.equal(viewState.visibilityAnnouncement(grown), '新增 2 题：第 3 题 迁移窗口、第 4 题 迁移方案');

  // 新增一题。
  const oneMore = viewState.visibilityDiff(untouched, rollingBack);
  assert.deepEqual(oneMore.added, [{ id: 'rollback', title: '回滚原因', position: 4 }]);
  assert.equal(viewState.visibilityAnnouncement(oneMore), '新增第 4 题：回滚原因');

  // 隐藏一题，且序号重排：第 3 题 window 隐藏后，原第 4 题 owner 变成第 3 题。
  const shrunk = viewState.visibilityDiff(migrating, untouched);
  assert.deepEqual(shrunk.added, []);
  assert.deepEqual(shrunk.removed, [{ id: 'window', title: '迁移窗口', previousPosition: 3 }]);
  assert.equal(migrating.findIndex((question) => question.id === 'owner'), 3);
  assert.equal(untouched.findIndex((question) => question.id === 'owner'), 2);
  assert.equal(viewState.visibilityAnnouncement(shrunk), '隐藏第 3 题：迁移窗口');

  // 同时增删：切分支时一批题换成另一批。
  const swapped = viewState.visibilityDiff(withPlan, rollingBack);
  assert.deepEqual(swapped.added, [{ id: 'rollback', title: '回滚原因', position: 4 }]);
  assert.deepEqual(swapped.removed.map((item) => item.id), ['window', 'plan']);
  assert.equal(
    viewState.visibilityAnnouncement(swapped),
    '新增第 4 题：回滚原因；隐藏 2 题：迁移窗口、迁移方案',
  );
  assert.equal(viewState.visibilityAnnouncement(viewState.visibilityDiff(withPlan, withPlan)), '');

  // 页面手里只留着上一次的可见性签名，播报的「变化前」序列是从签名还原出来的：
  // 还原结果必须和当初那份可见题序列逐个对得上，否则序号会算错、还会平白多播报几题。
  const allQuestions = viewRound.questions.questions;
  const signatureOf = (visible) => visible.map((question) => question.id).join('|');
  assert.deepEqual(
    viewState.questionsFromSignature(allQuestions, signatureOf(withPlan)),
    withPlan,
  );
  assert.deepEqual(viewState.questionsFromSignature(allQuestions, ''), []);
  // 轮次切换后拿旧签名来问，认不出的 id 直接丢掉，不凭空造题。
  assert.deepEqual(
    viewState.questionsFromSignature(allQuestions, 'entry|gone-in-this-round'),
    [allQuestions.find((question) => question.id === 'entry')],
  );
  assert.equal(
    viewState.visibilityAnnouncement(viewState.visibilityDiff(
      viewState.questionsFromSignature(allQuestions, signatureOf(migrating)),
      untouched,
    )),
    '隐藏第 3 题：迁移窗口',
  );

  // 已答计数与「下一道待答题」。跳答（先答后面的题）后仍要指回真正没答的那一道。
  draftOf('entry').selectedOptionIds = ['option-1'];
  draftOf('window').customText = '';
  draftOf('background').customText = '上一轮遗留';
  draftOf('rollback').customText = '这题此刻不可见，不该计入';
  assert.deepEqual(visibleIdsNow(), ['entry', 'background', 'window', 'owner']);
  assert.equal(viewState.answeredQuestionCount(viewRound, true, draft), 2);
  assert.equal(viewState.firstUnansweredId(viewRound, true, draft), 'window');
  assert.equal(viewState.questionState(viewSet.questions[1], true, null, draft, null), 'done');
  assert.equal(viewState.questionState(viewSet.questions[2], true, null, draft, null), 'todo');
  assert.equal(viewState.questionState(viewSet.questions[2], true, null, draft, 'window'), 'current');

  draftOf('owner').customText = '张三';
  // 从已答的 owner（最后一题）往后找不到，绕回开头才是那道跳过的 window。
  assert.equal(viewState.nextUnansweredIdFrom(viewRound, true, draft, 'owner'), 'window');
  draftOf('window').customText = '周六 02:00-04:00';
  draftOf('plan').customText = '灰度切流';
  assert.deepEqual(visibleIdsNow(), ['entry', 'background', 'window', 'plan', 'owner']);
  assert.equal(viewState.answeredQuestionCount(viewRound, true, draft), 5);
  assert.equal(viewState.firstUnansweredId(viewRound, true, draft), null);
  assert.equal(viewState.nextUnansweredIdFrom(viewRound, true, draft, 'entry'), null);

  const first = await createRound({
    sessionTitle: '个人工作台需求确认收集',
    title: '第一轮：目标确认',
    questions: [
      {
        id: 'scope',
        type: 'single',
        title: '优先范围',
        text: '## 优先范围\n\n先做**个人**还是**团队**？',
        options: [
          { id: 'personal', text: '个人工作台', recommended: true, reason: '先覆盖高频场景。' },
          { id: 'team', text: '团队工作台' },
        ],
      },
      {
        id: 'modules',
        type: 'multiple',
        text: '首批模块',
        options: [
          { id: 'tasks', text: '任务', recommended: true, reason: '主入口。' },
          { id: 'notes', text: '笔记', recommended: true, reason: '沉淀上下文。' },
          { id: 'calendar', text: '日历' },
        ],
      },
      {
        id: 'context',
        type: 'text',
        text: '补充背景',
        required: false,
        recommendedDraft: '先做本地 Demo。',
      },
      {
        id: 'channel',
        type: 'single',
        text: '提醒渠道',
        options: [
          { id: 'email', text: '邮件' },
          { id: 'chat', text: '即时消息' },
        ],
      },
    ],
  }, { dataDir: dataRoot, cwd: temporaryRoot });

  // title 缺省时取正文首个非空行，左栏导航才有短标签可用。
  {
    const storedFirst = await loadSessionBundle(dataRoot, first.sessionId);
    const stored = storedFirst.rounds[0].questions.questions;
    assert.equal(stored[0].title, '优先范围', '显式 title 必须原样保留');
    assert.equal(stored[1].title, '首批模块', 'title 缺省应取 text 首个非空行');
    // 单选最多一个推荐项：两个「推荐」徽标会让用户不知道照哪个。
    assert.equal(stored[0].options.filter((option) => option.recommended).length, 1);
    assert.equal(stored[1].options.filter((option) => option.recommended).length, 2);
  }

  const invalidOther = await createRound({
    sessionTitle: '非法选项验证',
    title: '第一轮',
    questions: [
      {
        id: 'restricted',
        type: 'single',
        text: '固定选项',
        options: [
          { id: 'one', text: '选项一' },
          { id: 'two', text: '选项二' },
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
        text: '必填多选',
        required: true,
        minSelections: 2,
        options: [
          { id: 'alpha', text: '甲' },
          { id: 'beta', text: '乙' },
          { id: 'gamma', text: '丙' },
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
        text: '必填多选',
        required: true,
        minSelections: 2,
        options: [
          { id: 'alpha', text: '甲' },
          { id: 'beta', text: '乙' },
          { id: 'gamma', text: '丙' },
        ],
      },
    ],
  }, { dataDir: dataRoot, cwd: temporaryRoot });

  // 旧格式必须当场报错，不能静默丢掉推荐徽标或把 label 当成空文本。
  await assert.rejects(
    () => createRound({
      sessionTitle: '旧格式必须报错',
      title: '第一轮',
      questions: [
        {
          id: 'legacy',
          type: 'single',
          title: '旧写法',
          description: '旧的题级描述',
          options: [{ id: 'a', label: '甲' }, { id: 'b', label: '乙' }],
          recommendedOptionIds: ['a'],
        },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    (error) => {
      assert.match(error.message, /缺少 text/);
      assert.match(error.message, /recommendedOptionIds/);
      return true;
    },
  );

  // type 不再有默认值：漏写必须报错，而不是猜成文本题。
  await assert.rejects(
    () => createRound({
      sessionTitle: 'type 必填',
      title: '第一轮',
      questions: [{ id: 'q1', text: '没写 type' }],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    /必须写明 type/,
  );

  // 选项一律是 JSON 对象，字符串写法不收。
  await assert.rejects(
    () => createRound({
      sessionTitle: '选项必须是对象',
      title: '第一轮',
      questions: [{ id: 'q1', type: 'single', text: '甲', options: ['乙', '丙'] }],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    /必须是 JSON 对象/,
  );

  // reason 只属于推荐项，写了 reason 却没标 recommended 是写漏了。
  await assert.rejects(
    () => createRound({
      sessionTitle: 'reason 依赖 recommended',
      title: '第一轮',
      questions: [{
        id: 'q1',
        type: 'single',
        text: '甲',
        options: [{ id: 'a', text: '乙', reason: '因为' }, { id: 'b', text: '丙' }],
      }],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    /没有 recommended: true/,
  );

  // 条件题：showWhen 只能指向前面的题，匹配方式必须配得上那道题的类型。
  const branchingQuestions = () => [
    {
      id: 'entry',
      type: 'single',
      text: '入口选择',
      options: [
        { id: 'a', text: '甲' },
        { id: 'b', text: '乙' },
        { id: 'c', text: '丙' },
        { id: 'd', text: '丁' },
      ],
    },
    { id: 'only-a', type: 'text', text: '仅甲追问', showWhen: { questionId: 'entry', optionIds: ['a'] } },
    {
      id: 'a-or-b',
      type: 'single',
      text: '甲乙共有追问',
      showWhen: { questionId: 'entry', optionIds: ['a', 'b'] },
      options: [{ id: 'yes', text: '是' }, { id: 'no', text: '否' }],
    },
    { id: 'only-c', type: 'text', text: '仅丙追问', showWhen: { questionId: 'entry', optionIds: ['c'] } },
    {
      id: 'c-timeout',
      type: 'text',
      text: '丙提到超时才追问',
      showWhen: { questionId: 'only-c', contains: ['超时', 'timeout'] },
    },
  ];
  const createBranching = (sessionTitle) => createRound({
    sessionTitle,
    title: '第一轮',
    questions: branchingQuestions(),
  }, { dataDir: dataRoot, cwd: temporaryRoot });

  const branchA = await createBranching('分支甲');
  const branchD = await createBranching('分支丁');
  const branchMissing = await createBranching('分支必填未答');
  const branchChain = await createBranching('分支链式');
  const branchChainFull = await createBranching('分支链式补全');

  {
    const stored = (await loadSessionBundle(dataRoot, branchA.sessionId)).rounds[0].questions.questions;
    assert.deepEqual(stored[1].showWhen, { questionId: 'entry', optionIds: ['a'] });
    assert.equal(stored[0].showWhen, null, '没写 showWhen 的题必须显式落成 null');
    assert.deepEqual(stored[4].showWhen, { questionId: 'only-c', contains: ['超时', 'timeout'] });
  }

  // 只能依赖排在前面的题：顺序即依赖序，环在这里就被挡住。
  await assert.rejects(
    () => createRound({
      sessionTitle: '条件不能向后引用',
      title: '第一轮',
      questions: [
        { id: 'q1', type: 'text', text: '甲', showWhen: { questionId: 'q2', optionIds: ['x'] } },
        { id: 'q2', type: 'single', text: '乙', options: [{ id: 'x', text: 'X' }, { id: 'y', text: 'Y' }] },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    /只能依赖排在它前面的题/,
  );

  await assert.rejects(
    () => createRound({
      sessionTitle: '条件引用不存在的选项',
      title: '第一轮',
      questions: [
        { id: 'q1', type: 'single', text: '甲', options: [{ id: 'x', text: 'X' }, { id: 'y', text: 'Y' }] },
        { id: 'q2', type: 'text', text: '乙', showWhen: { questionId: 'q1', optionIds: ['z'] } },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    /不存在的选项：z/,
  );

  await assert.rejects(
    () => createRound({
      sessionTitle: '选择题只能用 optionIds',
      title: '第一轮',
      questions: [
        { id: 'q1', type: 'single', text: '甲', options: [{ id: 'x', text: 'X' }, { id: 'y', text: 'Y' }] },
        { id: 'q2', type: 'text', text: '乙', showWhen: { questionId: 'q1', answered: true } },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    /只能用 optionIds 匹配/,
  );

  await assert.rejects(
    () => createRound({
      sessionTitle: '文本题不能用 optionIds',
      title: '第一轮',
      questions: [
        { id: 'q1', type: 'text', text: '甲' },
        { id: 'q2', type: 'text', text: '乙', showWhen: { questionId: 'q1', optionIds: ['x'] } },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    /只能用 answered \/ contains \/ matches 匹配/,
  );

  await assert.rejects(
    () => createRound({
      sessionTitle: '匹配方式只能写一种',
      title: '第一轮',
      questions: [
        { id: 'q1', type: 'text', text: '甲' },
        { id: 'q2', type: 'text', text: '乙', showWhen: { questionId: 'q1', answered: true, contains: ['x'] } },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    /必须且只能写一种匹配方式/,
  );

  await assert.rejects(
    () => createRound({
      sessionTitle: '正则必须能编译',
      title: '第一轮',
      questions: [
        { id: 'q1', type: 'text', text: '甲' },
        { id: 'q2', type: 'text', text: '乙', showWhen: { questionId: 'q1', matches: '([' } },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    /不是合法正则/,
  );

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
      questions: [{ id: 'q1', type: 'text', text: '甲' }],
    }, { dataDir: idleRoot, cwd: temporaryRoot });
    const second = await createRound({
      sessionTitle: '乙会话',
      title: '第一轮',
      questions: [{ id: 'q1', type: 'text', text: '乙' }],
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
        text: '交付到哪一步',
        required: true,
        options: [{ id: 'mr', text: '开 MR' }, { id: 'commit', text: '只 commit' }],
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
        { id: 'q/1', type: 'single', text: '甲', options: [{ id: 'ok-1', text: 'x' }, { id: 'bad opt', text: 'y' }] },
        { id: '..', type: 'single', text: '乙', options: [{ id: 'a/b', text: 'x' }, { id: 'c d', text: 'y' }] },
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
      questions: [{ id: 'q1', type: 'text', text: '甲' }],
    }, { dataDir: dataRoot, cwd: temporaryRoot }),
    /sessionId must contain 3-128 safe characters/,
  );

  // 渲染组件命中缓存时必须直接回文件，绝不联网：这是离线可用的前提。
  const vendorDir = path.join(temporaryRoot, 'vendor');
  await fs.mkdir(vendorDir, { recursive: true });
  const cachedVendors = {
    mermaid: 'mermaid-11.16.1.min.js',
    marked: 'marked-15.0.7.min.js',
    purify: 'purify-3.2.4.min.js',
    highlight: 'highlight-11.11.1.min.js',
  };
  for (const [name, file] of Object.entries(cachedVendors)) {
    await fs.writeFile(path.join(vendorDir, file), `globalThis.${name} = "cached";`);
  }
  process.env.ASK_UI_VENDOR_DIR = vendorDir;
  for (const name of Object.keys(cachedVendors)) {
    const vendorResponse = await fetch(`${base}/vendor/${name}.min.js`);
    assert.equal(vendorResponse.status, 200, `${name} 应命中缓存`);
    assert.equal(vendorResponse.headers.get('content-type'), 'text/javascript; charset=utf-8');
    assert.equal(await vendorResponse.text(), `globalThis.${name} = "cached";`);
  }
  // 未登记的组件名不得变成任意文件读取。
  assert.equal((await fetch(`${base}/vendor/unknown.min.js`)).status, 401);
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

  // 条件题的提交语义：隐藏题不校验、不落盘，可见题该必填还是必填。
  {
    const submitBranch = (sessionId, answers) => fetch(
      `${base}/api/sessions/${sessionId}/rounds/1/answers`,
      { method: 'POST', headers, body: JSON.stringify({ answers }) },
    );
    const readAnswers = async (sessionId) => (
      await loadSessionBundle(dataRoot, sessionId)
    ).rounds[0].answers;

    assert.equal((await submitBranch(branchA.sessionId, [
      { questionId: 'entry', selectedOptionIds: ['a'] },
      { questionId: 'only-a', customText: '甲路径的补充' },
      { questionId: 'a-or-b', selectedOptionIds: ['yes'] },
      // 用户选甲之前在丙分支留下的草稿：屏幕上已经不存在，不该进答案集。
      { questionId: 'only-c', customText: '丙路径的旧草稿' },
    ])).status, 200);
    const branchAAnswers = await readAnswers(branchA.sessionId);
    assert.deepEqual(
      branchAAnswers.answers.map((answer) => answer.questionId),
      ['entry', 'only-a', 'a-or-b'],
      '隐藏题不得进答案集',
    );
    assert.deepEqual(branchAAnswers.hiddenQuestionIds, ['only-c', 'c-timeout']);

    // 选丁：后面所有条件题都不出现，只答一题也能提交。
    assert.equal((await submitBranch(branchD.sessionId, [
      { questionId: 'entry', selectedOptionIds: ['d'] },
    ])).status, 200);
    assert.deepEqual(
      (await readAnswers(branchD.sessionId)).answers.map((answer) => answer.questionId),
      ['entry'],
    );

    // 可见的必填题仍然挡提交。
    assert.equal((await submitBranch(branchMissing.sessionId, [
      { questionId: 'entry', selectedOptionIds: ['a'] },
      { questionId: 'a-or-b', selectedOptionIds: ['yes'] },
    ])).status, 422);

    // 链式：丙的回答里没有关键词，第三层不出现。
    assert.equal((await submitBranch(branchChain.sessionId, [
      { questionId: 'entry', selectedOptionIds: ['c'] },
      { questionId: 'only-c', customText: '一切正常' },
    ])).status, 200);
    assert.deepEqual(
      (await readAnswers(branchChain.sessionId)).answers.map((answer) => answer.questionId),
      ['entry', 'only-c'],
    );

    // 命中关键词后第三层出现，且必填生效。
    assert.equal((await submitBranch(branchChainFull.sessionId, [
      { questionId: 'entry', selectedOptionIds: ['c'] },
      { questionId: 'only-c', customText: '接口超时了' },
    ])).status, 422);
    assert.equal((await submitBranch(branchChainFull.sessionId, [
      { questionId: 'entry', selectedOptionIds: ['c'] },
      { questionId: 'only-c', customText: '接口超时了' },
      { questionId: 'c-timeout', customText: '重试两次仍然超时' },
    ])).status, 200);
    assert.deepEqual(
      (await readAnswers(branchChainFull.sessionId)).answers.map((answer) => answer.questionId),
      ['entry', 'only-c', 'c-timeout'],
    );
  }

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
        text: '布局方式',
        options: [
          { id: 'tabs', text: 'Tab 切换', recommended: true, reason: '切换成本最低。' },
          { id: 'board', text: '看板' },
        ],
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

  // 真跑出来的 answers.json 必须符合 references/answerset.schema.json——Agent 是照那份
  // 契约读答案的，落盘结构一旦偏离，读答案的一侧会静默拿错字段。
  for (const round of directBundle.rounds) {
    if (!round.answers) continue;
    const verdict = validateAgainstSchema(round.answers, answerSetSchema);
    assert.ok(verdict.valid, `第 ${round.roundNumber} 轮的 answers.json 不符合 AnswerSet schema：\n${formatSchemaErrors(verdict.errors)}`);
  }

  process.stdout.write('ask-ui self-test passed\n');
} finally {
  if (server) await new Promise((resolve) => server.close(resolve));
  await stopDetachedServer(directDataRoot);
  await fs.rm(temporaryRoot, { recursive: true, force: true });
}
