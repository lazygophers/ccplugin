// SKEIN webapp · task 页 (htm 重写版 stub, 实现归 T6)。
// 现 task.js = 列表/详情/DAG/exec runRead; T6 重写两复杂页 (task + spec)。
//
// render(mount, params, ctx):
//   params.id 存在 → /task?id=<tid> 详情; 无 id → 列表 (ctx.api.data() 取 cards)。

export async function render(mount, params, ctx) {
  const { api, onLive } = ctx;
  // TODO T6: 实现 task 列表/详情 (params.id ? ctx.api.task(id) : ctx.api.data(); DAG; exec runRead)。
  const tid = params.id ? " · " + params.id : "";
  mount.innerHTML =
    '<div class="glass-card p-8 max-w-2xl mx-auto text-center text-muted">' +
    '<div class="eyebrow">任务' + tid + "</div>" +
    '<h2 class="text-2xl font-bold text-head mt-2">SKEIN Task</h2>' +
    '<p class="mt-2 text-sm">待 T6 实现 · 列表/详情/DAG/exec</p>' +
    "</div>";
}
