// SKEIN webapp 看板页: 迁移自 board/board-render.js + switcher.js + doc.js。
// 两栏 (左 sticky 总计+DAG / 右 task 卡片流), 卡片/subtask/SVG DAG/文档弹层, onLive 软刷。
// ponytail: 沿用旧看板的命令式 innerHTML 渲染 + 忠实移植的像素级 dagHtml (Sugiyama), 不重写成
//           petite-vue 响应式 — 那是把已验证的纯函数渲染器整段重造, 收益仅换范式。组件样式从
//           board/base.css 迁进本页 <style> (同一批 CSS 变量, 主题随 <html data-theme> 自动换)。
import { dagHtml, setNodeMaps } from "../dag.js";

// 组件样式: 从 board/base.css 迁移 (令牌变量已由 dist/app.css 的 input.css 定义, 主题自动生效)。
// 顶栏/搜索/fab/switcher 归 webapp topbar, 此处不含。<style> 随 #view 清空自动移除, 不污染他页。
const BOARD_CSS = `
.layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px;align-items:start;margin-top:0}
.col-side{position:sticky;top:var(--topbar,70px);height:calc(100vh - var(--topbar,70px) - 14px)}
.col-side .card{margin-bottom:0;height:100%;overflow:hidden;display:flex;flex-direction:column}
.col-side .card>:not(.dag-view){flex:0 0 auto}
.col-side .dag-view{flex:1 1 auto;min-height:0;display:flex;flex-direction:column}
.col-side .dag-wrap{flex:1 1 auto;min-height:0;max-height:none}
.col-side .dag{max-width:100%;height:auto;margin:4px auto 0}
.col-main{min-width:0}
@media(max-width:900px){.layout{grid-template-columns:1fr}.col-side{position:static;height:auto}.col-side .card{height:auto;overflow:visible;display:block}.col-side .dag-view{display:block}.col-side .dag-wrap{max-height:none}}
.dag-switch{display:inline-flex;margin:2px 0 12px;border:1px solid var(--brd);border-radius:7px;overflow:hidden}
.dag-switch button{border:0;background:var(--card);color:var(--muted);font:12px var(--font);padding:5px 12px;cursor:pointer;transition:background .2s,color .2s}
.dag-switch button+button{border-left:1px solid var(--brd)}
.dag-switch button.on{background:var(--accent);color:#fff}
.dag-switch button:disabled{opacity:.4;cursor:not-allowed}
.dag-view[hidden]{display:none}
.stats{display:flex;gap:8px;margin:0 0 12px;flex-wrap:wrap}
.stat{flex:1 1 0;min-width:54px;background:var(--bg);border:1px solid var(--brd);border-radius:8px;padding:8px 6px;text-align:center;cursor:pointer;font:inherit;color:inherit;transition:border-color .18s,background .18s,box-shadow .18s}
.stat:hover{border-color:var(--accent)}
.stat.on{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 12%,var(--bg));box-shadow:inset 0 0 0 1px var(--accent)}
.stat-n{display:block;font-size:20px;font-weight:600;color:var(--head);line-height:1.1}
.stat-l{display:block;font-size:11px;color:var(--muted);margin-top:2px}
.stat.on .stat-l{color:var(--head)}
.card{background:var(--card);border:1px solid var(--brd);border-radius:var(--radius);padding:20px 24px;margin:0 0 18px;scroll-margin-top:calc(var(--topbar, 70px) + 16px)}
.card.next-up{border-color:var(--accent);box-shadow:inset 3px 0 0 var(--accent)}
.next-up-chip{margin-left:8px;padding:0 8px;border-radius:9px;background:var(--accent);color:var(--bg);font-size:11px;line-height:17px;font-weight:600;vertical-align:baseline}
.card h2{margin:0 0 5px;font-size:17px;font-weight:600;letter-spacing:-.01em;color:var(--head);display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.card-link{color:inherit;text-decoration:none;border-bottom:1px dashed transparent}
.card-link:hover{color:var(--accent);border-bottom-color:var(--accent)}
.card-detail-btn{margin-left:auto;display:inline-flex;align-items:center;color:var(--muted);text-decoration:none;border:1px solid var(--brd);border-radius:6px;padding:2px 4px;transition:color .18s,border-color .18s}
.card-detail-btn:hover{color:var(--accent);border-color:var(--accent)}
.name{margin:0 0 10px;color:var(--head);font-size:15px;font-weight:500}
.meta{margin:0 0 6px;font-size:13px;line-height:1.55;color:var(--muted)}
.badge{display:inline-block;padding:0 8px;border-radius:9px;color:#fff;font-size:11px;line-height:17px;font-weight:500;vertical-align:baseline}
.badge.s-pending,.badge.ss-pending{background:var(--st-pending)}
.badge.s-active,.badge.ss-running{background:var(--st-active)}
.badge.s-check{background:var(--st-check)}
.badge.s-done,.badge.ss-done{background:var(--st-done)}
.badge.ss-failed{background:var(--st-failed)}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:2px}
th,td{text-align:left;padding:4px 7px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:11px;letter-spacing:.02em;white-space:nowrap}
td{line-height:1.4}
.empty{color:var(--muted);font-style:italic;opacity:.8}
.bar{position:relative;background:var(--line);border-radius:4px;height:7px;margin:3px 0 12px;overflow:visible}
.fill{position:relative;overflow:hidden;height:100%;border-radius:4px;background:var(--accent);transition:width .4s;transform-origin:left;animation:bar-in .55s cubic-bezier(.4,0,.2,1)}
.bar.sub .fill{background:var(--accent2)}
.bar.prog .fill{--c:color-mix(in srgb,var(--st-done) calc(var(--p,100)*1%),var(--st-failed));background:linear-gradient(90deg,color-mix(in srgb,var(--c) 62%,var(--bg)),var(--c))}
.pct{position:absolute;top:50%;right:0;left:auto;transform:translateY(-50%);font-size:10px;line-height:1;color:var(--head);background:var(--card);padding:1px 3px;border-radius:3px}
td .bar{margin:1px 0;min-width:78px}
.bar.done .fill::after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(90deg,transparent 0,color-mix(in srgb,#fff 42%,transparent) 50%,transparent 100%);background-size:45% 100%;background-repeat:no-repeat;animation:bar-scan 1.7s linear infinite}
@keyframes bar-scan{from{background-position:-45% 0}to{background-position:145% 0}}
@keyframes bar-in{from{transform:scaleX(0)}}
@media(prefers-reduced-motion:reduce){html:not([data-motion=full]) .fill{animation:none}html:not([data-motion=full]) .bar.done .fill::after{display:none}}
.bar.voff .fill,.bar.voff .fill::after{animation-play-state:paused}
.stage-chip{display:inline-block;margin-left:8px;padding:0 7px;border-radius:9px;font-size:10px;line-height:17px;font-weight:600;letter-spacing:.02em;vertical-align:baseline;color:#fff}
.stage-chip.st-plan{background:var(--muted)}
.stage-chip.st-exec{background:var(--accent)}
.stage-chip.st-check{background:var(--st-check)}
.stage-chip.st-done{background:var(--st-done)}
.dag{display:block;max-width:100%;height:auto;margin:4px 0 8px}
.dag g.n-pending>rect:first-of-type{fill:color-mix(in srgb,var(--st-pending) 15%,var(--bg));stroke:var(--st-pending)}
.dag g.n-active>rect:first-of-type{fill:color-mix(in srgb,var(--st-active) 15%,var(--bg));stroke:var(--st-active);stroke-width:2;transform-box:fill-box;transform-origin:center;animation:node-pulse 1.8s ease-in-out infinite}
.dag g.n-check>rect:first-of-type{fill:color-mix(in srgb,var(--st-check) 15%,var(--bg));stroke:var(--st-check)}
.dag g.n-done>rect:first-of-type{fill:color-mix(in srgb,var(--st-done) 15%,var(--bg));stroke:var(--st-done)}
.dag g.n-failed>rect:first-of-type{fill:color-mix(in srgb,var(--st-failed) 15%,var(--bg));stroke:var(--st-failed)}
@keyframes node-pulse{0%,100%{filter:drop-shadow(0 0 0 transparent)}50%{filter:drop-shadow(0 0 5px var(--st-active))}}
@media(prefers-reduced-motion:reduce){html:not([data-motion=full]) .dag g.n-active>rect:first-of-type{animation:none}}
.dag-wrap{position:relative;overflow:visible;max-width:100%}
.dag-wrap svg .has-tip{cursor:pointer}
.dag svg a,.dag a{cursor:pointer}
.dag a .has-link,.dag .has-link{cursor:pointer}
.dag a:hover rect:first-of-type{stroke-width:2}
.dag-tip{display:none;pointer-events:none;position:fixed;z-index:1000;background:var(--card);border:1px solid var(--brd);border-radius:8px;padding:14px 16px;box-shadow:0 6px 20px rgba(0,0,0,.18);max-width:min(680px,92vw);min-width:360px;max-height:74vh;overflow:auto;font-size:13px;line-height:1.5}
.dag-tip .dag{margin:2px 0 0;max-width:none}
.dag-tip .meta{font-size:13px}
.dag-tip .bar{margin-bottom:10px}
.task-detail{margin-top:6px}
.dag g.dag-dim{opacity:.22;transition:opacity .2s}
.dag g.dag-hit>rect:first-of-type{stroke-width:2.5;filter:drop-shadow(0 0 3px var(--accent))}
.doc-links{display:flex;flex-wrap:wrap;gap:6px;margin:2px 0 8px}
.doc-link{background:var(--sel-bg);color:var(--sel-fg);border:1px solid var(--brd);border-radius:5px;padding:2px 9px;font:12px var(--font);cursor:pointer;transition:background .18s,color .18s}
.doc-link:hover{background:var(--accent);color:#fff;border-color:var(--accent)}
.doc-modal[hidden]{display:none}
.doc-modal{position:fixed;inset:0;z-index:2000;display:flex;align-items:center;justify-content:center;padding:32px}
.doc-backdrop{position:absolute;inset:0;background:rgba(0,0,0,.5)}
.doc-panel{position:relative;background:var(--card);border:1px solid var(--brd);border-radius:var(--radius,12px);width:min(860px,100%);max-height:85vh;display:flex;flex-direction:column;box-shadow:0 12px 40px rgba(0,0,0,.35)}
.doc-head{display:flex;align-items:center;gap:12px;padding:14px 18px;border-bottom:1px solid var(--line)}
.doc-title{flex:1;font-size:14px;font-weight:600;color:var(--head)}
.doc-close{background:none;border:none;color:var(--muted);font-size:16px;cursor:pointer;line-height:1;padding:2px 6px;border-radius:5px}
.doc-close:hover{background:var(--sel-bg);color:var(--head)}
.doc-copy{background:none;border:1px solid var(--line);color:var(--muted);font-size:12px;cursor:pointer;line-height:1;padding:4px 9px;border-radius:6px}
.doc-copy:hover:not(:disabled){background:var(--sel-bg);color:var(--head);border-color:var(--accent)}
.doc-copy:disabled{opacity:.45;cursor:default}
.doc-body{padding:18px 22px;overflow-y:auto;color:var(--fg);font-size:14px;line-height:1.65}
.doc-loading,.doc-err{color:var(--muted)}
.markdown{font-size:14.5px;line-height:1.7;word-wrap:break-word}
.markdown>:first-child{margin-top:0}
.markdown>:last-child{margin-bottom:0}
.markdown h1,.markdown h2,.markdown h3,.markdown h4,.markdown h5,.markdown h6{color:var(--head);font-weight:650;line-height:1.3;margin:1.5em 0 .6em}
.markdown h1{font-size:1.7em;padding-bottom:.3em;border-bottom:1px solid var(--line)}
.markdown h2{font-size:1.35em;padding-bottom:.25em;border-bottom:1px solid var(--line)}
.markdown h3{font-size:1.15em}
.markdown h4{font-size:1em}
.markdown h5,.markdown h6{font-size:.9em;color:var(--muted)}
.markdown p{margin:.75em 0}
.markdown ul,.markdown ol{margin:.75em 0;padding-left:1.7em}
.markdown li{margin:.3em 0}
.markdown li>ul,.markdown li>ol{margin:.3em 0}
.markdown li::marker{color:var(--muted)}
.markdown ul:has(>li>input[type=checkbox]),.markdown li:has(>input[type=checkbox]){list-style:none}
.markdown li>input[type=checkbox]{margin:0 .5em 0 -1.4em;vertical-align:middle;accent-color:var(--accent)}
.markdown code{background:color-mix(in srgb,var(--muted) 18%,transparent);border-radius:5px;padding:.15em .4em;font-size:.88em;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.markdown pre{background:var(--sel-bg);border:1px solid var(--line);border-radius:9px;padding:14px 16px;overflow-x:auto;margin:.9em 0;line-height:1.5}
.markdown pre code{background:none;padding:0;font-size:.86em}
.markdown blockquote{border-left:3px solid var(--accent);margin:.9em 0;padding:.3em 0 .3em 16px;color:var(--muted)}
.markdown blockquote>:first-child{margin-top:0}.markdown blockquote>:last-child{margin-bottom:0}
.markdown hr{border:none;border-top:2px solid var(--line);margin:1.5em 0}
.markdown a{color:var(--accent);text-decoration:none}
.markdown a:hover{text-decoration:underline}
.markdown strong{color:var(--head);font-weight:650}
.markdown img{max-width:100%;border-radius:8px}
.markdown table{border-collapse:collapse;margin:1em 0;width:auto;max-width:100%;display:block;overflow-x:auto;font-size:.92em}
.markdown th,.markdown td{border:1px solid var(--brd);padding:7px 13px;text-align:left}
.markdown th{background:var(--sel-bg);color:var(--head);font-weight:600}
.markdown tr:nth-child(2n) td{background:color-mix(in srgb,var(--muted) 7%,transparent)}
.prd{margin:4px 0 8px;display:flex;flex-direction:column;gap:8px}
.prd-sec{background:color-mix(in srgb,var(--muted) 6%,transparent);border:1px solid var(--line);border-radius:7px;padding:7px 10px}
.prd-h{display:flex;align-items:center;gap:6px;font-size:12px;font-weight:600;color:var(--head);margin-bottom:4px}
.prd-p{margin-left:auto;font-size:11px;font-weight:500;color:var(--muted);background:var(--sel-bg);border-radius:9px;padding:1px 7px}
.prd-list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:2px}
.prd-list li{position:relative;padding-left:18px;font-size:12.5px;line-height:1.5;color:var(--fg)}
.prd-list li::before{content:"○";position:absolute;left:0;color:var(--muted)}
.prd-list li.done{color:var(--muted);text-decoration:line-through}
.prd-list li.done::before{content:"●";color:var(--accent)}
.queue{margin:2px 0 10px;max-height:40vh;overflow-y:auto}
.q-list{list-style:none;margin:4px 0 0;padding:0;display:flex;flex-direction:column;gap:3px}
.q-item{display:flex;align-items:baseline;gap:6px;font-size:12.5px;line-height:1.45}
.q-ord{flex:0 0 auto;width:16px;text-align:right;color:var(--muted);font-size:11px;font-variant-numeric:tabular-nums}
.q-chip{flex:0 0 auto;padding:0 6px;border-radius:8px;font-size:10px;line-height:16px;color:#fff}
.q-ready{background:var(--st-active)}
.q-block{background:var(--st-pending)}
.q-name{flex:1 1 auto;color:var(--fg);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.q-agent{flex:0 0 auto;color:var(--muted);font-size:11px}
.cmd-bar{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 14px}
.cmd-bar .cmd-spacer{flex:1 1 auto}
.cmd-btn{background:var(--card);color:var(--head);border:1px solid var(--brd);border-radius:8px;padding:6px 12px;font:12px var(--font);cursor:pointer;transition:background .18s,border-color .18s}
.cmd-btn:hover{border-color:var(--accent);color:var(--accent)}
.cmd-btn:disabled{opacity:.5;cursor:not-allowed}
.cmd-new{background:var(--accent);color:#fff;border-color:var(--accent)}
.cmd-new:hover{color:#fff;filter:brightness(.95)}
.cmd-form{background:var(--card);border:1px solid var(--brd);border-radius:var(--radius);padding:14px 18px;margin:0 0 14px}
.cmd-form[hidden]{display:none}
.cmd-form .f{display:flex;flex-direction:column;gap:3px;margin-bottom:8px}
.cmd-form .f>span{font-size:11px;color:var(--muted)}
.cmd-form .f>input,.cmd-form .f>textarea{background:var(--bg);color:var(--fg);border:1px solid var(--brd);border-radius:6px;padding:5px 8px;font:13px var(--font);resize:vertical}
.cmd-out{margin-top:10px;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.cmd-out .h{padding:6px 10px;font-size:12px;background:var(--line);color:var(--head);display:flex;align-items:center;gap:8px}
.cmd-out .h .ok{color:var(--st-done)}.cmd-out .h .fail{color:var(--st-failed)}
.cmd-out pre{margin:0;padding:10px;overflow:auto;max-height:320px;font:12px/1.5 var(--font);background:var(--bg);color:var(--fg);white-space:pre-wrap;word-break:break-word}
.cmd-out pre.err{color:var(--st-failed);max-height:220px}
`;

// ── 纯渲染函数 (移植自 board-render.js, 忠实保留像素/边染色逻辑) ──

function esc(s) {
  return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function mdInline(s) {
  s = esc(s);
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  s = s.replace(/\*\*([^*]+?)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/(?<![*\w])[*_]([^*_]+?)[*_](?![*\w])/g, "<em>$1</em>");
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (m, txt, url) {
    if (/^(?:https?:|\/|\.|#)/.test(url) && url.indexOf('"') < 0 && url.indexOf(" ") < 0) {
      return '<a href="' + url + '" target="_blank" rel="noopener">' + txt + "</a>";
    }
    return m;
  });
  return s;
}
function badge(text, clsmap) {
  return '<span class="badge ' + (clsmap[text] || "") + '">' + esc(text) + "</span>";
}
// task 阶段 chip (plan/exec/check/done, 后端 card.stage 提供); 颜色随 stage。
function stageChip(stage) {
  if (!stage) return "";
  var label = { plan: "plan", exec: "exec", check: "check", done: "done" }[stage];
  if (!label) return "";
  return '<span class="stage-chip st-' + stage + '">' + label + "</span>";
}
function fmtDur(mins) {
  if (mins == null) return "-";
  return mins < 60 ? mins + "m" : Math.floor(mins / 60) + "h" + String(mins % 60).padStart(2, "0") + "m";
}
function bar(pct, sub, cls) {
  var p = Math.min(pct, 100);
  var kind = cls || "prog";
  var c = "bar " + kind + (sub ? " sub" : "") + (p >= 100 ? " done" : "");
  var style = "width:" + p + "%" + (kind === "prog" ? ";--p:" + p : "");
  return '<div class="' + c + '"><div class="fill" style="' + style + '"></div><span class="pct">' + p + "%</span></div>";
}

// ── DAG (SVG 有向连接图) 已抽到 src/dag.js (dagHtml + setNodeMaps) ──

function buildTip(tip) {
  var subDag = tip.subNodes ? dagHtml(tip.subNodes, null, null, false) : "";
  if (!subDag) {
    subDag = tip.subs
      ? '<p class="meta">' + tip.subs.map(function (s) { return esc(s.name) + " " + s.pct + "%"; }).join(" · ") + "</p>"
      : '<p class="empty">无 subtask</p>';
  }
  return '<p class="meta">' + esc(tip.name) + " · 总进度</p>" + bar(tip.pct, true, "") + subDag;
}
function prdBlock(prd) {
  if (!prd || !prd.length) return "";
  var parts = prd.filter(function (sec) { return sec.name !== "验收标准"; }).map(function (sec) {
    var b = sec.badge ? '<span class="prd-p">' + sec.badge[0] + "/" + sec.badge[1] + "</span>" : "";
    var lis = sec.items.map(function (it) {
      var cls = it.kind === "check" ? (it.done ? "done" : "") : it.proseCls;
      return '<li class="' + cls + '">' + mdInline(it.text) + "</li>";
    }).join("");
    return '<div class="prd-sec"><div class="prd-h">' + esc(sec.name) + b + '</div><ul class="prd-list">' + lis + "</ul></div>";
  }).join("");
  return '<div class="prd">' + parts + "</div>";
}
function docRow(links) {
  if (!links || !links.length) return "";
  var dl = links.map(function (l) {
    return '<button type="button" class="doc-link" data-doc="' + esc(l.doc) + '" data-title="' + esc(l.title) + '">' + esc(l.label) + "</button>";
  }).join("");
  return '<p class="doc-links">' + dl + "</p>";
}
function subtable(rows, ssCls) {
  if (!rows || !rows.length) return '<p class="empty">无 subtask</p>';
  // ponytail: 时间戳为 epoch 秒, 转分钟; running 耗时显示 "..." (无 tnow), pending 显示 "-"
  function durCell(a, b) {
    if (!a || !b) return "-";
    return fmtDur(Math.round((b - a) / 60));
  }
  var srows = rows.map(function (s) {
    var elapsed = !s.started ? "-" : (s.finished ? durCell(s.started, s.finished) : "...");
    var waited = durCell(s.created, s.started);
    return "<tr><td>" + esc(s.sid) + "</td><td>" + esc(s.name) + "</td>"
      + "<td>" + badge(s.status, ssCls) + "</td>"
      + "<td>" + bar(s.pct, true, "") + "</td>"
      + "<td>" + esc(s.agent) + "</td>"
      + "<td>" + esc((s.skills || []).join(",") || "-") + "</td>"
      + "<td>" + esc((s.depNames || []).join(", ") || "-") + "</td>"
      + "<td>" + esc((s.acc || []).join("; ") || "-") + "</td>"
      + "<td>" + elapsed + "</td><td>" + waited + "</td></tr>";
  }).join("");
  return "<table><thead><tr><th>sid</th><th>名称</th><th>状态</th><th>进度</th>"
    + "<th>agent</th><th>skills</th><th>依赖</th><th>验收标准</th><th>耗时</th><th>等待</th></tr></thead>"
    + "<tbody>" + srows + "</tbody></table>";
}

// 总览 (左栏) + 卡片流 (右栏) HTML 串
function buildLayoutHtml(data) {
  setNodeMaps(data.nodeVar, data.nodeCls);
  var ov = data.overview;
  var fo = data.filterOpts;
  var S_ACTIVE = fo[1][0], S_CHECK = fo[2][0], S_PENDING = fo[3][0], S_DONE = fo[4][0];
  function statcard(label, key, filter, cls) {
    return '<button type="button" class="stat' + (cls ? " " + cls : "") + '" data-filter="' + esc(filter) + '">'
      + '<span class="stat-n">' + (key === "__total__" ? ov.taskCount : (ov.stats[key] || 0))
      + '</span><span class="stat-l">' + esc(label) + "</span></button>";
  }
  var stats = '<div class="stats" id="sw-filter">'
    + statcard("总计", "__total__", "", "stat-all")
    + statcard("已完成", S_DONE, S_DONE) + statcard("进行中", S_ACTIVE, S_ACTIVE)
    + statcard("检查中", S_CHECK, S_CHECK) + statcard("待处理", S_PENDING, S_PENDING) + "</div>";
  var sw = '<div class="dag-switch" role="group">'
    + '<button type="button" data-dag="task" class="on">task 维度</button>'
    + '<button type="button" data-dag="full"' + (ov.hasSub ? "" : " disabled") + ">subtask 维度</button></div>";

  var td = ov.taskDag;
  var tipMap = {};
  Object.keys(td.tips || {}).forEach(function (id) { tipMap[id] = buildTip(td.tips[id]); });
  var taskView = '<div class="dag-view" data-dag="task">' + dagHtml(td.nodes, tipMap, td.links, true) + "</div>";
  var fullView = ov.fullDag
    ? '<div class="dag-view" data-dag="full" hidden>' + dagHtml(ov.fullDag.nodes, null, null, true) + "</div>"
    : "";

  var queue = "";
  var pq = (ov.pendingQueue || []).filter(function (q) { return q.ready; });
  if (pq.length) {
    var qrows = pq.map(function (q, k) {
      return '<li class="q-item"><span class="q-ord">' + (k + 1) + "</span>"
        + '<span class="q-chip q-ready">就绪</span>'
        + '<span class="q-name">' + esc(q.tid) + "/" + esc(q.sid) + " · " + esc(q.name) + "</span>"
        + '<span class="q-agent">' + esc(q.agent) + "</span></li>";
    }).join("");
    queue = '<div class="queue"><p class="meta">就绪队列 · 调度序 · ' + pq.length + "</p>"
      + '<ol class="q-list">' + qrows + "</ol></div>";
  }

  var overview = '<section class="card"><h2>任务进展</h2>' + sw + stats
    + '<p class="meta">' + ov.taskCount + " task</p>"
    + '<p class="meta">当前进度</p>' + bar(ov.combinedPct, false, "")
    + queue + taskView + fullView + "</section>";

  var cards = data.cards.map(function (c) {
    var h2 = "<h2>" + '<a class="card-link" href="/task?id=' + encodeURIComponent(c.id) + '">' + esc(c.id) + "</a> " + badge(c.status, data.stClsMap)
      + (c.nextUp ? "<span class=next-up-chip>▶ 下一个</span>" : "")
      + '<a class="card-detail-btn" href="/task?id=' + encodeURIComponent(c.id) + '" title="详情" aria-label="详情">'
      + '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>'
      + "</a></h2>";
    var meta1 = '<p class="meta">前置: ' + esc((c.depNames || []).join(", ") || "-") + " · "
      + "worktree: " + esc(c.worktree || "-") + " · "
      + "耗时 " + fmtDur(c.elapsed) + " · "
      + "等待 " + fmtDur(c.started && c.created ? Math.round((c.started - c.created) / 60) : null) + "</p>";
    return '<section class="card' + (c.nextUp ? " next-up" : "") + '" id="task-' + esc(c.id)
      + '" data-status="' + esc(c.status) + '" data-search="' + esc(c.search) + '">'
      + h2 + '<p class="name">' + esc(c.name) + "</p>"
      + docRow(c.docLinks) + prdBlock(c.prd) + meta1
      + '<p class="meta">子任务 ' + c.sdone + "/" + c.stotal + "</p>" + bar(c.spct, true, "") + stageChip(c.stage)
      + '<div class="task-detail">'
      + dagHtml(c.subNodes, null, null, (c.subNodes || []).length > 4)
      + subtable(c.subtable, data.ssClsMap) + "</div></section>";
  }).join("");
  var main = data.cards.length ? cards : '<p class="empty">无 task</p>';
  return '<aside class="col-side">' + overview + '</aside><main class="col-main">' + main + "</main>";
}

// ── 交互 (移植自 switcher.js): 状态筛选 / DAG 维度切换 / 节点浮层 / 进度条门控 ──
let filterSet = ["进行中", "检查中", "待处理"];  // 内存态, 软刷存活, 换页重置

function bindContent(layout, io) {
  function curFilters() {
    var b = layout.querySelector("#sw-filter");
    if (!b) return [];
    return Array.prototype.filter.call(b.querySelectorAll(".stat.on"), function (s) { return !s.classList.contains("stat-all"); })
      .map(function (s) { return s.getAttribute("data-filter"); });
  }
  function syncTotalState(b) { var all = b.querySelector(".stat-all"); if (all) all.classList.toggle("on", !b.querySelector(".stat.on:not(.stat-all)")); }
  function applyCards() {
    var fs = curFilters(), all = fs.length === 0;
    layout.querySelectorAll("section.card[data-status]").forEach(function (c) {
      c.style.display = (all || fs.indexOf(c.getAttribute("data-status")) >= 0) ? "" : "none";
    });
    layout.querySelectorAll(".col-side .dag-wrap svg g[data-status]").forEach(function (g) {
      var st = g.getAttribute("data-status");
      g.classList.toggle("dag-dim", !all && !!st && fs.indexOf(st) < 0);
    });
  }

  var fbox = layout.querySelector("#sw-filter");
  if (fbox) {
    fbox.querySelectorAll(".stat").forEach(function (s) { var f = s.getAttribute("data-filter"); s.classList.toggle("on", !!f && filterSet.indexOf(f) >= 0); });
    syncTotalState(fbox);
    fbox.addEventListener("click", function (e) {
      var b = e.target.closest(".stat"); if (!b || !fbox.contains(b)) return;
      if (b.classList.contains("stat-all")) fbox.querySelectorAll(".stat").forEach(function (s) { s.classList.remove("on"); });
      else b.classList.toggle("on");
      syncTotalState(fbox);
      filterSet = curFilters();
      applyCards();
    });
  }
  applyCards();

  layout.querySelectorAll(".dag-switch").forEach(function (sw) {
    var card = sw.closest(".card");
    function show(v) {
      sw.querySelectorAll("button").forEach(function (b) { b.classList.toggle("on", b.getAttribute("data-dag") === v); });
      card.querySelectorAll(".dag-view").forEach(function (vw) { vw.hidden = vw.getAttribute("data-dag") !== v; });
      try { localStorage.setItem("skein-dagview", v); } catch (_) {}
    }
    sw.querySelectorAll("button").forEach(function (b) { b.addEventListener("click", function () { if (!b.disabled) show(b.getAttribute("data-dag")); }); });
    var saved; try { saved = localStorage.getItem("skein-dagview"); } catch (_) {}
    if (saved && card.querySelector('.dag-view[data-dag="' + saved + '"]:not([disabled])')) {
      var btn = sw.querySelector('button[data-dag="' + saved + '"]');
      if (btn && !btn.disabled) show(saved);
    }
  });

  layout.querySelectorAll(".dag-wrap").forEach(function (wrap) {
    wrap.querySelectorAll("svg .has-tip[data-tip]").forEach(function (g) {
      var tip = wrap.querySelector('.dag-tip[data-for="' + g.getAttribute("data-tip") + '"]');
      if (!tip) return;
      g.addEventListener("mouseenter", function () {
        tip.style.display = "block";
        var gb = g.getBoundingClientRect(), tb = tip.getBoundingClientRect();
        var vw = window.innerWidth, vh = window.innerHeight;
        var left = Math.min(gb.left, vw - tb.width - 8);
        var top = gb.bottom + 6 + tb.height > vh ? gb.top - tb.height - 6 : gb.bottom + 6;
        tip.style.left = Math.max(8, left) + "px";
        tip.style.top = Math.max(8, top) + "px";
      });
      g.addEventListener("mouseleave", function () { tip.style.display = "none"; });
    });
  });

  // ponytail: 拦截 DAG 节点 <a href="#task-<id>"> 点击 — 后端 skein.py 仍发哈希锚点, 但 history 路由
  //           改造后哈希被 SPA 吞噬跳首页。此处仅拦 #task- 前缀, preventDefault + scrollIntoView,
  //           其他哈希放行。
  layout.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#task-"]');
    if (!a) return;
    var el = document.getElementById(a.getAttribute("href").slice(1));
    if (!el) return;
    e.preventDefault();
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  if (io) { io.disconnect(); layout.querySelectorAll(".col-main .bar").forEach(function (b) { io.observe(b); }); }
}

// 软刷保滚动位: 换 layout innerHTML 前记左栏 DAG 滚动 + 窗口滚动, 渲染后复原 (移植自 board-render)
function renderLayout(layout, data, io) {
  var savedScroll = {}, savedWin = window.pageYOffset;
  layout.querySelectorAll(".col-side .dag-view > .dag-wrap").forEach(function (w) {
    var v = w.closest(".dag-view");
    if (v) savedScroll[v.getAttribute("data-dag")] = { t: w.scrollTop, l: w.scrollLeft };
  });

  layout.innerHTML = buildLayoutHtml(data);
  bindContent(layout, io);

  layout.querySelectorAll(".col-side .dag-view > .dag-wrap").forEach(function (w) {
    var v = w.closest(".dag-view"), s = v && savedScroll[v.getAttribute("data-dag")];
    if (s) { w.scrollTop = s.t; w.scrollLeft = s.l; return; }
    var node = w.querySelector(".n-active") || w.querySelector(".n-check");
    if (!node) return;
    var nr = node.getBoundingClientRect(), wr = w.getBoundingClientRect();
    w.scrollTop += (nr.top - wr.top) - (w.clientHeight - nr.height) / 2;
    w.scrollLeft += (nr.left - wr.left) - (w.clientWidth - nr.width) / 2;
  });
  window.scrollTo({ top: savedWin, behavior: "instant" });
}

// ── 文档弹层: 点 .doc-link → fetch task/<id>/<f>.md → ctx.md 渲染 → 弹层 ──
function wireDocModal(mount, modal, ctx) {
  var titleEl = modal.querySelector(".doc-title");
  var bodyEl = modal.querySelector(".doc-body");
  var copyBtn = modal.querySelector(".doc-copy");
  var lastSrc = "";

  function open(doc, title) {
    titleEl.textContent = title || "";
    lastSrc = "";
    copyBtn.disabled = true;
    bodyEl.innerHTML = '<p class="doc-loading">载入中…</p>';
    modal.hidden = false;
    // /task/<id>/<f>.md 静态直出; getJSON 对非 JSON 响应返回文本
    ctx.api.getJSON("/" + doc.replace(/^\/+/, "")).then(function (t) {
      lastSrc = String(t);
      copyBtn.disabled = false;
      bodyEl.innerHTML = ctx.md.render(lastSrc);
      ctx.md.sanitize(bodyEl);
    }).catch(function (e) {
      bodyEl.innerHTML = "";
      var p = document.createElement("p");
      p.className = "doc-err";
      p.textContent = "读取失败: " + doc + " (" + (e && e.message || e) + ")";
      bodyEl.appendChild(p);
    });
  }
  function close() { modal.hidden = true; bodyEl.innerHTML = ""; lastSrc = ""; }
  function copySrc() {
    if (!lastSrc) return;
    var flash = function (ok) { copyBtn.textContent = ok ? "✓ 已复制" : "✕ 复制失败"; setTimeout(function () { copyBtn.textContent = "⧉ 复制"; }, 1400); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(lastSrc).then(function () { flash(true); }, function () { flash(false); });
    } else { flash(false); }
  }

  mount.addEventListener("click", function (e) {
    var b = e.target.closest(".doc-link");
    if (b && !modal.contains(b)) { open(b.getAttribute("data-doc"), b.getAttribute("data-title")); return; }
    if (e.target.closest(".doc-copy")) { copySrc(); return; }
    if (e.target.closest(".doc-close") || e.target.classList.contains("doc-backdrop")) close();
  });
  document.addEventListener("keydown", function onKey(e) {
    if (!document.body.contains(modal)) { document.removeEventListener("keydown", onKey); return; }
    if (e.key === "Escape" && !modal.hidden) close();
  });
}

// ── 命令快捷条: [+新建 task] 展开表单 → api.exec("create"); [current/ready/pop/doctor] 一键查询 ──
// ponytail: exec 结果走 esc() 转义后注入 .cmd-out (stdout/stderr 均为后端命令输出, 防 XSS)。
function wireCmdBar(mount, ctx) {
  var bar = mount.querySelector(".cmd-bar");
  var form = mount.querySelector('[data-form="create"]');
  var out = mount.querySelector("[data-out]");
  if (!bar || !ctx || !ctx.api || !ctx.api.exec) return;

  function renderResult(r) {
    if (r && r.err) {
      out.hidden = false;
      out.innerHTML = '<div class="h"><code>' + esc(r.cmd) + '</code><span class="fail">' + esc(r.err) + '</span></div>';
      return;
    }
    var ok = r && r.exit === 0;
    var head = '<div class="h"><code>' + esc(r.cmd) + '</code><span>exit ' + r.exit + '</span>'
      + '<span class="' + (ok ? "ok" : "fail") + '">' + (ok ? "ok" : "fail") + "</span></div>";
    var o = r.stdout ? "<pre>" + esc(r.stdout) + "</pre>" : "";
    var e = r.stderr ? '<pre class="err">' + esc(r.stderr) + "</pre>" : "";
    out.hidden = false;
    out.innerHTML = head + o + e;
  }
  async function run(cmd, args) {
    out.hidden = false;
    out.innerHTML = '<div class="h"><code>' + esc(cmd) + "</code><span>运行中…</span></div>";
    var r;
    try {
      var res = await ctx.api.exec(cmd, args || {});
      r = { cmd: res.cmd || cmd, exit: res.exit, stdout: res.stdout || "", stderr: res.stderr || "" };
    } catch (ex) {
      r = { cmd: cmd, err: (ex && ex.message) || String(ex) };
    }
    renderResult(r);
    if (cmd === "create" && r && r.exit === 0) {
      form.reset();
      form.hidden = true;
      var refresh = mount._skeinRefresh;        // render() 注入的刷新句柄
      if (refresh) refresh();
    }
  }

  bar.addEventListener("click", function (e) {
    var t = e.target.closest("button");
    if (!t || !bar.contains(t)) return;
    if (t.dataset.cmd === "toggle-new") { form.hidden = !form.hidden; if (!form.hidden) form.elements.id.focus(); return; }
    if (t.dataset.cmd === "cancel-new") { form.hidden = true; form.reset(); return; }
    var q = t.dataset.quick;
    if (q) run(q);
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var deps = form.elements.deps.value.trim();
    run("create", {
      id: form.elements.id.value.trim(),
      name: form.elements.name.value.trim(),
      desc: form.elements.desc.value.trim(),
      deps: deps ? deps.split(/[,，\s]+/).filter(Boolean).join(",") : "",
    });
  });
}

export async function render(mount, params, ctx) {
  // sticky 左栏 top = 实测 topbar 高 (webapp 无 switcher.js 写 --topbar, 此处补)
  var tb = document.querySelector(".topbar");
  if (tb) document.documentElement.style.setProperty("--topbar", tb.offsetHeight + "px");

  mount.innerHTML =
    "<style>" + BOARD_CSS + "</style>"
    + '<div class="cmd-bar">'
    + '<button type="button" class="cmd-btn cmd-new" data-cmd="toggle-new">＋ 新建 task</button>'
    + '<span class="cmd-spacer"></span>'
    + '<button type="button" class="cmd-btn" data-quick="doctor">doctor</button>'
    + '</div>'
    + '<form class="cmd-form" hidden data-form="create">'
    + '<div class="f"><span>id *</span><input name="id" placeholder="task id" required></div>'
    + '<div class="f"><span>name *</span><input name="name" placeholder="task 名称" required></div>'
    + '<div class="f"><span>desc *</span><textarea name="desc" rows="2" placeholder="简述" required></textarea></div>'
    + '<div class="f"><span>deps (逗号分隔, 选填)</span><input name="deps" placeholder="dep1,dep2"></div>'
    + '<div style="display:flex;align-items:center;gap:10px">'
    + '<button type="submit" class="cmd-btn cmd-new">提交</button>'
    + '<button type="button" class="cmd-btn" data-cmd="cancel-new">取消</button>'
    + '</div></form>'
    + '<div class="cmd-out" hidden data-out></div>'
    + '<div class="layout"></div>'
    + '<div class="doc-modal" hidden><div class="doc-backdrop"></div>'
    + '<div class="doc-panel"><div class="doc-head"><span class="doc-title"></span>'
    + '<button type="button" class="doc-copy" disabled>⧉ 复制</button>'
    + '<button type="button" class="doc-close" aria-label="关闭">✕</button></div>'
    + '<div class="doc-body markdown"></div></div></div>';

  var layout = mount.querySelector(".layout");
  var io = ("IntersectionObserver" in window)
    ? new IntersectionObserver(function (es) { es.forEach(function (e) { e.target.classList.toggle("voff", !e.isIntersecting); }); }, { rootMargin: "120px" })
    : null;

  wireDocModal(mount, mount.querySelector(".doc-modal"), ctx);
  wireCmdBar(mount, ctx);

  async function refresh() {
    var data = await ctx.api.data();
    renderLayout(layout, data, io);
  }
  mount._skeinRefresh = refresh;
  await refresh();
  ctx.onLive(function () { refresh().catch(function () {}); });  // 数据软刷 (切页自动退订)
}
