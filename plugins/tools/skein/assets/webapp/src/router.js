// SKEIN webapp hash 路由核心: 7 route, 切页只换 #view 内容 (无整页刷新), page 模块懒加载。
//
// ── page 模块加载契约 (s4-s10 遵循) ──
//   路径:   ./pages/<name>.js  (name = dashboard|board|queue|task|spec|commands|archive)
//   导出:   export function render(mount, params, ctx)
//     mount  — #view 容器 DOM (已清空); page 自行填充内容 (innerHTML / petite-vue createApp().mount(mount))
//     params — 路由参数对象, 如 #/task/:id → { id: "<tid>" }; 无参为 {}
//     ctx    — { api, md, onLive }
//              api    = lib/api.js 全部导出 (dashboard/queue/task/spec/exec/search/setTheme/getJSON/postJSON…)
//              md     = lib/md.js (render/sanitize/mount)
//              onLive = (cb) => void  订阅数据软刷 (WS "data"); router 切页时自动退订, page 无需清理
//   render 可为 async; 返回值忽略。抛错 → router 显错误占位, 不影响顶栏/其他页。
//
// 未建的 page (s4-s10 尚未落地) 动态 import 失败 → 显 "该页开发中" 占位, 不报错。

import * as live from "./lib/live.js";

const ROUTES = ["dashboard", "board", "queue", "task", "spec", "commands", "archive"];
const DEFAULT = "dashboard";

// 解析 location.hash → { name, params }
function parse() {
  const raw = location.hash.replace(/^#\/?/, "");           // "task/abc" | "dashboard" | ""
  const seg = raw.split("/").filter(Boolean);
  let name = seg[0] || DEFAULT;
  if (!ROUTES.includes(name)) name = DEFAULT;
  const params = {};
  if (name === "task" && seg[1]) params.id = decodeURIComponent(seg[1]);
  return { name, params };
}

let cleanups = [];                                          // 当前页 onLive 退订句柄
function teardown() { cleanups.forEach((u) => { try { u(); } catch (_) {} }); cleanups = []; }

function placeholder(mount, name, msg) {
  mount.innerHTML = "";
  const box = document.createElement("div");
  box.className = "mx-auto max-w-lg py-24 text-center text-muted";
  box.innerHTML = '<div class="text-2xl mb-2">🧵</div><div>' +
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

// 顶栏 nav 高亮跟随当前 route (匹配 href 首段)
function highlightNav(name) {
  document.querySelectorAll("[data-nav]").forEach((a) => {
    const href = (a.getAttribute("href") || "").replace(/^#\/?/, "").split("/")[0];
    a.classList.toggle("active", href === name);
    if (href === name) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
}

export function start(injectedDeps) {
  deps = injectedDeps || {};
  if (!location.hash) location.replace("#/" + DEFAULT);      // 首屏默认落 dashboard
  window.addEventListener("hashchange", navigate);
  navigate();
}

// 供顶栏搜索/页面内跳转用: 编程式导航 (不整页刷)
export function go(hash) { location.hash = hash.charAt(0) === "#" ? hash : "#/" + hash; }
