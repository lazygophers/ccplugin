// SKEIN Queue 页 (#/queue): 待执行队列 — 三区展示。
//   (1) 就绪 task 批 readyTasks (可 start; id/名/依赖, 跳 #/task/:id)
//   (2) 就绪 subtask 调度序 readySubtasks (active task 内可 claim; tid/sid/名/agent)
//   (3) 待执行总览 pendingQueue (全部未完成 task/subtask 双层调度序; ready 点区分就绪/排队)
// 只读视图; 数据 api.queue() 一次拉全 (readyTasks/readySubtasks/pendingQueue), onLive 软刷。
// page 契约: render(mount, params, ctx); ctx={api, md, onLive}; 响应式走 window.PetiteVue.createApp.

const TPL = `
<div class="max-w-4xl mx-auto">
  <div v-if="loadErr" class="card p-10 text-center text-muted">
    <div class="text-3xl mb-2">⚠️</div>
    <div class="text-sm" style="color:var(--st-failed)">{{ loadErr }}</div>
  </div>

  <template v-else>
    <!-- 全空态 -->
    <div v-if="!readyTasks.length && !readySubtasks.length && !pendingQueue.length"
      class="card p-16 text-center text-muted">
      <div class="text-4xl mb-3">✅</div>
      <div class="text-sm">队列已清空 — 无就绪 task、无待派 subtask。</div>
    </div>

    <template v-else>
      <!-- (1) 就绪 task 批 -->
      <section class="card p-5 mb-4">
        <div class="flex items-center gap-2 mb-3">
          <span class="w-2 h-2 rounded-full" style="background:var(--st-pending)"></span>
          <h2 class="text-sm font-semibold" style="color:var(--head)">就绪 task 批</h2>
          <span class="text-xs text-muted">{{ readyTasks.length }}</span>
          <span class="text-[11px] text-muted">依赖已满足, 可 <code>skein start</code></span>
        </div>
        <div v-if="!readyTasks.length" class="text-muted text-center py-6 text-sm">无就绪 task</div>
        <div v-else class="space-y-1.5">
          <a v-for="t in readyTasks" :key="t.id" :href="'#/task/'+encodeURIComponent(t.id)"
            class="flex items-center gap-2 rounded p-2 hover:bg-[var(--line)]" style="border:1px solid var(--line)">
            <code class="text-[11px] text-muted shrink-0">{{ t.id }}</code>
            <span class="text-sm truncate">{{ t.name }}</span>
            <span class="flex-1"></span>
            <span v-if="t.deps && t.deps.length" class="text-[11px] text-muted shrink-0">依赖 {{ t.deps.join(', ') }}</span>
          </a>
        </div>
      </section>

      <!-- (2) 就绪 subtask 调度序 -->
      <section class="card p-5 mb-4">
        <div class="flex items-center gap-2 mb-3">
          <span class="w-2 h-2 rounded-full" style="background:var(--st-active)"></span>
          <h2 class="text-sm font-semibold" style="color:var(--head)">就绪 subtask</h2>
          <span class="text-xs text-muted">{{ readySubtasks.length }}</span>
          <span class="text-[11px] text-muted">active task 内可立即 claim (调度序)</span>
        </div>
        <div v-if="!readySubtasks.length" class="text-muted text-center py-6 text-sm">无就绪 subtask</div>
        <ol v-else class="space-y-1.5">
          <li v-for="(s,idx) in readySubtasks" :key="s.tid+'/'+s.sid"
            class="flex items-center gap-2 rounded p-2" style="border:1px solid var(--line)">
            <span class="text-[11px] text-muted w-5 text-right shrink-0 select-none">{{ idx+1 }}</span>
            <a :href="'#/task/'+encodeURIComponent(s.tid)" class="shrink-0">
              <code class="text-[11px] text-muted">{{ s.tid }}/{{ s.sid }}</code>
            </a>
            <span class="text-sm truncate">{{ s.name }}</span>
            <span class="flex-1"></span>
            <span class="text-[11px] text-muted shrink-0">{{ s.agent }}</span>
          </li>
        </ol>
      </section>

      <!-- (3) 待执行总览 (双层调度序) -->
      <section class="card p-5">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-sm font-semibold" style="color:var(--head)">待执行总览</h2>
          <span class="text-xs text-muted">{{ pendingQueue.length }}</span>
          <span class="text-[11px] text-muted">全部未完成 subtask, 双层调度序</span>
        </div>
        <div v-if="!pendingQueue.length" class="text-muted text-center py-6 text-sm">队列为空 — 无待派 subtask</div>
        <div v-else class="space-y-1.5">
          <a v-for="q in pendingQueue" :key="q.tid+'/'+q.sid" :href="'#/task/'+encodeURIComponent(q.tid)"
            class="flex items-center gap-2 rounded p-2 hover:bg-[var(--line)]" style="border:1px solid var(--line)">
            <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="'background:'+(q.ready?'var(--st-active)':'var(--st-pending)')"
              :title="q.ready?'就绪':'排队中'"></span>
            <code class="text-[11px] text-muted shrink-0">{{ q.tid }}/{{ q.sid }}</code>
            <span class="text-sm truncate">{{ q.name }}</span>
            <span class="flex-1"></span>
            <span v-if="q.est" class="text-[11px] text-muted shrink-0">{{ q.est }}</span>
            <span class="text-[11px] text-muted shrink-0">{{ q.agent }}</span>
          </a>
        </div>
      </section>
    </template>
  </template>
</div>`;

export async function render(mount, params, ctx) {
  const { api, onLive } = ctx;

  // 先拉数据再 createApp (对齐 dashboard.js/task.js: petite-vue 无对外句柄, 初始态直接注入)。
  async function fetchState() {
    try {
      const r = await api.queue();
      return {
        loadErr: "", readyTasks: r.readyTasks || [],
        readySubtasks: r.readySubtasks || [], pendingQueue: r.pendingQueue || [],
      };
    } catch (e) {
      return {
        loadErr: (e && e.message) || String(e),
        readyTasks: [], readySubtasks: [], pendingQueue: [],
      };
    }
  }

  async function mountApp() {
    const st = await fetchState();
    mount.innerHTML = TPL;
    window.PetiteVue.createApp(st).mount(mount);
  }

  await mountApp();
  // ponytail: 软刷整体重挂 — queue 无本地交互态可丢, 无需精细 diff。
  onLive && onLive(mountApp);
}
