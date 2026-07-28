// SKEIN webapp WS 软刷 (htm 重写版) — 连 /__skein__/live。
//
// ── 协议 (T3 后端对齐, 现 _watch_loop 仅二分, 待 T3 拆 per-resource) ──
//   收 {type:"reload"}                          → 整页刷 (资产变)
//   收 {type:"data"}                            → 软刷全部订阅者 (兜底)
//   收 {type:"task-changed", id}                → 软刷订阅 id 的页 (T3 落地)
//   收 {type:"spec-changed", path}              → spec 页软刷 (T3 落地)
//   兜底兼容字符串 "reload" / "data" (现 skein.py 协议), T3 改 JSON 后双兼容期可去。
//
// page 经 ctx.onLive(cb) 或 ctx.onLive(cb, {taskId:"xxx"}) 订阅; router 切页自动退订。
// file:// 无 WS 端点 → 直接退出。

const subs = new Set();              // 全局软刷订阅 (无 id 过滤)
const taskSubs = new Map();          // taskId → Set<cb>; per-resource 精准 swap (T3 落地后用)

export function subscribe(cb, opts) {
  if (opts && opts.taskId) {
    let set = taskSubs.get(opts.taskId);
    if (!set) { set = new Set(); taskSubs.set(opts.taskId, set); }
    set.add(cb);
    return () => { set.delete(cb); if (!set.size) taskSubs.delete(opts.taskId); };
  }
  subs.add(cb);
  return () => subs.delete(cb);
}

function broadcast(cb, msg) { try { cb(msg); } catch (_) {} }  // msg: cb 拿到消息对象 (旧无参用法仍兼容, 忽略参数即可)

// GRACE 5min: WS 断后未恢复 → 判定服务已停, 落遮罩 (现版 live.js:13-16)。
const GRACE = 5 * 60 * 1000;
function giveUp() {
  try { window.close(); } catch (_) {}
  // ponytail: 内联遮罩 (不走 design.css) — 服务停时 CSS 可能加载不全, 兜底 system-ui。
  document.documentElement.innerHTML =
    '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font:16px/1.6 system-ui;color:#666;text-align:center">' +
    "SKEIN 看板服务已停止<br>(5 分钟未恢复, 请重开 <code>skein serve</code>)</div>";
}

let started = false;
export function start() {
  if (started || location.protocol === "file:") return;
  started = true;
  let seen = false, deadTimer = null;

  function dispatch(payload) {
    // 兼容现字符串协议 ("reload"/"data") + T3 JSON 协议
    if (payload === "reload") return location.reload();
    if (payload === "data") { const m = { type: "data" }; return subs.forEach((cb) => broadcast(cb, m)); }
    let m = null;
    try { m = typeof payload === "string" ? JSON.parse(payload) : payload; } catch (_) { return; }
    if (!m || typeof m !== "object") return;
    if (m.type === "reload") return location.reload();
    if (m.type === "data") return subs.forEach((cb) => broadcast(cb, m));
    if (m.type === "task-changed" && m.id) {
      // card 增量已随消息带上, 订阅者原地 patch 即可; 无需再对全体 subs 兜底广播 (卡片带 null 代表被删)。
      subs.forEach((cb) => broadcast(cb, m));
      const set = taskSubs.get(m.id);
      if (set) set.forEach((cb) => broadcast(cb, m));
    }
    if (m.type === "spec-changed") subs.forEach((cb) => broadcast(cb, m));  // ponytail: spec 页保守, 全订阅软刷
  }

  (function conn() {
    const ws = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/__skein__/live");
    ws.onopen = () => {
      if (deadTimer) { clearTimeout(deadTimer); deadTimer = null; }
      if (seen) location.reload(); else seen = true;            // 服务重启后整页刷
    };
    ws.onmessage = (e) => dispatch(e.data);
    ws.onclose = () => {
      if (!deadTimer) deadTimer = setTimeout(giveUp, GRACE);
      setTimeout(conn, 2000);                                   // 2s 重连
    };
    ws.onerror = () => { try { ws.close(); } catch (_) {} };
  })();
}
