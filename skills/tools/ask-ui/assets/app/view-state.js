// 答题页的状态推导：可见题序列、每题状态、已答计数、下一道待答题。
// 和 conditions.js 一样只有这一份实现，不碰 document —— app.js 只负责把这里返回的
// 纯数据映射到 DOM，Node 直接 import 就能测，页面「第几题该高亮」不再是一段没有测试的逻辑。
//
// 这里的函数一律不改传进来的数组：草稿（pendingAnswers）由 app.js 独占持有，
// 推导过程顺手往里塞一条空答案，会让提交上去的 answers.json 多出用户没碰过的题。

import { visibleQuestionIds } from './conditions.js';

// 推荐值只做视觉提示，绝不预填答案：只有用户点过、选过、输入过才算已答。
export function defaultAnswer(question) {
  return {
    questionId: question.id,
    selectedOptionIds: [],
    customText: '',
    supplementaryText: '',
  };
}

export function normalizeAnswer(answer) {
  const normalized = structuredClone(answer);
  normalized.selectedOptionIds ||= [];
  normalized.customText ||= '';
  normalized.supplementaryText ||= '';
  return normalized;
}

export function answersForRound(round) {
  const source = round.answers?.answers || round.questions.questions.map(defaultAnswer);
  const byId = new Map(source.map((answer) => [answer.questionId, answer]));
  return round.questions.questions.map((question) => normalizeAnswer(
    byId.get(question.id) || defaultAnswer(question),
  ));
}

// 条件题：正在编辑时按手里这份草稿算可见性，只读轮次按已提交的答案算。
function answersInPlay(round, editable, pendingAnswers) {
  return editable ? (pendingAnswers || []) : (round.answers?.answers || []);
}

export function visibleQuestionsOf(round, editable, pendingAnswers) {
  const questions = round.questions.questions;
  const visible = visibleQuestionIds(questions, answersInPlay(round, editable, pendingAnswers));
  return questions.filter((question) => visible.has(question.id));
}

export function visibilitySignature(round, editable, pendingAnswers) {
  return visibleQuestionsOf(round, editable, pendingAnswers).map((question) => question.id).join('|');
}

export function optionLabel(question, optionId) {
  return question.options?.find((option) => option.id === optionId)?.text || optionId;
}

export function displayAnswer(question, answer) {
  if (!answer) return '未填写';
  const parts = question.type === 'text'
    ? [answer.customText?.trim()].filter(Boolean)
    : (answer.selectedOptionIds || []).map((id) => optionLabel(question, id));
  const primary = parts.length ? parts.join('、') : '未填写';
  const supplement = answer.supplementaryText?.trim();
  return supplement ? `${primary}；补充：${supplement}` : primary;
}

export function selectionCount(question, answer) {
  if (question.type === 'text') return answer.customText.trim() ? 1 : 0;
  return (answer.selectedOptionIds || []).length;
}

// 只写补充说明、一个选项都不选，同样算这一题已经回答。
export function isAnswered(question, editable, submittedAnswers, pendingAnswers) {
  const pool = editable ? pendingAnswers : submittedAnswers;
  const answer = pool?.find((item) => item.questionId === question.id);
  if (!answer) return false;
  return selectionCount(question, answer) > 0 || Boolean(answer.supplementaryText?.trim());
}

export function answeredQuestionCount(round, editable, pendingAnswers) {
  return visibleQuestionsOf(round, editable, pendingAnswers).reduce((count, question) => (
    count + (isAnswered(question, editable, round.answers?.answers, pendingAnswers) ? 1 : 0)
  ), 0);
}

export function questionState(question, editable, submittedAnswers, pendingAnswers, focusedQuestionId) {
  if (editable && question.id === focusedQuestionId) return 'current';
  return isAnswered(question, editable, submittedAnswers, pendingAnswers) ? 'done' : 'todo';
}

export function firstUnansweredId(round, editable, pendingAnswers) {
  const pending = visibleQuestionsOf(round, editable, pendingAnswers).find(
    (question) => !isAnswered(question, editable, round.answers?.answers, pendingAnswers),
  );
  return pending?.id || null;
}

// 单选选完就把用户送到下一道没答的题：从当前位置往后找，找不到再从头绕回来，
// 这样跳答过的题不会被落下。全部答完时返回 null。
export function nextUnansweredIdFrom(round, editable, pendingAnswers, questionId) {
  const visible = visibleQuestionsOf(round, editable, pendingAnswers);
  const from = visible.findIndex((question) => question.id === questionId);
  const pending = [...visible.slice(from + 1), ...visible.slice(0, from + 1)]
    .find((question) => !isAnswered(question, editable, round.answers?.answers, pendingAnswers));
  return pending?.id || null;
}
