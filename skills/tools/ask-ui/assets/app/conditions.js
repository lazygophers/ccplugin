// 条件题（showWhen）的可见性判定。页面渲染和服务端校验必须给出完全一样的答案，
// 所以只有这一份实现：Node 直接 import，浏览器由 app.js 以 module 方式加载。

function textOf(answer) {
  return String(answer?.customText || '').trim();
}

// 匹配只看主回答：选择题看选项，文本题看输入框。补充说明是给 Agent 的旁注，
// 拿它触发分支会让用户在写完一句备注后突然冒出新题。
function conditionHit(condition, answer) {
  if (!answer) return false;
  if (condition.optionIds) {
    return (answer.selectedOptionIds || []).some((id) => condition.optionIds.includes(id));
  }
  const text = textOf(answer);
  if (condition.answered) return text.length > 0;
  if (condition.contains) {
    const lower = text.toLowerCase();
    return condition.contains.some((keyword) => lower.includes(keyword.toLowerCase()));
  }
  return new RegExp(condition.matches).test(text);
}

// showWhen 只能指向排在前面的题（normalizeQuestionSet 里强制），所以顺序遍历一趟就够，
// 父题不可见时子题一并不可见。
export function visibleQuestionIds(questions, answers = []) {
  const answerById = new Map(
    (Array.isArray(answers) ? answers : []).map((answer) => [String(answer.questionId), answer]),
  );
  const visible = new Set();
  for (const question of questions) {
    const condition = question.showWhen;
    if (!condition) {
      visible.add(question.id);
      continue;
    }
    if (!visible.has(condition.questionId)) continue;
    if (conditionHit(condition, answerById.get(condition.questionId))) visible.add(question.id);
  }
  return visible;
}

export function visibleQuestions(questions, answers = []) {
  const visible = visibleQuestionIds(questions, answers);
  return questions.filter((question) => visible.has(question.id));
}
