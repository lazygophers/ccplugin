// DAG 布局自检: node plugins/tools/skein/assets/webapp/tests/dag-layout.check.mjs
// board.js 是浏览器 ESM (依赖 htm/DOM), 不能整体 import — 只把纯函数 sugiyama 抠出来跑
import { readFileSync } from 'fs';
const src = readFileSync(new URL('../src/new/pages/board.js', import.meta.url), 'utf8');
const cut = (name) => {
  const a = src.indexOf('function ' + name + '(');
  return src.slice(a, src.indexOf('\n}\n', a) + 2);
};
// 布局链是纯函数, 整串 eval 出来 (layoutPacked 依赖 components/sugiyama/packLayout)。
// eval 的输入是本仓库自己的源码, 非外部输入 — 这里只是绕开 board.js 的浏览器 ESM 依赖。
const { sugiyama, layoutPacked } = eval(
  `(() => { ${['sugiyama', 'packLayout', 'components', 'transpose', 'layoutComponent', 'layoutPacked'].map(cut).join('\n')}
   return { sugiyama, layoutPacked }; })()`);

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

// 7. 分量装箱: 互不相连的小簇各自布局后铺满宽度, 不占独立层位、不产生跨分量长线
{
  const g = {};
  for (let i = 0; i < 30; i++) g['iso' + i] = [];        // 30 个孤立节点
  g.c0 = []; g.c1 = ['c0']; g.c2 = ['c1'];               // 一条 3 节点链
  const packed = layoutPacked(Object.keys(g), id => g[id], S, 1400, 800, () => ({}));
  console.assert(packed.width <= 1400, '装箱后不许超宽, 实际 ' + packed.width);
  const cols = new Set(packed.nodes.map(n => n.x)).size;
  const rows = new Set(packed.nodes.map(n => n.y)).size;
  console.assert(cols >= 4 && rows >= 4, `孤立节点应铺成网格, 实际 ${cols}列 ${rows}行`);
  console.assert(packed.height < 12 * S.rowH, '装箱后高度应收敛, 实际 ' + packed.height);
  // 分量间不该有边; 每条边两端必属同一分量 (这里只有 c0->c1->c2)
  console.assert(packed.edges.length === 2, '边数应为 2, 实际 ' + packed.edges.length);
  console.log(`7 分量装箱 OK ${cols}列x${rows}行 size=${Math.round(packed.width)}x${Math.round(packed.height)}`);
}

// 8. 正交走线数据: 跨带边带 laneY 通道, 长边带拐点
{
  const g = { a: [] };
  for (let i = 1; i < 30; i++) g['n' + i] = ['n' + (i - 1) || 'a'];
  g.n1 = ['a'];
  const packed = layoutPacked(Object.keys(g), id => g[id], S, 900, 700, () => ({}));
  const cross = packed.edges.filter(e => e.cross);
  console.assert(packed.edges.every(e => Array.isArray(e.bends)), '每条边应有 bends 数组');
  console.assert(cross.every(e => e.laneY > 0), '跨带边应有正的 laneY 通道');
  console.log('8 走线数据 OK edges=' + packed.edges.length + ' cross=' + cross.length);
}

// 9. 方向自选: 链状分量竖排 (面积远小于横排折带), 不再一律自左往右
{
  const g = { c0: [] };
  for (let i = 1; i < 24; i++) g['c' + i] = ['c' + (i - 1)];
  const packed = layoutPacked(Object.keys(g), id => g[id], S, 1400, 800, () => ({}));
  console.assert(packed.width <= S.colW * 2 + S.padX * 2, '24 节点链应竖排成窄柱, 实际宽 ' + packed.width);
  const xs = new Set(packed.nodes.map(n => n.x));
  console.assert(xs.size <= 2, '竖排应只占 1~2 列, 实际 ' + xs.size);
  console.log(`9 方向自选 OK ${xs.size}列 size=${Math.round(packed.width)}x${Math.round(packed.height)}`);
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
