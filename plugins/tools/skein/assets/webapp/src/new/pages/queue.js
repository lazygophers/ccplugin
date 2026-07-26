// SKEIN webapp · queue 队列页 (htm 重写版 stub, 实现归 T5)。
// 现 queue.js = 只读视图 (readyTasks/readySubtasks/pendingQueue); T5 重写三只读页 (dashboard/queue/archive)。
//
// render(mount, params, ctx):
//   ctx.api.queue() 拉队列; onLive 软刷 (无本地态可丢)。

export async function render(mount, params, ctx) {
  const { api, onLive } = ctx;
  // TODO T5: 实现 queue (ctx.api.queue() + readyTasks/readySubtasks/pendingQueue 渲染)。
  mount.innerHTML =
    '<div class="glass-card p-8 max-w-2xl mx-auto text-center text-muted">' +
    '<div class="eyebrow">队列</div>' +
    '<h2 class="text-2xl font-bold text-head mt-2">SKEIN Queue</h2>' +
    '<p class="mt-2 text-sm">待 T5 实现 · 只读队列视图 (readyTasks/readySubtasks/pendingQueue)</p>' +
    "</div>";
}
