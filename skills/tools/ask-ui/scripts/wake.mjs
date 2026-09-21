// 主动唤醒 module：提交后把「答案已就绪」投回宿主（Claude Code / Codex App Server）。
// provider 差异在 adapters/ 里，这里只管：挑 adapter、落 wake 状态、留日志文件。
import fs from 'node:fs/promises';
import path from 'node:path';

import { wakeClaudeCode } from './adapters/claude-code.mjs';
import { wakeCodexAppServer } from './adapters/codex-app-server.mjs';
import { askDirectory, atomicWriteJson, now, readAsk, updateIndex, writeAsk } from './store.mjs';

async function recordWakeState(dataRoot, askId, value) {
  const ask = await readAsk(dataRoot, askId);
  ask.wakeState = { ...(ask.wakeState || {}), ...value, updatedAt: now() };
  await writeAsk(dataRoot, ask);
  await updateIndex(dataRoot, ask);
}

export async function triggerWake(dataRoot, askId) {
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

export { recordWakeState };
