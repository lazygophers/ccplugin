// 数据规范化: skein API 字段名/状态 → 前端统一形状

const STATUS_MAP: Record<string, string> = {
  '待处理': 'planning', '规划中': 'planning', 'pending': 'planning', 'plan': 'planning',
  '就绪': 'ready', '待执行': 'ready', 'ready': 'ready',
  '进行中': 'active', '运行中': 'active', '执行中': 'active', 'active': 'active', 'exec': 'active',
  '检查中': 'check', '验收中': 'check', '待验收': 'check', 'check': 'check',
  '已完成': 'done', '完成': 'done', 'done': 'done',
  '失败': 'failed', '已失败': 'failed', 'failed': 'failed',
  '已取消': 'cancelled',
  '已归档': 'archived',
};

export function normalizeStatus(s: string): string { return STATUS_MAP[s] || s; }

export interface NormSubtask {
  sid: string;
  id: string;
  name: string;
  title: string;
  desc: string;
  status: string;
  dependsOn: string[];
  deps: string[];
  progress: number | null;
  estimate: number | null;
  skills: string[];
  startedAt: number | null;
  finishedAt: number | null;
  [key: string]: unknown;
}

export interface NormTask {
  id: string;
  name: string;
  title: string;
  description: string;
  desc: string;
  status: string;
  stage: string;
  deps: string[];
  subtasks: NormSubtask[];
  contracts: { id: string; desc?: string }[];
  kind: string;
  parent: string | null;
  createdAt: number | null;
  startedAt: number | null;
  finishedAt: number | null;
  checkedAt: number | null;
  [key: string]: unknown;
}

export function normalizeSubtask(s: Record<string, unknown>): NormSubtask {
  const statusRaw = (s.status || s.st || 'pending') as string;
  const status = STATUS_MAP[statusRaw] || statusRaw;
  return {
    ...s,
    sid: (s.sid || s.id) as string,
    id: (s.sid || s.id) as string,
    title: (s.title || s.name || '') as string,
    name: (s.title || s.name || '') as string,
    description: (s.description || s.desc || '') as string,
    desc: (s.description || s.desc || '') as string,
    status,
    dependsOn: (s.dependsOn || s.depends_on || s.deps || []) as string[],
    deps: (s.dependsOn || s.depends_on || s.deps || []) as string[],
    progress: (s.pct != null ? s.pct : s.progress != null ? s.progress : null) as number | null,
    estimate: (s.estimate != null ? Number(s.estimate) : null) as number | null,
    skills: (s.skills || []) as string[],
    startedAt: (s.started ? (s.started as number) * 1000 : null) as number | null,
    finishedAt: (s.finished ? (s.finished as number) * 1000 : null) as number | null,
  } as NormSubtask;
}

export function normalizeTask(t: Record<string, unknown>): NormTask {
  if (!t) return t as never;
  const statusRaw = (t.status || t.st || 'pending') as string;
  const status = STATUS_MAP[statusRaw] || statusRaw;
  const createdTs = (t.createdAt || (t.created ? (t.created as number) * 1000 : null)) as number | null;
  const startedTs = (t.startedAt || (t.started ? (t.started as number) * 1000 : null)) as number | null;
  const finishedTs = (t.completedAt || t.finishedAt || (t.finished ? (t.finished as number) * 1000 : null)) as number | null;

  return {
    ...t,
    id: t.id as string,
    title: (t.title || t.name || '') as string,
    name: (t.title || t.name || '') as string,
    description: (t.description || t.desc || '') as string,
    desc: (t.description || t.desc || '') as string,
    status,
    stage: (t.stage || (status === 'planning' ? 'plan' : status === 'ready' ? 'ready' : status === 'active' ? 'exec' : status === 'check' ? 'check' : 'done')) as string,
    deps: (t.deps || []) as string[],
    subtasks: ((t.subtasks || t.subtable || []) as Record<string, unknown>[]).map(normalizeSubtask),
    contracts: (t.contracts || []) as { id: string; desc?: string }[],
    kind: (t.kind || 'task') as string,
    parent: (t.parent || null) as string | null,
    createdAt: createdTs,
    startedAt: startedTs,
    finishedAt: finishedTs,
    checkedAt: (t.checkedAt || (t.checked ? (t.checked as number) * 1000 : null)) as number | null,
  } as NormTask;
}

export function normalizeTasks(list: Record<string, unknown>[]): NormTask[] {
  return (list || []).map(normalizeTask);
}
