// 答案校验 module：纯函数，不碰磁盘。可见集、必填、选项合法性都在这里判定，
// store 的 submitAnswers 是它唯一的调用方。
import { visibleQuestionIds } from '../assets/app/conditions.js';

const SUPPLEMENTARY_TEXT_MAX_LENGTH = 2000;

export function normalizeAnswer(answer, question) {
  const selected = Array.isArray(answer?.selectedOptionIds)
    ? [...new Set(answer.selectedOptionIds.map(String))]
    : [];
  const customText = String(answer?.customText || '');
  const supplementaryText = String(answer?.supplementaryText || '');
  return {
    questionId: question.id,
    selectedOptionIds: selected,
    customText,
    supplementaryText,
  };
}

export function validateAnswers(questionSet, rawAnswers) {
  const answerMap = new Map(
    (Array.isArray(rawAnswers) ? rawAnswers : []).map((answer) => [String(answer.questionId), answer]),
  );
  // 条件没满足的题在屏幕上根本不存在：先按提交上来的答案算出可见集，隐藏题既不校验
  // 也不落盘，Agent 读到的答案集与用户看到的表单一一对应。
  const normalizedForVisibility = questionSet.questions.map(
    (question) => normalizeAnswer(answerMap.get(question.id), question),
  );
  const visible = visibleQuestionIds(questionSet.questions, normalizedForVisibility);
  const hiddenQuestionIds = questionSet.questions
    .filter((question) => !visible.has(question.id))
    .map((question) => question.id);
  const errors = [];
  const answers = questionSet.questions.filter((question) => visible.has(question.id)).map((question) => {
    const answer = normalizeAnswer(answerMap.get(question.id), question);
    if (answer.supplementaryText.length > SUPPLEMENTARY_TEXT_MAX_LENGTH) {
      errors.push(`${question.title} supplement exceeds ${SUPPLEMENTARY_TEXT_MAX_LENGTH} characters`);
    }
    // 只写补充说明、一个选项都不选，同样是一个有效回答。
    const answeredBySupplement = Boolean(answer.supplementaryText.trim());
    if (question.type === 'text') {
      if (question.required && !answer.customText.trim() && !answeredBySupplement) {
        errors.push(`${question.title} is required`);
      }
      if (answer.customText.length > question.maxLength) {
        errors.push(`${question.title} exceeds ${question.maxLength} characters`);
      }
      answer.selectedOptionIds = [];
      return answer;
    }

    const allowed = new Set(question.options.map((option) => option.id));
    if (answer.selectedOptionIds.some((optionId) => !allowed.has(optionId))) {
      errors.push(`${question.title} contains an unknown option`);
    }
    if (answer.customText.trim()) {
      errors.push(`${question.title} does not allow a custom answer`);
    }
    const selectionCount = answer.selectedOptionIds.length;
    if (question.required && selectionCount === 0 && !answeredBySupplement) {
      errors.push(`${question.title} is required`);
    }
    if (question.type === 'single' && selectionCount > 1) {
      errors.push(`${question.title} allows only one answer`);
    }
    // 补充说明可以替代选择，但一旦选了，数量仍须落在 min/max 区间内。
    if (question.type === 'multiple' && !(selectionCount === 0 && answeredBySupplement)) {
      if (selectionCount < question.minSelections) {
        errors.push(`${question.title} requires at least ${question.minSelections} selections`);
      }
      if (selectionCount > question.maxSelections) {
        errors.push(`${question.title} allows at most ${question.maxSelections} selections`);
      }
    }
    return answer;
  });
  return { answers, errors, hiddenQuestionIds };
}
