// SKEIN webapp hx-push-url 路由 (htm + 原生 DOM 重写版)。
//   history.pushState + 拦截 a[href] click 实现 hx-push-url 效果 (不引 htmx 库)。
//   6 route + DEFAULT=board (与现 router.js:18-32 语义对齐)。
//
// ── page 模块契约 (core `[arch] SPA page 模块统一契约`) ──
//   路径: ./pages/<name>.js (name = board|task|queue|dashboard|archive|spec)
//   导出: export async function render(mount, params, ctx)
//     mount  — #view 容器 DOM (router 已清空)
//     params — { id? } (仅 /task?id=<tid> 用)
//     ctx    — { api, md, h, onLive, navigate }
//   ctx.onLive(remountFn) 订阅 WS 软刷, router 切页自动退订。
//   render 抛错 → 占位错误框, 不影响顶栏。

const ROUTES = ["board", "task", "tasks", "queue", "dashboard", "archive", "spec"];
const DEFAULT = "dashboard";

function parse() {
  const seg = location.pathname.split("/").filter(Boolean);  // ["task","abc"] | ["board"] | []
  let name = seg[0] || DEFAULT;
  if (!ROUTES.includes(name)) name = DEFAULT;
  const params = {};
  if (name === "task") {
    // 支持两种格式: /task/:id (路径参数) 和 /task?id=xxx (查询参数)
    const pathId = seg[1];
    if (pathId) params.id = decodeURIComponent(pathId);
    else {
      const id = new URLSearchParams(location.search).get("id");
      if (id) params.id = decodeURIComponent(id);
    }
  }
  return { name, params };
}

let cleanups = [];
function teardown() { cleanups.forEach((u) => { try { u(); } catch (_) {} }); cleanups = []; }

function placeholder(mount, name, msg) {
  mount.innerHTML = "";
  const box = document.createElement("div");
  box.className = "mx-auto max-w-lg py-24 text-center text-muted";
  box.innerHTML =
    '<div class="empty-ico opacity-50"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg></div>' +
    '<div class="mt-2">' + msg + "</div>" +
    '<div class="text-xs mt-2 opacity-60">' + name + "</div>";
  mount.appendChild(box);
}

function highlightNav(name) {
  // task 详情页也高亮 tasks 导航
  const navName = name === "task" ? "tasks" : name;
  document.querySelectorAll("[data-nav]").forEach((a) => {
    const href = (a.getAttribute("href") || "").split("/").filter(Boolean)[0];
    const on = href === navName;
    a.classList.toggle("active", on);
    if (on) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
}

let injectedDeps = null;
let navToken = 0;

async function navigate() {
  const token = ++navToken;
  const { name, params } = parse();
  const mount = document.getElementById("view");
  if (!mount) return;

  highlightNav(name);
  teardown();
  placeholder(mount, name, "加载中…");

  const ctx = Object.assign({}, injectedDeps.ctx, {
    onLive: (cb) => { const u = injectedDeps.onLive(cb); cleanups.push(u); },
  });

  let mod;
  try {
    mod = await import(`./pages/${name}.js`);
  } catch (_) {
    if (token === navToken) placeholder(mount, name, "该页开发中");
    return;
  }
  if (token !== navToken) return;
  try {
    if (typeof mod.render !== "function") throw new Error("page 未导出 render()");
    mount.innerHTML = "";
    await mod.render(mount, params, ctx);
  } catch (e) {
    if (token === navToken) placeholder(mount, name, "加载失败: " + (e && e.message || e));
  }
}

export async function start({ ctx, onLive }) {
  injectedDeps = { ctx, onLive };

  // 首屏: 根路径 (/) 落默认页; replaceState 不触发 popstate, 手动 navigate。
  if (location.pathname === "/" || !location.pathname) {
    history.replaceState({}, "", "/" + DEFAULT);
  }
  window.addEventListener("popstate", navigate);

  // hx-push-url 核心: 拦截站内 a[href] click → pushState + navigate (不整页刷)。
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
  return go;
}

// 编程式导航 (顶栏搜索 / 页面跳转)
export function go(path) {
  const p = path.charAt(0) === "/" ? path : "/" + path;
  history.pushState({}, "", p);
  navigate();
}
