// SKEIN webapp API 层 — fetch 封装 + 各 endpoint 签名
// 对齐 FastAPI backend: /__skein__/*

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

function getJSON<T>(path: string): Promise<T> { return req<T>(path); }
function postJSON<T>(path: string, body?: unknown): Promise<T> {
  return req<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
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
  contracts?: { id: string; desc?: string }[];
  kind?: string;
  parent?: string | null;
  started?: number | null;
  confirmed?: number | null;
  finished?: number | null;
  checked?: number | null;
  created?: number | null;
}

export interface DashboardData {
  overview: { total: number; active: number; done: number; pending: number; ready: number };
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
  id: () => getJSON<string>(`${BASE}/id`),
  rev: () => getJSON<string>(`${BASE}/rev`),
  data: () => getJSON<BoardData>(`${BASE}/data`),
  dashboard: () => getJSON<DashboardData>(`${BASE}/dashboard`),
  queue: () => getJSON<{ items: QueueItem[] }>(`${BASE}/queue`),
  task: (tid: string) => getJSON<Task>(`${BASE}/task?id=${encodeURIComponent(tid)}`),
  spec: () => getJSON<{ items: SpecItem[] }>(`${BASE}/spec`),
  specMeta: () => getJSON<SpecMetaItem[]>(`${BASE}/spec/meta`),
  specFile: (path: string) => getJSON<{ content: string }>(`${BASE}/spec/file?path=${encodeURIComponent(path)}`),
  specSave: (path: string, content: string) => postJSON(`${BASE}/spec/save`, { path, content }),
  specCreate: (path: string, content?: string) => postJSON(`${BASE}/spec/create`, { path, content: content || "" }),
  specDelete: (path: string) => postJSON(`${BASE}/spec/delete`, { path }),
  specSearch: (q: string) => getJSON<SpecSearchResult[]>(`${BASE}/spec/search?q=${encodeURIComponent(q)}`),
  archive: () => getJSON<{ tasks: Task[] }>(`${BASE}/archive`),
  archiveDel: (id: string) => postJSON(`${BASE}/archive/del`, { id }),
  trash: () => getJSON<{ tasks: Task[] }>(`${BASE}/trash`),
  trashPurge: (id?: string) => postJSON(`${BASE}/trash/purge`, id ? { id } : {}),
  search: (q: string) => getJSON<{ results: Task[] }>(`${BASE}/search?q=${encodeURIComponent(q)}`),
  getConfig: () => getJSON<Record<string, unknown>>(`${BASE}/config`),
  setConfig: (cfg: Record<string, unknown>) => postJSON(`${BASE}/config`, cfg),
  exec: (cmd: string, args?: Record<string, unknown>) => postJSON(`${BASE}/exec`, { cmd, ...args }),
};
