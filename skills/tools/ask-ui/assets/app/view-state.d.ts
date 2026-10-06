// view-state.js 的类型契约（实现保持 .js，见 conditions.d.ts 头注释）。
import type { ConditionQuestion } from './conditions.js';

export interface FormState {
  questions: { questions: ConditionQuestion[] };
  answers?: { answers?: unknown } | null;
}

// 草稿答案：字段经 normalizeAnswer 补齐后必有，页面与测试都会直接改写。
export interface DraftAnswer {
  questionId: string;
  selectedOptionIds: string[];
  customText: string;
  supplementaryText: string;
}

export declare function defaultAnswer(question: ConditionQuestion): DraftAnswer;
export declare function normalizeAnswer(answer: DraftAnswer): DraftAnswer;
export declare function answersForForm(form: FormState): DraftAnswer[];
export declare function visibleQuestionsOf(
  form: FormState,
  editable: boolean,
  pendingAnswers: DraftAnswer[] | null,
): ConditionQuestion[];
export declare function visibilitySignature(
  form: FormState,
  editable: boolean,
  pendingAnswers: DraftAnswer[] | null,
): string;
export declare function optionLabel(question: ConditionQuestion, optionId: string): string;
export declare function displayAnswer(question: ConditionQuestion, answer: DraftAnswer | null): string;
export declare function selectionCount(question: ConditionQuestion, answer: DraftAnswer): number;
export declare function isAnswered(
  question: ConditionQuestion,
  editable: boolean,
  submittedAnswers: DraftAnswer[] | null,
  pendingAnswers: DraftAnswer[] | null,
): boolean;
export declare function answeredQuestionCount(
  form: FormState,
  editable: boolean,
  pendingAnswers: DraftAnswer[] | null,
): number;
export declare function questionState(
  question: ConditionQuestion,
  editable: boolean,
  submittedAnswers: DraftAnswer[] | null,
  pendingAnswers: DraftAnswer[] | null,
  focusedQuestionId: string | null,
): 'current' | 'done' | 'todo';
export declare function firstUnansweredId(
  form: FormState,
  editable: boolean,
  pendingAnswers: DraftAnswer[] | null,
): string | null;
export declare function nextUnansweredIdFrom(
  form: FormState,
  editable: boolean,
  pendingAnswers: DraftAnswer[] | null,
  questionId: string,
): string | null;
