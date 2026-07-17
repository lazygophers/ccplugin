// SKEIN Dashboard 页 (默认首页 #/dashboard): 织机总览 — 经线墙 KPI (完成率环/活跃梭/纬线总数/织入进度)
// + 织面状态分布 (task 级 statusDist / subtask 级 subStatusDist, 经线股分段) + 上机队列 (bobbin 线轴摘要, 跳 #/queue)。
// 只读视图; 数据 api.dashboard() 一次拉全 (proj/taskCount/doneRate/activeCount/combinedPct/statusDist/subStatusDist/estMeta/pendingQueue), onLive 软刷。
// 合体: C 骨 (.wrap/.eyebrow/.page-head 布局原语 + .loom-face/.weft-row/.knot/.bobbin 织机隐喻) × A 皮 (.card 玻璃流沙/.skein-bar 蓝金流光/.entrance 入场)。
// page 契约: render(mount, params, ctx); ctx={api, md, onLive}; 响应式走 window.PetiteVue.createApp.

// 状态中文 → --st-* 色令牌 (task S_* 与 subtask SS_* 合并; 运行中 复用 active 色)
const ST_VAR = {
  "待处理": "--st-pending", "进行中": "--st-active", "运行中": "--st-active",
  "检查中": "--st-check", "已完成": "--st-done", "失败": "--st-failed",
};
const stColor = (st) => `var(${ST_VAR[st] || "--st-pending"})`;
// 织结状态映射 (knot 修饰类)
const KNOT_CLS = {
  "待处理": "pending", "进行中": "active", "运行中": "active",
  "检查中": "check", "已完成": "done", "失败": "failed",
};

// 分布字典 → 有序分段 (固定状态序, 只留计数>0), 供经线股分段 + 图例 + 织结
const ST_ORDER = ["进行中", "运行中", "检查中", "待处理", "已完成", "失败"];
function segments(dist) {
  const d = dist || {};
  const total = Object.values(d).reduce((a, b) => a + b, 0);
  const segs = ST_ORDER.filter((k) => d[k] > 0).map((k) => ({
    label: k, count: d[k], color: stColor(k), knot: KNOT_CLS[k],
    pct: total ? (d[k] / total) * 100 : 0,
  }));
  return { total, segs };
}

const C = 2 * Math.PI * 26;  // 完成率环周长 (r=26)

const TPL = `
<div class="wrap">
  <!-- 页头: C 骨 .eyebrow + .page-head -->
  <div class="eyebrow">Loom Overview · 织机总览</div>
  <div class="page-head">
    <h1>{{ proj || 'SKEIN' }} 织场</h1>
    <p>经纬交织进度 · 实时统计</p>
  </div>

  <!-- 项目为空: 首页空态 -->
  <div v-if="loadErr" class="card p-10 text-center text-muted">
    <div class="text-3xl mb-2">⚠️</div>
    <div class="text-sm" style="color:var(--st-failed)">{{ loadErr }}</div>
  </div>
  <div v-else-if="!taskCount" class="card p-16 text-center text-muted">
    <div class="text-4xl mb-3">🧵</div>
    <div class="text-sm">空织机 — 用 <code>skein create</code> 挂上第一根经线。</div>
  </div>

  <div v-else>
    <!-- KPI 经线墙: A 皮玻璃卡 + C 骨栅格 -->
    <section class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
      <!-- 完成率环 -->
      <div class="card p-4 flex items-center gap-3">
        <svg width="64" height="64" viewBox="0 0 64 64" class="shrink-0 -rotate-90">
          <circle cx="32" cy="32" r="26" fill="none" stroke="var(--line)" stroke-width="7"></circle>
          <circle cx="32" cy="32" r="26" fill="none" stroke="var(--st-done)" stroke-width="7"
            stroke-linecap="round" :stroke-dasharray="C" :stroke-dashoffset="C*(1-doneRate/100)"></circle>
        </svg>
        <div>
          <div class="text-xl font-semibold" style="color:var(--head)">{{ doneRate }}%</div>
          <div class="text-xs text-muted">下机率</div>
        </div>
      </div>
      <!-- 活跃梭子 -->
      <div class="card p-4">
        <div class="text-2xl font-semibold" style="color:var(--st-active)" :data-count="activeCount">{{ activeCount }}</div>
        <div class="text-xs text-muted mt-1">游走梭 (进行/检查)</div>
      </div>
      <!-- 纬线总数 -->
      <div class="card p-4">
        <div class="text-2xl font-semibold" style="color:var(--head)" :data-count="taskCount">{{ taskCount }}</div>
        <div class="text-xs text-muted mt-1">纬线总数 (task)</div>
      </div>
      <!-- 织入进度: A 皮 .skein-bar 蓝金流光 -->
      <div class="card p-4">
        <div class="text-2xl font-semibold" style="color:var(--head)">{{ combinedPct }}%</div>
        <div class="text-xs text-muted mt-1">织入进度 (含 subtask)</div>
        <div class="mt-2 skein-bar">
          <div class="skein-fill" :style="'width:'+combinedPct+'%'"></div>
        </div>
      </div>
    </section>

    <div v-if="estMeta" class="text-xs text-muted mb-4 px-1">{{ estMeta }}</div>

    <!-- 织面状态分布: C 骨 .loom-face + 经线股 + 织结 -->
    <section class="loom-face mb-4">
      <div class="px-5 pt-5 pb-1 text-sm font-semibold" style="color:var(--head)">状态织面 · 经线股分布</div>
      <div v-for="(row, ri) in dists" :key="row.key" class="weft-row" :class="ri===0?'':''">
        <div class="weft-tag">
          <div class="code">{{ row.label }}</div>
          <div class="desc">{{ row.total }} 根</div>
        </div>
        <div>
          <div v-if="!row.total" class="text-xs text-muted py-1">无数据</div>
          <template v-else>
            <!-- 经线股分段条 -->
            <div class="flex h-3 rounded overflow-hidden" style="background:var(--line)">
              <div v-for="s in row.segs" :key="s.label" :title="s.label+' '+s.count"
                :style="'width:'+s.pct+'%;background:'+s.color"></div>
            </div>
            <!-- 织结行 + 图例 -->
            <div class="knots mt-2.5">
              <div v-for="s in row.segs" :key="s.label" class="inline-flex items-center gap-1.5" :title="s.label+' '+s.count">
                <span class="knot" :class="s.knot"></span>
                <span class="text-xs text-muted">{{ s.label }} <span style="color:var(--head)">{{ s.count }}</span></span>
              </div>
            </div>
          </template>
        </div>
        <div class="weft-meta">
          <div class="frac">{{ row.total }}<small> 根</small></div>
        </div>
      </div>
    </section>

    <!-- 上机队列: C 骨 .bobbin 线轴 -->
    <section class="card p-5">
      <div class="flex items-center gap-2 mb-3">
        <h2 class="text-sm font-semibold" style="color:var(--head)">上机队列 · 待织线轴</h2>
        <span class="text-xs text-muted">{{ pendingQueue.length }}</span>
        <span class="flex-1"></span>
        <a href="#/queue" class="btn btn-primary" style="padding:5px 12px;font-size:12px">查看全部 →</a>
      </div>
      <div v-if="!pendingQueue.length" class="text-muted text-center py-6 text-sm">线轴架空 — 无待上机 subtask</div>
      <div v-else class="deck-grid">
        <a v-for="q in pendingQueue.slice(0, 6)" :key="q.tid+'/'+q.sid" :href="'#/task/'+encodeURIComponent(q.tid)" class="bobbin entrance" :style="q.ready?'':'border-left-color:var(--st-pending)'">
          <span class="spool" :style="q.ready?'':'color:var(--st-pending);background:color-mix(in srgb,var(--st-pending) 16%,transparent);border-color:color-mix(in srgb,var(--st-pending) 35%,transparent)'">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="6" rx="7" ry="2.5"/><path d="M5 6v12c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V6"/><path d="M5 12c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5"/></svg>
          </span>
          <div class="min-w-0 flex-1">
            <div class="b-name">{{ q.name }}</div>
            <div class="b-meta"><code style="font-size:11px">{{ q.tid }}/{{ q.sid }}</code> · {{ q.agent }}</div>
          </div>
          <span v-if="q.ready" class="ready-tag">就绪</span>
        </a>
      </div>
    </section>
  </div>
</div>`;

export async function render(mount, params, ctx) {
  const { api, onLive } = ctx;

  // 先拉数据再 createApp (对齐 task.js/spec.js: petite-vue 无对外句柄, 初始态直接注入)。
  async function fetchState() {
    try {
      const r = await api.dashboard();
      return {
        loadErr: "", proj: r.proj || "", taskCount: r.taskCount || 0, doneRate: r.doneRate || 0,
        activeCount: r.activeCount || 0, combinedPct: r.combinedPct || 0,
        estMeta: r.estMeta || "", pendingQueue: r.pendingQueue || [],
        dists: [
          Object.assign({ key: "task", label: "任务级" }, segments(r.statusDist)),
          Object.assign({ key: "sub", label: "子任务级" }, segments(r.subStatusDist)),
        ],
      };
    } catch (e) {
      return {
        loadErr: (e && e.message) || String(e), proj: "", taskCount: 0, doneRate: 0,
        activeCount: 0, combinedPct: 0, estMeta: "", pendingQueue: [], dists: [],
      };
    }
  }

  async function mountApp() {
    const st = await fetchState();
    mount.innerHTML = TPL;
    window.PetiteVue.createApp(Object.assign({ C }, st)).mount(mount);
  }

  await mountApp();
  // ponytail: 软刷整体重挂 — dashboard 无本地交互态可丢, 无需精细 diff。
  onLive && onLive(mountApp);
}
