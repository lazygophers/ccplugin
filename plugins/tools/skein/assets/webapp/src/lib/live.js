// SKEIN webapp 热重载 (迁移自 board/live.js): 连 WS /__skein__/live。
//   "reload" → 整页刷 (服务端资产变); onopen 重连 (服务端重启) 同样整页刷;
//   "data"   → 数据变: 通知当前页订阅者软刷 (不整页刷, 保滚动/状态)。
// file:// 无 WS 端点 → 直接退出。页面经 ctx.onLive(cb) 订阅; router 在切页时清理订阅。

const subs = new Set();

// 订阅数据软刷; 返回退订函数 (router 切页时调用清理, 避免旧页回调泄漏)。
export function subscribe(cb) { subs.add(cb); return () => subs.delete(cb); }

// 后端挂: WS 断后每 2s 重连; 5 分钟内未重连成功 → 判定服务已停, 自动关页 (window.close 被浏览器拦则整页遮罩)。
const GRACE = 5 * 60 * 1000;
function giveUp() {
  try { window.close(); } catch (_) {}  // 仅能关脚本自开的窗; 拦住不抛错, 落遮罩兜底
  document.documentElement.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font:16px/1.6 system-ui;color:#666;text-align:center">SKEIN 看板服务已停止<br>(5 分钟未恢复, 请重开 <code>skein serve</code>)</div>';
}

let started = false;
export function start() {
  if (started || location.protocol === "file:") return;
  started = true;
  let seen = false, deadTimer = null;
  (function conn() {
    const ws = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/__skein__/live");
    ws.onopen = () => { if (deadTimer) { clearTimeout(deadTimer); deadTimer = null; } if (seen) location.reload(); else seen = true; };
    ws.onmessage = (e) => {
      if (e.data === "reload") location.reload();
      else if (e.data === "data") subs.forEach((cb) => { try { cb(); } catch (_) {} });
    };
    ws.onclose = () => { if (!deadTimer) deadTimer = setTimeout(giveUp, GRACE); setTimeout(conn, 2000); };
    ws.onerror = () => { try { ws.close(); } catch (_) {} };
  })();
}
