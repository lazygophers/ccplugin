// SKEIN webapp · archive 归档页 (htm 重写版 stub, 实现归 T5)。
// 现 archive.js = 只读归档列表; T5 重写三只读页 (dashboard/queue/archive)。
//
// render(mount, params, ctx):
//   ctx.api.archive() 拉归档; onLive 软刷 (无本地态)。

export async function render(mount, params, ctx) {
  const { api, onLive } = ctx;
  // TODO T5: 实现 archive (ctx.api.archive() + 列表渲染/搜索筛选)。
  mount.innerHTML =
    '<div class="glass-card p-8 max-w-2xl mx-auto text-center text-muted">' +
    '<div class="eyebrow">归档</div>' +
    '<h2 class="text-2xl font-bold text-head mt-2">SKEIN Archive</h2>' +
    '<p class="mt-2 text-sm">待 T5 实现 · 只读归档列表</p>' +
    "</div>";
}
