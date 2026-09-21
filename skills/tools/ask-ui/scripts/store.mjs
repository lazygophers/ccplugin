// 落盘 module：ask 的全部 IO 都在这里——目录、index、questions.json / answers.json /
// draft.json / ask.json 的读写。answerSet 落盘前按 references/answerset.schema.json
// 校验，Agent 照那份契约读答案，写侧漂移当场暴露。
import {
  constants as fsConstants,
  existsSync,
} from 'node:fs';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { createHash, randomBytes, randomUUID } from 'node:crypto';

import { normalizeQuestionSet } from './questionset.mjs';
import { validateAnswers } from './answers.mjs';
import { validateAgainstSchema, formatSchemaErrors } from './schema-validator.mjs';

const SCHEMA_VERSION = '1.0';

export function now() {
  return new Date().toISOString();
}

// sessionId 会成为文件系统路径的一段，必须挡住 . / .. / 分隔符。
export function assertSafeId(value, label = 'id') {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]{2,127}$/.test(value || '')) {
    throw new Error(`${label} must contain 3-128 safe characters`);
  }
  return value;
}

export function makeAskId(title = 'ask-ui') {
  const slug = String(title)
    .normalize('NFKD')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toLowerCase()
    .slice(0, 36) || 'ask-ui';
  const stamp = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 14);
  return `${slug}-${stamp}-${randomBytes(2).toString('hex')}`;
}

export function askDirectory(dataRoot, askId) {
  return path.join(dataRoot, 'asks', assertSafeId(askId, 'askId'));
}

export async function readJson(file, fallback = undefined) {
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

export async function atomicWriteJson(file, value) {
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

export async function ensureDataRoot(requested, cwd = process.cwd()) {
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

export async function readAsk(dataRoot, askId) {
  return readJson(path.join(askDirectory(dataRoot, askId), 'ask.json'));
}

export async function writeAsk(dataRoot, ask) {
  ask.updatedAt = now();
  await atomicWriteJson(path.join(askDirectory(dataRoot, ask.askId), 'ask.json'), ask);
  return ask;
}

export async function updateIndex(dataRoot, ask, extra = {}) {
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

export async function loadAskBundle(dataRoot, askId) {
  const directory = askDirectory(dataRoot, askId);
  const ask = await readAsk(dataRoot, askId);
  return {
    schemaVersion: SCHEMA_VERSION,
    ask,
    questions: await readJson(path.join(directory, 'questions.json')),
    answers: await readJson(path.join(directory, 'answers.json'), null),
    draft: await readJson(path.join(directory, 'draft.json'), null),
  };
}

// 填到一半的答案每改一下就落盘：关页、刷新、换浏览器、服务重启都接得回来。
// 不校验必填、不校验选项——草稿本来就是半成品，校验留给提交那一步。
export async function saveDraft(dataRoot, askId, payload) {
  const directory = askDirectory(dataRoot, askId);
  const ask = await readAsk(dataRoot, askId);
  if (ask.status !== 'waiting_for_user') throw new Error('Ask is not accepting answers');
  const draft = {
    schemaVersion: SCHEMA_VERSION,
    askId,
    updatedAt: now(),
    answers: Array.isArray(payload?.answers) ? payload.answers : [],
  };
  await atomicWriteJson(path.join(directory, 'draft.json'), draft);
  return draft;
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
  // Agent 照 references/answerset.schema.json 读答案，落盘前按同一份校验，
  // 写侧偏离契约当场抛错，不留静默漂移。
  const schemaVerdict = validateAgainstSchema(
    answerSet,
    JSON.parse(await fs.readFile(new URL('../references/answerset.schema.json', import.meta.url), 'utf8')),
  );
  if (!schemaVerdict.valid) {
    throw new Error(`answers.json 不符合 AnswerSet schema（写侧漂移）：\n${formatSchemaErrors(schemaVerdict.errors)}`);
  }
  await atomicWriteJson(path.join(directory, 'answers.json'), answerSet);
  await fs.rm(path.join(directory, 'draft.json'), { force: true });
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
