// answers module 的测试：validateAnswers 的分支语义（纯函数直测）+ 视图状态与
// conditions.js 的可见集对齐。
import assert from 'node:assert/strict';

import { validateAnswers } from './answers.mjs';
import { normalizeQuestionSet } from './questionset.mjs';
import { visibleQuestionIds } from '../assets/app/conditions.js';
import * as viewState from '../assets/app/view-state.js';

export async function test() {
  const setOf = (questions) => normalizeQuestionSet({ title: '校验用例', questions });

  // 必填多选：一个选项都不选，只写补充说明，也应当通过，且不触发 minSelections。
  {
    const questions = setOf([
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
    ]).questions;
    const supplementOnly = validateAnswers({ questions }, [
      {
        questionId: 'must-pick',
        selectedOptionIds: [],
        customText: '',
        supplementaryText: '三个都不合适，我想要按项目分组。',
      },
    ]);
    assert.deepEqual(supplementOnly.errors, [], '只写补充说明应通过');

    // 但只要选了，数量仍须满足 minSelections。
    const belowMinimum = validateAnswers({ questions }, [
      {
        questionId: 'must-pick',
        selectedOptionIds: ['alpha'],
        customText: '',
        supplementaryText: '只选一个',
      },
    ]);
    assert.ok(belowMinimum.errors.length > 0, '选了 1 个却要求至少 2 个，应报错');
  }

  // 未知选项 / 选择题不收自定义答案 / 文本超长 / 单选多选。
  {
    const questions = setOf([
      {
        id: 'pick',
        type: 'single',
        text: '固定选项',
        options: [
          { id: 'one', text: '选项一' },
          { id: 'two', text: '选项二' },
        ],
      },
      { id: 'note', type: 'text', text: '备注', required: false, maxLength: 10 },
    ]).questions;
    assert.ok(validateAnswers({ questions }, [
      { questionId: 'pick', selectedOptionIds: ['nope'] },
    ]).errors.length > 0, '未知选项应报错');
    assert.ok(validateAnswers({ questions }, [
      { questionId: 'pick', selectedOptionIds: ['one'], customText: '选项之外的答案' },
    ]).errors.length > 0, '选择题不收自定义答案');
    assert.ok(validateAnswers({ questions }, [
      { questionId: 'note', customText: 'x'.repeat(11) },
    ]).errors.length > 0, '文本超长应报错');
    assert.ok(validateAnswers({ questions }, [
      { questionId: 'pick', selectedOptionIds: ['one', 'two'] },
    ]).errors.length > 0, '单选只许选一个');
  }

  // 条件题的提交语义：隐藏题不校验、不进答案集。
  {
    const branching = () => setOf([
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
    ]).questions;

    // 选甲：only-a / a-or-b 可见，丙分支的草稿既不校验也不落盘。
    const branchA = validateAnswers({ questions: branching() }, [
      { questionId: 'entry', selectedOptionIds: ['a'] },
      { questionId: 'only-a', customText: '甲路径的补充' },
      { questionId: 'a-or-b', selectedOptionIds: ['yes'] },
      { questionId: 'only-c', customText: '丙路径的旧草稿' },
    ]);
    assert.deepEqual(branchA.errors, []);
    assert.deepEqual(
      branchA.answers.map((answer) => answer.questionId),
      ['entry', 'only-a', 'a-or-b'],
      '隐藏题不得进答案集',
    );
    assert.deepEqual(branchA.hiddenQuestionIds, ['only-c', 'c-timeout']);

    // 选丁：后面所有条件题都不出现，只答一题也算答完。
    const branchD = validateAnswers({ questions: branching() }, [
      { questionId: 'entry', selectedOptionIds: ['d'] },
    ]);
    assert.deepEqual(
      branchD.answers.map((answer) => answer.questionId),
      ['entry'],
    );

    // 可见的必填题仍然挡提交。
    const missing = validateAnswers({ questions: branching() }, [
      { questionId: 'entry', selectedOptionIds: ['a'] },
      { questionId: 'a-or-b', selectedOptionIds: ['yes'] },
    ]);
    assert.ok(missing.errors.length > 0, '可见的必填追问没答，应报错');

    // 链式：丙的回答里没有关键词，第三层不出现。
    const chain = validateAnswers({ questions: branching() }, [
      { questionId: 'entry', selectedOptionIds: ['c'] },
      { questionId: 'only-c', customText: '一切正常' },
    ]);
    assert.deepEqual(
      chain.answers.map((answer) => answer.questionId),
      ['entry', 'only-c'],
    );

    // 命中关键词后第三层出现，且必填生效。
    const chainFull = validateAnswers({ questions: branching() }, [
      { questionId: 'entry', selectedOptionIds: ['c'] },
      { questionId: 'only-c', customText: '接口超时了' },
    ]);
    assert.ok(chainFull.errors.length > 0, '第三层出现后没答，应报错');
    const chainAnswered = validateAnswers({ questions: branching() }, [
      { questionId: 'entry', selectedOptionIds: ['c'] },
      { questionId: 'only-c', customText: '接口超时了' },
      { questionId: 'c-timeout', customText: '重试两次仍然超时' },
    ]);
    assert.deepEqual(
      chainAnswered.answers.map((answer) => answer.questionId),
      ['entry', 'only-c', 'c-timeout'],
    );
  }

  // ---- 视图状态模块（assets/app/view-state.js）----
  //
  // 页面「第几题该高亮、已答几道、下一道待答题是谁」从 app.js 搬进这个不碰 DOM 的模块，
  // 这里直接喂问题集与答案断言返回值。可见题序列还要和 conditions.js 判定逐条对齐：
  // 两边一旦漂移，用户屏幕上看到的题和服务端校验的题就不是同一批。
  const viewSet = normalizeQuestionSet({
    title: '视图状态用例',
    questions: [
      { id: 'entry', type: 'single', text: '选一个方向', options: [{ text: '迁移' }, { text: '回滚' }] },
      { id: 'background', type: 'text', text: '背景说明' },
      { id: 'window', type: 'text', text: '迁移窗口', showWhen: { questionId: 'entry', optionIds: ['option-1'] } },
      { id: 'plan', type: 'text', text: '迁移方案', showWhen: { questionId: 'window', answered: true } },
      { id: 'owner', type: 'text', text: '负责人' },
      { id: 'rollback', type: 'text', text: '回滚原因', showWhen: { questionId: 'entry', optionIds: ['option-2'] } },
    ],
  });
  const viewForm = { questions: viewSet, answers: null };
  const draft = viewState.answersForForm(viewForm);
  const draftOf = (id) => draft.find((answer) => answer.questionId === id);
  const visibleIdsNow = () => {
    const sequence = viewState.visibleQuestionsOf(viewForm, true, draft).map((question) => question.id);
    assert.deepEqual(
      sequence,
      [...visibleQuestionIds(viewSet.questions, draft)],
      '视图状态模块与 conditions.js 对同一份答案给出的可见题必须一致',
    );
    return sequence;
  };

  const untouched = viewState.visibleQuestionsOf(viewForm, true, draft);
  assert.deepEqual(visibleIdsNow(), ['entry', 'background', 'owner']);

  draftOf('entry').selectedOptionIds = ['option-1'];
  const migrating = viewState.visibleQuestionsOf(viewForm, true, draft);
  assert.deepEqual(visibleIdsNow(), ['entry', 'background', 'window', 'owner']);

  draftOf('window').customText = '周六 02:00-04:00';
  assert.deepEqual(visibleIdsNow(), ['entry', 'background', 'window', 'plan', 'owner']);

  draftOf('entry').selectedOptionIds = ['option-2'];
  assert.deepEqual(visibleIdsNow(), ['entry', 'background', 'owner', 'rollback']);

  // 序号按可见顺序重排：第 3 题「迁移窗口」隐藏后，原第 4 题「负责人」变成第 3 题。
  // 页面上题卡的 .question-number 和左栏序号都靠这个位置算，错一位就全错。
  assert.equal(migrating.findIndex((question) => question.id === 'owner'), 3);
  assert.equal(untouched.findIndex((question) => question.id === 'owner'), 2);

  // 已答计数与「下一道待答题」。跳答（先答后面的题）后仍要指回真正没答的那一道。
  draftOf('entry').selectedOptionIds = ['option-1'];
  draftOf('window').customText = '';
  draftOf('background').customText = '先前遗留';
  draftOf('rollback').customText = '这题此刻不可见，不该计入';
  assert.deepEqual(visibleIdsNow(), ['entry', 'background', 'window', 'owner']);
  assert.equal(viewState.answeredQuestionCount(viewForm, true, draft), 2);
  assert.equal(viewState.firstUnansweredId(viewForm, true, draft), 'window');
  assert.equal(viewState.questionState(viewSet.questions[1], true, null, draft, null), 'done');
  assert.equal(viewState.questionState(viewSet.questions[2], true, null, draft, null), 'todo');
  assert.equal(viewState.questionState(viewSet.questions[2], true, null, draft, 'window'), 'current');

  draftOf('owner').customText = '张三';
  // 从已答的 owner（最后一题）往后找不到，绕回开头才是那道跳过的 window。
  assert.equal(viewState.nextUnansweredIdFrom(viewForm, true, draft, 'owner'), 'window');
  draftOf('window').customText = '周六 02:00-04:00';
  draftOf('plan').customText = '灰度切流';
  assert.deepEqual(visibleIdsNow(), ['entry', 'background', 'window', 'plan', 'owner']);
  assert.equal(viewState.answeredQuestionCount(viewForm, true, draft), 5);
  assert.equal(viewState.firstUnansweredId(viewForm, true, draft), null);
  assert.equal(viewState.nextUnansweredIdFrom(viewForm, true, draft, 'entry'), null);
}
