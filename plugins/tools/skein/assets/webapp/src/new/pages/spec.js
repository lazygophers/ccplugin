// SKEIN webapp · spec 规范页 (htm 重写版 stub, 实现归 T6)。
// 现 spec.js = 树/编辑/diff 确认/保存; 无 onLive (编辑态保守不软刷); T6 重写两复杂页 (task + spec)。
//
// render(mount, params, ctx):
//   ctx.api.spec() 拉树; ctx.api.specFile(path) 读文件; ctx.api.specSave(path, content) 保存 (diff 确认)。

export async function render(mount, params, ctx) {
  const { api } = ctx;
  // TODO T6: 实现 spec (树/编辑/diff 确认/保存); 无 onLive (编辑态保守)。
  mount.innerHTML =
    '<div class="glass-card p-8 max-w-2xl mx-auto text-center text-muted">' +
    '<div class="eyebrow">规范</div>' +
    '<h2 class="text-2xl font-bold text-head mt-2">SKEIN Spec</h2>' +
    '<p class="mt-2 text-sm">待 T6 实现 · 树/编辑/diff 确认/保存 (无 onLive)</p>' +
    "</div>";
}
