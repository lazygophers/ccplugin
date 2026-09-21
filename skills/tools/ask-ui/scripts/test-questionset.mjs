// questionset module 的测试：schema 与业务校验的同判、跨字段规则、旧字段拦截。
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

import { normalizeQuestionSet } from './questionset.mjs';
import { validateAgainstSchema, formatSchemaErrors } from './schema-validator.mjs';

const questionSetSchema = JSON.parse(
  await fs.readFile(fileURLToPath(new URL('../references/questionset.schema.json', import.meta.url)), 'utf8'),
);
const exampleQuestionSet = JSON.parse(
  await fs.readFile(fileURLToPath(new URL('../references/example-question-set.json', import.meta.url)), 'utf8'),
);

const runtimeVerdict = (doc) => {
  try {
    normalizeQuestionSet(doc, { cwd: process.cwd() });
    return { valid: true, message: '' };
  } catch (error) {
    return { valid: false, message: error.message };
  }
};

export async function test() {
  const baseQuestion = { id: 'q1', type: 'single', text: '选一个', options: [{ text: '甲' }, { text: '乙' }] };
  const wrap = (...questions) => ({ title: '对齐用例', questions });

  // ---- schema 与业务校验同判 ----
  //
  // schema 是写给人和 Agent 看的 interface，questionset.mjs 的业务校验报的是中文错误。
  // 两边必须说同一件事，否则 Agent 照 schema 写出来的 JSON 会在运行时被拒。
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
    assert.ok(byRuntime.valid, `${name} 通过了 schema 却被业务校验拒收：${byRuntime.message}`);
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
    ['questions 为空', { title: '空', questions: [] }],
  ];

  for (const [name, doc] of rejectedByBoth) {
    assert.ok(!validateAgainstSchema(doc, questionSetSchema).valid, `${name} 应被 schema 拒收`);
    assert.ok(!runtimeVerdict(doc).valid, `${name} 应被业务校验拒收`);
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
    assert.ok(!runtimeVerdict(doc).valid, `${name} 应被业务校验拒收`);
  }

  // ---- 业务校验的错误信息 ----
  // 旧格式必须当场报错，不能静默丢掉推荐徽标或把 label 当成空文本。
  const legacy = runtimeVerdict({
    title: '旧格式必须报错',
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
  });
  assert.ok(!legacy.valid);
  assert.match(legacy.message, /缺少 text/);
  assert.match(legacy.message, /recommendedOptionIds/);

  // type 不再有默认值：漏写必须报错，而不是猜成文本题。
  assert.throws(
    () => normalizeQuestionSet({ title: 't', questions: [{ id: 'q1', text: '没写 type' }] }),
    /必须写明 type/,
  );

  // 选项一律是 JSON 对象，字符串写法不收。
  assert.throws(
    () => normalizeQuestionSet({ title: 't', questions: [{ id: 'q1', type: 'single', text: '甲', options: ['乙', '丙'] }] }),
    /必须是 JSON 对象/,
  );

  // reason 只属于推荐项，写了 reason 却没标 recommended 是写漏了。
  assert.throws(
    () => normalizeQuestionSet({
      title: 't',
      questions: [{
        id: 'q1',
        type: 'single',
        text: '甲',
        options: [{ id: 'a', text: '乙', reason: '因为' }, { id: 'b', text: '丙' }],
      }],
    }),
    /没有 recommended: true/,
  );

  // 条件题：showWhen 只能指向前面的题，匹配方式必须配得上那道题的类型。
  assert.throws(
    () => normalizeQuestionSet({
      title: 't',
      questions: [
        { id: 'q1', type: 'text', text: '甲', showWhen: { questionId: 'q2', optionIds: ['x'] } },
        { id: 'q2', type: 'single', text: '乙', options: [{ id: 'x', text: 'X' }, { id: 'y', text: 'Y' }] },
      ],
    }),
    /只能依赖排在它前面的题/,
  );

  assert.throws(
    () => normalizeQuestionSet({
      title: 't',
      questions: [
        { id: 'q1', type: 'single', text: '甲', options: [{ id: 'x', text: 'X' }, { id: 'y', text: 'Y' }] },
        { id: 'q2', type: 'text', text: '乙', showWhen: { questionId: 'q1', optionIds: ['z'] } },
      ],
    }),
    /不存在的选项：z/,
  );

  assert.throws(
    () => normalizeQuestionSet({
      title: 't',
      questions: [
        { id: 'q1', type: 'single', text: '甲', options: [{ id: 'x', text: 'X' }, { id: 'y', text: 'Y' }] },
        { id: 'q2', type: 'text', text: '乙', showWhen: { questionId: 'q1', answered: true } },
      ],
    }),
    /只能用 optionIds 匹配/,
  );

  assert.throws(
    () => normalizeQuestionSet({
      title: 't',
      questions: [
        { id: 'q1', type: 'text', text: '甲' },
        { id: 'q2', type: 'text', text: '乙', showWhen: { questionId: 'q1', optionIds: ['x'] } },
      ],
    }),
    /只能用 answered \/ contains \/ matches 匹配/,
  );

  assert.throws(
    () => normalizeQuestionSet({
      title: 't',
      questions: [
        { id: 'q1', type: 'text', text: '甲' },
        { id: 'q2', type: 'text', text: '乙', showWhen: { questionId: 'q1', answered: true, contains: ['x'] } },
      ],
    }),
    /必须且只能写一种匹配方式/,
  );

  assert.throws(
    () => normalizeQuestionSet({
      title: 't',
      questions: [
        { id: 'q1', type: 'text', text: '甲' },
        { id: 'q2', type: 'text', text: '乙', showWhen: { questionId: 'q1', matches: '([' } },
      ],
    }),
    /不是合法正则/,
  );

  // 非法 id 必须一次报全：逐个报会让调用方每修一处就重跑一次。
  assert.throws(
    () => normalizeQuestionSet({
      title: '非法 id 一次报全',
      questions: [
        { id: 'q/1', type: 'single', text: '甲', options: [{ id: 'ok-1', text: 'x' }, { id: 'bad opt', text: 'y' }] },
        { id: '..', type: 'single', text: '乙', options: [{ id: 'a/b', text: 'x' }, { id: 'c d', text: 'y' }] },
      ],
    }),
    (error) => {
      const reported = error.message.split('；');
      assert.equal(reported.length, 5, `期望一次报 5 处，实际 ${reported.length}：${error.message}`);
      for (const bad of ['q/1', 'bad opt', '..', 'a/b', 'c d']) {
        assert.ok(error.message.includes(bad), `缺少对 ${bad} 的报错`);
      }
      return true;
    },
  );

  // 轮次与会话的旧字段必须当场报错指路，不能静默吞掉。
  assert.throws(
    () => normalizeQuestionSet({
      sessionId: '../escape',
      roundNumber: 2,
      basedOnRound: 1,
      title: '旧字段必须报错',
      questions: [{ id: 'q1', type: 'text', text: '甲' }],
    }),
    (error) => {
      assert.match(error.message, /sessionId 已移除/);
      assert.match(error.message, /roundNumber 已移除/);
      assert.match(error.message, /basedOnRound 已移除/);
      return true;
    },
  );

  // 改名的 session* 字段同样报错并给出新名。
  assert.throws(
    () => normalizeQuestionSet({
      sessionTitle: '改名字段',
      sessionSummary: 'x',
      sessionBackground: 'y',
      questions: [{ id: 'q1', type: 'text', text: '甲' }],
    }),
    (error) => {
      assert.match(error.message, /sessionTitle 已改名：直接写 title/);
      assert.match(error.message, /sessionSummary 已改名：直接写 summary/);
      assert.match(error.message, /sessionBackground 已改名：直接写 background/);
      return true;
    },
  );
}
