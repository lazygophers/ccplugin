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

function makeSessionId(title = 'ask-ui') {
  const slug = String(title)
    .normalize('NFKD')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toLowerCase()
    .slice(0, 36) || 'ask-ui';
  const stamp = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 14);
  return `${slug}-${stamp}-${randomBytes(2).toString('hex')}`;
}

function roundDirectory(dataRoot, sessionId, roundNumber) {
  return path.join(
    dataRoot,
    'sessions',
    assertSafeId(sessionId, 'sessionId'),
    'rounds',
    String(roundNumber).padStart(3, '0'),
  );
}

function sessionDirectory(dataRoot, sessionId) {
  return path.join(dataRoot, 'sessions', assertSafeId(sessionId, 'sessionId'));
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

function normalizeQuestionSet(input, { cwd = process.cwd() } = {}) {
  if (!input || typeof input !== 'object' || !Array.isArray(input.questions)) {
    throw new Error('QuestionSet requires a questions array');
  }
  if (input.questions.length === 0) throw new Error('QuestionSet cannot be empty');

  // 逐题 fail-fast 会让调用方每修一个 id 就重跑一次。一次把所有题的问题报全，改一遍就能过。
  const questions = [];
  const errors = [];
  input.questions.forEach((question, index) => {
    try {
      questions.push(normalizeQuestion(question, index));
    } catch (error) {
      errors.push(error.message);
    }
  });
  if (errors.length) throw new Error(errors.join('；'));

  return {
    schemaVersion: SCHEMA_VERSION,
    sessionId: input.sessionId ? assertSafeId(String(input.sessionId), 'sessionId') : null,
    projectName: String(input.projectName || path.basename(path.resolve(cwd))),
    sessionTitle: String(input.sessionTitle || input.title || 'Ask UI 问题收集'),
    sessionSummary: String(input.sessionSummary || ''),
    sessionBackground: String(input.sessionBackground || ''),
    roundNumber: Number.isInteger(input.roundNumber) ? input.roundNumber : null,
    title: String(input.title || '需求确认'),
    purpose: String(input.purpose || ''),
    basedOnRound: Number.isInteger(input.basedOnRound) ? input.basedOnRound : null,
    wake: normalizeWake(input.wake, cwd),
    questions,
  };
}

async function readSession(dataRoot, sessionId) {
  return readJson(path.join(sessionDirectory(dataRoot, sessionId), 'session.json'));
}

async function writeSession(dataRoot, session) {
  session.updatedAt = now();
  session.roundCount = session.rounds.length;
  session.totalQuestionCount = session.rounds.reduce(
    (sum, round) => sum + round.questionCount,
    0,
  );
  session.currentRound = session.rounds.length
    ? Math.max(...session.rounds.map((round) => round.roundNumber))
    : 0;
  await atomicWriteJson(
    path.join(sessionDirectory(dataRoot, session.sessionId), 'session.json'),
    session,
  );
  return session;
}

async function updateIndex(dataRoot, session, extra = {}) {
  const indexFile = path.join(dataRoot, 'index.json');
  const index = await readJson(indexFile, {
    schemaVersion: SCHEMA_VERSION,
    sessions: [],
  });
  const summary = {
    sessionId: session.sessionId,
    title: session.title,
    status: session.status,
    currentRound: session.currentRound,
    updatedAt: session.updatedAt,
  };
  const existing = index.sessions.findIndex((item) => item.sessionId === session.sessionId);
  if (existing >= 0) index.sessions[existing] = summary;
  else index.sessions.push(summary);
  index.sessions.sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
  Object.assign(index, extra, { updatedAt: now() });
  await atomicWriteJson(indexFile, index);
}

export async function createRound(input, options = {}) {
  const cwd = options.cwd || process.cwd();
  const dataRoot = await ensureDataRoot(options.dataDir, cwd);
  const deliveryMode = options.deliveryMode || 'manual';
  if (!['direct', 'manual'].includes(deliveryMode)) {
    throw new Error('deliveryMode must be direct or manual');
  }
  const questionSet = normalizeQuestionSet(input, { cwd });
  const sessionId = questionSet.sessionId || makeSessionId(questionSet.sessionTitle);
  const sessionFile = path.join(sessionDirectory(dataRoot, sessionId), 'session.json');
  const existingSession = await readJson(sessionFile, null);
  const session = existingSession || {
    schemaVersion: SCHEMA_VERSION,
    sessionId,
    projectName: questionSet.projectName,
    title: questionSet.sessionTitle,
    summary: questionSet.sessionSummary,
    background: questionSet.sessionBackground,
    status: 'active',
    workspace: path.resolve(cwd),
    wake: questionSet.wake,
    createdAt: now(),
    updatedAt: now(),
    currentRound: 0,
    roundCount: 0,
    totalQuestionCount: 0,
    rounds: [],
  };

  if (session.status === 'completed' || session.status === 'cancelled') {
    throw new Error(`Session ${sessionId} is ${session.status}; create a new session`);
  }

  const roundNumber = questionSet.roundNumber
    || (session.rounds.length ? Math.max(...session.rounds.map((item) => item.roundNumber)) + 1 : 1);
  if (!Number.isInteger(roundNumber) || roundNumber < 1) {
    throw new Error('roundNumber must be a positive integer');
  }
  if (session.rounds.some((item) => item.roundNumber === roundNumber)) {
    throw new Error(`Round ${roundNumber} already exists in ${sessionId}`);
  }

  const basedOnRound = questionSet.basedOnRound
    ?? (roundNumber > 1 ? roundNumber - 1 : null);
  if (basedOnRound !== null && !session.rounds.some((item) => item.roundNumber === basedOnRound)) {
    throw new Error(`basedOnRound ${basedOnRound} does not exist`);
  }

  const storedQuestionSet = {
    schemaVersion: SCHEMA_VERSION,
    sessionId,
    roundNumber,
    title: questionSet.title,
    purpose: questionSet.purpose,
    basedOnRound,
    createdAt: now(),
    questions: questionSet.questions,
  };
  const roundDir = roundDirectory(dataRoot, sessionId, roundNumber);
  await fs.mkdir(roundDir, { recursive: true });
  await atomicWriteJson(path.join(roundDir, 'questions.json'), storedQuestionSet);

  if (basedOnRound !== null) {
    const previous = session.rounds.find((item) => item.roundNumber === basedOnRound);
    if (previous?.status === 'submitted') {
      previous.status = 'processed';
      previous.processedAt = now();
    }
  }
  session.title = session.title || questionSet.sessionTitle;
  session.summary = session.summary || questionSet.sessionSummary;
  session.projectName = session.projectName || questionSet.projectName;
  session.background = session.background || questionSet.sessionBackground;
  if (questionSet.wake.mode !== 'manual' || !existingSession) session.wake = questionSet.wake;
  session.rounds.push({
    roundNumber,
    title: storedQuestionSet.title,
    purpose: storedQuestionSet.purpose,
    basedOnRound,
    status: 'waiting_for_user',
    deliveryMode,
    questionCount: storedQuestionSet.questions.length,
    createdAt: storedQuestionSet.createdAt,
  });
  await writeSession(dataRoot, session);
  await updateIndex(dataRoot, session, { activeSessionId: sessionId });

  return {
    status: 'created',
    dataRoot,
    sessionId,
    roundNumber,
    questionsPath: path.join(roundDir, 'questions.json'),
    session,
  };
}

export async function submittedRoundResult(dataRoot, sessionId, roundNumber) {
  const session = await readSession(dataRoot, sessionId);
  const round = session.rounds.find((item) => item.roundNumber === roundNumber);
  if (!round) throw new Error(`Round ${roundNumber} not found`);
  if (!['submitted', 'processed'].includes(round.status)) {
    throw new Error(`Round ${roundNumber} has not been submitted`);
  }
  const directory = roundDirectory(dataRoot, sessionId, roundNumber);
  return {
    status: 'submitted',
    sessionId,
    sessionTitle: session.title,
    roundNumber,
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
  const errors = [];
  const answers = questionSet.questions.map((question) => {
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
  return { answers, errors };
}

export async function loadSessionBundle(dataRoot, sessionId) {
  const session = await readSession(dataRoot, sessionId);
  const rounds = [];
  for (const roundSummary of [...session.rounds].sort((a, b) => a.roundNumber - b.roundNumber)) {
    const directory = roundDirectory(dataRoot, sessionId, roundSummary.roundNumber);
    rounds.push({
      ...roundSummary,
      questions: await readJson(path.join(directory, 'questions.json')),
      answers: await readJson(path.join(directory, 'answers.json'), null),
    });
  }
  return { schemaVersion: SCHEMA_VERSION, session, rounds };
}

export async function submitAnswers(dataRoot, sessionId, roundNumber, payload) {
  const session = await readSession(dataRoot, sessionId);
  const round = session.rounds.find((item) => item.roundNumber === roundNumber);
  if (!round) throw new Error(`Round ${roundNumber} not found`);
  const directory = roundDirectory(dataRoot, sessionId, roundNumber);
  const existing = await readJson(path.join(directory, 'answers.json'), null);
  if (existing) {
    return { duplicate: true, answerSet: existing, session };
  }
  if (round.status !== 'waiting_for_user') throw new Error('Round is not accepting answers');

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
    sessionId,
    roundNumber,
    submittedAt: now(),
    answers: validated.answers,
  };
  await atomicWriteJson(path.join(directory, 'answers.json'), answerSet);
  round.status = 'submitted';
  round.submittedAt = answerSet.submittedAt;
  await writeSession(dataRoot, session);
  await updateIndex(dataRoot, session, {
    activeSessionId: sessionId,
    lastSubmittedSessionId: sessionId,
  });
  return { duplicate: false, answerSet, session };
}

async function listSessions(dataRoot) {
  const sessionsRoot = path.join(dataRoot, 'sessions');
  let entries = [];
  try {
    entries = await fs.readdir(sessionsRoot, { withFileTypes: true });
  } catch (error) {
    if (error.code === 'ENOENT') return [];
    throw error;
  }
  const sessions = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    try {
      sessions.push(await readSession(dataRoot, entry.name));
    } catch {
      // A damaged session is reported by status when addressed explicitly.
    }
  }
  return sessions;
}

export async function resumeRound(dataRoot, requestedSessionId = null) {
  let candidates = [];
  if (requestedSessionId) {
    candidates = [await readSession(dataRoot, requestedSessionId)];
  } else {
    candidates = (await listSessions(dataRoot)).filter((session) =>
      session.rounds.some((round) => round.status === 'submitted'));
  }

  const submitted = candidates.flatMap((session) =>
    session.rounds
      .filter((round) => round.status === 'submitted')
      .map((round) => ({ session, round })));

  if (submitted.length === 0) {
    return { status: 'waiting', sessionId: requestedSessionId };
  }
  if (!requestedSessionId && submitted.length > 1) {
    return {
      status: 'ambiguous',
      candidates: submitted.map(({ session, round }) => ({
        sessionId: session.sessionId,
        title: session.title,
        summary: session.summary,
        workspace: session.workspace,
        roundNumber: round.roundNumber,
        submittedAt: round.submittedAt,
      })),
    };
  }

  const { session, round } = submitted.sort((left, right) =>
    right.round.submittedAt.localeCompare(left.round.submittedAt))[0];
  return submittedRoundResult(dataRoot, session.sessionId, round.roundNumber);
}

export async function completeSession(dataRoot, sessionId, status = 'completed') {
  const session = await readSession(dataRoot, sessionId);
  if (!['completed', 'cancelled'].includes(status)) throw new Error('Invalid final status');
  for (const round of session.rounds) {
    if (round.status === 'submitted') {
      round.status = 'processed';
      round.processedAt = now();
    }
  }
  session.status = status;
  session.completedAt = now();
  await writeSession(dataRoot, session);
  await updateIndex(dataRoot, session, { activeSessionId: null });
  return session;
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
  addSecurityHeaders(response);
  response.writeHead(200, { 'Content-Type': contentType(file) });
  createReadStream(file).pipe(response);
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

async function recordWakeState(dataRoot, sessionId, value) {
  const session = await readSession(dataRoot, sessionId);
  session.wakeState = { ...(session.wakeState || {}), ...value, updatedAt: now() };
  await writeSession(dataRoot, session);
  await updateIndex(dataRoot, session);
}

async function triggerWake(dataRoot, sessionId, roundNumber) {
  const session = await readSession(dataRoot, sessionId);
  const binding = session.wake;
  if (binding?.mode !== 'auto') return { status: 'manual' };
  if (!binding.provider || !binding.sessionRef) {
    await recordWakeState(dataRoot, sessionId, {
      status: 'unavailable',
      error: 'Missing provider session reference',
    });
    return { status: 'unavailable' };
  }

  const directory = roundDirectory(dataRoot, sessionId, roundNumber);
  const answersPath = path.join(directory, 'answers.json');
  const questionsPath = path.join(directory, 'questions.json');
  const prompt = [
    `Ask UI session "${session.title}" round ${roundNumber} has been submitted.`,
    `Read questions from: ${questionsPath}`,
    `Read answers from: ${answersPath}`,
    'Continue the original workflow using these answers.',
    'If two or more independent follow-up questions are needed, create the next Ask UI round with the same sessionId.',
    'If the workflow is complete, mark the Ask UI session complete.',
    'Do not repeat or overwrite a submitted round.',
  ].join('\n');

  await recordWakeState(dataRoot, sessionId, {
    status: 'running',
    provider: binding.provider,
    roundNumber,
    startedAt: now(),
  });
  try {
    const result = binding.provider === 'claude-code'
      ? await wakeClaudeCode({ binding, prompt })
      : await wakeCodexAppServer({ binding, prompt });
    const logDirectory = path.join(sessionDirectory(dataRoot, sessionId), 'wake');
    await fs.mkdir(logDirectory, { recursive: true });
    const logFile = path.join(logDirectory, `${Date.now()}-${binding.provider}.json`);
    await atomicWriteJson(logFile, result);
    await recordWakeState(dataRoot, sessionId, {
      status: 'succeeded',
      provider: binding.provider,
      roundNumber,
      completedAt: now(),
      logFile,
    });
    return { status: 'succeeded', logFile };
  } catch (error) {
    await recordWakeState(dataRoot, sessionId, {
      status: 'failed',
      provider: binding.provider,
      roundNumber,
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
        && (requestUrl.pathname === '/' || requestUrl.pathname.startsWith('/session/'))
      ) {
        sendFile(response, path.join(APP_ROOT, 'index.html'));
        return;
      }

      const apiMatch = requestUrl.pathname.match(
        /^\/api\/sessions\/([^/]+)(?:\/rounds\/(\d+)\/(answers)|\/(status))?$/,
      );
      if (!apiMatch) {
        sendJson(response, 404, { error: 'Not found' });
        return;
      }
      const sessionId = assertSafeId(decodeURIComponent(apiMatch[1]), 'sessionId');
      const roundNumber = apiMatch[2] ? Number(apiMatch[2]) : null;
      const operation = apiMatch[3] || apiMatch[4] || null;

      if (request.method === 'GET' && operation === 'status') {
        const session = await readSession(dataRoot, sessionId);
        sendJson(response, 200, { session });
        return;
      }
      if (request.method === 'GET' && operation === null) {
        sendJson(response, 200, await loadSessionBundle(dataRoot, sessionId));
        return;
      }
      if (request.method === 'POST' && operation === 'answers') {
        const result = await submitAnswers(
          dataRoot,
          sessionId,
          roundNumber,
          await readRequestJson(request),
        );
        sendJson(response, 200, result);
        if (!result.duplicate) {
          if (onSubmitted) {
            setTimeout(() => {
              try {
                onSubmitted({ sessionId, roundNumber, result });
              } catch {
                // Submission is already durable; observer failures must not alter it.
              }
            }, 0);
          }
          const submittedRound = result.session.rounds.find(
            (round) => round.roundNumber === roundNumber,
          );
          if (enableWake && submittedRound?.deliveryMode !== 'direct') {
            setTimeout(() => {
              triggerWake(dataRoot, sessionId, roundNumber).catch(() => {});
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

// 常驻服务此前没有任何终点：每轮提问都会留下一个永不退出的进程。
// 只要还有人可能来答题就继续跑，否则收摊。
export async function hasPendingRound(dataRoot) {
  const index = await readJson(path.join(dataRoot, 'index.json'), null);
  if (!index?.sessions?.length) return false;
  for (const entry of index.sessions) {
    const session = await readJson(
      path.join(dataRoot, 'sessions', entry.sessionId, 'session.json'),
      null,
    );
    if (session?.status !== 'active') continue;
    if (session.rounds.some((round) => round.status === 'waiting_for_user')) return true;
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
    if (await hasPendingRound(dataRoot)) return;
    onExit(`idle for ${Math.round(idleMs / 60000)} minutes with no unanswered round`);
  }, Math.min(idleMs, 30_000));
  timer.unref();
  return timer;
}

// 只在没有任何一轮还等着人回答时才停，且只按 server.json 里记的 pid 精确停。
async function stopIdleServer(dataRoot) {
  if (await hasPendingRound(dataRoot)) return false;
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

async function waitForRoundSubmission(dataRoot, sessionId, roundNumber, signal) {
  while (!signal.aborted) {
    const session = await readSession(dataRoot, sessionId);
    const round = session.rounds.find((item) => item.roundNumber === roundNumber);
    if (!round) throw new Error(`Round ${roundNumber} not found`);
    if (['submitted', 'processed'].includes(round.status)) return round;
    if (session.status !== 'active') {
      throw new Error(`Ask UI session is ${session.status}`);
    }
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
  process.stdout.write(`  resume [--session <id>] [--data-dir <dir>]\n`);
  process.stdout.write(`  status --session <id> [--data-dir <dir>]\n`);
  process.stdout.write(`  complete --session <id> [--data-dir <dir>]\n`);
  process.stdout.write(`  cancel --session <id> [--data-dir <dir>]\n`);
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const command = args._[0] || 'help';
  const dataRoot = await ensureDataRoot(args['data-dir']);

  if (command === 'ask') {
    const created = await createRound(await readInput(args.input), {
      dataDir: dataRoot,
      cwd: process.cwd(),
      deliveryMode: 'direct',
    });
    const server = await ensureServer(dataRoot, { port: Number(args.port) || 0 });
    const url = `http://127.0.0.1:${server.port}/session/${encodeURIComponent(created.sessionId)}?token=${encodeURIComponent(server.token)}`;
    const abortController = new AbortController();
    const interrupt = (signal) => abortController.abort(
      new Error(`Ask UI wait interrupted by ${signal}; saved session data was preserved`),
    );
    const onSigint = () => interrupt('SIGINT');
    const onSigterm = () => interrupt('SIGTERM');
    process.once('SIGINT', onSigint);
    process.once('SIGTERM', onSigterm);
    process.stderr.write(`Ask UI ready at ${url}\n`);
    process.stderr.write(`ask-ui-session: ${created.sessionId}\n`);
    process.stderr.write(`Waiting for round ${created.roundNumber} submission; data is saved under ${dataRoot}\n`);
    // 这条命令会阻塞到用户提交为止，很容易被 harness 转到后台。一旦转后台，
    // 任务输出里 stdout 和 stderr 是混在一起的，直接 JSON.parse 必然失败。
    process.stderr.write(`If this command is backgrounded or interrupted, do not parse the task output; run: ask-ui.mjs resume --session ${created.sessionId}\n`);
    // 页面在提交后自行关闭，所以每一轮都要重新打开浏览器。
    if (!args['no-open']) openBrowser(url);
    try {
      await waitForRoundSubmission(
        dataRoot,
        created.sessionId,
        created.roundNumber,
        abortController.signal,
      );
      // 转后台时 stdout 会和 stderr 混在一起，这行是「结果已就绪」的唯一可靠信号。
      process.stderr.write(`ask-ui-submitted: ${created.sessionId} round ${created.roundNumber}\n`);
      print(await submittedRoundResult(dataRoot, created.sessionId, created.roundNumber));
    } finally {
      process.removeListener('SIGINT', onSigint);
      process.removeListener('SIGTERM', onSigterm);
    }
    return;
  }

  if (command === 'create') {
    const created = await createRound(await readInput(args.input), {
      dataDir: dataRoot,
      cwd: process.cwd(),
      deliveryMode: 'manual',
    });
    if (args['no-serve']) {
      print({ ...created, session: undefined });
      return;
    }
    const server = await ensureServer(dataRoot);
    const url = `http://127.0.0.1:${server.port}/session/${encodeURIComponent(created.sessionId)}?token=${encodeURIComponent(server.token)}`;
    if (!args['no-open']) openBrowser(url);
    print({
      status: 'created',
      sessionId: created.sessionId,
      roundNumber: created.roundNumber,
      dataRoot,
      questionsPath: created.questionsPath,
      url,
      marker: `ask-ui-session: ${created.sessionId}`,
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
    print(await resumeRound(dataRoot, args.session || null));
    return;
  }

  if (command === 'status') {
    if (!args.session) throw new Error('--session is required');
    print(await loadSessionBundle(dataRoot, args.session));
    return;
  }

  if (command === 'complete' || command === 'cancel') {
    if (!args.session) throw new Error('--session is required');
    const completed = await completeSession(
      dataRoot,
      args.session,
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
