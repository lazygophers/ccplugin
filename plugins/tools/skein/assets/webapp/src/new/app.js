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
  '进行中': 'active', '运行中': 'active', '执行中': 'active', 'active': 'active', 'exec': 'active',  // 运行中 = SS_RUNNING (subtask 级)
  '检查中': 'check', '验收中': 'check', '待验收': 'check', 'check': 'check',
  '已完成': 'done', '完成': 'done', 'done': 'done',
  '失败': 'failed', '已失败': 'failed', 'failed': 'failed',
  '已取消': 'cancelled',
  '已归档': 'archived',
};

// 中文/英文状态 → 5 状态系统 (统计类接口只回状态计数时用)
export function normalizeStatus(s) { return STATUS_MAP[s] || s; }

// ---- 生命周期时间线 (board 详情面板 / task 详情页共用) ----
// 阶段序: 已过的阶段=done, 正处的阶段=current, 之后=pending。
// 关键: 当前阶段绝不标 done — 状态 active 时「执行」应是「当前」而非「已完成」。
const STAGE_ORDER = { planning: 0, ready: 1, active: 2, check: 3, done: 4 };
const STAGE_COLORS = {
  created:  '#74b9e8',
  ready:    '#429cd1',
  started:  '#237bb8',
  checked:  '#c9a227',
  finished: '#48bb78',
};

export function buildTimeline(task) {
  const st = task.status || 'planning';
  const idx = STAGE_ORDER[st];
  // failed 无阶段序 → 回落时间戳判定 (失败点未知, 有时间戳的阶段算走过)
  const byTs = idx == null;
  const at = (i, ts) => (byTs ? !!ts : idx > i);
  return [
    {
      key: 'created', label: '创建', name: '创建任务', desc: '任务创建与初始化',
      time: task.createdAt, done: !!task.createdAt, current: false,
      color: STAGE_COLORS.created,
    },
    {
      key: 'ready', label: '就绪', name: '进入待执行', desc: '规划完成，等待开始执行',
      time: task.readyAt, done: at(1, task.readyAt), current: idx === 1,
      color: STAGE_COLORS.ready,
    },
    {
      key: 'started', label: '执行', name: '开始执行', desc: '任务执行中，子任务调度',
      time: task.startedAt, done: at(2, task.startedAt), current: idx === 2,
      color: STAGE_COLORS.started,
    },
    {
      key: 'checked', label: '验收', name: '进入验收', desc: 'checkpoint 核对 + 场景自适应校验',
      time: task.checkedAt, done: at(3, task.checkedAt), current: idx === 3,
      color: STAGE_COLORS.checked,
    },
    {
      key: 'finished', label: '完成', name: '已完成', desc: '任务完成，归档沉淀',
      time: task.finishedAt, done: byTs ? !!task.finishedAt : idx >= 4, current: false,
      color: STAGE_COLORS.finished,
    },
  ];
}

// ---- 剩余工时预估 (ETA) ----
// 综合五路输入: ① subtask 逐项预估工时 ② 各 subtask 当前百分比 ③ subtask DAG 排序 (关键路径)
//   ④ 并发上限 (并行墙钟下界) ⑤ 已完成 subtask 的实际耗时 / 预估比 (校准因子)。
// 口径 = 工时 (人时经并发折算后的墙钟), 非日历时间 — 不含等待/空档。
//
// task 自身开销 = task.estimate - Σ subtask.estimate (即 plan/grill/check/finish),
// 按阶段剩余系数折算: 越靠后剩得越少。
const OWN_LEFT = { planning: 1, ready: 0.85, active: 0.6, check: 0.25, done: 0, failed: 0.6 };

function subRemain(s, fallbackEst) {
  if (s.status === 'done') return 0;
  const est = (typeof s.estimate === 'number' && s.estimate > 0) ? s.estimate : fallbackEst;
  if (!est) return 0;
  const pct = Math.min(100, Math.max(0, Number(s.progress ?? s.pct ?? 0)));
  return est * (1 - pct / 100);
}

// DAG 最长加权路径 (权 = 该 subtask 剩余工时)。成环时退化为总和, 不死循环。
function criticalPath(subs, remOf) {
  const byId = new Map(subs.map(s => [s.sid || s.id, s]));
  const memo = new Map(), inStack = new Set();
  const walk = (id) => {
    if (memo.has(id)) return memo.get(id);
    if (inStack.has(id)) return 0;               // 成环: 断掉这条边
    const s = byId.get(id);
    if (!s) return 0;
    inStack.add(id);
    const deps = s.dependsOn || s.deps || [];
    const best = deps.reduce((m, d) => Math.max(m, walk(d)), 0);
    inStack.delete(id);
    const v = best + remOf(s);
    memo.set(id, v);
    return v;
  };
  return subs.reduce((m, s) => Math.max(m, walk(s.sid || s.id)), 0);
}

// 校准因子: 已完成 subtask 的 Σ实际耗时 / Σ预估。样本不足或离谱 (超 [0.25,4]) 则不校准。
function calibration(subs) {
  let act = 0, est = 0;
  for (const s of subs) {
    if (s.status !== 'done' || !s.startedAt || !s.finishedAt) continue;
    if (!(typeof s.estimate === 'number' && s.estimate > 0)) continue;
    act += (s.finishedAt - s.startedAt) / 3600000;
    est += s.estimate;
  }
  if (!est || !act) return 1;
  const r = act / est;
  return (r < 0.25 || r > 4) ? 1 : r;
}

// 返回 {hours, calib, own, work, critical} 或 null (已完成 / 无任何工时数据)。
export function etaOf(task, maxActive) {
  const st = task.status || 'planning';
  if (st === 'done' || st === 'archived' || st === 'cancelled') return null;
  const subs = task.subtasks || [];
  const withEst = subs.filter(s => typeof s.estimate === 'number' && s.estimate > 0);
  // 老数据无 subtask 工时: 用同 task 已填项均值兜底; 全无则整体退回 task.estimate 按进度折算
  const fallbackEst = withEst.length
    ? withEst.reduce((a, s) => a + s.estimate, 0) / withEst.length : 0;
  const remOf = (s) => subRemain(s, fallbackEst);
  const work = subs.reduce((a, s) => a + remOf(s), 0);

  const subSum = subs.reduce((a, s) => a + (Number(s.estimate) || 0), 0);
  const taskEst = Number(task.estimate) || 0;
  const own = Math.max(0, taskEst - subSum) * (OWN_LEFT[st] ?? 0.6);

  if (!work && !own) {
    if (!taskEst) return null;
    const pct = Math.min(100, Math.max(0, Number(task.progress) || 0));
    return { hours: taskEst * (1 - pct / 100), calib: 1, own: 0, work: 0, critical: 0 };
  }
  const calib = calibration(subs);
  const n = Math.max(1, Number(maxActive) || 1);
  const critical = criticalPath(subs, remOf);
  // 并行墙钟下界: 关键路径压不动, 其余按并发摊
  const wall = Math.max(critical, work / n);
  return { hours: (wall + own) * calib, calib, own, work, critical };
}

// 工时 → 人话。<1h 出分钟, <16h 出小时, 否则按 8h/人日 出天。
export function fmtHours(h) {
  if (h == null || !isFinite(h) || h <= 0) return '—';
  if (h < 1) return Math.max(1, Math.round(h * 60)) + ' 分钟';
  if (h < 16) return (h < 10 ? h.toFixed(1) : Math.round(h)) + ' 小时';
  const d = h / 8;
  return (d < 10 ? d.toFixed(1) : Math.round(d)) + ' 人日';
}

// 已完成的实际耗时 (墙钟: 起始→完成)。返回 {hours, est, delta} 或 null。
// 起始优先 startedAt (真正开工), 缺则退回 createdAt。delta = 实际/预估 - 1。
export function actualOf(task) {
  const end = task.finishedAt, start = task.startedAt || task.createdAt;
  if (!end || !start || end <= start) return null;
  const hours = (end - start) / 3600000;
  const est = Number(task.estimate) || 0;
  return { hours, est, delta: est ? hours / est - 1 : null };
}

// 偏差人话: "+35%" / "-12%"; 5% 以内算准, 返回 null。
function deltaText(d) {
  if (d == null || Math.abs(d) < 0.05) return null;
  return (d > 0 ? '超出 +' : '提前 ') + Math.round(Math.abs(d) * 100) + '%';
}

// 一行摘要: 未完成出 "剩余约 3.5 小时 (关键路径 2h · ...)"; 已完成出 "实际耗时 X (预估 Y · 超出 +30%)"
export function etaText(task, maxActive) {
  const st = task.status || 'planning';
  if (st === 'done' || st === 'archived') {
    const a = actualOf(task);
    if (!a) return null;
    const parts = [];
    if (a.est) parts.push(`预估 ${fmtHours(a.est)}`);
    const dt = deltaText(a.delta);
    if (dt) parts.push(dt);
    return { main: `实际耗时 ${fmtHours(a.hours)}`, detail: parts.join(' · '), actual: a };
  }
  const e = etaOf(task, maxActive);
  if (!e) return null;
  const parts = [];
  if (e.critical) parts.push(`关键路径 ${fmtHours(e.critical)}`);
  if (e.own) parts.push(`自身开销 ${fmtHours(e.own)}`);
  if (Math.abs(e.calib - 1) > 0.05) parts.push(`实测校准 ×${e.calib.toFixed(2)}`);
  return { main: `剩余约 ${fmtHours(e.hours)}`, detail: parts.join(' · '), eta: e };
}

// ---- 执行阶段子时间线: 每个 subtask 的执行过程 (默认折叠) ----
// board 详情面板 / task 详情页共用 (与 buildTimeline 同模式, 挂在时间线「执行」节点下)
const TL_SUB_COLOR = {
  planning: 'st-planning', ready: 'st-ready',
  active:   'st-active',  check: 'st-check',
  done:     'st-done',    failed: 'st-failed',
};
const TL_SUB_LABEL = {
  planning: '规划中', ready: '待执行',
  active:   '执行中', check: '验收中',
  done:     '已完成', failed: '失败',
};
export function subTimelineView(subs, taskId) {
  const ordered = [...subs].sort((a, b) => (a.startedAt || Infinity) - (b.startedAt || Infinity));
  return h('details.tl-sub', [
    h('summary.tl-sub-sum', `子任务执行过程 (${subs.length})`),
    h('div.tl-sub-list',
      ordered.map(s => {
        const st = s.status || 'planning';
        // 已完成: 实际耗时 + 与预估的对比; 未完成: 只出预估
        const est = (typeof s.estimate === 'number' && s.estimate > 0) ? s.estimate : 0;
        let dur = '';
        if (s.startedAt && s.finishedAt) {
          const act = (s.finishedAt - s.startedAt) / 3600000;
          const dt = est ? deltaText(act / est - 1) : null;
          dur = `实际 ${fmtHours(act)}` + (est ? ` / 预估 ${fmtHours(est)}` : '')
              + (dt ? ` (${dt})` : '');
        } else if (est) {
          dur = `预估 ${fmtHours(est)}`;
        }
        return h('div.tl-sub-item', [
          h(`span.w-1.5.h-1.5.rounded-full.flex-shrink-0.mt-1.5.bg-${TL_SUB_COLOR[st]}`),
          h('div.min-w-0.flex-1', [
            h('div.flex.items-center.gap-2.min-w-0', [
              h('span.text-xs.text-fg.truncate', s.title || s.name || s.sid),
              subIdChip(taskId, s),
            ]),
            h('div.text-xs.text-muted.mt-0.5',
              [TL_SUB_LABEL[st] || st,
               s.startedAt ? `起 ${fmtTime(s.startedAt)}` : null,
               s.finishedAt ? `止 ${fmtTime(s.finishedAt)}` : null,
               dur || null,
              ].filter(Boolean).join(' · ')),
          ]),
        ]);
      })
    ),
  ]);
}

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
    estimate: s.estimate != null ? Number(s.estimate) : null,
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

// ── ID 点击复制 (taskId / subtaskId) ──
// ponytail: 原地文案反馈 800ms 后还原, 不加 toast 组件
// opts: { label 显示文本(默认 '#'+text) / copy 实际写剪贴板内容(默认 text) / cls 附加 class }
export function copyChip(text, opts) {
  const o = opts || {};
  const label = o.label != null ? o.label : ('#' + text);
  const copyText = o.copy != null ? o.copy : text;
  const txt = h('span.copy-chip-text', label);
  const el = h('span.copy-chip',
    { class: o.cls || null, title: '点击复制: ' + copyText, role: 'button', tabindex: '0' },
    [txt, h('i.fa.fa-square-o.copy-chip-icon')]);   // fa 子集无 fa-clone/fa-copy, 用已有 square-o
  let timer = null;
  const fire = async (e) => {
    e.preventDefault();
    e.stopPropagation();   // 卡片/DAG 节点父级带 click 导航, 复制不该顺带跳转
    const ok = await writeClipboard(copyText);
    el.classList.add(ok ? 'is-copied' : 'is-failed');
    txt.textContent = ok ? '已复制' : '复制失败';
    clearTimeout(timer);
    timer = setTimeout(() => {
      el.classList.remove('is-copied', 'is-failed');
      txt.textContent = label;
    }, 800);
  };
  el.addEventListener('click', fire);
  el.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') fire(e); });
  return el;
}

// subtask 的 id chip: 显示裸 sid, 复制 `<taskId> <sid>` (可整段粘进 skein subtask 命令)
export function subIdChip(taskId, sub) {
  const sid = sub && (sub.sid || sub.id);
  if (!sid) return null;
  return copyChip(sid, {
    label: sid,
    copy: taskId ? taskId + ' ' + sid : sid,
    cls: 'copy-chip-sub font-mono text-xs text-muted',
  });
}

async function writeClipboard(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch { /* 落 execCommand 兜底 */ }
  // skein serve 走 http://localhost, 非 secure context 时 clipboard API 不可用
  try {
    const ta = h('textarea', { style: { position: 'fixed', left: '-9999px', opacity: '0' } });
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand('copy');
    ta.remove();
    return ok;
  } catch { return false; }
}

// ── 确认 / 提示弹窗 (替 window.confirm/alert, 走站内样式) ──
// ponytail: 原生 <dialog> + 已有 .dag-modal 样式, 不写 overlay/焦点陷阱 (dialog.showModal 自带)
// 返回 Promise<boolean>: 确定 true, 取消/Esc/点关闭 false。cancel: null → 单按钮提示框。
export function confirmDialog(opts) {
  const o = opts || {};
  const { title = '确认', message = '', ok = '确定', cancel = '取消', danger = false } = o;
  return new Promise((resolve) => {
    let settled = false;
    const finish = (v) => {
      if (settled) return;
      settled = true;
      dlg.close();
      dlg.remove();
      resolve(v);
    };
    const dlg = h('dialog.dag-modal',
      { onclose: () => finish(false) },   // Esc / 外部 close 一律当取消
      h('div.dag-modal-inner', [
        h('div.dag-modal-head', [
          h('h3.dag-modal-title', [
            // 图标限 icons.css 子集内 (fa 子集只含实际用到的字形, 加新图标要重生成 woff2)
            h(`i.fa.${danger ? 'fa-exclamation-triangle' : 'fa-check-circle'}`),
            title,
          ]),
          h('button.dag-modal-close', { onclick: () => finish(false), title: '关闭' }, '×'),
        ]),
        h('div.text-sm.text-fg.whitespace-pre-wrap.leading-relaxed', message),
        h('div.flex.justify-end.gap-2.mt-2', [
          cancel ? h('button.antd-btn.antd-btn-default', { onclick: () => finish(false) }, cancel) : null,
          h('button.antd-btn' + (danger ? '.antd-btn-danger' : ''),
            { onclick: () => finish(true) }, ok),
        ]),
      ]));
    document.body.appendChild(dlg);
    dlg.showModal();
  });
}

export function alertDialog(message, title) {
  return confirmDialog({ title: title || '提示', message, ok: '知道了', cancel: null });
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
