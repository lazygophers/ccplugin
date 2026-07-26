// SKEIN webapp · board 页 (htm 重写版 stub, 实现归 T4)。
// 现 board.js = 命令式 innerHTML + dagHtml (Sugiyama); T4 重写保留 dag.js 纯函数。
//
// render(mount, params, ctx) 契约: core `[arch] SPA page 模块统一契约`
//   ctx = { api, md, h, onLive, navigate }
//   onLive(remountFn) → WS 软刷; router 切页自动退订。

export async function render(mount, params, ctx) {
  const { api, onLive } = ctx;
  // TODO T4: 实现 board (ctx.api.data() 拉 cards/overview/nodeVar/nodeCls + dag.js 渲染)。
  mount.innerHTML =
    '<div class="glass-card p-8 max-w-2xl mx-auto text-center text-muted">' +
    '<div class="eyebrow">看板</div>' +
    '<h2 class="text-2xl font-bold text-head mt-2">SKEIN Board</h2>' +
    '<p class="mt-2 text-sm">待 T4 实现 · 命令式 innerHTML → htm 片段 (保留 dag.js Sugiyama)</p>' +
    "</div>";
}
