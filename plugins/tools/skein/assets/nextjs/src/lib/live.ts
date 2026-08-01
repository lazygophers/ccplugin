// SKEIN webapp WS 软刷 — 连 /__skein__/live
//
// 协议:
//   {type:"reload"}               → 整页刷
//   {type:"data"}                 → 软刷全部订阅者
//   {type:"task-changed", id}     → 软刷订阅 id 的页
//   {type:"spec-changed", path}   → spec 页软刷

type LiveMessage =
  | { type: "reload" }
  | { type: "data" }
  | { type: "task-changed"; id: string }
  | { type: "spec-changed"; path?: string };

type Subscriber = (msg: LiveMessage) => void;
type Unsubscribe = () => void;

const subs = new Set<Subscriber>();
const taskSubs = new Map<string, Set<Subscriber>>();

export function subscribe(cb: Subscriber, opts?: { taskId?: string }): Unsubscribe {
  if (opts?.taskId) {
    let set = taskSubs.get(opts.taskId);
    if (!set) { set = new Set(); taskSubs.set(opts.taskId, set); }
    set.add(cb);
    return () => { set!.delete(cb); if (!set!.size) taskSubs.delete(opts.taskId!); };
  }
  subs.add(cb);
  return () => subs.delete(cb);
}

const GRACE = 5 * 60 * 1000;

function giveUp() {
  try { window.close(); } catch {}
  document.documentElement.innerHTML =
    '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font:16px/1.6 \'Maple Mono\',\'Maple Mono NF\',monospace;color:#666;text-align:center">' +
    "SKEIN 看板服务已停止<br>(5 分钟未恢复, 请重开 <code>skein serve</code>)</div>";
}

let started = false;

export function startLive() {
  if (started || location.protocol === "file:") return;
  started = true;
  let seen = false;
  let deadTimer: ReturnType<typeof setTimeout> | null = null;

  function dispatch(payload: string) {
    if (payload === "reload") return location.reload();
    if (payload === "data") { const m: LiveMessage = { type: "data" }; return subs.forEach(cb => cb(m)); }
    let m: LiveMessage | null = null;
    try { m = JSON.parse(payload); } catch { return; }
    if (!m) return;
    subs.forEach(cb => cb(m!));
    if (m.type === "task-changed" && m.id) {
      const set = taskSubs.get(m.id);
      set?.forEach(cb => cb(m!));
    }
  }

  (function conn() {
    const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/__skein__/live`);
    ws.onopen = () => {
      if (deadTimer) { clearTimeout(deadTimer); deadTimer = null; }
      if (seen) location.reload(); else seen = true;
    };
    ws.onmessage = (e) => dispatch(e.data as string);
    ws.onclose = () => {
      if (!deadTimer) deadTimer = setTimeout(giveUp, GRACE);
      setTimeout(conn, 2000);
    };
    ws.onerror = () => { try { ws.close(); } catch {} };
  })();
}
