// SKEIN Task 页: 单 task 审阅 — 头 (id/名/状态/描述) + 规划三文档 (prd/design/findings, md 渲染) + subtask 列表 (状态/进度/deps) + 契约区。
// 只读视图; 数据 api.task(id) 一次拉全, onLive 软刷。task 不存在(404) → 友好空态。
// page 契约: render(mount, params, ctx); params={id}; ctx={api, md, onLive}; 响应式走 window.PetiteVue.createApp.

// 状态中文 → badge 令牌类 (task S_* 与 subtask SS_* 合并; 运行中 复用 active 色)
const BADGE = {
  "待处理": "badge-pending", "进行中": "badge-active", "运行中": "badge-active",
  "检查中": "badge-check", "已完成": "badge-done", "失败": "badge-failed",
};
const badgeCls = (st) => BADGE[st] || "badge-pending";

// subtask 完成百分比 (对齐后端 _sub_pct: done 强制 100; 验收done/验收, 无验收未完成即 0)
function subPct(s) {
  if (s.status === "已完成") return 100;
  const crit = (s["验收"] || []).length;
  return crit ? Math.round(((s["验收done"] || []).length / crit) * 100) : 0;
}

const TPL = `
<div class="max-w-4xl mx-auto">
  <!-- 加载失败 / 404 空态 -->
  <div v-if="loadErr" class="card p-10 text-center text-muted">
    <div class="text-3xl mb-2">{{ notFound ? '🔍' : '⚠️' }}</div>
    <div class="text-sm" :style="notFound ? '' : 'color:var(--st-failed)'">{{ loadErr }}</div>
    <a href="#/" class="inline-block mt-4 text-sm" style="color:var(--accent)">← 返回看板</a>
  </div>

  <div v-else>
    <!-- task 头 -->
    <header class="card p-5 mb-4">
      <div class="flex items-center gap-3 flex-wrap">
        <code class="text-sm px-2 py-0.5 rounded" style="background:var(--line);color:var(--head)">{{ task.id }}</code>
        <h1 class="text-lg font-semibold" style="color:var(--head)">{{ task.name || task.id }}</h1>
        <span class="badge" :class="badgeCls(task.status)">{{ task.status }}</span>
        <span v-if="archived" class="badge badge-done opacity-70">已归档</span>
        <span class="flex-1"></span>
        <span v-if="task.deps && task.deps.length" class="text-xs text-muted">依赖 {{ task.deps.join(', ') }}</span>
      </div>
      <p v-if="task.desc" class="text-sm text-muted mt-2 whitespace-pre-wrap">{{ task.desc }}</p>
    </header>

    <!-- 规划三文档 tab -->
    <section class="card mb-4 overflow-hidden">
      <div class="flex" style="border-bottom:1px solid var(--line)">
        <button v-for="d in docTabs" :key="d.key"
          class="px-4 py-2 text-sm relative"
          :style="tab===d.key ? 'color:var(--accent);border-bottom:2px solid var(--accent)' : 'color:var(--muted)'"
          @click="tab=d.key">
          {{ d.label }}
          <span v-if="!docs[d.key]" class="ml-1 text-[10px] opacity-50">空</span>
        </button>
      </div>
      <div class="p-5">
        <div v-if="!docs[tab]" class="text-muted text-center py-16 text-sm">
          <div class="text-2xl mb-1">📄</div>{{ docLabel(tab) }} 暂无内容
        </div>
        <div v-else class="md-body" v-html="renderedDoc"></div>
      </div>
    </section>

    <!-- subtask 列表 -->
    <section class="card p-5 mb-4">
      <div class="flex items-center gap-2 mb-3">
        <h2 class="text-sm font-semibold" style="color:var(--head)">子任务</h2>
        <span class="text-xs text-muted">{{ subtasks.length }}</span>
      </div>
      <div v-if="!subtasks.length" class="text-muted text-center py-8 text-sm">尚无子任务拆分</div>
      <div v-else class="space-y-2">
        <div v-for="s in subtasks" :key="s.sid" class="rounded p-3" style="border:1px solid var(--line)">
          <div class="flex items-center gap-2 flex-wrap">
            <code class="text-xs" style="color:var(--head)">{{ s.sid }}</code>
            <span class="text-sm">{{ s.name || s.sid }}</span>
            <span class="badge text-[11px]" :class="badgeCls(s.status)">{{ s.status }}</span>
            <span class="flex-1"></span>
            <span v-if="s.agent" class="text-[11px] text-muted">{{ s.agent }}</span>
          </div>
          <p v-if="s.desc" class="text-xs text-muted mt-1 whitespace-pre-wrap">{{ s.desc }}</p>
          <!-- 进度条 -->
          <div class="flex items-center gap-2 mt-2">
            <div class="flex-1 h-1.5 rounded overflow-hidden" style="background:var(--line)">
              <div class="h-full rounded" :style="'width:'+pct(s)+'%;background:var(--st-done)'"></div>
            </div>
            <span class="text-[11px] text-muted w-9 text-right">{{ pct(s) }}%</span>
          </div>
          <div v-if="deps(s).length" class="text-[11px] text-muted mt-1">依赖: {{ deps(s).join(', ') }}</div>
        </div>
      </div>
    </section>

    <!-- 契约区 (空则不显) -->
    <section v-if="contracts.length" class="card p-5">
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

const DOC_TABS = [
  { key: "prd", label: "PRD" },
  { key: "design", label: "详细设计" },
  { key: "findings", label: "调研收敛" },
];

export async function render(mount, params, ctx) {
  const { api, md, onLive } = ctx;

  // 先拉数据再 createApp (对齐 spec.js: petite-vue 无对外实例句柄, 初始态直接注入)。
  async function fetchState() {
    try {
      const r = await api.task(params.id);
      return { loadErr: "", notFound: false,
        task: r.task || {}, docs: r.docs || {},
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
    const st = await fetchState();
    mount.innerHTML = TPL;
    window.PetiteVue.createApp(Object.assign({
      tab: "prd",
      docTabs: DOC_TABS,
      badgeCls,
      pct: subPct,
      deps: (s) => s.depends_on || [],
      docLabel: (k) => (DOC_TABS.find((d) => d.key === k) || {}).label || k,
      get renderedDoc() { return md.renderSafe(this.docs[this.tab] || ""); },
    }, st)).mount(mount);
  }

  await mountApp();
  // ponytail: 软刷整体重挂 — task 详情小, 无需精细 diff; 会丢当前 tab 选择, 可接受。
  onLive && onLive(mountApp);
}
