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

// 重新导出, 方便 page 直接 import { h, api, fmtRelative, fmtTime } from '../app.js'
export { api, md };

// ---- 时间格式化工具 ----
export function fmtRelative(ts) {
  if (!ts) return '';
  const d = typeof ts === 'number' ? new Date(ts) : new Date(ts);
  const diff = Date.now() - d.getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return '刚刚';
  const min = Math.floor(sec / 60);
  if (min < 60) return min + ' 分钟前';
  const hr = Math.floor(min / 60);
  if (hr < 24) return hr + ' 小时前';
  const day = Math.floor(hr / 24);
  if (day < 30) return day + ' 天前';
  const mon = Math.floor(day / 30);
  if (mon < 12) return mon + ' 个月前';
  return Math.floor(mon / 12) + ' 年前';
}

export function fmtTime(ts) {
  if (!ts) return '';
  const d = typeof ts === 'number' ? new Date(ts) : new Date(ts);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${y}-${m}-${day} ${hh}:${mm}`;
}

// ---- 任务数据规范化: 统一 skein API 的字段名和状态 ----
// 5 状态系统: planning(规划中) / ready(待执行) / active(执行中) / check(验收中) / done(已完成)
const STATUS_MAP = {
  '待处理': 'planning', '规划中': 'planning', 'pending': 'planning', 'plan': 'planning',
  '就绪': 'ready', '待执行': 'ready', 'ready': 'ready',
  '进行中': 'active', '执行中': 'active', 'active': 'active', 'exec': 'active',
  '检查中': 'check', '验收中': 'check', '待验收': 'check', 'check': 'check',
  '已完成': 'done', '完成': 'done', 'done': 'done',
  '失败': 'failed', '已失败': 'failed', 'failed': 'failed',
  '已取消': 'cancelled',
  '已归档': 'archived',
};

// ---- 优先级工具 (0-10 分, 默认 5 = 中) ----
export function prioLevel(p) {
  const n = p != null ? Number(p) : 5;
  if (n >= 7) return 'high';
  if (n >= 4) return 'mid';
  return 'low';
}
export function prioLabel(p) {
  const lvl = prioLevel(p);
  return { high: '高优先级', mid: '中优先级', low: '低优先级' }[lvl];
}
export function prioShortLabel(p) {
  const lvl = prioLevel(p);
  return { high: '高', mid: '中', low: '低' }[lvl];
}
export function prioColor(p) {
  const lvl = prioLevel(p);
  return { high: 'danger', mid: 'warning', low: 'accent' }[lvl];
}
export function prioTextColor(p) {
  const lvl = prioLevel(p);
  return { high: 'text-danger', mid: 'text-warn', low: 'text-muted' }[lvl];
}

export function normalizeTask(t) {
  if (!t) return t;
  const statusRaw = t.status || t.st || 'pending';
  const status = STATUS_MAP[statusRaw] || statusRaw;
  const createdTs = t.createdAt || (t.created ? t.created * 1000 : null);
  const startedTs = t.startedAt || (t.started ? t.started * 1000 : null);
  const finishedTs = t.completedAt || t.finishedAt || (t.finished ? t.finished * 1000 : null);
  const updatedTs = t.updatedAt || (t.updated ? t.updated * 1000 : finishedTs || createdTs);
  return {
    ...t,
    id: t.id,
    title: t.title || t.name || '',
    name: t.title || t.name || '',
    description: t.description || t.desc || '',
    desc: t.description || t.desc || '',
    status,
    stage: t.stage || (status === 'planning' ? 'plan' : status === 'ready' ? 'ready' : status === 'active' ? 'exec' : status === 'check' ? 'check' : 'done'),
    priority: t.priority != null ? Number(t.priority) : (t.prio != null ? Number(t.prio) : 5),
    createdAt: createdTs,
    startedAt: startedTs,
    updatedAt: updatedTs,
    completedAt: finishedTs,
    finishedAt: finishedTs,
    checkedAt: t.checkedAt || (t.checked ? t.checked * 1000 : null),
    deps: t.deps || [],
    depNames: t.depNames || [],
    assignee: t.assignee || t.owner || '',
    estimate: t.estimate || t.est || null,
    progress: t.progress != null ? t.progress : (t.spct != null ? t.spct : t.sdone != null && t.stotal ? Math.round(t.sdone / t.stotal * 100) : null),
    subtasks: (t.subtasks || t.subtable || []).map(s => normalizeSubtask(s)),
    subNodes: t.subNodes || null,
    contracts: t.contracts || [],
    prd: t.prd || null,
    docs: t.docs || null,
    parent: t.parent || null,
    kind: t.kind || 'task',
  };
}

function normalizeSubtask(s) {
  if (!s) return s;
  const statusRaw = s.status || s.st || 'pending';
  const status = STATUS_MAP[statusRaw] || statusRaw;
  return {
    ...s,
    sid: s.sid || s.id,
    id: s.sid || s.id,
    title: s.title || s.name || '',
    name: s.title || s.name || '',
    description: s.description || s.desc || '',
    desc: s.description || s.desc || '',
    status,
    dependsOn: s.dependsOn || s.depends_on || s.deps || [],
    deps: s.dependsOn || s.depends_on || s.deps || [],
    depNames: s.depNames || [],
    progress: s.pct != null ? s.pct : s.progress,
    agent: s.agent || '',
    skills: s.skills || [],
    acc: s.acc || [],
    createdAt: s.created ? s.created * 1000 : null,
    startedAt: s.started ? s.started * 1000 : null,
    finishedAt: s.finished ? s.finished * 1000 : null,
  };
}

export function normalizeTasks(list) {
  return (list || []).map(normalizeTask);
}

// ---- htm: 极简 h(tag.class1.class2, props, ...children) → DOM ----──
// 支持 htm 风格的简写: 'div.w-10.h-10.text-center' → tag + className 解析
// ponytail: 零 vDOM/diff; 仅满足本 webapp 的 DOM 构造, 复杂场景留待 page 自行扩展。
export function h(tag, props, ...children) {
  if (typeof tag === "function") return tag(props || {}, children);   // 函数组件

  // 解析 tag 中的 class: 'div.w-10.h-10' → 'div' + 'w-10 h-10'
  // 支持 #id 语法: 'div#main.container' → 'div' + id='main' + 'container'
  // 支持转义点: 'lg\\:grid-cols-4' → 'lg:grid-cols-4' (去掉反斜杠)
  let tagName = tag;
  let classesFromTag = '';
  let idFromTag = null;

  if (typeof tag === 'string' && (tag.includes('.') || tag.includes('#'))) {
    const parts = tag.split(/(?=[.#])/);  // 按 . 或 # 分割, 保留分隔符
    tagName = parts[0];
    for (let i = 1; i < parts.length; i++) {
      const p = parts[i];
      if (p.startsWith('.')) {
        // 去掉类名中的反斜杠转义 (\: → :, \. → .)
        const cls = p.slice(1).replace(/\\:/g, ':').replace(/\\\./g, '.');
        classesFromTag += (classesFromTag ? ' ' : '') + cls;
      } else if (p.startsWith('#')) {
        idFromTag = p.slice(1).replace(/\\:/g, ':').replace(/\\\./g, '.');
      }
    }
  }

  const SVG_TAGS = new Set(['svg', 'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'ellipse', 'text', 'g', 'defs', 'use', 'tspan', 'linearGradient', 'radialGradient', 'stop', 'clipPath', 'mask', 'pattern', 'marker', 'image', 'view']);
  const isSvg = SVG_TAGS.has(tagName);
  const el = isSvg
    ? document.createElementNS('http://www.w3.org/2000/svg', tagName)
    : document.createElement(tagName);

  // 如果 props 不是对象 (是数组/字符串/数字/null), 把它当作 children 处理
  let actualProps = props;
  if (props == null || typeof props !== 'object' || Array.isArray(props) || props.nodeType) {
    if (props != null) children.unshift(props);
    actualProps = {};
  }

  // 应用从 tag 解析出的 class/id
  if (classesFromTag) {
    if (actualProps.class || actualProps.className) {
      actualProps.class = classesFromTag + ' ' + (actualProps.class || actualProps.className);
    } else {
      actualProps.class = classesFromTag;
    }
  }
  if (idFromTag && !actualProps.id) {
    actualProps.id = idFromTag;
  }

  if (actualProps) for (const k in actualProps) {
    const v = actualProps[k];
    if (v == null || v === false) continue;
    if (k === "class" || k === "className") {
      if (isSvg) el.setAttribute('class', v);
      else el.className = v;
    }
    else if (k === "style" && typeof v === "object") Object.assign(el.style, v);
    else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === "html") el.innerHTML = v;
    else if (v === true) el.setAttribute(k, "");
    else el.setAttribute(k, String(v));
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    if (c.nodeType) el.appendChild(c);
    else el.appendChild(document.createTextNode(String(c)));
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

// ── 主题切换 (浅海滩蓝金 / 暗夜幕) ──
const THEMES = ["light", "dark"];
const DEFAULT_THEME = "dark";

function applyTheme(pref) {
  const html = document.documentElement;
  if (pref === "dark") html.setAttribute("data-theme", "skein-dark");
  else html.setAttribute("data-theme", "skein-light");
  document.body.classList.toggle("bg-fluid-dark", pref === "dark");
  document.body.classList.toggle("bg-fluid-light", pref !== "dark");
  // 更新切换按钮图标文字
  const btn = document.getElementById("theme-toggle-btn");
  if (btn) {
    const label = btn.querySelector("span");
    if (label) label.textContent = pref === "dark" ? "亮色模式" : "暗色模式";
  }
}

function wireTheme() {
  let pref = DEFAULT_THEME;
  try {
    const saved = localStorage.getItem("skein-theme");
    if (saved && THEMES.includes(saved)) {
      pref = saved;
    } else if (saved) {
      localStorage.setItem("skein-theme", DEFAULT_THEME);
    }
  } catch (_) {}
  applyTheme(pref);
  const btn = document.getElementById("theme-toggle-btn");
  if (btn) {
    btn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") === "skein-dark" ? "dark" : "light";
      const next = current === "dark" ? "light" : "dark";
      try { localStorage.setItem("skein-theme", next); } catch (_) {}
      applyTheme(next);
    });
  }
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
  setQuery: null,             // router 启动时填充: (params, replace?) => void
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
  const { go, setQuery } = await router.start({ ctx, onLive });
  ctx.navigate = go;
  ctx.setQuery = setQuery;
  // ponytail: htm 延迟加载 (本地 vendor → CDN), 不阻塞 boot; page 用时 ctx.h 已可用 (本文件内置)。
  loadHtm().then((htmFn) => { ctx.htm = htmFn; }).catch(() => {});
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
else boot();
