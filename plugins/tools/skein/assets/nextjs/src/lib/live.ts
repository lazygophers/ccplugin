// SKEIN webapp WS 软刷 — 连 /__skein__/live
//
// 协议 (服务端消息):
//   {type:"reload"}               → 整页刷
//   {type:"data"}                 → 软刷全部订阅者
//   {type:"task-changed", id, card}  → 软刷订阅 id 的页 (card 有值=新建/更新, null=归档/删除)
//   {type:"spec-changed", path}   → spec 页软刷
//
// 协议 (客户端本地状态, 不来自服务端 — 由 startLive 自己派发):
//   {type:"offline"}              → 连接断开, 正在重连 (非静默失效的提示信号; 只提示, 永不放弃重连)
//
// 断线追赶: 重连成功 (ws.onopen 且此前已连过一次) 直接整页重载, 保证断线期间丢失的
// task-changed 消息靠重新拉全量数据补齐 —— 不额外发明追赶协议, 复用既有整页刷兜底路径。

type LiveMessage =
  | { type: "reload" }
  | { type: "data" }
  | { type: "task-changed"; id: string; card: Record<string, unknown> | null }
  | { type: "spec-changed"; path?: string }
  | { type: "offline" };

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

let started = false;

export function startLive() {
  if (started || location.protocol === "file:") return;
  started = true;
  let seen = false;
  let offline = false;

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
      offline = false;
      if (seen) location.reload(); else seen = true;
    };
    ws.onmessage = (e) => dispatch(e.data as string);
    ws.onclose = () => {
      // 首次转为断线时立刻提示 (静默重试期间用户不该以为一切正常)
      if (!offline) { offline = true; subs.forEach(cb => cb({ type: "offline" })); }
      setTimeout(conn, 2000);  // 无限重连 — 服务端停多久都只挂横幅, 不自毁页面 (用户可能只是重启 serve)
    };
    ws.onerror = () => { try { ws.close(); } catch {} };
  })();
}
