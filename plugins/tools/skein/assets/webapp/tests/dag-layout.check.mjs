// DAG 布局自检: node plugins/tools/skein/assets/webapp/tests/dag-layout.check.mjs
// board.js 是浏览器 ESM (依赖 htm/DOM), 不能整体 import — 只把纯函数 sugiyama 抠出来跑
import { readFileSync } from 'fs';
const src = readFileSync(new URL('../src/new/pages/board.js', import.meta.url), 'utf8');
const start = src.indexOf('function sugiyama(');
const end = src.indexOf('\n}\n', start) + 2;
const sugiyama = eval('(' + src.slice(start, end) + ')');

const S = { colW: 300, rowH: 200, padX: 40, padY: 30, gapX: 30, gapY: 20 };
const run = (g, view) => sugiyama(Object.keys(g), id => g[id], { ...S, maxWidth: view.w, viewH: view.h });

// 1. 下沉紧缩: 无依赖的 src 应贴到消费者前一层, 而非留在 rank 0
{
  const g = { a: [], b: ['a'], c: ['b'], src: [], sink: ['c', 'src'] };
  const r = run(g, { w: 1200, h: 700 });
  const rk = {}; r.layers.forEach((l, i) => l.forEach(n => { if (!n.dummy) rk[n.id] = i; }));
  console.assert(rk.src === rk.sink - 1, 'src 应下沉到 sink 前一层, 实际 ' + JSON.stringify(rk));
  // 所有边 rank 严格递增
  for (const [id, deps] of Object.entries(g)) for (const d of deps)
    console.assert(rk[d] < rk[id], `边 ${d}->${id} rank 未递增`);
  console.log('1 下沉 OK', JSON.stringify(rk));
}

// 2. 宽度硬约束: 长链 (层数远超可用列数) 必须折成蛇形带, 画布永不超宽
{
  const g = { n0: [] };
  for (let i = 1; i < 40; i++) g['n' + i] = ['n' + (i - 1)];
  for (const vw of [700, 1200, 1888, 2400]) {
    const r = run(g, { w: vw, h: 800 });
    console.assert(r.width <= vw, `画布超宽: ${r.width} > ${vw}`);
    const bands = new Set(r.layers.flat().map(n => n.band)).size;
    console.assert(bands > 1, `40 层在 ${vw}px 内应折成多带, 实际 ${bands}`);
  }
  const r = run(g, { w: 1888, h: 800 });
  console.log('2 宽度硬约束 OK w=' + r.width + ' bands=' + (new Set(r.layers.flat().map(n => n.band)).size));
}

// 2b. 视口变窄 -> 画布跟着变窄 (宽度自适应)
{
  const g = { n0: [] };
  for (let i = 1; i < 40; i++) g['n' + i] = ['n' + (i - 1)];
  const wideView = run(g, { w: 2000, h: 700 });
  const narrowView = run(g, { w: 700, h: 900 });
  console.assert(narrowView.width < wideView.width, `窄视口应更窄: ${narrowView.width} vs ${wideView.width}`);
  console.assert(narrowView.height > wideView.height, '窄视口应更高 (往下续排)');
  console.log('2b 自适应 OK 宽视口=' + wideView.width + ' 窄视口=' + narrowView.width);
}

// 3. 小图装得下就不折带
{
  const g = { a: [], b: ['a'], c: ['a'], d: ['b', 'c'] };
  const r = run(g, { w: 1200, h: 700 });
  console.assert(new Set(r.layers.flat().map(n => n.band)).size === 1, '小图不该折带');
  console.assert(r.width <= 1200, '小图不该超宽');
  console.log('3 小图 OK ' + r.width + 'x' + r.height);
}

// 4. 无坐标重叠 + 长边有拐点
{
  const g = { a: [], b: ['a'], c: ['b'], far: ['a'] };  // far 会被下沉, 造不出长边; 用 sink 强制
  g.sink = ['a', 'c'];
  const r = run(g, { w: 1200, h: 700 });
  const seen = new Set();
  for (const l of r.layers) for (const n of l) {
    const k = n.x + ',' + n.y;
    console.assert(!seen.has(k), '坐标重叠 ' + n.id + ' @ ' + k);
    seen.add(k);
  }
  const longEdge = r.edges.find(e => e.from.id === 'a' && e.to.id === 'sink');
  console.assert(longEdge && longEdge.chain.length > 0, '跨层边应有虚点拐点');
  console.log('4 无重叠 + 长边拐点 OK chain=' + longEdge.chain.length);
}

// 4b. 宽 fan-out 在带内折行, 不堆成柱子
{
  const g = { root: [] };
  for (let i = 0; i < 30; i++) g['k' + i] = ['root'];
  const r = run(g, { w: 1400, h: 800 });
  const cols = new Set(r.layers[1].map(n => n.x)).size;
  console.assert(cols > 1, '宽层应折行, 实际列数 ' + cols);
  console.assert(r.width <= 1400, '折行后仍不许超宽, 实际 ' + r.width);
  console.assert(r.height < 30 * S.rowH, '折行后高度应收敛, 实际 ' + r.height);
  console.log('4b 层内折行 OK cols=' + cols + ' size=' + Math.round(r.width) + 'x' + Math.round(r.height));
}

// 5. 环兜底不死循环
{
  const r = run({ a: ['b'], b: ['a'], c: ['a'] }, { w: 1200, h: 700 });
  console.log('5 环兜底 OK layers=' + r.layers.length);
}

// 6. 千节点性能
{
  const g = { r0: [] };
  for (let i = 1; i < 1000; i++) g['n' + i] = i > 3 ? ['n' + (i - 3)] : ['r0'];
  const t = process.hrtime.bigint();
  const r = run(g, { w: 1600, h: 900 });
  const ms = Number(process.hrtime.bigint() - t) / 1e6;
  console.log('6 千节点 OK ' + Math.round(ms) + 'ms size=' + Math.round(r.width) + 'x' + Math.round(r.height));
  console.assert(ms < 5000, '千节点应在 5s 内, 实际 ' + ms);
  console.assert(r.width <= 1600, '千节点也不许超宽, 实际 ' + r.width);
}
