// SKEIN Task 页: 单 task 审阅 — 两栏布局 (左: subtask DAG+列表+目标/验收 / 右: 文档 tab 默认 PRD)。
// 只读视图; 数据 api.task(id) 一次拉全 (task/docs/subtasks/contracts), onLive 软刷。task 不存在(404) → 友好空态。
// page 契约: render(mount, params, ctx); params={id}; ctx={api, md, onLive}; 响应式走 window.PetiteVue.createApp.
import { dagHtml, setNodeMaps } from "../dag.js";
import { parsePrdSections, findSection } from "../prd-parse.js";

// 状态中文 → badge 令牌类 (task S_* 与 subtask SS_* 合并; 运行中 复用 active 色)
const BADGE = {
  "待处理": "badge-pending", "进行中": "badge-active", "运行中": "badge-active",
  "检查中": "badge-check", "已完成": "badge-done", "失败": "badge-failed",
};
const badgeCls = (st) => BADGE[st] || "badge-pending";

// task 阶段 label (plan/exec/check/done): task.json 无 stage 字段, 由 status 派生 (对齐后端 _task_stage)。
// ponytail: 详情接口 _task_detail 直返 task.json 原文无 stage, 前端就近派生, 不改后端契约。
const STAGE_OF = { "已完成": "done", "检查中": "check", "进行中": "exec", "运行中": "exec", "待处理": "plan" };
const stageOf = (st) => STAGE_OF[st] || "plan";
const STAGE_LABEL = { plan: "plan", exec: "exec", check: "check", done: "done" };
const STAGE_CLS = { plan: "stg-plan", exec: "stg-exec", check: "stg-check", done: "stg-done" };
function stageChip(status) {
  const s = stageOf(status), lbl = STAGE_LABEL[s];
  return lbl ? `<span class="stage-chip ${STAGE_CLS[s]}">${lbl}</span>` : "";
}

// DAG 节点染色映射 (status → CSS 变量 / class)。对齐后端 _board_data 的 node_var/node_cls。
// ponytail: _task_detail 不返回 nodeVar/nodeCls, 此处硬编码同一份 (task/subtask 状态中文集合的并集)。
const NODE_VAR = {
  "待处理": "--st-pending", "进行中": "--st-active", "运行中": "--st-active",
  "检查中": "--st-check", "已完成": "--st-done", "失败": "--st-failed",
};
const NODE_CLS = {
  "待处理": "n-pending", "进行中": "n-active", "运行中": "n-active",
  "检查中": "n-check", "已完成": "n-done", "失败": "n-failed",
};

// 页内样式: 命令快捷条 + 两栏布局 (grid 2fr/3fr, 窄屏堆叠) + markdown 渲染体 + DAG SVG 染色。
// board.js 的 .dag g.n-* rect 染色规则在此复刻一份 (task 详情页 DAG 独立渲染, 不引 board BOARD_CSS)。
const TASK_STYLE = `<style>
.tcmd{background:var(--card);color:var(--head);border:1px solid var(--brd);border-radius:8px;padding:5px 11px;font:12px var(--font);cursor:pointer}
.tcmd:hover:not(:disabled){border-color:var(--accent);color:var(--accent)}
.tcmd:disabled{opacity:.5;cursor:not-allowed}
.tcmd-out{margin-top:10px;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.tcmd-out-h{padding:6px 10px;font-size:12px;background:var(--line);color:var(--head);display:flex;align-items:center;gap:8px}
.tcmd-out-h .ok{color:var(--st-done)}.tcmd-out-h .fail{color:var(--st-failed)}
.tcmd-out pre{margin:0;padding:10px;overflow:auto;max-height:320px;font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--bg);color:var(--fg);white-space:pre-wrap;word-break:break-word}
.tcmd-out pre.err{color:var(--st-failed);max-height:220px}
/* 两栏: 桌面 2fr(左 subtask) / 3fr(右文档); ≤900px 堆叠 (左上右下) */
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
.copy-id{background:none;border:1px solid var(--line);color:var(--muted);font-size:11px;line-height:1;cursor:pointer;padding:2px 5px;border-radius:5px;vertical-align:middle}
.copy-id:hover{background:var(--sel-bg);color:var(--head);border-color:var(--accent)}
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
.stage-chip.stg-exec{background:var(--accent)}
.stage-chip.stg-check{background:var(--st-check)}
.stage-chip.stg-done{background:var(--st-done)}
.sec-empty{color:var(--muted);font-size:12.5px;font-style:italic;opacity:.85}
</style>`;

// html 转义 (renderResult 走 v-html, stdout/stderr 是命令输出须转义防注入)
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
  const rel = hrs >= 24 ? `${Math.floor(hrs / 24)}d ago` : `${hrs}h ago`;
  return `${mm}-${dd} ${hh}:${mi} (${rel})`;
}

// subtask 完成百分比 (对齐后端 _sub_pct: done 强制 100; 验收done/验收, 无验收未完成即 0)
function subPct(s) {
  if (s.status === "已完成") return 100;
  const crit = (s["验收"] || []).length;
  return crit ? Math.round(((s["验收done"] || []).length / crit) * 100) : 0;
}

const TPL = `
<div class="px-7">
  <!-- 加载失败 / 404 空态 -->
  <div v-if="loadErr" class="card p-10 text-center text-muted">
    <div class="empty-ico" v-if="notFound"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></div>
    <div class="empty-ico" v-else><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>
    <div class="text-sm" :style="notFound ? '' : 'color:var(--st-failed)'">{{ loadErr }}</div>
    <a href="/" class="inline-block mt-4 text-sm" style="color:var(--accent)">← 返回看板</a>
  </div>

  <div v-else>
    <!-- task 头 (全宽) -->
    <header class="card p-5 mb-4">
      <div class="flex items-center gap-3 flex-wrap">
        <button class="back-btn" @click="history.back()">← 返回</button>
        <code class="text-sm px-2 py-0.5 rounded" style="background:var(--line);color:var(--head)">{{ task.id }}</code>
        <button class="copy-id" :title="copied===task.id ? '已复制' : '复制 id'" @click="copyId(task.id)">{{ copied===task.id ? '✓' : '⧉' }}</button>
        <h1 v-if="task.name" class="text-lg font-semibold" style="color:var(--head)">{{ task.name }}</h1>
        <span class="badge" :class="badgeCls(task.status)">{{ task.status }}</span>
        <span class="stage-chip" :class="stageCls(task.status)" v-if="task.status">{{ stageLabel(task.status) }}</span>
        <span v-if="archived" class="badge badge-done opacity-70">已归档</span>
        <span class="flex-1"></span>
        <span v-if="task.deps && task.deps.length" class="text-xs text-muted">依赖 {{ task.deps.join(', ') }}</span>
      </div>
      <p v-if="task.desc" class="text-sm text-muted mt-2 whitespace-pre-wrap">{{ task.desc }}</p>
      <!-- 命令快捷条: status / contract / subtask-list (id 自动填当前 task) -->
      <div class="mt-3 flex flex-wrap items-center gap-2">
        <button class="tcmd" :disabled="running" @click="runRead('status')">status</button>
        <button class="tcmd" :disabled="running" @click="runRead('contract')">contract</button>
        <button class="tcmd" :disabled="running" @click="runRead('subtask-list')">subtask-list</button>
        <span v-if="running" class="text-[11px] text-muted">运行中…</span>
      </div>
      <div v-if="result" class="tcmd-out" v-html="renderResult()"></div>
    </header>

    <!-- 两栏: 左 subtask 区 / 右 文档 tab -->
    <div class="task-layout">
      <!-- 左栏 -->
      <div class="tl-col">
        <!-- subtask DAG 图 (≥2 节点才渲染) -->
        <section v-if="subDag" class="card p-4">
          <div class="flex items-center gap-2 mb-3">
            <h2 class="text-sm font-semibold" style="color:var(--head)">子任务图</h2>
            <span class="text-xs text-muted">{{ subtasks.length }}</span>
          </div>
          <div class="task-dag" v-html="subDag"></div>
        </section>

        <!-- subtask 列表 (状态/进度/依赖) -->
        <section class="card p-5">
          <div class="flex items-center gap-2 mb-3">
            <h2 class="text-sm font-semibold" style="color:var(--head)">子任务</h2>
            <span class="text-xs text-muted">{{ subtasks.length }}</span>
          </div>
          <div v-if="!subtasks.length" class="text-muted text-center py-8 text-sm">尚无子任务拆分</div>
          <div v-else class="space-y-2">
            <div v-for="s in subtasks" :key="s.sid" class="rounded p-3" :class="s.status === '运行中' ? 'sub-active' : ''" style="border:1px solid var(--line)">
              <div class="flex items-center gap-2 flex-wrap">
                <code class="text-xs" style="color:var(--head)">{{ s.sid }}</code>
                <button class="copy-id" :title="copied===s.sid ? '已复制' : '复制 id'" @click="copyId(s.sid)">{{ copied===s.sid ? '✓' : '⧉' }}</button>
                <span class="text-sm">{{ s.name || s.sid }}</span>
                <span class="badge text-[11px]" :class="badgeCls(s.status)">{{ s.status }}</span>
                <span class="flex-1"></span>
                <span v-if="s.agent" class="text-[11px] text-muted">{{ s.agent }}</span>
              </div>
              <p v-if="s.desc" class="text-xs text-muted mt-1 whitespace-pre-wrap">{{ s.desc }}</p>
              <div class="flex items-center gap-2 mt-2">
                <div class="flex-1 h-1.5 rounded overflow-hidden" style="background:var(--line)">
                  <div class="h-full rounded" :style="'width:'+pct(s)+'%;background:var(--st-done)'"></div>
                </div>
                <span class="text-[11px] text-muted w-9 text-right">{{ pct(s) }}%</span>
              </div>
              <div v-if="deps(s).length" class="text-[11px] text-muted mt-1">依赖: {{ deps(s).join(', ') }}</div>
              <div class="text-[11px] text-muted mt-1 flex flex-wrap gap-x-3 gap-y-0.5">
                <span>建: {{ fmtMix(s.created) }}</span>
                <span>起: {{ fmtMix(s.started) }}</span>
                <span>讫: {{ fmtMix(s.finished) }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 目标 (PRD 抽出) -->
        <section v-if="goalHtml" class="card p-5">
          <h2 class="text-sm font-semibold mb-2" style="color:var(--head)">目标</h2>
          <div class="md-body" v-html="goalHtml"></div>
        </section>

        <!-- 边界 (PRD 抽出) -->
        <section v-if="boundaryHtml" class="card p-5">
          <h2 class="text-sm font-semibold mb-2" style="color:var(--head)">边界</h2>
          <div class="md-body" v-html="boundaryHtml"></div>
        </section>

        <!-- 验收标准 (PRD 抽出) -->
        <section v-if="acceptHtml" class="card p-5">
          <h2 class="text-sm font-semibold mb-2" style="color:var(--head)">验收标准</h2>
          <div class="md-body" v-html="acceptHtml"></div>
        </section>
      </div>

      <!-- 右栏: 文档 tab (默认 PRD). data-cur-tab 反映当前 tab, 供软刷重挂前 DOM 抽取保状态 -->
      <section class="card overflow-hidden" :data-cur-tab="tab">
        <div class="flex" style="border-bottom:1px solid var(--line)">
          <button v-for="d in docTabs" :key="d.key"
            class="px-4 py-2 text-sm relative"
            :style="tab===d.key ? 'color:var(--accent);border-bottom:2px solid var(--accent)' : 'color:var(--muted)'"
            @click="tab=d.key">
            {{ d.label }}
            <span v-if="!docs[d.key] && !(d.key==='research' && Object.keys(research).length)" class="ml-1 text-[10px] opacity-50">空</span>
          </button>
        </div>
        <div class="p-5">
          <div v-if="tab==='research' && Object.keys(research).length === 0" class="text-muted text-center py-16 text-sm">
            <div class="empty-ico"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>暂无调研笔记
          </div>
          <div v-else-if="tab==='research'" class="space-y-3">
            <div v-for="name in researchKeys" :key="name" class="rounded p-4" style="border:1px solid var(--line)">
              <div class="text-sm font-semibold mb-2" style="color:var(--head)">{{ name }}</div>
              <div class="md-body" v-html="researchHtml(name)"></div>
            </div>
          </div>
          <div v-else-if="!docs[tab]" class="text-muted text-center py-16 text-sm">
            <div class="empty-ico"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>{{ docLabel(tab) }} 暂无内容
          </div>
          <!-- PRD: 按 ## 章节拆 card 竖排; 章节内一级 - [ ] 由 md 渲染为只读 todo checkbox -->
          <div v-else-if="tab==='prd'" class="space-y-3">
            <div v-for="sec in prdSections" :key="sec.title" class="rounded p-4" style="border:1px solid var(--line)">
              <div v-if="sec.title" class="text-sm font-semibold mb-2" style="color:var(--head)">{{ sec.title }}</div>
              <div class="md-body" v-html="sec.html"></div>
            </div>
          </div>
          <!-- design/findings: 保持整篇 md -->
          <div v-else class="md-body" v-html="renderedDoc"></div>
        </div>
      </section>
    </div>

    <!-- 契约区 (全宽底部, 空则不显) -->
    <section v-if="contracts.length" class="card p-5 mt-4">
      <div class="flex items-center gap-2 mb-3">
        <h2 class="text-sm font-semibold" style="color:var(--head)">契约</h2>
        <span class="text-xs text-muted">{{ contracts.length }}</span>
      </div>
      <ol class="space-y-1.5">
        <li v-for="(c,i) in contracts" :key="i" class="text-sm flex gap-2">
          <span class="text-muted select-none">{{ i+1 }}.</span>
          <span class="whitespace-pre-wrap">{{ c }}</span>
        </li>
      </ol>
    </section>
  </div>
</div>`;

// 右栏文档 tab 顺序: 详细设计优先 (默认), PRD 次之, 调研收敛最后。
const DOC_TABS = [
  { key: "design", label: "详细设计" },
  { key: "prd", label: "PRD" },
  { key: "findings", label: "调研收敛" },
  { key: "research", label: "调研过程" },
];

// ── 列表视图 (无 id: /task) ── 数据复用 /__skein__/data → cards (每项 id/name/status/desc/spct)。
const LIST_TPL = `
<div class="px-7">
  <div class="flex items-center gap-2 mb-4 px-1">
    <h1 class="text-lg font-semibold" style="color:var(--head)">任务</h1>
    <span v-if="!loadErr && items.length" class="text-xs text-muted">{{ items.length }}</span>
  </div>
  <div v-if="loadErr" class="card p-10 text-center text-muted">
    <div class="empty-ico"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>
    <div class="text-sm" style="color:var(--st-failed)">{{ loadErr }}</div>
  </div>
  <div v-else-if="!items.length" class="card p-16 text-center text-muted">
    <div class="empty-ico"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg></div>
    <div class="text-sm">暂无任务 — 在 .skein/task.json 添加后即显示。</div>
  </div>
  <div v-else class="space-y-2">
    <a v-for="t in items" :key="t.id" :href="'/task?id='+encodeURIComponent(t.id)"
      class="card block p-4 hover:bg-[var(--line)] transition-colors">
      <div class="flex items-center gap-2 flex-wrap">
        <code class="text-xs px-1.5 py-0.5 rounded" style="background:var(--line);color:var(--head)">{{ t.id }}</code>
        <span class="text-sm font-medium" style="color:var(--head)">{{ t.name || t.id }}</span>
        <span class="badge text-[11px]" :class="badgeCls(t.status)">{{ t.status }}</span>
        <span class="flex-1"></span>
        <span class="text-[11px] text-muted shrink-0">{{ t.spct }}%</span>
      </div>
      <p v-if="t.desc" class="text-xs text-muted mt-1.5 whitespace-pre-wrap line-clamp-2">{{ t.desc }}</p>
    </a>
  </div>
</div>`;

// 从 task.subtasks 构造 DAG 节点数组: [sid, name, status, depends_on(sid 数组), pct, desc]。
// 对齐后端 _board_data 的 node() 形状; dagHtml 自行按 depends_on 连边 (无需显式 links)。
function buildSubDag(subtasks) {
  if (!subtasks || subtasks.length < 1) return "";
  const nodes = subtasks.map((s) => [
    s.sid, s.name || s.sid, s.status, s.depends_on || [], subPct(s), s.desc || "",
  ]);
  return dagHtml(nodes, null, null, nodes.length > 4);
}

export async function render(mount, params, ctx) {
  const { api, md, onLive } = ctx;

  // 无 id → 列表视图 (复用 /__skein__/data; 不走 api.task, 避免空 id 拉详情 404)
  if (!params.id) {
    async function fetchList() {
      try {
        const cards = ((await api.data()) || {}).cards || [];
        return { loadErr: "", items: cards };
      } catch (e) {
        return { loadErr: (e && e.message) || String(e), items: [] };
      }
    }
    async function mountList() {
      const st = await fetchList();
      mount.innerHTML = LIST_TPL;
      window.PetiteVue.createApp(Object.assign({ badgeCls, stageCls: (st) => STAGE_CLS[stageOf(st)], stageLabel: (st) => STAGE_LABEL[stageOf(st)] }, st)).mount(mount);
    }
    await mountList();
    onLive && onLive(mountList);
    return;
  }

  // 先拉数据再 createApp (对齐 spec.js: petite-vue 无对外实例句柄, 初始态直接注入)。
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
        loadErr: notFound ? `未找到 task「${params.id}」— 可能不存在或已清理。`
                          : (e && e.message) || String(e),
        task: {}, docs: {}, subtasks: [], contracts: [], archived: false };
    }
  }

  async function mountApp() {
    // 保状态: 重挂前从旧 DOM 抽当前 tab (data-cur-tab) + 滚动位置, 重挂后回填 (软刷不丢 tab/滚动)。
    // ponytail: petite-vue 无实例句柄读 tab, 用 DOM 抽最小侵入, 不动响应式架构。
    let savedTab = null, savedScroll = 0;
    const cur = mount.querySelector("[data-cur-tab]");
    if (cur) savedTab = cur.getAttribute("data-cur-tab");
    savedScroll = window.scrollY;

    const st = await fetchState();
    // DAG 染色映射注入 (每次渲染前; dag.js 模块级 NODE_VAR/NODE_CLS 单例)
    setNodeMaps(NODE_VAR, NODE_CLS);
    // subtask DAG 字符串在 createApp 前算好注入 (ponytail: 静态, 无需响应式)
    const subDag = buildSubDag(st.subtasks);
    // PRD 目标 / 验收标准 抽取 + md 渲染 (docs.prd 为 null 时 findSection 返回 "")
    const prdSecs = parsePrdSections(st.docs.prd || "");
    const goalHtml = md.renderSafe(findSection(prdSecs, "目标"));
    const boundaryHtml = md.renderSafe(findSection(prdSecs, "边界"));
    const acceptHtml = md.renderSafe(findSection(prdSecs, "验收标准", "验收"));
    // 默认 tab: design 优先, design 为空则回落 prd (避免默认空 tab); 软刷保留上次选择。
    const defaultTab = st.docs.design ? "design" : "prd";
    const initialTab = savedTab || defaultTab;
    mount.innerHTML = TASK_STYLE + TPL;
    window.PetiteVue.createApp(Object.assign({
      tab: initialTab,
      docTabs: DOC_TABS,
      badgeCls,
      stageCls: (st) => STAGE_CLS[stageOf(st)],
      stageLabel: (st) => STAGE_LABEL[stageOf(st)],
      fmtMix,
      pct: subPct,
      deps: (s) => s.depends_on || [],
      docLabel: (k) => (DOC_TABS.find((d) => d.key === k) || {}).label || k,
      subDag,
      goalHtml,
      boundaryHtml,
      acceptHtml,
      get renderedDoc() { return md.renderSafe(this.docs[this.tab] || ""); },
      get researchKeys() { return Object.keys(this.research).sort(); },
      researchHtml(name) { return md.renderSafe(this.research[name] || ""); },
      // PRD 章节化 (仅 tab==='prd' 用): 各节 body 走同一 md.renderSafe 栈 → 只读 todo 复用 md 输出。
      get prdSections() {
        const map = parsePrdSections(this.docs.prd || "");
        return Object.keys(map).map(function (title) {
          return { title, html: md.renderSafe(map[title]) };
        });
      },
      result: null,
      running: false,
      copied: "",
      copyId(v) {
        if (!v || !navigator.clipboard) return;
        navigator.clipboard.writeText(v).then(() => {
          this.copied = v;
          setTimeout(() => { if (this.copied === v) this.copied = ""; }, 1200);
        });
      },
      async runRead(cmd) {
        if (this.running || !this.task.id) return;
        this.running = true;
        try {
          const res = await ctx.api.exec(cmd, { id: this.task.id });
          this.result = { cmd: res.cmd || cmd, exit: res.exit, stdout: res.stdout || "", stderr: res.stderr || "" };
        } catch (ex) {
          this.result = { cmd, err: (ex && ex.message) || String(ex) };
        }
        this.running = false;
      },
      // ponytail: exec 输出经 esc() 转义后 v-html 注入 (stdout/stderr 为后端命令输出, 防 XSS)。
      renderResult() {
        const r = this.result; if (!r) return "";
        if (r.err) return `<div class="tcmd-out-h"><code>${esc(r.cmd)}</code><span class="fail">${esc(r.err)}</span></div>`;
        const ok = r.exit === 0;
        const head = `<div class="tcmd-out-h"><code>${esc(r.cmd)}</code><span>exit ${r.exit}</span><span class="${ok ? "ok" : "fail"}">${ok ? "ok" : "fail"}</span></div>`;
        const o = r.stdout ? `<pre>${esc(r.stdout)}</pre>` : "";
        const e = r.stderr ? `<pre class="err">${esc(r.stderr)}</pre>` : "";
        return head + o + e;
      },
    }, st)).mount(mount);
    // 恢复滚动: rAF 等 DOM 布局完成后再 scrollTo, 否则位置无效。
    if (savedScroll) requestAnimationFrame(() => window.scrollTo(0, savedScroll));
  }

  await mountApp();
  // ponytail: 软刷整体重挂 — task 详情小; mountApp 内抽 tab/滚动状态保活, 用户无感刷新。
  onLive && onLive(mountApp);
}
