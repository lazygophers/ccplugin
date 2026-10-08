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

import { normalizeQuestionSet, type Question, type QuestionSet, type WakeBinding } from './questionset.mjs';
import { validateAnswers, type NormalizedAnswer } from './answers.mjs';
import { validateAgainstSchema, formatSchemaErrors } from './schema-validator.mjs';

const SCHEMA_VERSION = '1.0';

// HTTP 出口用 error.statusCode 回状态码，这里补上字段声明，路由层不用再断言。
declare global {
  interface Error {
    statusCode?: number;
  }
}

export type AskStatus = 'waiting_for_user' | 'submitted' | 'completed' | 'cancelled';
export type DeliveryMode = 'direct' | 'manual';

export interface Ask {
  schemaVersion: string;
  askId: string;
  projectName?: string;
  title: string;
  summary?: string;
  background?: string;
  purpose?: string;
  status: AskStatus;
  deliveryMode: DeliveryMode;
  workspace?: string;
  wake?: WakeBinding | null;
  createdAt: string;
  updatedAt: string;
  questionCount?: number;
  submittedAt?: string;
  completedAt?: string;
  wakeState?: Record<string, unknown>;
}

export interface StoredQuestionSet {
  schemaVersion: string;
  askId: string;
  title: string;
  purpose: string;
  createdAt: string;
  questions: Question[];
}

export interface AnswerSet {
  schemaVersion: string;
  submissionId: string;
  askId: string;
  submittedAt: string;
  answers: NormalizedAnswer[];
  hiddenQuestionIds: string[];
}

export interface CreateAskResult {
  status: 'created';
  dataRoot: string;
  askId: string;
  questionsPath: string;
  ask: Ask;
}

export interface AskBundle {
  schemaVersion: string;
  ask: Ask;
  questions: StoredQuestionSet;
  answers: AnswerSet | null;
  draft: { answers?: unknown } | null;
}

export function now(): string {
  return new Date().toISOString();
}

// sessionId 会成为文件系统路径的一段，必须挡住 . / .. / 分隔符。
export function assertSafeId(value: string, label = 'id'): string {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]{2,127}$/.test(value || '')) {
    throw new Error(`${label} must contain 3-128 safe characters`);
  }
  return value;
}

export function makeAskId(): string {
  // 12 hex characters are random bytes, not a standard UUID.
  return randomBytes(6).toString('hex');
}

export function askDirectory(dataRoot: string, askId: string): string {
  return path.join(dataRoot, 'asks', assertSafeId(askId, 'askId'));
}

export async function readJson<T = any>(file: string, fallback?: T | null): Promise<T> {
  try {
    return JSON.parse(await fs.readFile(file, 'utf8')) as T;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT' && fallback !== undefined) return fallback as T;
    if (error instanceof SyntaxError) {
      // 带上原始报错的位置信息，写坏 JSON 的调用方才能一次改对，不用二分找。
      throw new Error(`Invalid JSON in ${file}: ${error.message}`);
    }
    throw error;
  }
}

export async function atomicWriteJson(file: string, value: unknown): Promise<void> {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const temporary = `${file}.${process.pid}.${randomBytes(4).toString('hex')}.tmp`;
  await fs.writeFile(temporary, `${JSON.stringify(value)}\n`, 'utf8');
  try {
    await fs.rename(temporary, file);
  } catch (error) {
    if (!['EEXIST', 'EPERM'].includes((error as NodeJS.ErrnoException).code || '')) throw error;
    await fs.copyFile(temporary, file);
    await fs.rm(temporary, { force: true });
  }
}

export async function ensureDataRoot(requested?: string, cwd = process.cwd()): Promise<string> {
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

export async function readAsk(dataRoot: string, askId: string): Promise<Ask> {
  return readJson<Ask>(path.join(askDirectory(dataRoot, askId), 'ask.json'));
}

export async function writeAsk(dataRoot: string, ask: Ask): Promise<Ask> {
  ask.updatedAt = now();
  await atomicWriteJson(path.join(askDirectory(dataRoot, ask.askId), 'ask.json'), ask);
  return ask;
}

interface AskIndex {
  schemaVersion: string;
  asks?: { askId: string; title: string; status: AskStatus; updatedAt: string }[];
  updatedAt?: string;
  [key: string]: unknown;
}

export async function updateIndex(dataRoot: string, ask: Ask, extra: Record<string, unknown> = {}): Promise<void> {
  const indexFile = path.join(dataRoot, 'index.json');
  // 旧版 index.json 里只有 sessions 数组；asks 缺失时补一个空数组，旧条目原样保留。
  const index = await readJson<AskIndex>(indexFile, null) || { schemaVersion: SCHEMA_VERSION };
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

export interface CreateAskOptions {
  dataDir?: string;
  cwd?: string;
  deliveryMode?: DeliveryMode;
}

export async function createAsk(input: unknown, options: CreateAskOptions = {}): Promise<CreateAskResult> {
  const cwd = options.cwd || process.cwd();
  const dataRoot = await ensureDataRoot(options.dataDir, cwd);
  const deliveryMode = options.deliveryMode || 'manual';
  if (!['direct', 'manual'].includes(deliveryMode)) {
    throw new Error('deliveryMode must be direct or manual');
  }
  const questionSet: QuestionSet = normalizeQuestionSet(input, { cwd });
  const askId = makeAskId();
  const directory = askDirectory(dataRoot, askId);
  await fs.mkdir(path.dirname(directory), { recursive: true });
  await fs.mkdir(directory);

  const storedQuestionSet: StoredQuestionSet = {
    schemaVersion: SCHEMA_VERSION,
    askId,
    title: questionSet.title,
    purpose: questionSet.purpose,
    createdAt: now(),
    questions: questionSet.questions,
  };
  await atomicWriteJson(path.join(directory, 'questions.json'), storedQuestionSet);

  const ask: Ask = {
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

export async function submittedAskResult(dataRoot: string, askId: string) {
  const directory = askDirectory(dataRoot, askId);
  const ask = await readAsk(dataRoot, askId);
  if (ask.status !== 'submitted') {
    throw new Error(`Ask ${askId} has not been submitted`);
  }
  return {
    status: 'submitted' as const,
    askId,
    title: ask.title,
    questionsPath: path.join(directory, 'questions.json'),
    answersPath: path.join(directory, 'answers.json'),
    questions: await readJson<StoredQuestionSet>(path.join(directory, 'questions.json')),
    answers: await readJson<AnswerSet>(path.join(directory, 'answers.json')),
  };
}

export async function loadAskBundle(dataRoot: string, askId: string): Promise<AskBundle> {
  const directory = askDirectory(dataRoot, askId);
  const ask = await readAsk(dataRoot, askId);
  return {
    schemaVersion: SCHEMA_VERSION,
    ask,
    questions: await readJson<StoredQuestionSet>(path.join(directory, 'questions.json')),
    answers: await readJson<AnswerSet | null>(path.join(directory, 'answers.json'), null),
    draft: await readJson<AskBundle['draft']>(path.join(directory, 'draft.json'), null),
  };
}

// 填到一半的答案每改一下就落盘：关页、刷新、换浏览器、服务重启都接得回来。
// 不校验必填、不校验选项——草稿本来就是半成品，校验留给提交那一步。
export async function saveDraft(dataRoot: string, askId: string, payload: { answers?: unknown }) {
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

export async function submitAnswers(dataRoot: string, askId: string, payload: { submissionId?: unknown; answers?: unknown }) {
  const directory = askDirectory(dataRoot, askId);
  const ask = await readAsk(dataRoot, askId);
  const existing = await readJson<AnswerSet | null>(path.join(directory, 'answers.json'), null);
  if (existing) {
    return { duplicate: true as const, answerSet: existing, ask };
  }
  if (ask.status !== 'waiting_for_user') throw new Error('Ask is not accepting answers');

  const questions = await readJson<StoredQuestionSet>(path.join(directory, 'questions.json'));
  const validated = validateAnswers(questions, payload.answers);
  if (validated.errors.length) {
    const error = new Error(validated.errors.join('; '));
    error.statusCode = 422;
    throw error;
  }
  const answerSet: AnswerSet = {
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
  return { duplicate: false as const, answerSet, ask };
}

async function listAsks(dataRoot: string): Promise<Ask[]> {
  const asksRoot = path.join(dataRoot, 'asks');
  let entries: import('node:fs').Dirent[];
  try {
    entries = await fs.readdir(asksRoot, { withFileTypes: true });
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return [];
    throw error;
  }
  const asks: Ask[] = [];
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

export type ResumeResult =
  | { status: 'waiting'; askId: string | null }
  | { status: 'ambiguous'; candidates: { askId: string; title: string; summary?: string; workspace?: string; submittedAt?: string }[] }
  | Awaited<ReturnType<typeof submittedAskResult>>;

export async function resumeAsk(dataRoot: string, requestedAskId: string | null = null): Promise<ResumeResult> {
  let candidates: Ask[] = [];
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
    String(right.submittedAt).localeCompare(String(left.submittedAt)))[0];
  return submittedAskResult(dataRoot, latest.askId);
}

export async function completeAsk(dataRoot: string, askId: string, status: 'completed' | 'cancelled' = 'completed'): Promise<Ask> {
  const ask = await readAsk(dataRoot, askId);
  if (!['completed', 'cancelled'].includes(status)) throw new Error('Invalid final status');
  // waiting_for_user 也允许收尾：问错了、任务取消时，没人答的表单同样要作废。
  ask.status = status;
  ask.completedAt = now();
  await writeAsk(dataRoot, ask);
  // 调用方必须先读完答案，再到这里清掉本次提问；只删自己的 ask 目录。
  await fs.rm(askDirectory(dataRoot, askId), { recursive: true, force: true });
  const index = await readJson<AskIndex>(path.join(dataRoot, 'index.json'), { schemaVersion: SCHEMA_VERSION });
  if (Array.isArray(index.asks)) index.asks = index.asks.filter((entry) => entry.askId !== askId);
  for (const key of ['activeAskId', 'lastSubmittedAskId']) {
    if (index[key] === askId) index[key] = null;
  }
  await atomicWriteJson(path.join(dataRoot, 'index.json'), { ...index, updatedAt: now() });
  return ask;
}

export async function hasPendingAsk(dataRoot: string): Promise<boolean> {
  const index = await readJson<AskIndex | null>(path.join(dataRoot, 'index.json'), null);
  if (!index?.asks?.length) return false;
  for (const entry of index.asks) {
    const ask = await readJson<Ask | null>(
      path.join(dataRoot, 'asks', entry.askId, 'ask.json'),
      null,
    );
    if (ask?.status === 'waiting_for_user') return true;
  }
  return false;
}
