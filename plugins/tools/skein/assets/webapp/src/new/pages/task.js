// SKEIN webapp · task 页 (htm + 原生 DOM 重写版, 替 petite-vue)。
// 单 task 审阅 — 两栏: 左 (时间线 + subtask DAG + subtask 列表 + 目标/边界/验收)
//                  右 (文档 tab: design / PRD / findings / research).
// 只读视图 (无命令快捷条 — 已被 skein 移除); 数据 api.task(id) 一次拉全, onLive 定向订阅软刷。
//
// render(mount, params, ctx) 契约: core `[arch] SPA page 模块统一契约`
//   ctx = { api, md, h, onLive, navigate }
//   onLive(cb, {taskId}) 定向订阅 WS task-changed (router 切页自动退订)。
//
// ponytail: 外壳 ctx.h() 构造真 DOM + 内层 HTML 串 (含 SVG dagHtml) 经 innerHTML 注入 — 对齐
//           board.js 已验证模式。import dag.js 复用 Sugiyama (未重造)。tab/滚动状态重挂前抽 DOM 保活。
import { dagHtml, setNodeMaps } from "../../dag.js";
import { parsePrdSections, findSection } from "../../prd-parse.js";

// 状态中文 → badge 令牌类 (task S_* 与 subtask SS_* 合并; 运行中 复用 active 色)
const BADGE = {
  "待处理": "badge-pending", "就绪": "badge-pending", "进行中": "badge-active", "运行中": "badge-active",
  "检查中": "badge-check", "已完成": "badge-done", "失败": "badge-failed",
};
const badgeCls = (st) => BADGE[st] || "badge-pending";

// task 阶段 label (plan/exec/check/done): task.json 无 stage 字段, 由 status 派生。
// ponytail: 详情接口 _task_detail 直返 task.json 原文无 stage, 前端就近派生, 不改后端契约。
const STAGE_OF = { "已完成": "done", "检查中": "check", "进行中": "exec", "运行中": "exec", "就绪": "ready", "待处理": "plan" };
const stageOf = (st) => STAGE_OF[st] || "plan";
const STAGE_LABEL = { plan: "plan", ready: "ready", exec: "exec", check: "check", done: "done" };
const STAGE_CLS = { plan: "stg-plan", ready: "stg-ready", exec: "stg-exec", check: "stg-check", done: "stg-done" };
function stageChip(status) {
  const s = stageOf(status), lbl = STAGE_LABEL[s];
  return lbl ? '<span class="stage-chip ' + STAGE_CLS[s] + '">' + lbl + "</span>" : "";
}

// DAG 节点染色映射 (status → CSS 变量 / class)。对齐后端 _board_data 的 node_var/node_cls。
// ponytail: _task_detail 不返回 nodeVar/nodeCls, 此处硬编码同一份 (task/subtask 状态中文集合的并集)。
const NODE_VAR = {
  "待处理": "--st-pending", "就绪": "--st-pending", "进行中": "--st-active", "运行中": "--st-active",
  "检查中": "--st-check", "已完成": "--st-done", "失败": "--st-failed",
};
const NODE_CLS = {
  "待处理": "n-pending", "就绪": "n-pending", "进行中": "n-active", "运行中": "n-active",
  "检查中": "n-check", "已完成": "n-done", "失败": "n-failed",
};

// 页内样式: 两栏布局 + markdown 渲染体 + DAG SVG 染色 + 合并时间线 + stage-chip + copy-id.
// board.js 的 .dag g.n-* rect 染色规则在此复刻一份 (task 详情页 DAG 独立渲染, 不引 board BOARD_CSS)。
const TASK_CSS = `
.task-layout{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,3fr);gap:16px;align-items:start}
@media(max-width:900px){.task-layout{grid-template-columns:1fr}}
.tl-col{display:flex;flex-direction:column;gap:16px;min-width:0}
/* markdown 渲染体 (右栏文档 + 左栏目标/验收 共用) */
.md-body{font-size:14px;line-height:1.7;word-wrap:break-word}
.md-body>:first-child{margin-top:0}.md-body>:last-child{margin-bottom:0}
.md-body h1,.md-body h2,.md-body h3,.md-body h4{color:var(--head);font-weight:650;line-height:1.3;margin:1.2em 0 .5em}
.md-body h1{font-size:1.5em;padding-bottom:.25em;border-bottom:1px solid var(--line)}
.md-body h2{font-size:1.25em;padding-bottom:.2em;border-bottom:1px solid var(--line)}
.md-body h3{font-size:1.1em}
.md-body p{margin:.6em 0}
.md-body ul,.md-body ol{margin:.6em 0;padding-left:1.6em}
.md-body li{margin:.25em 0}
.md-body li::marker{color:var(--muted)}
.md-body ul:has(>li>input[type=checkbox]),.md-body li:has(>input[type=checkbox]){list-style:none}
/* 自绘 checkbox: 原生 disabled 未勾在暗底渲成灰实心方块 (误读为已完成) → appearance:none 空心框; 勾选才 accent 填充 + ✓ */
.md-body li>input[type=checkbox]{appearance:none;-webkit-appearance:none;box-sizing:border-box;width:13px;height:13px;margin:0 .5em 0 -1.3em;vertical-align:-2px;position:relative;border:1.5px solid var(--muted);border-radius:3px;background:transparent}
.md-body li>input[type=checkbox]:checked{background:var(--accent);border-color:var(--accent)}
.md-body li>input[type=checkbox]:checked::after{content:"";position:absolute;left:3.5px;top:.5px;width:3px;height:6.5px;border:solid #fff;border-width:0 2px 2px 0;transform:rotate(45deg)}
.md-body code{background:color-mix(in srgb,var(--muted) 18%,transparent);border-radius:5px;padding:.12em .35em;font-size:.88em;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.md-body pre{background:color-mix(in srgb,var(--fg) 6%,transparent);border:1px solid var(--line);border-radius:9px;padding:12px 14px;overflow-x:auto;margin:.8em 0;line-height:1.5}
.md-body pre code{background:none;padding:0;font-size:.86em}
.md-body blockquote{border-left:3px solid var(--accent);margin:.8em 0;padding:.2em 0 .2em 14px;color:var(--muted)}
.md-body hr{border:none;border-top:2px solid var(--line);margin:1.2em 0}
.md-body a{color:var(--accent);text-decoration:none}
.md-body a:hover{text-decoration:underline}
.md-body strong{color:var(--head);font-weight:650}
.md-body table{border-collapse:collapse;margin:.8em 0;width:auto;max-width:100%;display:block;overflow-x:auto;font-size:.92em}
.md-body th,.md-body td{border:1px solid var(--brd);padding:6px 11px;text-align:left}
.md-body th{background:color-mix(in srgb,var(--muted) 8%,transparent);color:var(--head);font-weight:600}
.copy-id{background:none;border:1px solid var(--line);color:var(--muted);font-size:11px;line-height:1;cursor:pointer;padding:2px 5px;border-radius:5px;vertical-align:middle;margin-left:4px}
.copy-id:hover{background:var(--sel-bg);color:var(--head);border-color:var(--accent)}
/* DAG SVG 节点状态染色 (迁自 board.js, 给 task 详情页 subtask DAG 用) */
.task-dag{overflow:auto;max-width:100%}
.task-dag .dag{display:block;max-width:100%;height:auto;margin:0 auto}
.task-dag g.n-pending>rect:first-of-type{fill:color-mix(in srgb,var(--st-pending) 15%,var(--bg));stroke:var(--st-pending)}
.task-dag g.n-active>rect:first-of-type{fill:color-mix(in srgb,var(--st-active) 15%,var(--bg));stroke:var(--st-active);stroke-width:2}
.task-dag g.n-check>rect:first-of-type{fill:color-mix(in srgb,var(--st-check) 15%,var(--bg));stroke:var(--st-check)}
.task-dag g.n-done>rect:first-of-type{fill:color-mix(in srgb,var(--st-done) 15%,var(--bg));stroke:var(--st-done)}
.task-dag g.n-failed>rect:first-of-type{fill:color-mix(in srgb,var(--st-failed) 15%,var(--bg));stroke:var(--st-failed)}
.back-btn{display:inline-flex;align-items:center;gap:4px;font-size:13px;color:var(--muted);background:transparent;border:1px solid var(--brd);border-radius:8px;padding:4px 10px;cursor:pointer}
.back-btn:hover{color:var(--accent);border-color:var(--accent)}
/* task 阶段 chip (与 board.js 同色语义: plan=muted/exec=accent/check=st-check/done=st-done) */
.stage-chip{display:inline-block;padding:0 7px;border-radius:9px;font-size:10px;line-height:17px;font-weight:600;letter-spacing:.02em;vertical-align:baseline;color:#fff}
.stage-chip.stg-plan{background:var(--muted)}
.stage-chip.stg-ready{background:var(--st-pending)}
.stage-chip.stg-exec{background:var(--accent)}
.stage-chip.stg-check{background:var(--st-check)}
.stage-chip.stg-done{background:var(--st-done)}
/* subtask 列表卡片 */
.sub-card{border:1px solid var(--line);border-radius:8px;padding:12px;background:var(--card)}
.sub-active{border-color:var(--accent);box-shadow:inset 2px 0 0 var(--accent)}
/* 合并时间线 (竖向圆点+连线, task 五态节点(强调点)与 subtask 事件(弱点)共轴) */
.tl-timeline{position:relative;padding-left:18px}
.tl-timeline::before{content:"";position:absolute;left:4px;top:4px;bottom:4px;width:1px;background:var(--line)}
.tl-item{position:relative;padding:4px 0 4px 14px;display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;font-size:12.5px}
.tl-item-dot{position:absolute;left:-14px;top:9px;width:8px;height:8px;border-radius:50%;border:2px solid var(--card)}
.tl-item-dot-task{background:var(--accent)}
.tl-item-dot-sub{background:var(--muted)}
.tl-item-label{color:var(--head)}
.tl-item-time{color:var(--muted);font-size:11.5px}
/* 进度条 (subtask) */
.sub-pct{display:flex;align-items:center;gap:8px;margin-top:8px}
.sub-pct-track{flex:1;height:6px;border-radius:3px;overflow:hidden;background:var(--line)}
.sub-pct-fill{height:100%;border-radius:3px;background:var(--st-done)}
.sub-pct-n{font-size:11px;color:var(--muted);width:36px;text-align:right}
/* 加载骨架 / 错误态 */
.task-skel{padding:64px 24px;text-align:center;color:var(--muted)}
.task-skel .spin{font-size:28px;color:var(--accent)}
.task-err{padding:64px 24px;text-align:center;color:var(--st-failed)}
`;

// 右栏文档 tab 顺序: 详细设计优先 (默认), PRD 次之, 调研收敛最后。
const DOC_TABS = [
  { key: "design", label: "详细设计" },
  { key: "prd", label: "PRD" },
  { key: "findings", label: "调研收敛" },
  { key: "research", label: "调研过程" },
];

// task 生命周期五态节点 (created/confirmed/started/checked/finished)。
const TASK_TS_LABELS = [
  ["created", "创建"], ["confirmed", "就绪"], ["started", "起始"], ["checked", "检查"], ["finished", "完成"],
];

// html 转义 (command 输出走 innerHTML, 防 XSS)
function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

// 混合时间格式: null → "-"; 否则 MM-DD HH:mm + 相对当前 (Xh ago / Xd ago)。
// ponytail: 相对粒度到小时/天够用, 分钟级抖动大不展示。
function fmtMix(ts) {
  if (!ts) return "-";
  const d = new Date(ts * 1000);
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  const hrs = Math.floor((Date.now() / 1000 - ts) / 3600);
  const rel = hrs >= 24 ? Math.floor(hrs / 24) + "d ago" : hrs + "h ago";
  return mm + "-" + dd + " " + hh + ":" + mi + " (" + rel + ")";
}

// subtask 完成百分比 (对齐后端 _sub_pct: done 强制 100; 验收done/验收, 无验收未完成即 0)
function subPct(s) {
  if (s.status === "已完成") return 100;
  const crit = (s["验收"] || []).length;
  return crit ? Math.round(((s["验收done"] || []).length / crit) * 100) : 0;
}

// 从 task.subtasks 构造 DAG 节点数组: [sid, name, status, depends_on(sid 数组), pct, desc]。
// 对齐后端 _board_data 的 node() 形状; dagHtml 自行按 depends_on 连边 (无需显式 links)。
function buildSubDag(subtasks) {
  if (!subtasks || subtasks.length < 1) return "";
  const nodes = subtasks.map((s) => [
    s.sid, s.name || s.sid, s.status, s.depends_on || [], subPct(s), s.desc || "",
  ]);
  return dagHtml(nodes, null, null, nodes.length > 4);
}

// 合并时间线: task 五态时刻 + 各 subtask 建/起/讫事件, 过滤 null/undefined, 按 ts 升序。
// ponytail: 老 task 无 confirmed 键(undefined) 与未到达态(null) 同走 falsy 分支自然跳过, 无需分别判空。
function buildTimeline(task, subtasks) {
  const evs = [];
  for (const [key, label] of TASK_TS_LABELS) {
    if (task && task[key]) evs.push({ ts: task[key], label, tag: "task", name: "" });
  }
  for (const s of subtasks || []) {
    const name = s.name || s.sid;
    if (s.created) evs.push({ ts: s.created, label: "建", tag: "sub", name });
    if (s.started) evs.push({ ts: s.started, label: "起", tag: "sub", name });
    if (s.finished) evs.push({ ts: s.finished, label: "讫", tag: "sub", name });
  }
  evs.sort((a, b) => a.ts - b.ts);
  return evs;
}

// 时间线 HTML 串 (合并 task 五态 + subtask 事件)
function timelineHtml(timeline) {
  if (!timeline || !timeline.length) return "";
  const items = timeline.map((ev) =>
    '<div class="tl-item">' +
    '<span class="tl-item-dot ' + (ev.tag === "task" ? "tl-item-dot-task" : "tl-item-dot-sub") + '"></span>' +
    '<span class="tl-item-label">' + esc(ev.tag === "task" ? ev.label : ev.name + " · " + ev.label) + "</span>" +
    '<span class="tl-item-time">' + esc(fmtMix(ev.ts)) + "</span>" +
    "</div>"
  ).join("");
  return '<div class="tl-timeline">' + items + "</div>";
}

// subtask 列表 HTML 串
function subListHtml(subtasks) {
  if (!subtasks || !subtasks.length) {
    return '<div class="text-muted text-center py-8 text-sm">尚无子任务拆分</div>';
  }
  return subtasks.map((s) => {
    const pct = subPct(s);
    const deps = (s.depends_on || []).join(", ");
    return '<div class="sub-card' + (s.status === "运行中" ? " sub-active" : "") + '">' +
      '<div class="flex items-center gap-2 flex-wrap">' +
      '<code class="text-xs" style="color:var(--head)">' + esc(s.sid) + "</code>" +
      '<button type="button" class="copy-id" data-copy="' + esc(s.sid) + '" title="复制 id">⧉</button>' +
      '<span class="text-sm">' + esc(s.name || s.sid) + "</span>" +
      '<span class="badge ' + badgeCls(s.status) + '">' + esc(s.status) + "</span>" +
      '<span class="flex-1"></span>' +
      (s.agent ? '<span class="text-[11px] text-muted">' + esc(s.agent) + "</span>" : "") +
      "</div>" +
      (s.desc ? '<p class="text-xs text-muted mt-1 whitespace-pre-wrap">' + esc(s.desc) + "</p>" : "") +
      '<div class="sub-pct">' +
      '<div class="sub-pct-track"><div class="sub-pct-fill" style="width:' + pct + '%"></div></div>' +
      '<span class="sub-pct-n">' + pct + "%</span>" +
      "</div>" +
      (deps ? '<div class="text-[11px] text-muted mt-1">依赖: ' + esc(deps) + "</div>" : "") +
      '<div class="text-[11px] text-muted mt-1 flex flex-wrap gap-x-3 gap-y-0.5">' +
      "<span>建: " + esc(fmtMix(s.created)) + "</span>" +
      "<span>起: " + esc(fmtMix(s.started)) + "</span>" +
      "<span>讫: " + esc(fmtMix(s.finished)) + "</span>" +
      "</div>" +
      "</div>";
  }).join("");
}

// ── 主 render 入口 ──
export async function render(mount, params, ctx) {
  const { api, md, h, onLive } = ctx;

  // 无 id → 列表视图 (复用 /__skein__/data → cards; 不走 api.task 避免 404)
  if (!params.id) {
    return renderList(mount, params, ctx);
  }

  // 注入页内样式 (随 #view 清空自动移除, 不污染他页)
  const styleEl = h("style", { html: TASK_CSS });
  const header = h("header", { class: "antd-card p-5 mb-4" });
  const layout = h("div", { class: "task-layout" });
  const leftCol = h("div", { class: "tl-col" });
  const rightCol = h("section", { class: "antd-card overflow-hidden" });
  const contractsCol = h("section", { class: "antd-card p-5 mt-4" });
  const skel = h("div", { class: "task-skel" },
    h("div", { class: "spin", "aria-hidden": "true" }, "◐"),
    h("div", { class: "mt-2 text-sm" }, "加载 task 详情…")
  );
  mount.append(styleEl, header, layout, skel);
  layout.append(leftCol, rightCol);

  let savedTab = null, savedScroll = 0;
  let lastDataSig = null;

  async function fetchState() {
    try {
      const r = await api.task(params.id);
      return { loadErr: "", notFound: false,
        task: r.task || {}, docs: r.docs || {},
        research: r.research || {},
        subtasks: r.subtasks || [], contracts: r.contracts || [], archived: !!r.archived };
    } catch (e) {
      const notFound = e && e.status === 404;
      return { notFound,
        loadErr: notFound ? "未找到 task「" + params.id + "」— 可能不存在或已清理。"
                          : (e && e.message) || String(e),
        task: {}, docs: {}, research: {}, subtasks: [], contracts: [], archived: false };
    }
  }

  async function refresh() {
    // 抽旧 DOM 状态 (tab/滚动), 重挂后回填
    const curTab = layout.getAttribute("data-cur-tab");
    if (curTab) savedTab = curTab;
    savedScroll = window.scrollY;

    const st = await fetchState();

    // 错误态: 清骨架 + 渲染错误框
    if (st.loadErr) {
      skel.remove();
      header.innerHTML = "";
      layout.style.display = "none";
      contractsCol.remove();
      const errBox = h("div", { class: "antd-card p-10 text-center text-muted" },
        h("div", { class: "empty-ico", style: { color: st.notFound ? "var(--accent)" : "var(--st-failed)" }, html:
          st.notFound
          ? '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
          : '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
        }),
        h("div", { class: "text-sm", style: { color: st.notFound ? "var(--muted)" : "var(--st-failed)" } }, st.loadErr),
        h("a", { href: "/", class: "inline-block mt-4 text-sm", style: { color: "var(--accent)" } }, "← 返回看板")
      );
      mount.append(errBox);
      return;
    }

    // 数据签名去抖 (WS 频繁推送同数据不重渲染)
    const sig = JSON.stringify(st);
    if (sig === lastDataSig) return;
    lastDataSig = sig;

    // DAG 染色映射注入 (每次渲染前; dag.js 模块级 NODE_VAR/NODE_CLS 单例)
    setNodeMaps(NODE_VAR, NODE_CLS);
    const subDag = buildSubDag(st.subtasks);
    const timeline = buildTimeline(st.task, st.subtasks);
    const prdSecs = parsePrdSections(st.docs.prd || "");
    const goalHtml = md.renderSafe(findSection(prdSecs, "目标"));
    const boundaryHtml = md.renderSafe(findSection(prdSecs, "边界"));
    const acceptHtml = md.renderSafe(findSection(prdSecs, "验收标准", "验收"));

    // 默认 tab: design 优先, design 为空则回落 prd
    const defaultTab = st.docs.design ? "design" : "prd";
    const curTab0 = savedTab || defaultTab;

    // 渲染头部
    const t = st.task;
    header.innerHTML =
      '<div class="flex items-center gap-3 flex-wrap">' +
      '<button type="button" class="back-btn" id="task-back">← 返回</button>' +
      '<code class="text-sm px-2 py-0.5 rounded" style="background:var(--line);color:var(--head)">' + esc(t.id) + "</code>" +
      '<button type="button" class="copy-id" data-copy="' + esc(t.id) + '" title="复制 id">⧉</button>' +
      (t.name ? '<h1 class="text-lg font-semibold" style="color:var(--head)">' + esc(t.name) + "</h1>" : "") +
      '<span class="badge ' + badgeCls(t.status) + '">' + esc(t.status) + "</span>" +
      stageChip(t.status) +
      (st.archived ? '<span class="badge badge-done opacity-70">已归档</span>' : "") +
      '<span class="flex-1"></span>' +
      (t.deps && t.deps.length ? '<span class="text-xs text-muted">依赖 ' + esc(t.deps.join(", ")) + "</span>" : "") +
      "</div>" +
      (t.desc ? '<p class="text-sm text-muted mt-2 whitespace-pre-wrap">' + esc(t.desc) + "</p>" : "");

    // 渲染左栏 (时间线 + subtask DAG + subtask 列表 + 目标/边界/验收)
    const leftParts = [];
    if (timeline.length) {
      leftParts.push(
        '<section class="antd-card p-5">' +
        '<h2 class="text-sm font-semibold mb-3" style="color:var(--head)">时间线</h2>' +
        timelineHtml(timeline) +
        "</section>"
      );
    }
    if (subDag) {
      leftParts.push(
        '<section class="antd-card p-4">' +
        '<div class="flex items-center gap-2 mb-3">' +
        '<h2 class="text-sm font-semibold" style="color:var(--head)">子任务图</h2>' +
        '<span class="text-xs text-muted">' + st.subtasks.length + "</span>" +
        "</div>" +
        '<div class="task-dag">' + subDag + "</div>" +
        "</section>"
      );
    }
    leftParts.push(
      '<section class="antd-card p-5">' +
      '<div class="flex items-center gap-2 mb-3">' +
      '<h2 class="text-sm font-semibold" style="color:var(--head)">子任务</h2>' +
      '<span class="text-xs text-muted">' + st.subtasks.length + "</span>" +
      "</div>" +
      '<div class="space-y-2">' + subListHtml(st.subtasks) + "</div>" +
      "</section>"
    );
    if (goalHtml) {
      leftParts.push(
        '<section class="antd-card p-5">' +
        '<h2 class="text-sm font-semibold mb-2" style="color:var(--head)">目标</h2>' +
        '<div class="md-body">' + goalHtml + "</div>" +
        "</section>"
      );
    }
    if (boundaryHtml) {
      leftParts.push(
        '<section class="antd-card p-5">' +
        '<h2 class="text-sm font-semibold mb-2" style="color:var(--head)">边界</h2>' +
        '<div class="md-body">' + boundaryHtml + "</div>" +
        "</section>"
      );
    }
    if (acceptHtml) {
      leftParts.push(
        '<section class="antd-card p-5">' +
        '<h2 class="text-sm font-semibold mb-2" style="color:var(--head)">验收标准</h2>' +
        '<div class="md-body">' + acceptHtml + "</div>" +
        "</section>"
      );
    }
    leftCol.innerHTML = leftParts.join("");

    // 渲染右栏 (文档 tab)
    layout.setAttribute("data-cur-tab", curTab0);
    rightCol.innerHTML = buildRightColHtml(curTab0, st, md);

    // 渲染契约区 (空则隐藏)
    if (st.contracts && st.contracts.length) {
      contractsCol.innerHTML =
        '<div class="flex items-center gap-2 mb-3">' +
        '<h2 class="text-sm font-semibold" style="color:var(--head)">契约</h2>' +
        '<span class="text-xs text-muted">' + st.contracts.length + "</span>" +
        "</div>" +
        '<ol class="space-y-1.5">' +
        st.contracts.map((c, i) =>
          '<li class="text-sm flex gap-2"><span class="text-muted select-none">' + (i + 1) + '.</span>' +
          '<span class="whitespace-pre-wrap">' + esc(c) + "</span></li>"
        ).join("") +
        "</ol>";
      if (!contractsCol.parentNode) mount.append(contractsCol);
    } else {
      contractsCol.remove();
    }

    if (skel.parentNode) skel.remove();
    layout.style.display = "";

    // 绑定 tab 切换 + 返回 + copy-id
    bindInteractions(rightCol, layout, st, md);

    // 恢复滚动: rAF 等 DOM 布局完成后再 scrollTo
    if (savedScroll) requestAnimationFrame(() => window.scrollTo(0, savedScroll));
  }

  await refresh();
  // ponytail: 定向订阅 task-changed (onLive 带 taskId 过滤); 软刷整体重挂, refresh 内抽 tab/滚动保活。
  if (onLive) {
    const unsub = onLive(function () { refresh().catch(function () {}); }, { taskId: params.id });
    return [unsub];
  }
}

// 右栏文档 tab HTML 串 (含 tab 头 + 当前 tab 内容)
function buildRightColHtml(curTab, st, md) {
  const tabsHead = '<div class="flex" style="border-bottom:1px solid var(--line)">' +
    DOC_TABS.map((d) => {
      const empty = !st.docs[d.key] && !(d.key === "research" && Object.keys(st.research || {}).length);
      const on = curTab === d.key;
      return '<button type="button" class="px-4 py-2 text-sm relative" data-tab="' + d.key + '"' +
        ' style="' + (on ? "color:var(--accent);border-bottom:2px solid var(--accent)" : "color:var(--muted)") + '">' +
        esc(d.label) +
        (empty ? '<span class="ml-1 text-[10px] opacity-50">空</span>' : "") +
        "</button>";
    }).join("") + "</div>";

  let body;
  if (curTab === "research" && Object.keys(st.research || {}).length === 0) {
    body = '<div class="text-muted text-center py-16 text-sm">' +
      '<div class="empty-ico"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>暂无调研笔记</div>';
  } else if (curTab === "research") {
    const keys = Object.keys(st.research).sort();
    body = '<div class="space-y-3">' +
      keys.map((name) =>
        '<div class="rounded p-4" style="border:1px solid var(--line)">' +
        '<div class="text-sm font-semibold mb-2" style="color:var(--head)">' + esc(name) + "</div>" +
        '<div class="md-body">' + md.renderSafe(st.research[name] || "") + "</div>" +
        "</div>"
      ).join("") + "</div>";
  } else if (!st.docs[curTab]) {
    const label = (DOC_TABS.find((d) => d.key === curTab) || {}).label || curTab;
    body = '<div class="text-muted text-center py-16 text-sm">' +
      '<div class="empty-ico"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>' +
      esc(label) + " 暂无内容</div>";
  } else if (curTab === "prd") {
    // PRD: 按 ## 章节拆 card 竖排
    const map = parsePrdSections(st.docs.prd || "");
    const secs = Object.keys(map);
    if (!secs.length) {
      body = '<div class="md-body">' + md.renderSafe(st.docs.prd || "") + "</div>";
    } else {
      body = '<div class="space-y-3">' +
        secs.map((title) =>
          '<div class="rounded p-4" style="border:1px solid var(--line)">' +
          (title ? '<div class="text-sm font-semibold mb-2" style="color:var(--head)">' + esc(title) + "</div>" : "") +
          '<div class="md-body">' + md.renderSafe(map[title]) + "</div>" +
          "</div>"
        ).join("") + "</div>";
    }
  } else {
    // design/findings: 整篇 md
    body = '<div class="md-body">' + md.renderSafe(st.docs[curTab] || "") + "</div>";
  }

  return '<div class="p-5">' + tabsHead + "</div>" + '<div class="p-5">' + body + "</div>";
}

// 绑定右栏 tab 切换 + 全局 copy-id + 返回按钮
function bindInteractions(rightCol, layout, st, md) {
  // tab 切换: 重渲染右栏 body (不重拉数据, 用闭包内 st)
  rightCol.querySelectorAll("[data-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const newTab = btn.getAttribute("data-tab");
      layout.setAttribute("data-cur-tab", newTab);
      rightCol.innerHTML = buildRightColHtml(newTab, st, md);
      bindInteractions(rightCol, layout, st, md);
    });
  });
}

// ── 列表视图 (无 id: /task) ──
async function renderList(mount, params, ctx) {
  const { api, h, onLive } = ctx;
  const skel = h("div", { class: "task-skel" },
    h("div", { class: "spin", "aria-hidden": "true" }, "◐"),
    h("div", { class: "mt-2 text-sm" }, "加载任务列表…")
  );
  const styleEl = h("style", { html: TASK_CSS });
  const wrap = h("div", { class: "px-7" });
  mount.append(styleEl, wrap, skel);

  async function refresh() {
    let loadErr = "", items = [];
    try {
      const r = await api.data();
      items = (r && r.cards) || [];
    } catch (e) {
      loadErr = (e && e.message) || String(e);
    }
    if (skel.parentNode) skel.remove();
    if (loadErr) {
      wrap.innerHTML = '<div class="antd-card p-10 text-center text-muted">' +
        '<div class="empty-ico" style="color:var(--st-failed)"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>' +
        '<div class="text-sm" style="color:var(--st-failed)">' + esc(loadErr) + "</div></div>";
      return;
    }
    if (!items.length) {
      wrap.innerHTML = '<div class="antd-card p-16 text-center text-muted">' +
        '<div class="empty-ico"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg></div>' +
        '<div class="text-sm">暂无任务 — 在 .skein/task.json 添加后即显示。</div></div>';
      return;
    }
    wrap.innerHTML =
      '<div class="flex items-center gap-2 mb-4 px-1">' +
      '<h1 class="text-lg font-semibold" style="color:var(--head)">任务</h1>' +
      '<span class="text-xs text-muted">' + items.length + "</span></div>" +
      '<div class="space-y-2">' +
      items.map((t) =>
        '<a class="antd-card block p-4 hover:bg-[var(--line)] transition-colors" href="/task?id=' + encodeURIComponent(t.id) + '">' +
        '<div class="flex items-center gap-2 flex-wrap">' +
        '<code class="text-xs px-1.5 py-0.5 rounded" style="background:var(--line);color:var(--head)">' + esc(t.id) + "</code>" +
        '<span class="text-sm font-medium" style="color:var(--head)">' + esc(t.name || t.id) + "</span>" +
        '<span class="badge ' + badgeCls(t.status) + '">' + esc(t.status) + "</span>" +
        '<span class="flex-1"></span>' +
        '<span class="text-[11px] text-muted shrink-0">' + (t.spct || 0) + "%</span>" +
        "</div>" +
        (t.desc ? '<p class="text-xs text-muted mt-1.5 whitespace-pre-wrap line-clamp-2">' + esc(t.desc) + "</p>" : "") +
        "</a>"
      ).join("") + "</div>";
  }

  await refresh();
  if (onLive) {
    const unsub = onLive(function () { refresh().catch(function () {}); });
    return [unsub];
  }
}
