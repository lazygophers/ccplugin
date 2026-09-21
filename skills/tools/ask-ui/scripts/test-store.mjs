// store module 的测试：createAsk 落盘、title/推荐徽标归一、resume/complete、
// 重复提交、hasPendingAsk 生命周期。
import assert from 'node:assert/strict';
import path from 'node:path';

import {
  completeAsk,
  createAsk,
  hasPendingAsk,
  loadAskBundle,
  resumeAsk,
  saveDraft,
  submitAnswers,
} from './store.mjs';
import { makeTempRoot } from './test-helpers.mjs';

export async function test() {
  const temporaryRoot = await makeTempRoot('store');
  const dataRoot = path.join(temporaryRoot, 'data');
  try {
    const first = await createAsk({
      title: '个人工作台需求确认收集',
      questions: [
        {
          id: 'scope',
          type: 'single',
          title: '优先范围',
          text: '## 优先范围\n\n先做**个人**还是**团队**？',
          options: [
            { id: 'personal', text: '个人工作台', recommended: true, reason: '先覆盖高频场景。' },
            { id: 'team', text: '团队工作台' },
          ],
        },
        {
          id: 'modules',
          type: 'multiple',
          text: '首批模块',
          options: [
            { id: 'tasks', text: '任务', recommended: true, reason: '主入口。' },
            { id: 'notes', text: '笔记', recommended: true, reason: '沉淀上下文。' },
            { id: 'calendar', text: '日历' },
          ],
        },
        {
          id: 'context',
          type: 'text',
          text: '补充背景',
          required: false,
          recommendedDraft: '先做本地 Demo。',
        },
        {
          id: 'channel',
          type: 'single',
          text: '提醒渠道',
          options: [
            { id: 'email', text: '邮件' },
            { id: 'chat', text: '即时消息' },
          ],
        },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot });

    // title 缺省时取正文首个非空行，左栏导航才有短标签可用。
    {
      const stored = (await loadAskBundle(dataRoot, first.askId)).questions.questions;
      assert.equal(stored[0].title, '优先范围', '显式 title 必须原样保留');
      assert.equal(stored[1].title, '首批模块', 'title 缺省应取 text 首个非空行');
      // 单选最多一个推荐项：两个「推荐」徽标会让用户不知道照哪个。
      assert.equal(stored[0].options.filter((option) => option.recommended).length, 1);
      assert.equal(stored[1].options.filter((option) => option.recommended).length, 2);
    }

    // q1、mr 这类短 id 只是 JSON 内部的引用键，不进文件路径，必须放行。
    const shortIds = await createAsk({
      title: '短 id 合法',
      questions: [
        {
          id: 'q1',
          type: 'single',
          text: '交付到哪一步',
          required: true,
          options: [{ id: 'mr', text: '开 MR' }, { id: 'commit', text: '只 commit' }],
        },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot });
    assert.match(shortIds.askId, /^[a-z0-9-]+$/, 'askId 由 CLI 生成');

    // 草稿：填到一半就落盘，不校验半成品。
    const draft = await saveDraft(dataRoot, first.askId, {
      answers: [{ questionId: 'scope', selectedOptionIds: ['personal'], customText: '' }],
    });
    assert.ok(draft.updatedAt, '草稿要落成 draft.json');

    // 提交：重复提交同一份答案只落一次盘。
    const answers = [
      {
        questionId: 'scope',
        selectedOptionIds: ['personal'],
        customText: '',
        supplementaryText: '先覆盖个人高频场景。',
      },
      { questionId: 'modules', selectedOptionIds: ['tasks', 'notes'], customText: '' },
      { questionId: 'context', selectedOptionIds: [], customText: '先做本地 Demo。' },
      { questionId: 'channel', selectedOptionIds: ['email'], customText: '', supplementaryText: '工作日才提醒。' },
    ];
    const submitted = await submitAnswers(dataRoot, first.askId, { submissionId: 'store-test', answers });
    assert.equal(submitted.duplicate, false);
    const duplicate = await submitAnswers(dataRoot, first.askId, { submissionId: 'store-test', answers });
    assert.equal(duplicate.duplicate, true, 'answers.json 已存在时重复提交应返回 duplicate');

    // resume 按提交时间取最新。
    const resumed = await resumeAsk(dataRoot, first.askId);
    assert.equal(resumed.status, 'submitted');
    assert.equal(resumed.askId, first.askId);
    assert.equal(resumed.answers.answers[0].supplementaryText, '先覆盖个人高频场景。');

    // 后续追问是独立的一次新提问：各自有自己的 id，互不干扰。
    const followUp = await createAsk({
      title: '个人工作台细节确认',
      questions: [
        {
          id: 'layout',
          type: 'single',
          text: '布局方式',
          options: [
            { id: 'board', text: '看板', recommended: true, reason: '信息密度更高。' },
            { id: 'list', text: '列表' },
          ],
        },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot });
    assert.notEqual(followUp.askId, first.askId);

    const completed = await completeAsk(dataRoot, first.askId);
    assert.equal(completed.status, 'completed');
    assert.equal((await loadAskBundle(dataRoot, followUp.askId)).ask.status, 'waiting_for_user');

    // 常驻服务必须有终点：还有人没答完就继续跑，最后一个会话结束就收摊。
    const idleRoot = path.join(temporaryRoot, 'idle-data');
    const askA = await createAsk({
      title: '甲提问',
      questions: [{ id: 'q1', type: 'text', text: '甲' }],
    }, { dataDir: idleRoot, cwd: temporaryRoot });
    const askB = await createAsk({
      title: '乙提问',
      questions: [{ id: 'q1', type: 'text', text: '乙' }],
    }, { dataDir: idleRoot, cwd: temporaryRoot });

    assert.equal(await hasPendingAsk(idleRoot), true, '两次提问都在等答，应判定为有人未答');

    await completeAsk(idleRoot, askA.askId, 'completed');
    assert.equal(await hasPendingAsk(idleRoot), true, '乙提问还在等，服务不该收摊');

    await completeAsk(idleRoot, askB.askId, 'completed');
    assert.equal(await hasPendingAsk(idleRoot), false, '提问都结束了，服务该收摊');
  } finally {
    const fs = await import('node:fs/promises');
    await fs.rm(temporaryRoot, { recursive: true, force: true });
  }
}
