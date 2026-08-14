// SKEIN webapp API 层 — fetch 封装 + 各 endpoint 签名
// 对齐 FastAPI backend: /__skein__/*
// 所有业务端点 POST-only; GET 仅限基础设施 (id/rev 探测, 前端 WS bootstrap 用)

const BASE = "/__skein__";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, { cache: "no-store", ...opts });
  } catch {
    throw new ApiError(0, "无法连接 skein serve — 需经 http 访问 (skein serve)");
  }
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try { const j = await res.json(); if (j?.error) msg = j.error; } catch {}
    throw new ApiError(res.status, msg);
  }
  const ct = res.headers.get("content-type") || "";
  return (ct.includes("application/json") ? res.json() : res.text()) as Promise<T>;
}

function getText(path: string): Promise<string> { return req<string>(path); }
function postJSON<T>(path: string, body?: unknown): Promise<T> {
  return req<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
}

export interface CliResult { ok: boolean; exit?: number; stdout?: string; stderr?: string }

// CLI 类端点在子进程非零退出时仍回 HTTP 200 (body.ok=false + stderr),
// 不在这里抛的话调用方的 await 正常返回 → UI 弹「成功」而后端什么都没做。
async function cliPost<T extends CliResult>(path: string, body: unknown): Promise<T> {
  const r = await postJSON<T>(path, body);
  if (r?.ok === false) {
    throw new ApiError(200, (r.stderr || r.stdout || "").trim() || `命令失败 (exit ${r.exit})`);
  }
  return r;
}

// ── Types ──
export interface Subtask {
  sid: string;
  name: string;
  desc?: string;
  status: string;
  depends_on: string[];
  skills: string[];
  estimate?: number;
  pct?: number;
  started?: number | null;
  finished?: number | null;
}

export interface Task {
  id: string;
  name: string;
  desc?: string;
  status: string;
  deps: string[];
  worktree?: string | null;
  pct?: number;
  subs?: [number, number, number, number]; // [done, run, pend, fail]
  ready?: boolean;
  subtasks?: Subtask[];
  kind?: string;
  parent?: string | null;
  priority?: string;
  started?: number | null;
  confirmed?: number | null;
  finished?: number | null;
  checked?: number | null;
  created?: number | null;
}

export interface DashboardData {
  overview: { total: number; active: number; done: number; pending: number };
  tasks: Task[];
}

export interface QueueItem {
  tid: string;
  sid: string;
  name: string;
  status: string;
  skills?: string[];
}

export interface SpecItem {
  id: string;
  title: string;
  category: string;
  namespace: string;
  inclusion: string;
}

export interface SpecSearchResult {
  path: string;
  title: string;
  snippet: string;
}

export interface SpecMetaItem {
  path: string;
  title: string;
  namespace: string;
  category: string;
  keywords: string[];
}

export interface BoardData {
  cards: Task[];
  overview: DashboardData["overview"];
}

// ── Endpoints ──
export const api = {
  // 基础设施 (GET — probe/WS bootstrap 用, 非 业务 API)
  id: () => getText(`${BASE}/id`),
  rev: () => getText(`${BASE}/rev`),
  // 业务 (全 POST)
  data: () => postJSON<BoardData>(`${BASE}/task/list`),
  dashboard: () => postJSON<DashboardData>(`${BASE}/task/dashboard`),
  queue: () => postJSON<{ items: QueueItem[] }>(`${BASE}/task/queue`),
  task: (tid: string) => postJSON<Task>(`${BASE}/task/get`, { id: tid }),
  search: (q: string) => postJSON<{ results: Task[] }>(`${BASE}/task/search`, { q }),
  spec: () => postJSON<{ items: SpecItem[] }>(`${BASE}/spec/list`),
  specMeta: () => postJSON<SpecMetaItem[]>(`${BASE}/spec/meta`),
  specFile: (path: string) => postJSON<{ content: string }>(`${BASE}/spec/get`, { path }),
  specSave: (path: string, content: string) => postJSON(`${BASE}/spec/save`, { path, content }),
  specCreate: (path: string, content?: string) => postJSON(`${BASE}/spec/create`, { path, content: content || "" }),
  specDelete: (path: string) => postJSON(`${BASE}/spec/delete`, { path }),
  specSearch: (q: string) => postJSON<SpecSearchResult[]>(`${BASE}/spec/search`, { q }),
  archive: () => postJSON<{ tasks: Task[] }>(`${BASE}/archive/list`),
  archiveDel: (id: string) => postJSON(`${BASE}/archive/delete`, { id }),
  trash: () => postJSON<{ tasks: Task[] }>(`${BASE}/trash/list`),
  trashPurge: (id?: string) => postJSON(`${BASE}/trash/purge`, id ? { id } : {}),
  getConfig: () => postJSON<Record<string, unknown>>(`${BASE}/system/config-get`),
  setConfig: (cfg: Record<string, unknown>) => postJSON(`${BASE}/system/config-set`, cfg),
  create: (id: string, name: string, desc: string, deps?: string) =>
    cliPost<CliResult>(`${BASE}/task/create`, { id, name, desc, deps }),
  confirm: (id: string, force = true) =>
    cliPost<CliResult>(`${BASE}/task/confirm`, { id, force }),
  revert: (id: string) =>
    cliPost<CliResult>(`${BASE}/task/revert`, { id }),
  priority: (id: string, set: string) =>
    cliPost<CliResult>(`${BASE}/task/priority`, { id, set }),
  del: (id: string, force = true) =>
    cliPost<CliResult>(`${BASE}/task/delete`, { id, force }),
  clean: (days = 0) =>
    cliPost<CliResult>(`${BASE}/task/clean`, { days }),
  prd: (id: string, action: string, type: string, list?: string) =>
    cliPost<CliResult>(`${BASE}/task/prd`, { id, action, type, list }),
  designSave: (id: string, content: string) =>
    postJSON<{ ok: boolean }>(`${BASE}/task/design-save`, { id, content }),
  subtaskAdd: (id: string, sid: string, name: string, desc: string, estimate: string, deps?: string) =>
    cliPost<CliResult>(`${BASE}/subtask/add`, { id, sid, name, desc, estimate, deps }),
  finish: (id: string, force = false) =>
    cliPost<CliResult & { id: string }>(`${BASE}/task/finish`, { id, force }),
};
