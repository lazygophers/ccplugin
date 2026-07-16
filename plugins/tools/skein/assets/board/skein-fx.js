// skein-fx — 缕光主题 JS 动效: canvas 莫奈水面光斑 (drifting bokeh) + 鼠标涟漪辉光。
// 自门控: 仅 data-theme=skein 激活; 其余主题直接 no-op。纯原生, 无依赖, 离线可跑。
(function () {
  var root = document.documentElement;
  if (root.getAttribute('data-theme') !== 'skein') return;
  // data-motion=full (默认) → 无视系统 reduce-motion; 去掉该属性才尊重系统
  if (root.getAttribute('data-motion') !== 'full'
    && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var cv = document.createElement('canvas');
  cv.setAttribute('aria-hidden', 'true');
  // z-index:-1 → 落在 body 莫奈渐变之上、卡片之下; pointer-events:none 不挡交互
  cv.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;z-index:-1;pointer-events:none';
  document.body.appendChild(cv);
  var ctx = cv.getContext('2d');

  // 取主题 accent 色 (随烘焙 palette 变, 不硬编码)
  function cssVar(n) { return getComputedStyle(root).getPropertyValue(n).trim() || '#8aa0ff'; }
  var COL = [cssVar('--accent'), cssVar('--accent2'), cssVar('--accent')];

  var dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
  var W = 0, H = 0;
  function resize() {
    W = window.innerWidth; H = window.innerHeight;
    cv.width = W * dpr; cv.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  window.addEventListener('resize', resize);

  // 光斑: 缓漂 + 呼吸缩放, 莫奈睡莲池碎光
  var N = Math.min(40, Math.round(W * H / 42000));
  var orbs = [];
  for (var i = 0; i < N; i++) {
    orbs.push({
      x: Math.random() * W, y: Math.random() * H,
      r: 40 + Math.random() * 120,
      vx: (Math.random() - 0.5) * 0.18, vy: (Math.random() - 0.5) * 0.14,
      col: COL[i % COL.length],
      ph: Math.random() * Math.PI * 2, ps: 0.004 + Math.random() * 0.006
    });
  }

  // 鼠标涟漪辉光
  var mouse = { x: -1e4, y: -1e4, a: 0 };
  window.addEventListener('pointermove', function (e) { mouse.x = e.clientX; mouse.y = e.clientY; mouse.a = 1; });

  function orb(x, y, r, col, alpha) {
    var g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, tint(col, alpha));
    g.addColorStop(1, tint(col, 0));
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
  }
  // 给 oklch/hex 色套透明度: 用 color-mix 兜底不可控, 改用 canvas globalAlpha 逐斑
  function tint(col, a) { return col; } // 颜色本体, alpha 走 globalAlpha

  function frame() {
    ctx.clearRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'lighter'; // 叠加发光
    for (var i = 0; i < orbs.length; i++) {
      var o = orbs[i];
      o.x += o.vx; o.y += o.vy; o.ph += o.ps;
      if (o.x < -o.r) o.x = W + o.r; if (o.x > W + o.r) o.x = -o.r;
      if (o.y < -o.r) o.y = H + o.r; if (o.y > H + o.r) o.y = -o.r;
      var breathe = 0.5 + 0.5 * Math.sin(o.ph);
      ctx.globalAlpha = 0.05 + 0.07 * breathe;
      orb(o.x, o.y, o.r * (0.85 + 0.25 * breathe), o.col, 1);
    }
    // 鼠标处一团随动辉光
    if (mouse.a > 0.01) {
      ctx.globalAlpha = 0.12 * mouse.a;
      orb(mouse.x, mouse.y, 160, COL[0], 1);
      mouse.a *= 0.94;
    }
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = 'source-over';
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
