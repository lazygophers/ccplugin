// ---- 数据规范化: skein API 字段名/状态 → 前端统一形状 ----
//
// 纯适配, 无 DOM 无副作用。单独成文件的理由同 eta.js: app.js 一被 import 就自启动, 这些函数
// 在浏览器外没法验证 —— 而 ETA 的正确性恰恰依赖状态映射对不对 (中文态没映上, OWN_LEFT 就走
// 兜底系数, 数字会静静地偏)。
//
// 字段兼容: 各端点的同一份数据键名不一 (subtable/subtasks、spct/progress、checked/checkedAt),
// 全部在这里抹平, 上层只认规范化后的形状。

// ---- 任务数据规范化: 统一 skein API 的字段名和状态 ----
// 5 状态系统: planning(规划中) / ready(待执行) / active(执行中) / check(验收中) / done(已完成)
const STATUS_MAP = {
  '待处理': 'planning', '规划中': 'planning', 'pending': 'planning', 'plan': 'planning',
  '就绪': 'ready', '待执行': 'ready', 'ready': 'ready',
  '进行中': 'active', '运行中': 'active', '执行中': 'active', 'active': 'active', 'exec': 'active',  // 运行中 = SS_RUNNING (subtask 级)
  '检查中': 'check', '验收中': 'check', '待验收': 'check', 'check': 'check',
  '已完成': 'done', '完成': 'done', 'done': 'done',
  '失败': 'failed', '已失败': 'failed', 'failed': 'failed',
  '已取消': 'cancelled',
  '已归档': 'archived',
};

// 中文/英文状态 → 5 状态系统 (统计类接口只回状态计数时用)
export function normalizeStatus(s) { return STATUS_MAP[s] || s; }

export function normalizeTask(t) {
  if (!t) return t;
  const statusRaw = t.status || t.st || 'pending';
  const status = STATUS_MAP[statusRaw] || statusRaw;
  const createdTs = t.createdAt || (t.created ? t.created * 1000 : null);
  const startedTs = t.startedAt || (t.started ? t.started * 1000 : null);
  const finishedTs = t.completedAt || t.finishedAt || (t.finished ? t.finished * 1000 : null);
  const updatedTs = t.updatedAt || (t.updated ? t.updated * 1000 : finishedTs || createdTs);
  return {
    ...t,
    id: t.id,
    title: t.title || t.name || '',
    name: t.title || t.name || '',
    description: t.description || t.desc || '',
    desc: t.description || t.desc || '',
    status,
    stage: t.stage || (status === 'planning' ? 'plan' : status === 'ready' ? 'ready' : status === 'active' ? 'exec' : status === 'check' ? 'check' : 'done'),
    priority: t.priority != null ? Number(t.priority) : (t.prio != null ? Number(t.prio) : 5),
    createdAt: createdTs,
    startedAt: startedTs,
    updatedAt: updatedTs,
    completedAt: finishedTs,
    finishedAt: finishedTs,
    checkedAt: t.checkedAt || (t.checked ? t.checked * 1000 : null),
    deps: t.deps || [],
    depNames: t.depNames || [],
    assignee: t.assignee || t.owner || '',
    estimate: t.estimate || t.est || null,
    progress: t.progress != null ? t.progress : (t.spct != null ? t.spct : t.sdone != null && t.stotal ? Math.round(t.sdone / t.stotal * 100) : null),
    subtasks: (t.subtasks || t.subtable || []).map(s => normalizeSubtask(s)),
    subNodes: t.subNodes || null,
    contracts: t.contracts || [],
    prd: t.prd || null,
    docs: t.docs || null,
    parent: t.parent || null,
    kind: t.kind || 'task',
  };
}

function normalizeSubtask(s) {
  if (!s) return s;
  const statusRaw = s.status || s.st || 'pending';
  const status = STATUS_MAP[statusRaw] || statusRaw;
  return {
    ...s,
    sid: s.sid || s.id,
    id: s.sid || s.id,
    title: s.title || s.name || '',
    name: s.title || s.name || '',
    description: s.description || s.desc || '',
    desc: s.description || s.desc || '',
    status,
    dependsOn: s.dependsOn || s.depends_on || s.deps || [],
    deps: s.dependsOn || s.depends_on || s.deps || [],
    depNames: s.depNames || [],
    progress: s.pct != null ? s.pct : s.progress,
    estimate: s.estimate != null ? Number(s.estimate) : null,
    skills: s.skills || [],
    acc: s.acc || [],
    createdAt: s.created ? s.created * 1000 : null,
    startedAt: s.started ? s.started * 1000 : null,
    finishedAt: s.finished ? s.finished * 1000 : null,
  };
}

export function normalizeTasks(list) {
  return (list || []).map(normalizeTask);
}
