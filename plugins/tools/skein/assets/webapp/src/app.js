// SKEIN webapp 引导入口 (index.html <script type=module> 加载)。
//   1. 载入 petite-vue (vendored IIFE, 暴露全局 PetiteVue) — 供 page 模块 createApp 用
//   2. 接线顶栏: nav 高亮由 router 管; 全局搜索下拉
//   3. 启动 live 热重载 + hash router (注入 api/md 依赖)
import * as api from "./lib/api.js";
import * as md from "./lib/md.js";
import * as live from "./lib/live.js";
import * as router from "./router.js";

// petite-vue 是 IIFE 打包 (非 ESM), import 拿不到具名导出 → 注入 <script> 挂全局 PetiteVue。
// 非阻塞: page 用时经 window.PetiteVue.createApp; 拉取失败仅影响需响应式的 page, 不阻断路由。
function loadPetiteVue() {
  if (window.PetiteVue) return;
  const s = document.createElement("script");
  s.src = "/vendor/petite-vue.js";
  s.async = true;
  document.head.appendChild(s);
}

// ── 全局搜索: 输入防抖 → api.search → 下拉结果; 点结果跳转 (task/subtask → #/task/:id) ──
function wireSearch() {
  const input = document.getElementById("global-search");
  if (!input) return;
  const box = document.createElement("div");
  box.className = "search-dropdown";
  box.setAttribute("role", "listbox");
  // 兜底内联样式: 即便 dist/app.css 未定义 .search-dropdown 也保证可见 (背景/边框取主题 CSS 变量)
  box.style.cssText = "position:fixed;max-height:60vh;overflow:auto;border-radius:8px;" +
    "background:var(--card,#fff);color:var(--fg,#111);border:1px solid var(--brd,#ddd);" +
    "box-shadow:0 8px 28px rgba(0,0,0,.18);padding:4px";
  box.hidden = true;
  document.body.appendChild(box);

  function place() {
    const r = input.getBoundingClientRect();
    box.style.position = "fixed";
    box.style.top = (r.bottom + 4) + "px";
    box.style.left = r.left + "px";
    box.style.width = r.width + "px";
    box.style.zIndex = "60";
  }
  function close() { box.hidden = true; box.innerHTML = ""; }
  function hitHash(h) {
    // task/subtask 命中 → 任务详情页; 其余 (spec/命令/…) 回落到对应 tab
    if (h.kind === "task" || h.kind === "subtask") return "#/task/" + encodeURIComponent(h.id);
    if (h.kind === "spec") return "#/spec";
    return "#/dashboard";
  }
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function renderHits(hits, q) {
    if (!hits || !hits.length) { box.innerHTML = '<div class="search-empty">无匹配: ' + esc(q) + "</div>"; box.hidden = false; place(); return; }
    box.innerHTML = hits.map((h) =>
      '<a class="search-hit" href="' + hitHash(h) + '">' +
      '<span class="search-kind">' + esc(h.kind || "") + "</span>" +
      '<span class="search-name">' + esc(h.name || h.id || "") + "</span>" +
      (h.snippet ? '<span class="search-snip">' + esc(h.snippet) + "</span>" : "") +
      "</a>").join("");
    box.hidden = false;
    place();
  }

  let timer = 0, lastReq = 0;
  input.addEventListener("input", () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (!q) { close(); return; }
    timer = setTimeout(() => {
      const my = ++lastReq;
      api.search(q).then((r) => {
        if (my !== lastReq) return;                         // 丢弃过期响应
        renderHits(r && r.hits, q);
      }).catch(() => { if (my === lastReq) close(); });
    }, 200);
  });
  input.addEventListener("keydown", (e) => { if (e.key === "Escape") { close(); input.blur(); } });
  // 点结果: 走 hash 跳转 (router 接管, 不整页刷) 后收起
  box.addEventListener("click", (e) => { if (e.target.closest(".search-hit")) close(); });
  document.addEventListener("click", (e) => { if (e.target !== input && !box.contains(e.target)) close(); });
  window.addEventListener("resize", () => { if (!box.hidden) place(); });
}

function boot() {
  loadPetiteVue();
  wireSearch();
  live.start();
  router.start({ api, md });
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
else boot();
