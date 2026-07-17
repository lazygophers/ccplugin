// SKEIN 归档页 (#/archive): 已归档 task 浏览 — 卡片列表 (id/名/状态 badge/描述/归档时间/subtask 数), 每项跳 #/task/:id 看详情+prd。
// 只读视图; 数据 api.archive() 一次拉全 ([{id,name,status,desc,finished,archivedAt,subs}]), 按 finished 倒序; onLive 软刷。空态友好占位。
// page 契约: render(mount, params, ctx); ctx={api, md, onLive}; 响应式走 window.PetiteVue.createApp.

// 状态中文 → badge 令牌类 (对齐 task.js)
const BADGE = {
  "待处理": "badge-pending", "进行中": "badge-active", "运行中": "badge-active",
  "检查中": "badge-check", "已完成": "badge-done", "失败": "badge-failed",
};
const badgeCls = (st) => BADGE[st] || "badge-pending";

// finished: Unix epoch 秒 → 本地日期串 (无则回落 archivedAt 的 月-日)
function finishedLabel(a) {
  if (a.finished) {
    const d = new Date(a.finished * 1000);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }
  return a.archivedAt || "—";
}

const STATUSES = ["", "已完成", "失败", "待处理", "进行中", "检查中"];

const TPL = `
<div class="max-w-4xl mx-auto">
  <div class="flex items-center gap-2 mb-4 px-1">
    <h1 class="text-lg font-semibold" style="color:var(--head)">归档</h1>
    <span v-if="!loadErr && items.length" class="text-xs text-muted">{{ filtered.length }}/{{ items.length }}</span>
  </div>

  <!-- 搜索 + 状态筛选 -->
  <div v-if="!loadErr && items.length" class="flex items-center gap-2 mb-3 px-1 flex-wrap">
    <input v-model="q" type="search" placeholder="搜索 id / 名称 / 描述…"
      class="flex-1 min-w-[12rem] px-3 py-1.5 text-sm rounded border bg-transparent"
      style="border-color:var(--line);color:var(--head)">
    <select v-model="statusFilter"
      class="px-2 py-1.5 text-sm rounded border bg-transparent"
      style="border-color:var(--line);color:var(--head)">
      <option v-for="s in statuses" :key="s" :value="s">{{ s || '全部状态' }}</option>
    </select>
  </div>

  <!-- 加载失败 -->
  <div v-if="loadErr" class="card p-10 text-center text-muted">
    <div class="text-3xl mb-2">⚠️</div>
    <div class="text-sm" style="color:var(--st-failed)">{{ loadErr }}</div>
  </div>

  <!-- 空态: 无归档 -->
  <div v-else-if="!items.length" class="card p-16 text-center text-muted">
    <div class="text-4xl mb-3">📦</div>
    <div class="text-sm">暂无归档 — 完成的 task 超保留期后会自动归档到这里。</div>
  </div>

  <!-- 空态: 有归档但无匹配 -->
  <div v-else-if="!filtered.length" class="card p-16 text-center text-muted">
    <div class="text-4xl mb-3">🔍</div>
    <div class="text-sm">无匹配结果 — 调整搜索词或状态筛选后重试。</div>
  </div>

  <!-- 归档卡片列表 (按 finished 倒序) -->
  <div v-else class="space-y-2">
    <a v-for="a in filtered" :key="a.id" :href="'#/task/'+encodeURIComponent(a.id)"
      class="card block p-4 hover:bg-[var(--line)] transition-colors">
      <div class="flex items-center gap-2 flex-wrap">
        <code class="text-xs px-1.5 py-0.5 rounded" style="background:var(--line);color:var(--head)">{{ a.id }}</code>
        <span class="text-sm font-medium" style="color:var(--head)">{{ a.name || a.id }}</span>
        <span class="badge text-[11px]" :class="badgeCls(a.status)">{{ a.status }}</span>
        <span class="badge badge-done opacity-70 text-[11px]">已归档</span>
        <span class="flex-1"></span>
        <span class="text-[11px] text-muted shrink-0">{{ fLabel(a) }}</span>
      </div>
      <p v-if="a.desc" class="text-xs text-muted mt-1.5 whitespace-pre-wrap line-clamp-2">{{ a.desc }}</p>
      <div class="text-[11px] text-muted mt-2">{{ a.subs }} 个子任务</div>
    </a>
  </div>
</div>`;

export async function render(mount, params, ctx) {
  const { api, onLive } = ctx;

  // 先拉数据再 createApp (对齐 dashboard.js/task.js: petite-vue 无对外句柄, 初始态直接注入)。
  async function fetchState() {
    try {
      const list = (await api.archive()) || [];
      // finished 倒序 (最近归档在前); 无 finished 沉底
      list.sort((x, y) => (y.finished || 0) - (x.finished || 0));
      return { loadErr: "", items: list };
    } catch (e) {
      return { loadErr: (e && e.message) || String(e), items: [] };
    }
  }

  async function mountApp() {
    const st = await fetchState();
    mount.innerHTML = TPL;
    // ponytail: 搜索/筛选态在软刷重挂时会清空 (petite-vue 整体重挂丢本地态) —
    // 归档列表只读且 onLive 频率低, 接受清空, 不上 hash 持久化。
    const app = Object.assign(
      {
        badgeCls,
        fLabel: finishedLabel,
        statuses: STATUSES,
        q: "",
        statusFilter: "",
        get filtered() {
          const q = this.q.trim().toLowerCase();
          const sf = this.statusFilter;
          return this.items.filter((a) => {
            if (sf && a.status !== sf) return false;
            if (!q) return true;
            return (
              String(a.id).toLowerCase().includes(q) ||
              (a.name || "").toLowerCase().includes(q) ||
              (a.desc || "").toLowerCase().includes(q)
            );
          });
        },
      },
      st
    );
    window.PetiteVue.createApp(app).mount(mount);
  }

  await mountApp();
  // ponytail: 软刷整体重挂 — 归档列表只读, 无本地交互态可丢。
  onLive && onLive(mountApp);
}
