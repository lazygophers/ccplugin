// 数据规范化: skein API 字段名/状态 → 前端统一形状

const STATUS_MAP: Record<string, string> = {
  '待处理': 'planning', '规划中': 'planning', 'pending': 'planning', 'plan': 'planning',
  '调研中': 'research', 'research': 'research',
  '进行中': 'active', '运行中': 'active', '执行中': 'active', 'active': 'active', 'exec': 'active',
  '检查中': 'check', '验收中': 'check', '待验收': 'check', 'check': 'check',
  '收尾中': 'finishing', 'finishing': 'finishing',
  '已完成': 'done', '完成': 'done', 'done': 'done',
  '失败': 'failed', '已失败': 'failed', 'failed': 'failed',
  '已取消': 'cancelled',
  '已归档': 'archived',
};

export function normalizeStatus(s: string): string { return STATUS_MAP[s] || s; }

// 优先级: 四档枚举 (机器值 urgent/high/normal/low, 展示层映射中文) — 与 skeinlib/model.py PRIORITIES 对齐
export const PRIORITIES = ["urgent", "high", "normal", "low"] as const;
export const PRIORITY_LABEL: Record<string, string> = { urgent: "紧急", high: "高", normal: "中", low: "低" };
export const PRIORITY_COLOR_VAR: Record<string, string> = { urgent: "--pri-urgent", high: "--pri-high", normal: "--pri-normal", low: "--pri-low" };
export const PRIORITY_RANK: Record<string, number> = { urgent: 3, high: 2, normal: 1, low: 0 };

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
  priority: string;
  createdAt: number | null;
  confirmedAt: number | null;
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
    stage: (t.stage || (status === 'planning' ? 'plan' : status === 'active' ? 'exec' : status === 'check' ? 'check' : 'done')) as string,
    deps: (t.deps || []) as string[],
    subtasks: ((t.subtasks || t.subtable || []) as Record<string, unknown>[]).map(normalizeSubtask),
    contracts: (t.contracts || []) as { id: string; desc?: string }[],
    // 真实值优先, 仅缺字段/非四档合法值 (如未迁移的存量数字) 时落中档兜底, 防选择器渲染出不存在的档位
    priority: PRIORITIES.includes(t.priority as typeof PRIORITIES[number]) ? (t.priority as string) : 'normal',
    kind: (t.kind || 'task') as string,
    parent: (t.parent || null) as string | null,
    createdAt: createdTs,
    confirmedAt: (t.confirmedAt || (t.confirmed ? (t.confirmed as number) * 1000 : null)) as number | null,
    startedAt: startedTs,
    finishedAt: finishedTs,
    checkedAt: (t.checkedAt || (t.checked ? (t.checked as number) * 1000 : null)) as number | null,
  } as NormTask;
}

export function normalizeTasks(list: Record<string, unknown>[]): NormTask[] {
  return (list || []).map(normalizeTask);
}

// task-changed 消息 (来自 live.ts) → 新卡片集: 纯函数, 输入当前卡片集 + 一条消息, 输出新卡片集。
// card 有值 = 该 task 新建或更新 (id 已在集合中就替换, 否则追加); card 为空 = 该 task 已消失 (归档/删除), 移除。
// extra: 覆盖不来自后端 card 的展示态字段 (如 board/page.tsx 附加的 maxActive), 与 msg.card 合并后再 normalize。
export function applyTaskChanged(
  tasks: NormTask[],
  msg: { id: string; card: Record<string, unknown> | null },
  extra: Record<string, unknown> = {}
): NormTask[] {
  if (!msg.card) return tasks.filter(t => t.id !== msg.id);
  const next = normalizeTask({ ...msg.card, ...extra });
  const idx = tasks.findIndex(t => t.id === msg.id);
  if (idx === -1) return [...tasks, next];
  const copy = tasks.slice();
  copy[idx] = next;
  return copy;
}

// 批量抗抖: 同一轮攒到一起的多条 task-changed 消息一次性折叠成一次卡片集变化,
// 避免每条消息各自触发一次重排 (布局计算随 task 数增长, 大量消息连发时逐条重排会卡死)。
// 纯函数, 语义等价于依次调用 applyTaskChanged, 仅合并成一次输出。
export function applyTaskChangedBatch(
  tasks: NormTask[],
  msgs: { id: string; card: Record<string, unknown> | null }[],
  extra: Record<string, unknown> = {}
): NormTask[] {
  return msgs.reduce((acc, msg) => applyTaskChanged(acc, msg, extra), tasks);
}
