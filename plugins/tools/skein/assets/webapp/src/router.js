// SKEIN webapp history (path + query) 路由核心: 7 route, 切页只换 #view 内容 (无整页刷新), page 模块懒加载。
//
// ── page 模块加载契约 (s4-s10 遵循) ──
//   路径:   ./pages/<name>.js  (name = dashboard|board|queue|task|spec|archive)
//   导出:   export function render(mount, params, ctx)
//     mount  — #view 容器 DOM (已清空); page 自行填充内容 (innerHTML / petite-vue createApp().mount(mount))
//     params — 路由参数对象, 如 /task?id=<tid> → { id: "<tid>" }; 无参为 {}
//     ctx    — { api, md, onLive }
//              api    = lib/api.js 全部导出 (dashboard/queue/task/spec/exec/search/setTheme/getJSON/postJSON…)
//              md     = lib/md.js (render/sanitize/mount)
//              onLive = (cb) => void  订阅数据软刷 (WS "data"); router 切页时自动退订, page 无需清理
//   render 可为 async; 返回值忽略。抛错 → router 显错误占位, 不影响顶栏/其他页。
//
// 未建的 page (s4-s10 尚未落地) 动态 import 失败 → 显 "该页开发中" 占位, 不报错。

import * as live from "./lib/live.js";

const ROUTES = ["dashboard", "board", "queue", "task", "spec", "archive"];
const DEFAULT = "dashboard";

// 解析 location.pathname + search → { name, params }
function parse() {
  const seg = location.pathname.split("/").filter(Boolean);  // ["task","abc"] | ["dashboard"] | []
  let name = seg[0] || DEFAULT;
  if (!ROUTES.includes(name)) name = DEFAULT;
  const params = {};
  if (name === "task") {
    const id = new URLSearchParams(location.search).get("id");
    if (id) params.id = decodeURIComponent(id);
  }
  return { name, params };
}

let cleanups = [];                                          // 当前页 onLive 退订句柄
function teardown() { cleanups.forEach((u) => { try { u(); } catch (_) {} }); cleanups = []; }

function placeholder(mount, name, msg) {
  mount.innerHTML = "";
  const box = document.createElement("div");
  box.className = "mx-auto max-w-lg py-24 text-center text-muted";
  box.innerHTML = '<div class="empty-ico"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg></div><div>' +
    msg + '</div><div class="text-xs mt-2 opacity-60">' + name + "</div>";
  mount.appendChild(box);
}

let deps = {};                                              // { api, md } — app.js 注入
let navToken = 0;                                           // 竞态守卫: 快速切页只让最后一次生效

async function navigate() {
  const token = ++navToken;
  const { name, params } = parse();
  const mount = document.getElementById("view");
  if (!mount) return;

  highlightNav(name);
  teardown();                                               // 清上一页的 live 订阅
  placeholder(mount, name, "加载中…");

  const ctx = {
    api: deps.api,
    md: deps.md,
    onLive: (cb) => { const u = live.subscribe(cb); cleanups.push(u); },
  };

  let mod;
  try {
    mod = await import(`./pages/${name}.js`);
  } catch (_) {
    if (token === navToken) placeholder(mount, name, "该页开发中");
    return;                                                 // 未建 page: 占位, 不报错
  }
  if (token !== navToken) return;                           // 已被更晚的导航接管
  try {
    if (typeof mod.render !== "function") throw new Error("page 未导出 render()");
    mount.innerHTML = "";
    await mod.render(mount, params, ctx);
  } catch (e) {
    if (token === navToken) placeholder(mount, name, "加载失败: " + (e && e.message || e));
  }
}

// 顶栏 nav 高亮跟随当前 route (匹配 href 首段, path 形如 /xxx)
function highlightNav(name) {
  document.querySelectorAll("[data-nav]").forEach((a) => {
    const href = (a.getAttribute("href") || "").split("/").filter(Boolean)[0];
    a.classList.toggle("active", href === name);
    if (href === name) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
}

export function start(injectedDeps) {
  deps = injectedDeps || {};
  // 首屏: 根路径 (/) 落默认页; pushState 不触发 popstate, 直接 navigate。
  if (location.pathname === "/" || !location.pathname) {
    history.replaceState({}, "", "/" + DEFAULT);
  }
  window.addEventListener("popstate", navigate);
  // 拦截站内 <a href="/xxx"> → go() (pushState), 不整页刷 (root cause: path href 默认整页跳)。
  document.addEventListener("click", (e) => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = e.target.closest("a[href]");
    if (!a) return;
    const url = new URL(a.href, location.href);
    if (url.origin !== location.origin) return;
    const path = url.pathname + url.search + url.hash;
    if (path === location.pathname + location.search + location.hash) return;
    e.preventDefault();
    history.pushState({}, "", path);
    navigate();
  });
  navigate();
}

// 供顶栏搜索/页面内跳转用: 编程式导航 (不整页刷)。
// pushState 不触发 popstate, 须手动 navigate()。
export function go(path) {
  const p = path.charAt(0) === "/" ? path : "/" + path;
  history.pushState({}, "", p);
  navigate();
}
