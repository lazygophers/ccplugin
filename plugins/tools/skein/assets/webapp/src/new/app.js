// SKEIN webapp 引导入口 (htm + 原生 DOM 重写版, 替 petite-vue)。
//   boot 序 (与现 app.js:194-202 语义对齐, 去 loadPetiteVue):
//   wireTheme → wireSearch → wireMotion → wireFab → initRouter → initLive
//
// ponytail: 不引 htmx 库 — 用 history.pushState + a[href] 拦截实现 hx-push-url 效果, 真"原生 DOM"。
// ponytail: htm ESM 优先本地 vendor (buildless + 零 CDN 信任), CDN 兜底; 极简 h() 把 tag 转 DOM。

import * as api from "./lib/api.js";
import * as md from "./lib/md.js";          // 复用现 lib/md.js (render/sanitize/mount) — 不重写
import * as live from "./lib/live.js";
import * as router from "./router.js";

// ── htm: 极简 h(tag, props, ...children) → DOM ──
// htm 返回构造对象 (string tag + props + children), 用 h() 转 DOM。10 行, 替 preact。
// ponytail: 零 vDOM/diff; 仅满足本 webapp 的 DOM 构造, 复杂场景留待 page 自行扩展。
export function h(tag, props, ...children) {
  if (typeof tag === "function") return tag(props || {}, children);   // 函数组件 (page 可用)
  const el = document.createElement(tag);
  if (props) for (const k in props) {
    const v = props[k];
    if (v == null || v === false) continue;
    if (k === "class" || k === "className") el.className = v;
    else if (k === "style" && typeof v === "object") Object.assign(el.style, v);
    else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === "html") el.innerHTML = v;                            // 显式 innerHTML (含 SVG / 大段模板)
    else if (v === true) el.setAttribute(k, "");
    else el.setAttribute(k, String(v));
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    el.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  return el;
}

// ── htm 加载: 本地 vendor 优先, CDN 兜底 — T3/T7 加 /vendor/htm.js 静态 mount ──
async function loadHtm() {
  try {
    // ponytail: 本地 vendor 路径 (T3 在 skein.py build_app 加 /vendor/htm.js mount 即可); 缺失抛错走 CDN。
    const mod = await import("/vendor/htm.js");
    if (mod && mod.default) return mod.default;
  } catch (_) { /* fall through */ }
  // 兜底: esm.sh CDN, 替代 standalone binary 让步 (design.md 决策)
  const mod = await import("https://esm.sh/htm@3.1.1");
  return mod.default;
}

// ── 主题切换 (浅海滩蓝金 / 暗夜幕) — 现版 app.js:87-123 原样迁移 ──
function applyTheme(pref) {
  const html = document.documentElement;
  if (pref === "dark") html.setAttribute("data-theme", "skein-dark");
  else if (pref === "light") html.setAttribute("data-theme", "skein-light");
  else html.removeAttribute("data-theme");                  // null = 系统跟随
  document.body.classList.toggle("bg-fluid-dark", pref === "dark");
  document.body.classList.toggle("bg-fluid-light", pref !== "dark");
  document.querySelectorAll("[data-theme-btn]").forEach((b) => {
    b.classList.toggle("text-accent", b.dataset.themeBtn === pref);
  });
}

function sysDark() {
  return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function wireTheme() {
  let pref = null;
  try { pref = localStorage.getItem("skein-theme"); } catch (_) {}
  applyTheme(pref);
  if (!pref && window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
      try { if (localStorage.getItem("skein-theme")) return; } catch (_) {}
      applyTheme(e.matches ? "dark" : "light");
    });
  }
  document.querySelectorAll("[data-theme-btn]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const want = btn.dataset.themeBtn;
      let next = want;
      try { if (localStorage.getItem("skein-theme") === want) next = null; } catch (_) {}
      try { if (next) localStorage.setItem("skein-theme", next); else localStorage.removeItem("skein-theme"); } catch (_) {}
      applyTheme(next);
    });
  });
}

// ── 全局搜索 (防抖 200ms → api.search → 下拉; 现版 app.js:22-81 迁移) ──
function wireSearch() {
  const input = document.getElementById("global-search");
  if (!input) return;
  const box = h("div", {
    class: "search-dropdown glass fixed z-float rounded-md border border-brd max-h-[60vh] overflow-auto p-1",
    role: "listbox", style: { display: "none" },
  });
  document.body.append(box);

  function place() {
    const r = input.getBoundingClientRect();
    box.style.top = (r.bottom + 4) + "px";
    box.style.left = r.left + "px";
    box.style.width = r.width + "px";
  }
  function close() { box.style.display = "none"; box.innerHTML = ""; }
  function hitHref(h2) {
    if (h2.kind === "task" || h2.kind === "subtask") return "/task?id=" + encodeURIComponent(h2.id);
    if (h2.kind === "spec") return "/spec";
    return "/dashboard";
  }
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function renderHits(hits, q) {
    if (!hits || !hits.length) {
      box.innerHTML = '<div class="search-empty px-3 py-2 text-sm text-muted">无匹配: ' + esc(q) + "</div>";
      box.style.display = "block"; place(); return;
    }
    box.innerHTML = hits.map((hh) =>
      '<a class="search-hit block px-3 py-1.5 rounded hover:bg-card/60 text-sm" href="' + hitHref(hh) + '">' +
      '<span class="search-kind text-xs text-muted mr-2">' + esc(hh.kind || "") + "</span>" +
      '<span class="search-name text-fg">' + esc(hh.name || hh.id || "") + "</span>" +
      (hh.snippet ? '<div class="search-snip text-xs text-muted mt-0.5">' + esc(hh.snippet) + "</div>" : "") +
      "</a>"
    ).join("");
    box.style.display = "block"; place();
  }

  let timer = 0, lastReq = 0;
  input.addEventListener("input", () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (!q) { close(); return; }
    timer = setTimeout(() => {
      const my = ++lastReq;
      api.search(q).then((r) => {
        if (my !== lastReq) return;
        renderHits(r && r.hits, q);
      }).catch(() => { if (my === lastReq) close(); });
    }, 200);
  });
  input.addEventListener("keydown", (e) => { if (e.key === "Escape") { close(); input.blur(); } });
  box.addEventListener("click", (e) => { if (e.target.closest(".search-hit")) close(); });
  document.addEventListener("click", (e) => { if (e.target !== input && !box.contains(e.target)) close(); });
  window.addEventListener("resize", () => { if (box.style.display !== "none") place(); });
}

// ── 动效 (尊重 reduced-motion): 数字递增 + 视口外暂停 ──
const reducedMotion = () => window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function runCounters(root) {
  if (reducedMotion()) return;
  const targets = Array.from(root.querySelectorAll("[data-count], .stat-n"));
  targets.forEach((el) => {
    let target = parseInt(el.dataset.count, 10);
    if (isNaN(target)) {
      target = parseInt((el.textContent || "").trim(), 10);
      if (isNaN(target)) return;
      el.dataset.count = target;
    }
    if (el.dataset.countDone) return;
    el.dataset.countDone = "1";
    const dur = 600, start = performance.now();
    el.textContent = "0";
    function step(now) {
      const p = Math.min((now - start) / dur, 1);
      el.textContent = String(Math.round((1 - Math.pow(1 - p, 3)) * target));
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });
}

let _io = null;
function wireViewportPause(root) {
  if (reducedMotion() || !("IntersectionObserver" in window)) return;
  const animated = root.querySelectorAll(".card, .entrance, .skein-bar, .sub-active, .qrow-active");
  if (!animated.length) return;
  if (!_io) {
    _io = new IntersectionObserver((entries) => {
      entries.forEach((e) => e.target.classList.toggle("paused", !e.isIntersecting));
    }, { rootMargin: "60px" });
  }
  animated.forEach((el) => _io.observe(el));
}

function replayMotion() {
  if (reducedMotion()) return;
  const view = document.getElementById("view");
  if (!view) return;
  runCounters(view);
  wireViewportPause(view);
}

function wireMotion() {
  const view = document.getElementById("view");
  if (!view) return;
  let timer = 0;
  const mo = new MutationObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(replayMotion, 60);
  });
  mo.observe(view, { childList: true, subtree: true });
  setTimeout(replayMotion, 120);
}

// ── fab 回到顶部 ──
function wireFab() {
  const fab = document.getElementById("fab-top");
  if (!fab) return;
  window.addEventListener("scroll", () => {
    const show = window.scrollY > 400;
    fab.style.opacity = show ? "1" : "0";
    fab.style.pointerEvents = show ? "auto" : "none";
  }, { passive: true });
  fab.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
}

// ── ctx 依赖容器 (page 经 render(mount, params, ctx) 注入) ──
// ctx.onLive(remountFn) 订阅 WS 数据软刷; router 切页自动退订 (core `frontend/soft-refresh-pattern`)。
const ctx = {
  api,
  md,
  h,                          // 极简 h() 转 DOM (htm tag → DOM)
  onLive: null,               // router 启动时填充: (cb) => unsubscribe
  navigate: null,             // router 启动时填充: (path) => void
};

async function boot() {
  wireTheme();
  wireSearch();
  wireMotion();
  wireFab();
  // 先连 WS (live.start 后 onLive 才能订阅广播); 再启 router (router.navigate 走首轮渲染)
  live.start();
  const onLive = live.subscribe;
  ctx.onLive = onLive;
  const navigate = await router.start({ ctx, onLive });
  ctx.navigate = navigate;
  // ponytail: htm 延迟加载 (本地 vendor → CDN), 不阻塞 boot; page 用时 ctx.h 已可用 (本文件内置)。
  loadHtm().then((htmFn) => { ctx.htm = htmFn; }).catch(() => {});
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
else boot();
