// SKEIN Queue 页 (/queue): 待执行队列 — 三区展示。
//   (1) 就绪 task 批 readyTasks (可 start; id/名/依赖, 跳 /task?id=:id)
//   (2) 就绪 subtask 调度序 readySubtasks (active task 内可 claim; tid/sid/名/agent)
//   (3) 待执行总览 pendingQueue (全部未完成 task/subtask 双层调度序; ready 点区分就绪/排队)
// 只读视图; 数据 api.queue() 一次拉全 (readyTasks/readySubtasks/pendingQueue), onLive 软刷。
// page 契约: render(mount, params, ctx); ctx={api, md, onLive}; 响应式走 window.PetiteVue.createApp.
//
// hover/click 详情浮层: hoverKey (当前 hover) + pinnedKey (当前钉住), 显隐 = hoverKey===key || pinnedKey===key;
// click 条目 toggle pinnedKey; document click (浮层外) 清 pinnedKey。

// 状态中文 → badge 令牌类 (复用 task.js 同名映射)。
const BADGE = {
  "待处理": "badge-pending", "进行中": "badge-active", "运行中": "badge-active",
  "检查中": "badge-check", "已完成": "badge-done", "失败": "badge-failed",
};
const badgeCls = (st) => BADGE[st] || "badge-pending";

const STYLE = `<style>
.qrow{position:relative}
.qpop{position:absolute;left:0;right:auto;top:100%;margin-top:4px;z-index:1000;
  min-width:240px;max-width:340px;background:var(--card);border:1px solid var(--brd);
  border-radius:8px;padding:10px 12px;font:12px var(--font);color:var(--head);
  box-shadow:0 4px 14px rgba(0,0,0,.18);cursor:default}
.qpop k{color:var(--muted);font-weight:600}
.qpop .bar{flex:1;height:6px;border-radius:4px;background:var(--line);overflow:hidden}
.qpop .bar>div{height:100%;background:var(--st-done)}
</style>`;

const TPL = `
<div class="px-7">
  <div v-if="loadErr" class="card p-10 text-center text-muted">
    <div class="empty-ico"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>
    <div class="text-sm" style="color:var(--st-failed)">{{ loadErr }}</div>
  </div>

  <div v-else>
    <!-- 全空态 -->
    <div v-if="!activeTasks.length && !runningSubs.length && !readyTasks.length && !readySubtasks.length && !pendingQueue.length"
      class="card p-16 text-center text-muted">
      <div class="empty-ico"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
      <div class="text-sm">队列已清空 — 无就绪 task、无待派 subtask。</div>
    </div>

    <template v-else>
      <!-- (0) 进行中: activeTasks + runningSubs -->
      <section v-if="activeTasks.length || runningSubs.length" class="card p-5 mb-4">
        <div class="flex items-center gap-2 mb-3">
          <span class="w-2 h-2 rounded-full" style="background:var(--st-active)"></span>
          <h2 class="text-sm font-semibold" style="color:var(--head)">进行中</h2>
          <span class="text-[11px] text-muted">活跃 task 实时进度 + 正在跑的 subtask</span>
        </div>
        <!-- active task 行 -->
        <div v-if="activeTasks.length" class="space-y-1.5 mb-3">
          <a v-for="t in activeTasks" :key="'at:'+t.id" :href="'/task?id='+encodeURIComponent(t.id)"
            class="qrow qrow-active flex items-center gap-2 rounded p-2 hover:bg-[var(--line)]"
            style="border:1px solid var(--line)">
            <code class="text-[11px] text-muted shrink-0">{{ t.id }}</code>
            <span class="text-sm truncate">{{ t.name }}</span>
            <span class="badge text-[11px] shrink-0" :class="badgeCls(t.status)">{{ t.status }}</span>
            <div class="flex-1 flex items-center gap-2 max-w-[200px]">
              <div class="bar flex-1"><div :style="'width:'+(t.pct||0)+'%'"></div></div>
              <span class="text-[11px] text-muted w-9 text-right">{{ t.pct||0 }}%</span>
            </div>
            <span class="text-[11px] text-muted shrink-0">{{ t.sdone }}/{{ t.stotal }}</span>
            <span class="text-[11px] text-muted shrink-0">{{ t.elapsed }}</span>
          </a>
        </div>
        <!-- running subtask 行 -->
        <div v-if="runningSubs.length" class="space-y-1.5">
          <a v-for="s in runningSubs" :key="'rs:'+s.tid+'/'+s.sid" :href="'/task?id='+encodeURIComponent(s.tid)"
            class="qrow qrow-active flex items-center gap-2 rounded p-2 hover:bg-[var(--line)]"
            style="border:1px solid var(--line)">
            <span class="w-1.5 h-1.5 rounded-full shrink-0" style="background:var(--st-active)"></span>
            <code class="text-[11px] text-muted shrink-0">{{ s.tid }}/{{ s.sid }}</code>
            <span class="text-sm truncate">{{ s.name }}</span>
            <span class="flex-1"></span>
            <span class="text-[11px] text-muted shrink-0">{{ s.agent }}</span>
            <span class="text-[11px] text-muted shrink-0">{{ s.elapsed }}</span>
          </a>
        </div>
      </section>

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
          <a v-for="t in readyTasks" :key="t.id" :href="'/task?id='+encodeURIComponent(t.id)"
            class="qrow flex items-center gap-2 rounded p-2 hover:bg-[var(--line)]"
            style="border:1px solid var(--line)"
            @mouseenter="hoverKey='t:'+t.id" @mouseleave="hoverKey=''" @click.prevent.stop="pin('t:'+t.id)">
            <code class="text-[11px] text-muted shrink-0">{{ t.id }}</code>
            <span class="text-sm truncate">{{ t.name }}</span>
            <span class="flex-1"></span>
            <span v-if="t.deps && t.deps.length" class="text-[11px] text-muted shrink-0">依赖 {{ t.deps.join(', ') }}</span>
            <div v-if="show('t:'+t.id)" class="qpop" @click.stop @mouseenter="hoverKey='t:'+t.id" @mouseleave="hoverKey=''">
              <div class="mb-1"><k>ID</k> <code>{{ t.id }}</code> <span class="badge text-[11px]" :class="badgeCls(t.status)">{{ t.status }}</span></div>
              <div class="mb-1"><k>名</k> {{ t.name }}</div>
              <p v-if="t.desc" class="text-muted whitespace-pre-wrap mb-1">{{ t.desc }}</p>
              <div v-if="t.deps && t.deps.length" class="mb-1"><k>依赖</k> {{ t.deps.join(', ') }}</div>
              <div class="flex items-center gap-2 mt-1">
                <k>进度</k><div class="bar"><div :style="'width:'+(t.spct||0)+'%'"></div></div>
                <span class="text-[11px] text-muted w-9 text-right">{{ t.spct||0 }}%</span>
              </div>
            </div>
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
            class="qrow flex items-center gap-2 rounded p-2 cursor-default" style="border:1px solid var(--line)"
            @mouseenter="hoverKey='s:'+s.tid+'/'+s.sid" @mouseleave="hoverKey=''" @click.stop="pin('s:'+s.tid+'/'+s.sid)">
            <span class="text-[11px] text-muted w-5 text-right shrink-0 select-none">{{ idx+1 }}</span>
            <a :href="'/task?id='+encodeURIComponent(s.tid)" class="shrink-0" @click.stop>
              <code class="text-[11px] text-muted">{{ s.tid }}/{{ s.sid }}</code>
            </a>
            <span class="text-sm truncate">{{ s.name }}</span>
            <span class="flex-1"></span>
            <span class="text-[11px] text-muted shrink-0">{{ s.agent }}</span>
            <div v-if="show('s:'+s.tid+'/'+s.sid)" class="qpop" @click.stop @mouseenter="hoverKey='s:'+s.tid+'/'+s.sid" @mouseleave="hoverKey=''">
              <div class="mb-1"><k>SUB</k> <code>{{ s.tid }}/{{ s.sid }}</code> <span class="badge text-[11px]" :class="badgeCls(s.status)">{{ s.status }}</span></div>
              <div class="mb-1"><k>名</k> {{ s.name }}</div>
              <p v-if="s.desc" class="text-muted whitespace-pre-wrap mb-1">{{ s.desc }}</p>
              <div class="mb-1"><k>agent</k> {{ s.agent }}</div>
              <div v-if="s.depends_on && s.depends_on.length"><k>依赖</k> {{ s.depends_on.join(', ') }}</div>
            </div>
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
          <a v-for="q in pendingQueue" :key="q.tid+'/'+q.sid" :href="'/task?id='+encodeURIComponent(q.tid)"
            class="qrow flex items-center gap-2 rounded p-2 hover:bg-[var(--line)]"
            style="border:1px solid var(--line)"
            @mouseenter="hoverKey='s:'+q.tid+'/'+q.sid" @mouseleave="hoverKey=''" @click.prevent.stop="pin('s:'+q.tid+'/'+q.sid)">
            <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="'background:'+(q.ready?'var(--st-active)':'var(--st-pending)')"
              :title="q.ready?'就绪':'排队中'"></span>
            <code class="text-[11px] text-muted shrink-0">{{ q.tid }}/{{ q.sid }}</code>
            <span class="text-sm truncate">{{ q.name }}</span>
            <span class="flex-1"></span>
            <span class="text-[11px] text-muted shrink-0">{{ q.agent }}</span>
            <div v-if="show('s:'+q.tid+'/'+q.sid)" class="qpop" @click.stop @mouseenter="hoverKey='s:'+q.tid+'/'+q.sid" @mouseleave="hoverKey=''">
              <div class="mb-1"><k>SUB</k> <code>{{ q.tid }}/{{ q.sid }}</code> <span class="badge text-[11px]" :class="badgeCls(q.status)">{{ q.status }}</span></div>
              <div class="mb-1"><k>名</k> {{ q.name }}</div>
              <p v-if="q.desc" class="text-muted whitespace-pre-wrap mb-1">{{ q.desc }}</p>
              <div class="mb-1"><k>agent</k> {{ q.agent }}</div>
              <div v-if="q.depends_on && q.depends_on.length"><k>依赖</k> {{ q.depends_on.join(', ') }}</div>
            </div>
          </a>
        </div>
      </section>
    </template>
  </div>
</div>`;

export async function render(mount, params, ctx) {
  const { api, onLive } = ctx;
  let docClick = null;

  // document click 监听 (浮层外清 pinnedKey); mountApp 重挂时去重, 防多次绑定。
  // ponytail: 用 mounted 实例闭包态 + 外层 guard 句柄, onLive 重挂无需手工解绑 (旧 mount DOM 被覆盖, listener 仍指旧闭包 pinnedKey 已失效由新实例接管)。
  async function fetchState() {
    try {
      const r = await api.queue();
      return {
        loadErr: "", readyTasks: r.readyTasks || [],
        readySubtasks: r.readySubtasks || [], pendingQueue: r.pendingQueue || [],
        activeTasks: r.activeTasks || [], runningSubs: r.runningSubs || [],
      };
    } catch (e) {
      return {
        loadErr: (e && e.message) || String(e),
        readyTasks: [], readySubtasks: [], pendingQueue: [],
        activeTasks: [], runningSubs: [],
      };
    }
  }

  async function mountApp() {
    const st = await fetchState();
    mount.innerHTML = STYLE + TPL;
    // 浮层状态对象 (闭包持有 = createApp 直接挂的 reactive state, 二者同一代理):
    //   - pin(key): 同 key 再 click 清空 (toggle); 否则钉住该 key。
    //   - show(key): 浮层显隐判据 = hoverKey===key || pinnedKey===key。
    //   - document click (浮层内已 @click.stop 阻断) → 清 pop.pinnedKey (与模板同源响应式)。
    const pop = Object.assign({
      hoverKey: "", pinnedKey: "",
      badgeCls,
      show(k) { return this.hoverKey === k || this.pinnedKey === k; },
      pin(k) { this.pinnedKey = this.pinnedKey === k ? "" : k; },
    }, st);
    window.PetiteVue.createApp(pop).mount(mount);
    // document click (浮层外) 清 pinnedKey; onLive 重挂前移除旧 listener 去重, 仅留最新 pop 句柄。
    if (docClick) document.removeEventListener("click", docClick);
    docClick = () => { pop.pinnedKey = ""; };
    document.addEventListener("click", docClick);
  }

  await mountApp();
  // ponytail: 软刷整体重挂 — queue 无本地交互态可丢, 无需精细 diff。
  onLive && onLive(mountApp);
}
