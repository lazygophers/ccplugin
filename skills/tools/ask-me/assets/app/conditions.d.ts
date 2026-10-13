// conditions.js 的类型契约。实现是浏览器与 Node 共用的一份 .js（浏览器资产不转 TS、
// 不加构建），类型写在这里；结构与 scripts/questionset.mts 的 Question 保持结构兼容。
export interface ConditionAnswer {
  questionId: string;
  selectedOptionIds?: string[];
  customText?: string;
  supplementaryText?: string;
}

export interface ConditionQuestion {
  id: string;
  type: string;
  showWhen: unknown;
  options?: { id: string; text?: string }[];
}

export declare function visibleQuestionIds(
  questions: ConditionQuestion[],
  answers?: ConditionAnswer[],
): Set<string>;

export declare function visibleQuestions(
  questions: ConditionQuestion[],
  answers?: ConditionAnswer[],
): ConditionQuestion[];
