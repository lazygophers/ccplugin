// wake module 的测试：manual 模式直接返回、缺 sessionRef 记 unavailable。
import assert from 'node:assert/strict';
import path from 'node:path';

import { triggerWake } from './wake.mjs';
import { createAsk, loadAskBundle } from './store.mjs';
import { makeTempRoot } from './test-helpers.mjs';

export async function test() {
  const temporaryRoot = await makeTempRoot('wake');
  const dataRoot = path.join(temporaryRoot, 'data');
  try {
    const manual = await createAsk({
      title: '手动模式',
      wake: { mode: 'manual' },
      questions: [{ id: 'q1', type: 'text', text: '甲' }],
    }, { dataDir: dataRoot, cwd: temporaryRoot });
    assert.deepEqual(await triggerWake(dataRoot, manual.askId), { status: 'manual' });
    assert.equal(
      (await loadAskBundle(dataRoot, manual.askId)).ask.wakeState,
      undefined,
      'manual 模式不该写 wakeState',
    );

    // auto 但缺 sessionRef：记 unavailable，不碰任何 adapter。
    const unavailable = await createAsk({
      title: '缺会话引用',
      wake: { mode: 'auto', provider: 'claude-code' },
      questions: [{ id: 'q1', type: 'text', text: '甲' }],
    }, { dataDir: dataRoot, cwd: temporaryRoot });
    assert.deepEqual(await triggerWake(dataRoot, unavailable.askId), { status: 'unavailable' });
    assert.equal((await loadAskBundle(dataRoot, unavailable.askId)).ask.wakeState.status, 'unavailable');
  } finally {
    const fs = await import('node:fs/promises');
    await fs.rm(temporaryRoot, { recursive: true, force: true });
  }
}
