// SKEIN webapp · dashboard 概览页 (htm 重写版 stub, 实现归 T5)。
// 现 dashboard.js = KPI 墙 + 状态分布; T5 重写三只读页 (dashboard/queue/archive)。
//
// render(mount, params, ctx):
//   ctx.api.dashboard() 拉 KPI (taskCount/doneRate/activeCount/combinedPct/statusDist/subStatusDist 等);
//   onLive 软刷 (无本地态)。

export async function render(mount, params, ctx) {
  const { api, onLive } = ctx;
  // TODO T5: 实现 dashboard KPI 墙 (taskCount/doneRate/activeCount/combinedPct/状态分布)。
  mount.innerHTML =
    '<div class="glass-card p-8 max-w-2xl mx-auto text-center text-muted">' +
    '<div class="eyebrow">概览</div>' +
    '<h2 class="text-2xl font-bold text-head mt-2">SKEIN Dashboard</h2>' +
    '<p class="mt-2 text-sm">待 T5 实现 · KPI 墙 + 状态分布</p>' +
    "</div>";
}
