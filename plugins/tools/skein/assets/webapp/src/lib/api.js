// SKEIN webapp API 层: fetch 封装 + 各 endpoint 便捷函数。
// 统一错误: 抛 ApiError{status,message}; 非 serve (file://) 或网络失败 → status=0 友好提示。
// 便捷函数直接返回解析后的 JSON; 调用方自行 try/catch 或用 .catch 出占位。

const BASE = "/__skein__";

export class ApiError extends Error {
  constructor(status, message) { super(message); this.name = "ApiError"; this.status = status; }
}

async function req(path, opts) {
  let res;
  try {
    res = await fetch(path, Object.assign({ cache: "no-store" }, opts));
  } catch (e) {
    // file:// 或断网: fetch 直接 reject
    throw new ApiError(0, "无法连接 skein serve — 需经 http 访问 (skein serve), file:// 直接打开不可用。");
  }
  if (!res.ok) {
    let msg = res.status + " " + res.statusText;
    try { const j = await res.json(); if (j && j.error) msg = j.error; } catch (_) {}
    throw new ApiError(res.status, msg);
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

export function getJSON(path) { return req(path); }
export function postJSON(path, body) {
  return req(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
}

// ── endpoint 便捷函数 (对齐 s2 后端契约) ──
export const dashboard = () => getJSON(BASE + "/dashboard");
export const queue = () => getJSON(BASE + "/queue");
export const task = (tid) => getJSON(BASE + "/task/" + encodeURIComponent(tid));
export const spec = () => getJSON(BASE + "/spec");
export const specFile = (path) => getJSON(BASE + "/spec/file?path=" + encodeURIComponent(path));
export const specSave = (path, content) => postJSON(BASE + "/spec/save", { path, content });
export const archive = () => getJSON(BASE + "/archive");
export const search = (q) => getJSON(BASE + "/search?q=" + encodeURIComponent(q));
export const getConfig = () => getJSON(BASE + "/config");
export const setConfig = (cfg) => postJSON(BASE + "/config", cfg).then((r) => (r && r.config) || cfg);
export const data = () => getJSON(BASE + "/data");
// exec: cmd + 其余参数平铺进 body (list/ready/pop/current/status/doctor/contract/subtask-list/create/subtask-add)
export const exec = (cmd, args) => postJSON(BASE + "/exec", Object.assign({ cmd }, args || {}));
