// SKEIN webapp 引导入口 (index.html <script type=module> 加载)。
//   1. 载入 petite-vue (vendored IIFE, 暴露全局 PetiteVue) — 供 page 模块 createApp 用
//   2. 接线顶栏: nav 高亮由 router 管; 全局搜索下拉
//   3. 启动 live 热重载 + hash router (注入 api/md 依赖)
import * as api from "./lib/api.js";
import * as md from "./lib/md.js";
import * as live from "./lib/live.js";
import * as router from "./router.js";
import * as configModal from "./lib/config-modal.js";

// petite-vue 是 IIFE 打包 (非 ESM), import 拿不到具名导出 → 注入 <script> 挂全局 PetiteVue。
// 非阻塞: page 用时经 window.PetiteVue.createApp; 拉取失败仅影响需响应式的 page, 不阻断路由。
function loadPetiteVue() {
  if (window.PetiteVue) return;
  const s = document.createElement("script");
  s.src = "/vendor/petite-vue.js";
  s.async = true;
  document.head.appendChild(s);
}

// ── 全局搜索: 输入防抖 → api.search → 下拉结果; 点结果跳转 (task/subtask → /task?id=:id) ──
function wireSearch() {
  const input = document.getElementById("global-search");
  if (!input) return;
  const box = document.createElement("div");
  box.className = "search-dropdown";
  box.setAttribute("role", "listbox");
  // 兜底内联样式: 即便 dist/app.css 未定义 .search-dropdown 也保证可见 (背景/边框取主题 CSS 变量)
  box.style.cssText = "position:fixed;z-index:1000;max-height:60vh;overflow:auto;border-radius:8px;" +
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
    if (h.kind === "task" || h.kind === "subtask") return "/task?id=" + encodeURIComponent(h.id);
    if (h.kind === "spec") return "/spec";
    return "/dashboard";
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

// ── 主题切换: 浅 (晨曦) / 暗 (夜空金沙) ──
// 优先级: localStorage 手动选择 > prefers-color-scheme 系统跟随。
// 手动 = light 时写 data-theme="skein-light" (覆盖系统); 暗同理; 清除 = 回落系统跟随 (不写 data-theme)。
// 实际只对「暗」需要 data-theme="skein-dark" (浅是 :root 默认), 浅显式落 data-theme="skein-light" 作占位以便 toggle 高亮。
function applyTheme(pref) {
  const html = document.documentElement;
  if (pref === "dark") html.setAttribute("data-theme", "skein-dark");
  else if (pref === "light") html.setAttribute("data-theme", "skein-light");
  else html.removeAttribute("data-theme");                  // null = 系统跟随
  document.querySelectorAll("[data-theme-btn]").forEach((b) => {
    b.classList.toggle("on", b.dataset.themeBtn === pref);
  });
}
function sysDark() {
  return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
}
function wireTheme() {
  // 首屏: 读记忆, 无则系统跟随 (applyTheme(null) 不写 data-theme, input.css 的 @media 接管)
  let pref = null;
  try { pref = localStorage.getItem("skein-theme"); } catch (_) {}
  applyTheme(pref);
  // 兜底: 若无手动记忆, 系统切暗时实时跟随 (有记忆则不动, 用户偏好优先)
  if (!pref && window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
      try { if (localStorage.getItem("skein-theme")) return; } catch (_) {}
      applyTheme(e.matches ? "dark" : "light");
      // 系统跟随模式下不点亮任一按钮 (pref=null), 但视觉已切; 此处仅同步视觉
    });
  }
  document.querySelectorAll("[data-theme-btn]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const want = btn.dataset.themeBtn;
      // 同键再点 = 取消 → 系统跟随
      let next = want;
      try { if (localStorage.getItem("skein-theme") === want) next = null; } catch (_) {}
      try { if (next) localStorage.setItem("skein-theme", next); else localStorage.removeItem("skein-theme"); } catch (_) {}
      applyTheme(next);
    });
  });
  // ponytail: 系统跟随时按钮都不点亮 (pref=null); 上面 applyTheme(null) 已正确清空。
}

// ── 流沙动效 (细节层): 数字递增 + 入场 + 视口外暂停 ──
// 路由切页只换 #view 内容 (router.js), 故监听 #view 子树变化 → 每次新页渲染后重跑。
// 挂点约定 (无侵入, 缺失即跳过):
//   [data-count]      数字递增目标 (dashboard KPI / board 统计 .stat-n)
//   .stat-n           无 data-count 时也尝试用其文本为数字递增 (board 卡)
//   .entrance         列表项/子元素入场 (translateY+opacity, CSS nth-child 错峰)
// 动效一律尊重 prefers-reduced-motion (CSS 已降级, JS 这里也跳过)。
const reducedMotion = () => window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function runCounters(root) {
  if (reducedMotion()) return;
  // 收集: 显式 [data-count] + board 的 .stat-n (取其文本整数作目标)
  const targets = Array.from(root.querySelectorAll("[data-count], .stat-n"));
  targets.forEach((el) => {
    let target = parseInt(el.dataset.count, 10);
    if (isNaN(target)) {
      target = parseInt((el.textContent || "").trim(), 10);
      if (isNaN(target)) return;                            // 非数字 (如 "-") 跳过
      el.dataset.count = target;                            // 标记避免重复
    }
    if (el.dataset.countDone) return;
    el.dataset.countDone = "1";
    const dur = 600, start = performance.now();
    el.textContent = "0";
    function step(now) {
      const p = Math.min((now - start) / dur, 1);
      el.textContent = String(Math.round((1 - Math.pow(1 - p, 3)) * target));  // easeOutCubic
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });
}

// 视口外暂停: 给所有带动画的卡/列表/进度条挂 observer, 离开视口加 .paused。
// ponytail: webapp 无 board 的 .voff; 用 IntersectionObserver 统一管, 根 margin 给一点缓冲。
function wireViewportPause(root) {
  if (reducedMotion() || !("IntersectionObserver" in window)) return;
  const animated = root.querySelectorAll(".card, .entrance, .skein-bar, .sub-active, .qrow-active");
  if (!animated.length) return;
  if (!wireViewportPause._io) {
    wireViewportPause._io = new IntersectionObserver((entries) => {
      entries.forEach((e) => e.target.classList.toggle("paused", !e.isIntersecting));
    }, { rootMargin: "60px" });
  }
  animated.forEach((el) => wireViewportPause._io.observe(el));
}

function replayMotion() {
  if (reducedMotion()) return;
  const view = document.getElementById("view");
  if (!view) return;
  runCounters(view);
  wireViewportPause(view);
}

function wireMotion() {
  // 监听 #view 子树变化 (router 切页 innerHTML 重写触发), 稍延迟让 petite-vue 渲染完。
  const view = document.getElementById("view");
  if (!view) return;
  let timer = 0;
  const mo = new MutationObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(replayMotion, 60);
  });
  mo.observe(view, { childList: true, subtree: true });
  // 首屏
  setTimeout(replayMotion, 120);
}

function boot() {
  loadPetiteVue();
  wireSearch();
  wireTheme();
  wireMotion();
  configModal.wire(api);
  live.start();
  router.start({ api, md });
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
else boot();
