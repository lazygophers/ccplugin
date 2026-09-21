// 问题集 module：QuestionSet JSON 的结构校验与规范化。
//
// 校验分两层，都在这一个 interface 背后：
// 1. schema-validator 按 references/questionset.schema.json 做结构检查（schema 先跑）；
// 2. 中文业务校验（跨字段规则、缺省值归一）产出最终错误信息。
// 两层必须同判：schema 拒而业务校验收（或反过来）都是漂移，当场抛内部错误。
import { readFileSync } from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { validateAgainstSchema, formatSchemaErrors } from './schema-validator.mjs';

const SCHEMA_VERSION = '1.0';

const questionSetSchema = JSON.parse(
  readFileSync(new URL('../references/questionset.schema.json', import.meta.url), 'utf8'),
);

// 问题/选项的 id 只是 JSON 内部的引用键，不进路径，q1、mr 这种短名合法。
function assertReferenceId(value, label = 'id') {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$/.test(value || '')) {
    throw new Error(`${label} 只能用字母或数字开头、由字母数字和 . _ - 组成，最长 128 个字符（收到 ${JSON.stringify(value)}）`);
  }
  return value;
}

function normalizeWake(rawWake, cwd) {
  const wake = rawWake && typeof rawWake === 'object' ? rawWake : {};
  const mode = ['auto', 'manual', 'unavailable'].includes(wake.mode)
    ? wake.mode
    : 'manual';
  const provider = ['claude-code', 'codex-app-server'].includes(wake.provider)
    ? wake.provider
    : null;
  return {
    mode: mode === 'auto' && !provider ? 'unavailable' : mode,
    provider,
    sessionRef: wake.sessionRef ? String(wake.sessionRef) : null,
    cwd: wake.cwd ? path.resolve(wake.cwd) : path.resolve(cwd),
  };
}

// 左栏导航要的是一行短标题，作者没写 title 时从正文首个非空行取。
function firstLine(text) {
  return text.split('\n').map((line) => line.trim()).find(Boolean) || '';
}

function normalizeQuestion(question, index) {
  if (!question || typeof question !== 'object' || Array.isArray(question)) {
    throw new Error(`第 ${index + 1} 题必须是 JSON 对象`);
  }

  // 一道题里所有的问题一起报，别让调用方修完 id 再来一轮才发现选项也不合法。
  const issues = [];
  const collect = (check) => {
    try {
      check();
    } catch (error) {
      issues.push(error.message);
    }
  };

  const id = String(question.id || `q${index + 1}`);
  collect(() => assertReferenceId(id, `第 ${index + 1} 题的 id`));

  const type = question.type;
  if (!['single', 'multiple', 'text'].includes(type)) {
    issues.push(`第 ${id} 题必须写明 type：single（单选）、multiple（多选）或 text（文本），收到 ${JSON.stringify(question.type)}`);
    throw new Error(issues.join('；'));
  }

  const text = String(question.text || '');
  if (!text.trim()) issues.push(`第 ${id} 题缺少 text（问题正文，支持 Markdown 与 Mermaid）`);
  if (question.recommendedOptionIds !== undefined) {
    issues.push(`第 ${id} 题不再支持题级 recommendedOptionIds：把 recommended 和 reason 写进对应选项里`);
  }

  const normalized = {
    id,
    type,
    text,
    title: String(question.title || '') || firstLine(text) || `问题 ${index + 1}`,
    background: String(question.background || ''),
    required: question.required !== false,
    // 跨题引用要等所有题都规范化完才能校验，这里先原样带着，第二趟在
    // normalizeConditions 里定形。
    showWhen: question.showWhen ?? null,
  };

  if (type === 'text') {
    normalized.recommendedDraft = String(question.recommendedDraft || '');
    normalized.recommendationReason = String(question.recommendationReason || '');
    normalized.multiline = question.multiline !== false;
    normalized.maxLength = Number.isInteger(question.maxLength)
      ? Math.max(1, question.maxLength)
      : 4000;
    if (issues.length) throw new Error(issues.join('；'));
    return normalized;
  }

  if (!Array.isArray(question.options) || question.options.length < 2) {
    issues.push(`第 ${id} 题是选择题，至少要有两个选项`);
    throw new Error(issues.join('；'));
  }
  normalized.options = question.options.map((option, optionIndex) => {
    const label = `第 ${id} 题第 ${optionIndex + 1} 个选项`;
    if (!option || typeof option !== 'object' || Array.isArray(option)) {
      issues.push(`${label}必须是 JSON 对象，形如 {"text":"甲","recommended":true,"reason":"..."}`);
      return { id: `option-${optionIndex + 1}`, text: '', description: '', recommended: false, reason: '' };
    }
    const optionId = String(option.id || `option-${optionIndex + 1}`);
    collect(() => assertReferenceId(optionId, `${label}的 id`));
    const optionText = String(option.text || '');
    if (!optionText.trim()) issues.push(`${label}缺少 text`);
    const recommended = option.recommended === true;
    const reason = String(option.reason || '');
    if (reason && !recommended) {
      issues.push(`${label}写了 reason 却没有 recommended: true——推荐原因只属于推荐项`);
    }
    return {
      id: optionId,
      text: optionText,
      description: String(option.description || ''),
      recommended,
      reason,
    };
  });
  if (issues.length) throw new Error(issues.join('；'));
  // 单选只认第一个推荐项：两个「推荐」徽标会让用户不知道该照哪个。
  if (type === 'single') {
    let seen = false;
    for (const option of normalized.options) {
      if (!option.recommended) continue;
      if (seen) {
        option.recommended = false;
        option.reason = '';
      }
      seen = true;
    }
  }
  if (type === 'multiple') {
    normalized.minSelections = Number.isInteger(question.minSelections)
      ? Math.max(0, question.minSelections)
      : normalized.required ? 1 : 0;
    normalized.maxSelections = Number.isInteger(question.maxSelections)
      ? Math.max(normalized.minSelections, question.maxSelections)
      : normalized.options.length;
  }
  return normalized;
}

const CONDITION_MATCHERS = ['optionIds', 'answered', 'contains', 'matches'];

// showWhen 指向别的题，只有拿到全部题目才校验得了：题必须排在前面（顺序即依赖序，
// 天然排除环），匹配方式必须配得上被指向那道题的类型。
function normalizeConditions(questions) {
  const errors = [];
  const byId = new Map();
  questions.forEach((question, index) => {
    byId.set(question.id, { question, index });
  });

  questions.forEach((question, index) => {
    const raw = question.showWhen;
    if (raw === null || raw === undefined) {
      question.showWhen = null;
      return;
    }
    const label = `第 ${question.id} 题的 showWhen`;
    if (typeof raw !== 'object' || Array.isArray(raw)) {
      errors.push(`${label}必须是 JSON 对象，形如 {"questionId":"q1","optionIds":["a"]}`);
      question.showWhen = null;
      return;
    }

    const sourceId = String(raw.questionId || '');
    const source = byId.get(sourceId);
    if (!source) {
      errors.push(`${label}引用了不存在的题 ${JSON.stringify(raw.questionId)}`);
      question.showWhen = null;
      return;
    }
    if (source.index >= index) {
      errors.push(`${label} 只能依赖排在它前面的题，${sourceId} 排在第 ${source.index + 1} 位`);
      question.showWhen = null;
      return;
    }

    const used = CONDITION_MATCHERS.filter((key) => raw[key] !== undefined);
    if (used.length !== 1) {
      errors.push(`${label}必须且只能写一种匹配方式（${CONDITION_MATCHERS.join(' / ')}），收到 ${used.length} 种`);
      question.showWhen = null;
      return;
    }
    const matcher = used[0];
    const isChoice = source.question.type !== 'text';
    if (isChoice && matcher !== 'optionIds') {
      errors.push(`${label}指向的是选择题 ${sourceId}，只能用 optionIds 匹配`);
      question.showWhen = null;
      return;
    }
    if (!isChoice && matcher === 'optionIds') {
      errors.push(`${label}指向的是文本题 ${sourceId}，只能用 answered / contains / matches 匹配`);
      question.showWhen = null;
      return;
    }

    if (matcher === 'optionIds') {
      const optionIds = Array.isArray(raw.optionIds) ? raw.optionIds.map(String) : [];
      if (!optionIds.length) {
        errors.push(`${label}的 optionIds 至少要写一个选项 id`);
        question.showWhen = null;
        return;
      }
      const known = new Set(source.question.options.map((option) => option.id));
      const unknown = optionIds.filter((optionId) => !known.has(optionId));
      if (unknown.length) {
        errors.push(`${label} 引用了 ${sourceId} 里不存在的选项：${unknown.join('、')}`);
        question.showWhen = null;
        return;
      }
      question.showWhen = { questionId: sourceId, optionIds };
      return;
    }

    if (matcher === 'answered') {
      if (raw.answered !== true) {
        errors.push(`${label}的 answered 只接受 true——不需要条件就整个删掉 showWhen`);
        question.showWhen = null;
        return;
      }
      question.showWhen = { questionId: sourceId, answered: true };
      return;
    }

    if (matcher === 'contains') {
      const keywords = (Array.isArray(raw.contains) ? raw.contains : [])
        .map(String)
        .filter((keyword) => keyword.trim());
      if (!keywords.length) {
        errors.push(`${label}的 contains 至少要写一个非空关键词`);
        question.showWhen = null;
        return;
      }
      question.showWhen = { questionId: sourceId, contains: keywords };
      return;
    }

    const pattern = String(raw.matches || '');
    try {
      new RegExp(pattern);
    } catch (error) {
      errors.push(`${label}的 matches 不是合法正则：${error.message}`);
      question.showWhen = null;
      return;
    }
    question.showWhen = { questionId: sourceId, matches: pattern };
  });

  if (errors.length) throw new Error(errors.join('；'));
}

// 轮次与 Session 的双层概念已合并成「一次提问」。旧字段当场报错并指路，
// 不做静默映射——调用方照旧文档写出来的 JSON 必须在入口就被拦下。
const REMOVED_INPUT_FIELDS = {
  sessionId: 'sessionId 已移除：每次 ask 都是一次独立提问，id 由 CLI 生成',
  roundNumber: 'roundNumber 已移除：轮次概念已删除，每次 ask 都是一次独立提问',
  basedOnRound: 'basedOnRound 已移除：轮次概念已删除，追问直接再发起一次 ask',
  sessionTitle: 'sessionTitle 已改名：直接写 title',
  sessionSummary: 'sessionSummary 已改名：直接写 summary',
  sessionBackground: 'sessionBackground 已改名：直接写 background',
};

function normalizeBusiness(input, cwd) {
  if (!input || typeof input !== 'object' || !Array.isArray(input.questions)) {
    throw new Error('QuestionSet requires a questions array');
  }
  if (input.questions.length === 0) throw new Error('QuestionSet cannot be empty');

  // 逐题 fail-fast 会让调用方每修一个 id 就重跑一次。一次把所有题的问题报全，改一遍就能过。
  const questions = [];
  const errors = [];
  for (const [field, message] of Object.entries(REMOVED_INPUT_FIELDS)) {
    if (input[field] !== undefined && input[field] !== null) errors.push(message);
  }
  input.questions.forEach((question, index) => {
    try {
      questions.push(normalizeQuestion(question, index));
    } catch (error) {
      errors.push(error.message);
    }
  });
  if (errors.length) throw new Error(errors.join('；'));
  normalizeConditions(questions);

  return {
    schemaVersion: SCHEMA_VERSION,
    projectName: String(input.projectName || ''),
    title: String(input.title || '未命名提问'),
    summary: String(input.summary || ''),
    background: String(input.background || ''),
    purpose: String(input.purpose || ''),
    wake: normalizeWake(input.wake, cwd),
    questions,
  };
}

export function normalizeQuestionSet(input, { cwd = process.cwd() } = {}) {
  // schema 先行：照 references/questionset.schema.json 写出来的 JSON 结构必须先过。
  const bySchema = validateAgainstSchema(input, questionSetSchema);

  // 业务校验产出中文错误（一次报全、带定位），它是抛给调用方的唯一错误来源。
  let business;
  try {
    business = normalizeBusiness(input, cwd);
  } catch (error) {
    // schema 收而业务拒 = 跨字段规则，正常；schema 拒而业务收则不可能走到这里。
    throw error;
  }

  // 两层必须同判：schema 拒了业务却收下，说明 references 与运行时漂移了，
  // 当场抛错把漂移暴露出来，绝不让两套规则各说各话。
  if (!bySchema.valid) {
    throw new Error(`QuestionSet schema 与运行时校验漂移（schema 拒收，运行时放行）：\n${formatSchemaErrors(bySchema.errors)}`);
  }
  return business;
}

export { assertReferenceId };
