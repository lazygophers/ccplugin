#!/usr/bin/env node

import { constants as fsConstants, createReadStream, existsSync, realpathSync } from 'node:fs';
import fs from 'node:fs/promises';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { randomBytes, randomUUID, createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { wakeClaudeCode } from './adapters/claude-code.mjs';
import { wakeCodexAppServer } from './adapters/codex-app-server.mjs';
import { visibleQuestionIds } from '../assets/app/conditions.js';

const SCRIPT_FILE = fileURLToPath(import.meta.url);
const SKILL_ROOT = path.resolve(path.dirname(SCRIPT_FILE), '..');
const APP_ROOT = path.join(SKILL_ROOT, 'assets', 'app');
const SCHEMA_VERSION = '1.0';
const MAX_BODY_BYTES = 1_048_576;
const SUPPLEMENTARY_TEXT_MAX_LENGTH = 2000;

// 页面用到的第三方渲染组件都不进仓库：首次用到时下载到公共缓存，
// 之后所有项目、所有 Session 共用同一份，离线也能渲染。
const VENDOR = {
  mermaid: {
    version: '11.16.1',
    url: (version) => `https://cdn.jsdelivr.net/npm/mermaid@${version}/dist/mermaid.min.js`,
  },
  marked: {
    version: '15.0.7',
    url: (version) => `https://cdn.jsdelivr.net/npm/marked@${version}/marked.min.js`,
  },
  purify: {
    version: '3.2.4',
    url: (version) => `https://cdn.jsdelivr.net/npm/dompurify@${version}/dist/purify.min.js`,
  },
  highlight: {
    version: '11.11.1',
    url: (version) => `https://cdn.jsdelivr.net/npm/@highlightjs/cdn-assets@${version}/highlight.min.js`,
  },
};

// 太短会在多轮提问之间反复重启服务、换掉用户手上的链接；太长又留垃圾进程。
const DEFAULT_IDLE_TIMEOUT_MS = 30 * 60 * 1000;

function idleTimeoutMs(value) {
  const minutes = Number(value ?? process.env.ASK_UI_IDLE_TIMEOUT_MINUTES);
  if (!Number.isFinite(minutes) || minutes <= 0) return DEFAULT_IDLE_TIMEOUT_MS;
  return minutes * 60 * 1000;
}

function vendorCacheRoot() {
  return process.env.ASK_UI_VENDOR_DIR || path.join(os.homedir(), '.agents', 'ask-ui', 'vendor');
}

function vendorCacheFile(name) {
  return path.join(vendorCacheRoot(), `${name}-${VENDOR[name].version}.min.js`);
}

function now() {
  return new Date().toISOString();
}

function parseArgs(argv) {
  const result = { _: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (!value.startsWith('--')) {
      result._.push(value);
      continue;
    }

    const key = value.slice(2);
    const next = argv[index + 1];
    if (next !== undefined && !next.startsWith('--')) {
      result[key] = next;
      index += 1;
    } else {
      result[key] = true;
    }
  }
  return result;
}

// sessionId 会成为文件系统路径的一段，必须挡住 . / .. / 分隔符。
function assertSafeId(value, label = 'id') {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]{2,127}$/.test(value || '')) {
    throw new Error(`${label} must contain 3-128 safe characters`);
  }
  return value;
}

// 问题和选项的 id 只是 JSON 内部的引用键，不进路径，所以 q1、mr 这种短名合法。
function assertReferenceId(value, label = 'id') {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$/.test(value || '')) {
    throw new Error(`${label} 只能用字母或数字开头、由字母数字和 . _ - 组成，最长 128 个字符（收到 ${JSON.stringify(value)}）`);
  }
  return value;
}

function makeAskId(title = 'ask-ui') {
  const slug = String(title)
    .normalize('NFKD')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toLowerCase()
    .slice(0, 36) || 'ask-ui';
  const stamp = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 14);
  return `${slug}-${stamp}-${randomBytes(2).toString('hex')}`;
}

function askDirectory(dataRoot, askId) {
  return path.join(dataRoot, 'asks', assertSafeId(askId, 'askId'));
}

async function readJson(file, fallback = undefined) {
  try {
    return JSON.parse(await fs.readFile(file, 'utf8'));
  } catch (error) {
    if (error.code === 'ENOENT' && fallback !== undefined) return fallback;
    if (error instanceof SyntaxError) {
      // 带上原始报错的位置信息，写坏 JSON 的调用方才能一次改对，不用二分找。
      throw new Error(`Invalid JSON in ${file}: ${error.message}`);
    }
    throw error;
  }
}

async function atomicWriteJson(file, value) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const temporary = `${file}.${process.pid}.${randomBytes(4).toString('hex')}.tmp`;
  await fs.writeFile(temporary, `${JSON.stringify(value)}\n`, 'utf8');
  try {
    await fs.rename(temporary, file);
  } catch (error) {
    if (!['EEXIST', 'EPERM'].includes(error.code)) throw error;
    await fs.copyFile(temporary, file);
    await fs.rm(temporary, { force: true });
  }
}

async function ensureDataRoot(requested, cwd = process.cwd()) {
  const primary = requested
    ? path.resolve(requested)
    : path.join(path.resolve(cwd), '.ask-ui');

  try {
    await fs.mkdir(primary, { recursive: true });
    await fs.access(primary, fsConstants.W_OK);
    if (path.basename(primary) === '.ask-ui') {
      const ignoreFile = path.join(primary, '.gitignore');
      if (!existsSync(ignoreFile)) {
        await fs.writeFile(ignoreFile, '*\n!.gitignore\n', 'utf8');
      }
    }
    return primary;
  } catch (error) {
    if (requested) throw error;
  }

  const workspaceHash = createHash('sha256')
    .update(path.resolve(cwd))
    .digest('hex')
    .slice(0, 16);
  const stateBase = process.platform === 'win32'
    ? process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local')
    : process.env.XDG_STATE_HOME || path.join(os.homedir(), '.local', 'state');
  const fallback = path.join(stateBase, 'ask-ui', 'workspaces', workspaceHash);
  await fs.mkdir(fallback, { recursive: true });
  await atomicWriteJson(path.join(fallback, 'workspace.json'), {
    cwd: path.resolve(cwd),
    fallback: true,
    updatedAt: now(),
  });
  return fallback;
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
      errors.push(`${label}只能依赖排在它前面的题，${sourceId} 排在第 ${source.index + 1} 位`);
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
        errors.push(`${label}引用了 ${sourceId} 里不存在的选项：${unknown.join('、')}`);
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

export function normalizeQuestionSet(input, { cwd = process.cwd() } = {}) {
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
    projectName: String(input.projectName || path.basename(path.resolve(cwd))),
    title: String(input.title || 'Ask UI 问题收集'),
    summary: String(input.summary || ''),
    background: String(input.background || ''),
    purpose: String(input.purpose || ''),
    wake: normalizeWake(input.wake, cwd),
    questions,
  };
}

async function readAsk(dataRoot, askId) {
  return readJson(path.join(askDirectory(dataRoot, askId), 'ask.json'));
}

async function writeAsk(dataRoot, ask) {
  ask.updatedAt = now();
  await atomicWriteJson(path.join(askDirectory(dataRoot, ask.askId), 'ask.json'), ask);
  return ask;
}

async function updateIndex(dataRoot, ask, extra = {}) {
  const indexFile = path.join(dataRoot, 'index.json');
  // 旧版 index.json 里只有 sessions 数组；asks 缺失时补一个空数组，旧条目原样保留。
  const index = await readJson(indexFile, null) || { schemaVersion: SCHEMA_VERSION };
  if (!Array.isArray(index.asks)) index.asks = [];
  const summary = {
    askId: ask.askId,
    title: ask.title,
    status: ask.status,
    updatedAt: ask.updatedAt,
  };
  const existing = index.asks.findIndex((item) => item.askId === ask.askId);
  if (existing >= 0) index.asks[existing] = summary;
  else index.asks.push(summary);
  index.asks.sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
  Object.assign(index, extra, { updatedAt: now() });
  await atomicWriteJson(indexFile, index);
}

export async function createAsk(input, options = {}) {
  const cwd = options.cwd || process.cwd();
  const dataRoot = await ensureDataRoot(options.dataDir, cwd);
  const deliveryMode = options.deliveryMode || 'manual';
  if (!['direct', 'manual'].includes(deliveryMode)) {
    throw new Error('deliveryMode must be direct or manual');
  }
  const questionSet = normalizeQuestionSet(input, { cwd });
  const askId = makeAskId(questionSet.title);
  const directory = askDirectory(dataRoot, askId);
  await fs.mkdir(directory, { recursive: true });

  const storedQuestionSet = {
    schemaVersion: SCHEMA_VERSION,
    askId,
    title: questionSet.title,
    purpose: questionSet.purpose,
    createdAt: now(),
    questions: questionSet.questions,
  };
  await atomicWriteJson(path.join(directory, 'questions.json'), storedQuestionSet);

  const ask = {
    schemaVersion: SCHEMA_VERSION,
    askId,
    projectName: questionSet.projectName,
    title: questionSet.title,
    summary: questionSet.summary,
    background: questionSet.background,
    purpose: questionSet.purpose,
    status: 'waiting_for_user',
    deliveryMode,
    workspace: path.resolve(cwd),
    wake: questionSet.wake,
    createdAt: storedQuestionSet.createdAt,
    updatedAt: storedQuestionSet.createdAt,
    questionCount: storedQuestionSet.questions.length,
  };
  await writeAsk(dataRoot, ask);
  await updateIndex(dataRoot, ask, { activeAskId: askId });

  return {
    status: 'created',
    dataRoot,
    askId,
    questionsPath: path.join(directory, 'questions.json'),
    ask,
  };
}

export async function submittedAskResult(dataRoot, askId) {
  const directory = askDirectory(dataRoot, askId);
  const ask = await readAsk(dataRoot, askId);
  if (ask.status !== 'submitted') {
    throw new Error(`Ask ${askId} has not been submitted`);
  }
  return {
    status: 'submitted',
    askId,
    title: ask.title,
    questionsPath: path.join(directory, 'questions.json'),
    answersPath: path.join(directory, 'answers.json'),
    questions: await readJson(path.join(directory, 'questions.json')),
    answers: await readJson(path.join(directory, 'answers.json')),
  };
}

function normalizeAnswer(answer, question) {
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

function validateAnswers(questionSet, rawAnswers) {
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

export async function loadAskBundle(dataRoot, askId) {
  const directory = askDirectory(dataRoot, askId);
  const ask = await readAsk(dataRoot, askId);
  return {
    schemaVersion: SCHEMA_VERSION,
    ask,
    questions: await readJson(path.join(directory, 'questions.json')),
    answers: await readJson(path.join(directory, 'answers.json'), null),
  };
}

export async function submitAnswers(dataRoot, askId, payload) {
  const directory = askDirectory(dataRoot, askId);
  const ask = await readAsk(dataRoot, askId);
  const existing = await readJson(path.join(directory, 'answers.json'), null);
  if (existing) {
    return { duplicate: true, answerSet: existing, ask };
  }
  if (ask.status !== 'waiting_for_user') throw new Error('Ask is not accepting answers');

  const questions = await readJson(path.join(directory, 'questions.json'));
  const validated = validateAnswers(questions, payload.answers);
  if (validated.errors.length) {
    const error = new Error(validated.errors.join('; '));
    error.statusCode = 422;
    throw error;
  }
  const answerSet = {
    schemaVersion: SCHEMA_VERSION,
    submissionId: String(payload.submissionId || `submit-${randomUUID()}`),
    askId,
    submittedAt: now(),
    answers: validated.answers,
    hiddenQuestionIds: validated.hiddenQuestionIds,
  };
  await atomicWriteJson(path.join(directory, 'answers.json'), answerSet);
  ask.status = 'submitted';
  ask.submittedAt = answerSet.submittedAt;
  await writeAsk(dataRoot, ask);
  await updateIndex(dataRoot, ask, {
    activeAskId: askId,
    lastSubmittedAskId: askId,
  });
  return { duplicate: false, answerSet, ask };
}

async function listAsks(dataRoot) {
  const asksRoot = path.join(dataRoot, 'asks');
  let entries = [];
  try {
    entries = await fs.readdir(asksRoot, { withFileTypes: true });
  } catch (error) {
    if (error.code === 'ENOENT') return [];
    throw error;
  }
  const asks = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    try {
      asks.push(await readAsk(dataRoot, entry.name));
    } catch {
      // A damaged ask is reported by status when addressed explicitly.
    }
  }
  return asks;
}

export async function resumeAsk(dataRoot, requestedAskId = null) {
  let candidates = [];
  if (requestedAskId) {
    candidates = [await readAsk(dataRoot, requestedAskId)];
  } else {
    candidates = (await listAsks(dataRoot)).filter((ask) => ask.status === 'submitted');
  }

  const submitted = candidates.filter((ask) => ask.status === 'submitted');

  if (submitted.length === 0) {
    return { status: 'waiting', askId: requestedAskId };
  }
  if (!requestedAskId && submitted.length > 1) {
    return {
      status: 'ambiguous',
      candidates: submitted.map((ask) => ({
        askId: ask.askId,
        title: ask.title,
        summary: ask.summary,
        workspace: ask.workspace,
        submittedAt: ask.submittedAt,
      })),
    };
  }

  const latest = submitted.sort((left, right) =>
    right.submittedAt.localeCompare(left.submittedAt))[0];
  return submittedAskResult(dataRoot, latest.askId);
}

export async function completeAsk(dataRoot, askId, status = 'completed') {
  const ask = await readAsk(dataRoot, askId);
  if (!['completed', 'cancelled'].includes(status)) throw new Error('Invalid final status');
  // waiting_for_user 也允许收尾：问错了、任务取消时，没人答的表单同样要作废。
  ask.status = status;
  ask.completedAt = now();
  await writeAsk(dataRoot, ask);
  await updateIndex(dataRoot, ask, { activeAskId: null });
  return ask;
}

function contentType(file) {
  if (file.endsWith('.html')) return 'text/html; charset=utf-8';
  if (file.endsWith('.js')) return 'text/javascript; charset=utf-8';
  if (file.endsWith('.css')) return 'text/css; charset=utf-8';
  return 'application/octet-stream';
}

function addSecurityHeaders(response) {
  response.setHeader('X-Content-Type-Options', 'nosniff');
  response.setHeader('X-Frame-Options', 'DENY');
  response.setHeader('Referrer-Policy', 'no-referrer');
  response.setHeader(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self' https://cdn.bootcdn.net 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'",
  );
}

function sendJson(response, statusCode, value) {
  addSecurityHeaders(response);
  response.writeHead(statusCode, { 'Content-Type': 'application/json; charset=utf-8' });
  response.end(`${JSON.stringify(value)}\n`);
}

function sendFile(response, file) {
  const stream = createReadStream(file);
  // 读文件的错误是异步从流里冒出来的，路由里的 try/catch 接不住。不挂这个监听，
  // 一个权限不对的组件文件就会让整个服务连同全部活跃会话一起退出。
  stream.on('error', (error) => {
    if (response.headersSent) {
      response.destroy();
      return;
    }
    sendJson(response, 500, { error: error.message });
  });
  // 头留到确认打得开文件之后再发，否则失败时已经发出去 200，改不回错误状态码。
  stream.on('open', () => {
    addSecurityHeaders(response);
    response.writeHead(200, { 'Content-Type': contentType(file) });
    stream.pipe(response);
  });
}

// 并发的同名组件请求只应触发一次下载，后到的请求等同一个 promise。
const vendorDownloads = new Map();

async function ensureVendor(name) {
  const cacheFile = vendorCacheFile(name);
  if (existsSync(cacheFile)) return cacheFile;
  if (!vendorDownloads.has(name)) {
    const url = VENDOR[name].url(VENDOR[name].version);
    vendorDownloads.set(name, (async () => {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to download ${name}: ${response.status} ${url}`);
      }
      const body = Buffer.from(await response.arrayBuffer());
      await fs.mkdir(vendorCacheRoot(), { recursive: true });
      const temporary = `${cacheFile}.${process.pid}.tmp`;
      await fs.writeFile(temporary, body);
      await fs.rename(temporary, cacheFile);
      return cacheFile;
    })().finally(() => { vendorDownloads.delete(name); }));
  }
  return vendorDownloads.get(name);
}

async function readRequestJson(request) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > MAX_BODY_BYTES) {
      const error = new Error('Request body is too large');
      error.statusCode = 413;
      throw error;
    }
    chunks.push(chunk);
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}');
  } catch {
    const error = new Error('Request body must be valid JSON');
    error.statusCode = 400;
    throw error;
  }
}

async function recordWakeState(dataRoot, askId, value) {
  const ask = await readAsk(dataRoot, askId);
  ask.wakeState = { ...(ask.wakeState || {}), ...value, updatedAt: now() };
  await writeAsk(dataRoot, ask);
  await updateIndex(dataRoot, ask);
}

async function triggerWake(dataRoot, askId) {
  const ask = await readAsk(dataRoot, askId);
  const binding = ask.wake;
  if (binding?.mode !== 'auto') return { status: 'manual' };
  if (!binding.provider || !binding.sessionRef) {
    await recordWakeState(dataRoot, askId, {
      status: 'unavailable',
      error: 'Missing provider session reference',
    });
    return { status: 'unavailable' };
  }

  const directory = askDirectory(dataRoot, askId);
  const answersPath = path.join(directory, 'answers.json');
  const questionsPath = path.join(directory, 'questions.json');
  const prompt = [
    `Ask UI "${ask.title}" has been submitted.`,
    `Read questions from: ${questionsPath}`,
    `Read answers from: ${answersPath}`,
    'Continue the original workflow using these answers.',
    'If two or more independent follow-up questions are needed, start a new Ask UI form.',
    'If the workflow is complete, no cleanup is required.',
    'Do not resubmit or overwrite the submitted answers.',
  ].join('\n');

  await recordWakeState(dataRoot, askId, {
    status: 'running',
    provider: binding.provider,
    startedAt: now(),
  });
  try {
    const result = binding.provider === 'claude-code'
      ? await wakeClaudeCode({ binding, prompt })
      : await wakeCodexAppServer({ binding, prompt });
    const logDirectory = path.join(directory, 'wake');
    await fs.mkdir(logDirectory, { recursive: true });
    const logFile = path.join(logDirectory, `${Date.now()}-${binding.provider}.json`);
    await atomicWriteJson(logFile, result);
    await recordWakeState(dataRoot, askId, {
      status: 'succeeded',
      provider: binding.provider,
      completedAt: now(),
      logFile,
    });
    return { status: 'succeeded', logFile };
  } catch (error) {
    await recordWakeState(dataRoot, askId, {
      status: 'failed',
      provider: binding.provider,
      completedAt: now(),
      error: error.message,
    });
    return { status: 'failed', error: error.message };
  }
}

export async function startHttpServer({
  dataRoot,
  token = randomBytes(24).toString('hex'),
  port = 0,
  persistServerInfo = true,
  enableWake = true,
  onSubmitted = null,
} = {}) {
  if (!dataRoot) throw new Error('dataRoot is required');
  await fs.mkdir(dataRoot, { recursive: true });

  const server = http.createServer(async (request, response) => {
    const requestUrl = new URL(request.url, 'http://127.0.0.1');
    if (request.method === 'GET' && requestUrl.pathname === '/app.js') {
      sendFile(response, path.join(APP_ROOT, 'app.js'));
      return;
    }
    if (request.method === 'GET' && requestUrl.pathname === '/conditions.js') {
      sendFile(response, path.join(APP_ROOT, 'conditions.js'));
      return;
    }
    if (request.method === 'GET' && requestUrl.pathname === '/view-state.js') {
      sendFile(response, path.join(APP_ROOT, 'view-state.js'));
      return;
    }
    if (request.method === 'GET' && requestUrl.pathname === '/fallback.css') {
      sendFile(response, path.join(APP_ROOT, 'fallback.css'));
      return;
    }
    const vendorMatch = requestUrl.pathname.match(/^\/vendor\/([a-z]+)\.min\.js$/);
    if (request.method === 'GET' && vendorMatch && VENDOR[vendorMatch[1]]) {
      // 只在页面真的用到该组件时才被请求，下载成本不会落到用不上的轮次上。
      try {
        sendFile(response, await ensureVendor(vendorMatch[1]));
      } catch (error) {
        sendJson(response, 502, { error: error.message });
      }
      return;
    }

    const bearer = request.headers.authorization?.replace(/^Bearer\s+/i, '');
    const suppliedToken = bearer || requestUrl.searchParams.get('token');

    if (suppliedToken !== token) {
      sendJson(response, 401, { error: 'Unauthorized' });
      return;
    }

    try {
      if (requestUrl.pathname === '/health') {
        sendJson(response, 200, { ok: true, pid: process.pid });
        return;
      }
      if (
        request.method === 'GET'
        && (requestUrl.pathname === '/' || requestUrl.pathname.startsWith('/ask/'))
      ) {
        sendFile(response, path.join(APP_ROOT, 'index.html'));
        return;
      }

      const apiMatch = requestUrl.pathname.match(
        /^\/api\/asks\/([^/]+)(?:\/(answers|status))?$/,
      );
      if (!apiMatch) {
        sendJson(response, 404, { error: 'Not found' });
        return;
      }
      const askId = assertSafeId(decodeURIComponent(apiMatch[1]), 'askId');
      const operation = apiMatch[2] || null;

      if (request.method === 'GET' && operation === 'status') {
        const ask = await readAsk(dataRoot, askId);
        sendJson(response, 200, { ask });
        return;
      }
      if (request.method === 'GET' && operation === null) {
        sendJson(response, 200, await loadAskBundle(dataRoot, askId));
        return;
      }
      if (request.method === 'POST' && operation === 'answers') {
        const result = await submitAnswers(
          dataRoot,
          askId,
          await readRequestJson(request),
        );
        sendJson(response, 200, result);
        if (!result.duplicate) {
          if (onSubmitted) {
            setTimeout(() => {
              try {
                onSubmitted({ askId, result });
              } catch {
                // Submission is already durable; observer failures must not alter it.
              }
            }, 0);
          }
          if (enableWake && result.ask.deliveryMode !== 'direct') {
            setTimeout(() => {
              triggerWake(dataRoot, askId).catch(() => {});
            }, 0);
          }
        }
        return;
      }
      sendJson(response, 405, { error: 'Method not allowed' });
    } catch (error) {
      sendJson(response, error.statusCode || 500, { error: error.message });
    }
  });

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(Number(port) || 0, '127.0.0.1', resolve);
  });
  const address = server.address();
  const info = {
    pid: process.pid,
    host: '127.0.0.1',
    port: address.port,
    token,
    dataRoot,
    startedAt: now(),
  };
  if (persistServerInfo) await atomicWriteJson(path.join(dataRoot, 'server.json'), info);
  return { server, info };
}

// 常驻服务此前没有任何终点：每次提问都会留下一个永不退出的进程。
// 只要还有人可能来答题就继续跑，否则收摊。
export async function hasPendingAsk(dataRoot) {
  const index = await readJson(path.join(dataRoot, 'index.json'), null);
  if (!index?.asks?.length) return false;
  for (const entry of index.asks) {
    const ask = await readJson(
      path.join(dataRoot, 'asks', entry.askId, 'ask.json'),
      null,
    );
    if (ask?.status === 'waiting_for_user') return true;
  }
  return false;
}

function watchForIdle(server, dataRoot, { idleMs, onExit }) {
  let lastRequestAt = Date.now();
  server.on('request', () => { lastRequestAt = Date.now(); });

  const timer = setInterval(async () => {
    // 数据目录被删掉，服务再挂着也没有意义——测试和临时会话都是这样留下垃圾进程的。
    if (!existsSync(dataRoot)) {
      onExit('data directory is gone');
      return;
    }
    if (Date.now() - lastRequestAt < idleMs) return;
    if (await hasPendingAsk(dataRoot)) return;
    onExit(`idle for ${Math.round(idleMs / 60000)} minutes with no unanswered form`);
  }, Math.min(idleMs, 30_000));
  timer.unref();
  return timer;
}

// 只在没有任何一次提问还等着人回答时才停，且只按 server.json 里记的 pid 精确停。
async function stopIdleServer(dataRoot) {
  if (await hasPendingAsk(dataRoot)) return false;
  const info = await readJson(path.join(dataRoot, 'server.json'), null);
  if (!info?.pid || !await serverIsAlive(info)) return false;
  process.kill(info.pid, 'SIGTERM');
  await fs.rm(path.join(dataRoot, 'server.json'), { force: true });
  return true;
}

async function serverIsAlive(info) {
  if (!info?.port || !info?.token) return false;
  try {
    const response = await fetch(
      `http://127.0.0.1:${info.port}/health?token=${encodeURIComponent(info.token)}`,
      { signal: AbortSignal.timeout(800) },
    );
    return response.ok;
  } catch {
    return false;
  }
}

async function ensureServer(dataRoot, { port = 0 } = {}) {
  const serverFile = path.join(dataRoot, 'server.json');
  const existing = await readJson(serverFile, null);
  if (await serverIsAlive(existing)) return existing;

  const token = randomBytes(24).toString('hex');
  const child = spawn(
    process.execPath,
    [SCRIPT_FILE, 'serve', '--data-dir', dataRoot, '--port', String(Number(port) || 0), '--token', token],
    { detached: true, stdio: 'ignore', windowsHide: true },
  );
  child.unref();

  const deadline = Date.now() + 8000;
  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    const info = await readJson(serverFile, null);
    if (info?.token === token && await serverIsAlive(info)) return info;
  }
  throw new Error('Ask UI server did not start');
}

async function waitForSubmission(dataRoot, askId, signal) {
  while (!signal.aborted) {
    const ask = await readAsk(dataRoot, askId);
    if (ask.status === 'submitted') return ask;
    if (ask.status !== 'waiting_for_user') throw new Error(`Ask UI form is ${ask.status}`);
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw signal.reason || new Error('Ask UI wait interrupted');
}

function openBrowser(url) {
  let child;
  if (process.platform === 'win32') {
    child = spawn('rundll32.exe', ['url.dll,FileProtocolHandler', url], {
      detached: true,
      stdio: 'ignore',
      windowsHide: true,
    });
  } else if (process.platform === 'darwin') {
    child = spawn('open', [url], { detached: true, stdio: 'ignore' });
  } else {
    child = spawn('xdg-open', [url], { detached: true, stdio: 'ignore' });
  }
  child.unref();
}

async function readInput(inputFile) {
  if (!inputFile) throw new Error('--input <questions.json> is required');
  if (inputFile !== '-') return readJson(path.resolve(inputFile));
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}

function print(value) {
  process.stdout.write(`${JSON.stringify(value)}\n`);
}

function help() {
  process.stdout.write(`Ask UI\n\n`);
  process.stdout.write(`  ask --input <file> [--data-dir <dir>] [--port <number>] [--no-open]\n`);
  process.stdout.write(`  create --input <file> [--data-dir <dir>] [--no-open] [--no-serve]\n`);
  process.stdout.write(`  serve [--data-dir <dir>] [--port <number>] [--token <token>]\n`);
  process.stdout.write(`  resume [--id <askId>] [--data-dir <dir>]\n`);
  process.stdout.write(`  status --id <askId> [--data-dir <dir>]\n`);
  process.stdout.write(`  complete --id <askId> [--data-dir <dir>]\n`);
  process.stdout.write(`  cancel --id <askId> [--data-dir <dir>]\n`);
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const command = args._[0] || 'help';
  const dataRoot = await ensureDataRoot(args['data-dir']);

  if (command === 'ask') {
    const created = await createAsk(await readInput(args.input), {
      dataDir: dataRoot,
      cwd: process.cwd(),
      deliveryMode: 'direct',
    });
    const server = await ensureServer(dataRoot, { port: Number(args.port) || 0 });
    const url = `http://127.0.0.1:${server.port}/ask/${encodeURIComponent(created.askId)}?token=${encodeURIComponent(server.token)}`;
    const abortController = new AbortController();
    const interrupt = (signal) => abortController.abort(
      new Error(`Ask UI wait interrupted by ${signal}; saved data was preserved`),
    );
    const onSigint = () => interrupt('SIGINT');
    const onSigterm = () => interrupt('SIGTERM');
    process.once('SIGINT', onSigint);
    process.once('SIGTERM', onSigterm);
    process.stderr.write(`Ask UI ready at ${url}\n`);
    process.stderr.write(`ask-ui-id: ${created.askId}\n`);
    process.stderr.write(`Waiting for submission; data is saved under ${dataRoot}\n`);
    // 这条命令会阻塞到用户提交为止，很容易被 harness 转到后台。一旦转后台，
    // 任务输出里 stdout 和 stderr 是混在一起的，直接 JSON.parse 必然失败。
    process.stderr.write(`If this command is backgrounded or interrupted, do not parse the task output; run: ask-ui.mjs resume --id ${created.askId}\n`);
    if (!args['no-open']) openBrowser(url);
    try {
      await waitForSubmission(dataRoot, created.askId, abortController.signal);
      // 转后台时 stdout 会和 stderr 混在一起，这行是「结果已就绪」的唯一可靠信号。
      process.stderr.write(`ask-ui-submitted: ${created.askId}\n`);
      print(await submittedAskResult(dataRoot, created.askId));
    } finally {
      process.removeListener('SIGINT', onSigint);
      process.removeListener('SIGTERM', onSigterm);
    }
    return;
  }

  if (command === 'create') {
    const created = await createAsk(await readInput(args.input), {
      dataDir: dataRoot,
      cwd: process.cwd(),
      deliveryMode: 'manual',
    });
    if (args['no-serve']) {
      print({ ...created, ask: undefined });
      return;
    }
    const server = await ensureServer(dataRoot);
    const url = `http://127.0.0.1:${server.port}/ask/${encodeURIComponent(created.askId)}?token=${encodeURIComponent(server.token)}`;
    if (!args['no-open']) openBrowser(url);
    print({
      status: 'created',
      askId: created.askId,
      dataRoot,
      questionsPath: created.questionsPath,
      url,
      marker: `ask-ui-id: ${created.askId}`,
    });
    return;
  }

  if (command === 'serve') {
    const started = await startHttpServer({
      dataRoot,
      port: Number(args.port) || 0,
      token: args.token || randomBytes(24).toString('hex'),
    });
    print(started.info);
    return new Promise((resolve) => {
      watchForIdle(started.server, dataRoot, {
        idleMs: idleTimeoutMs(args['idle-timeout']),
        onExit: (reason) => {
          process.stderr.write(`Ask UI server exiting: ${reason}\n`);
          started.server.close(() => resolve());
          // 已建立的 keep-alive 连接会拖住 close，直接断掉。
          started.server.closeAllConnections?.();
        },
      });
    });
  }

  if (command === 'resume') {
    print(await resumeAsk(dataRoot, args.id || null));
    return;
  }

  if (command === 'status') {
    if (!args.id) throw new Error('--id is required');
    print(await loadAskBundle(dataRoot, args.id));
    return;
  }

  if (command === 'complete' || command === 'cancel') {
    if (!args.id) throw new Error('--id is required');
    const completed = await completeAsk(
      dataRoot,
      args.id,
      command === 'cancel' ? 'cancelled' : 'completed',
    );
    // 收尾时顺手关掉常驻服务，不必等它自己 idle 超时。
    print({ ...completed, serverStopped: await stopIdleServer(dataRoot) });
    return;
  }

  help();
}

// argv[1] 是命令行里的字面路径，import.meta.url 是 Node 解析入口后 realpath 过的 URL。
// 经 symlink（skills add 的默认安装方式）或 /tmp 调用时两者不等，必须都归一到真实路径再比。
const isMain = process.argv[1]
  && pathToFileURL(realpathSync(path.resolve(process.argv[1]))).href === import.meta.url;
if (isMain) {
  main().catch((error) => {
    process.stderr.write(`${JSON.stringify({ error: error.message })}\n`);
    process.exitCode = 1;
  });
}
