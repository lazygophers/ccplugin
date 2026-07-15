// skein-anim — anime.js 编排的进阶动效: 右栏卡片错峰浮入 (首屏一次) + 概览统计数字滚动 (每次刷新)。
// 纯增强, 无则退化: anime 未加载 (A undefined) 各函数直接 no-op, 卡片保持默认可见。尊重 prefers-reduced-motion。
// 接线: 包裹 switcher.js 暴露的 window.__skeinBindContent → 每次软刷新重渲染 .layout 后重跑; 首屏本脚本执行时 .layout 已由 switcher 渲染完, 直接跑一次。
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var A = window.anime;
  var firstPaint = true;

  // 概览统计数字 0→目标 滚动 (值未变则跳过, 免每次刷新空跑)
  function countUp() {
    if (!A) return;
    document.querySelectorAll('.stat-n').forEach(function (el) {
      var target = parseInt(el.textContent, 10);
      if (isNaN(target)) return;
      if (el.__skTo === target) return;
      var from = el.__skTo != null ? el.__skTo : 0;
      el.__skTo = target;
      var o = { v: from };
      A({
        targets: o, v: target, round: 1, duration: 720, easing: 'easeOutCubic',
        update: function () { el.textContent = o.v; }
      });
    });
  }

  // 右栏 task 卡错峰浮入 (translateY + 淡入), 仅首屏 — 软刷新的新卡默认可见不再隐藏, 免实时更新时反复闪烁
  function enter() {
    if (!A) return;
    var cards = document.querySelectorAll('.col-main > .card');
    if (!cards.length) return;
    A.set(cards, { opacity: 0, translateY: 18 });
    A({
      targets: cards, opacity: 1, translateY: 0, duration: 560,
      delay: A.stagger(65, { start: 60 }), easing: 'easeOutCubic'
    });
  }

  function run() {
    if (reduce) return;
    countUp();
    if (firstPaint) { enter(); firstPaint = false; }
  }

  var prev = window.__skeinBindContent;
  window.__skeinBindContent = function () {
    if (prev) prev.apply(this, arguments);
    run();
  };

  if (document.readyState !== 'loading') run();
  else document.addEventListener('DOMContentLoaded', run);
})();
