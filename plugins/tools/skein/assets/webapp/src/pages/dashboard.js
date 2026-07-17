// SKEIN Dashboard 页 (默认首页 #/dashboard): 统计概览 — KPI 卡片行 (完成率环/活跃数/task总数/综合进度)
// + 状态分布 (task 级 statusDist / subtask 级 subStatusDist, 状态色分段条) + 待执行队列摘要 (pendingQueue 前几条, 跳 #/queue)。
// 只读视图; 数据 api.dashboard() 一次拉全 (proj/taskCount/doneRate/activeCount/combinedPct/statusDist/subStatusDist/estMeta/pendingQueue), onLive 软刷。
// page 契约: render(mount, params, ctx); ctx={api, md, onLive}; 响应式走 window.PetiteVue.createApp.

// 状态中文 → --st-* 色令牌 (task S_* 与 subtask SS_* 合并; 运行中 复用 active 色)
const ST_VAR = {
  "待处理": "--st-pending", "进行中": "--st-active", "运行中": "--st-active",
  "检查中": "--st-check", "已完成": "--st-done", "失败": "--st-failed",
};
const stColor = (st) => `var(${ST_VAR[st] || "--st-pending"})`;

// 分布字典 → 有序分段 (固定状态序, 只留计数>0), 供分段条 + 图例
const ST_ORDER = ["进行中", "运行中", "检查中", "待处理", "已完成", "失败"];
function segments(dist) {
  const d = dist || {};
  const total = Object.values(d).reduce((a, b) => a + b, 0);
  const segs = ST_ORDER.filter((k) => d[k] > 0).map((k) => ({
    label: k, count: d[k], color: stColor(k),
    pct: total ? (d[k] / total) * 100 : 0,
  }));
  return { total, segs };
}

const C = 2 * Math.PI * 26;  // 完成率环周长 (r=26)

const TPL = `
<div class="max-w-4xl mx-auto">
  <!-- 项目为空: 首页空态 -->
  <div v-if="loadErr" class="card p-10 text-center text-muted">
    <div class="text-3xl mb-2">⚠️</div>
    <div class="text-sm" style="color:var(--st-failed)">{{ loadErr }}</div>
  </div>
  <div v-else-if="!taskCount" class="card p-16 text-center text-muted">
    <div class="text-4xl mb-3">🧵</div>
    <div class="text-sm">暂无任务 — 用 <code>skein create</code> 建第一个 task。</div>
  </div>

  <div v-else>
    <!-- KPI 卡片行 -->
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
          <div class="text-xs text-muted">完成率</div>
        </div>
      </div>
      <!-- 活跃数 -->
      <div class="card p-4">
        <div class="text-2xl font-semibold" style="color:var(--st-active)" :data-count="activeCount">{{ activeCount }}</div>
        <div class="text-xs text-muted mt-1">活跃 task (进行/检查)</div>
      </div>
      <!-- task 总数 -->
      <div class="card p-4">
        <div class="text-2xl font-semibold" style="color:var(--head)" :data-count="taskCount">{{ taskCount }}</div>
        <div class="text-xs text-muted mt-1">task 总数</div>
      </div>
      <!-- 综合进度 -->
      <div class="card p-4">
        <div class="text-2xl font-semibold" style="color:var(--head)">{{ combinedPct }}%</div>
        <div class="text-xs text-muted mt-1">综合进度 (含 subtask)</div>
        <div class="mt-2 h-1.5 rounded overflow-hidden" style="background:var(--line)">
          <div class="h-full rounded" :style="'width:'+combinedPct+'%;background:var(--accent)'"></div>
        </div>
      </div>
    </section>

    <div v-if="estMeta" class="text-xs text-muted mb-4 px-1">{{ estMeta }}</div>

    <!-- 状态分布 -->
    <section class="card p-5 mb-4">
      <h2 class="text-sm font-semibold mb-4" style="color:var(--head)">状态分布</h2>
      <div class="space-y-5">
        <div v-for="row in dists" :key="row.key">
          <div class="flex items-center gap-2 mb-1.5">
            <span class="text-xs font-medium" style="color:var(--head)">{{ row.label }}</span>
            <span class="text-xs text-muted">{{ row.total }}</span>
          </div>
          <div v-if="!row.total" class="text-xs text-muted py-1">无数据</div>
          <template v-else>
            <div class="flex h-3 rounded overflow-hidden" style="background:var(--line)">
              <div v-for="s in row.segs" :key="s.label" :title="s.label+' '+s.count"
                :style="'width:'+s.pct+'%;background:'+s.color"></div>
            </div>
            <div class="flex flex-wrap gap-x-4 gap-y-1 mt-2">
              <span v-for="s in row.segs" :key="s.label" class="inline-flex items-center gap-1.5 text-xs text-muted">
                <span class="inline-block w-2.5 h-2.5 rounded-sm" :style="'background:'+s.color"></span>
                {{ s.label }} <span style="color:var(--head)">{{ s.count }}</span>
              </span>
            </div>
          </template>
        </div>
      </div>
    </section>

    <!-- 待执行队列摘要 -->
    <section class="card p-5">
      <div class="flex items-center gap-2 mb-3">
        <h2 class="text-sm font-semibold" style="color:var(--head)">待执行队列</h2>
        <span class="text-xs text-muted">{{ pendingQueue.length }}</span>
        <span class="flex-1"></span>
        <a href="#/queue" class="text-xs" style="color:var(--accent)">查看全部 →</a>
      </div>
      <div v-if="!pendingQueue.length" class="text-muted text-center py-6 text-sm">队列为空 — 无待派 subtask</div>
      <div v-else class="space-y-1.5">
        <a v-for="q in pendingQueue.slice(0, 6)" :key="q.tid+'/'+q.sid" :href="'#/task/'+encodeURIComponent(q.tid)"
          class="flex items-center gap-2 rounded p-2 hover:bg-[var(--line)]" style="border:1px solid var(--line)">
          <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="'background:'+(q.ready?'var(--st-active)':'var(--st-pending)')"
            :title="q.ready?'就绪':'排队中'"></span>
          <code class="text-[11px] text-muted shrink-0">{{ q.tid }}/{{ q.sid }}</code>
          <span class="text-sm truncate">{{ q.name }}</span>
          <span class="flex-1"></span>
          <span class="text-[11px] text-muted shrink-0">{{ q.agent }}</span>
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
        loadErr: "", taskCount: r.taskCount || 0, doneRate: r.doneRate || 0,
        activeCount: r.activeCount || 0, combinedPct: r.combinedPct || 0,
        estMeta: r.estMeta || "", pendingQueue: r.pendingQueue || [],
        dists: [
          Object.assign({ key: "task", label: "任务级" }, segments(r.statusDist)),
          Object.assign({ key: "sub", label: "子任务级" }, segments(r.subStatusDist)),
        ],
      };
    } catch (e) {
      return {
        loadErr: (e && e.message) || String(e), taskCount: 0, doneRate: 0,
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
