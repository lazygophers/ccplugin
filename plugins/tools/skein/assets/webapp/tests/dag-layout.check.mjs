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
const { sugiyama, layoutPacked, layoutGrid, edgeKinds, focusActive } = eval(
  `(() => { ${['sugiyama', 'packLayout', 'components', 'transpose', 'layoutComponent', 'layoutPacked', 'layoutGrid', 'edgeKinds', 'focusActive'].map(cut).join('\n')}
   return { sugiyama, layoutPacked, layoutGrid, edgeKinds, focusActive }; })()`);

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

// 10. 边语义色: 绿=依赖已完成 / 黄=阻塞但上游可执行 / 红=阻塞且上游被卡
{
  const T = {
    a: { status: 'done', deps: [] },          // a 完成 → a->b 绿
    b: { status: 'ready', deps: ['a'] },      // b 未完成但依赖全 done → b->c 黄
    c: { status: 'planning', deps: ['b'] },   // c 未完成且 b 未完成 → c->d 红
    d: { status: 'planning', deps: ['c'] },
  };
  const nd = (id) => ({ id, task: T[id] });
  const mk = (f, t) => ({ from: nd(f), to: nd(t) });
  const edges = [mk('a', 'b'), mk('b', 'c'), mk('c', 'd')];
  const kindOf = edgeKinds(edges);
  const got = edges.map(kindOf).join(',');
  console.assert(got === 'ready,blocked,stuck', '边语义应为 ready,blocked,stuck, 实际 ' + got);
  // 图外 id 视为已满足: 上游依赖被筛掉不该误判成红
  const orphan = [{ from: { id: 'x', task: { status: 'ready', deps: ['gone'] } }, to: nd('d') }];
  console.assert(edgeKinds(orphan)(orphan[0]) === 'blocked', '图外依赖应视为已满足');
  console.log('10 边语义 OK ' + got);
}

// 11. 满铺网格: 主看板布局。⌈N/列数⌉ 行, 不留稀疏层空行, 宽度不超约束, 无重叠
{
  // 稀疏长链 (每层 1 个节点) —— 分层排布最吃亏的形状
  const g = { n0: [] };
  for (let i = 1; i < 30; i++) g['n' + i] = ['n' + (i - 1)];
  const ids = Object.keys(g);
  const grid = layoutGrid(ids, id => g[id], S, 1400, () => ({}));
  const cols = Math.floor((1400 - S.padX * 2) / S.colW);       // = 4
  console.assert(grid.width <= 1400, '满铺不许超宽, 实际 ' + grid.width);
  console.assert(grid.nodes.length === 30, '节点应全画, 实际 ' + grid.nodes.length);
  const rows = new Set(grid.nodes.map(n => n.y)).size;
  console.assert(rows === Math.ceil(30 / cols), `应为 ${Math.ceil(30 / cols)} 行, 实际 ${rows}`);
  // 同形状走分层排布 = 30 行, 满铺应显著更矮
  const packed = layoutPacked(ids, id => g[id], S, 1400, 800, () => ({}));
  console.assert(grid.height < packed.height * 0.6, `满铺应远矮于分层: ${grid.height} vs ${packed.height}`);
  const seen = new Set();
  for (const n of grid.nodes) {
    const k = n.x + ',' + n.y;
    console.assert(!seen.has(k), '坐标重叠 ' + n.id);
    seen.add(k);
  }
  console.assert(grid.edges.length === 29, '边应全保留, 实际 ' + grid.edges.length);
  // 依赖深度递增 → 阅读序 (行主序) 递增, 边才不会大面积往回绕
  const pos = new Map(grid.nodes.map((n, i) => [n.id, i]));
  console.assert(grid.edges.every(e => pos.get(e.from.id) < pos.get(e.to.id)), '被依赖方应排在前面');
  console.log(`11 满铺网格 OK ${cols}列x${rows}行 size=${grid.width}x${grid.height} (分层为 ${Math.round(packed.height)})`);
}

// 12. 满铺网格环兜底: 有环也不死循环
{
  const grid = layoutGrid(['a', 'b', 'c'], id => ({ a: ['b'], b: ['a'], c: ['a'] })[id], S, 1400, () => ({}));
  console.assert(grid.nodes.length === 3, '环图节点应全画');
  console.log('12 满铺环兜底 OK ' + grid.width + 'x' + grid.height);
}

// 13. 进页自动定位: 视口居中到执行中的 task (画布几千 px, 从左上角开始等于没看到东西)
{
  const wrap = { clientWidth: 1000, clientHeight: 800, scrollTo(o) { this.last = o; } };
  const mk = (id, status, x, y) => ({ id, x, y, w: 300, h: 200, task: { status } });
  // active 优先于 check/ready/done
  const nodes = [mk('a', 'done', 0, 0), mk('b', 'check', 0, 400), mk('c', 'active', 600, 3000), mk('d', 'ready', 0, 800)];
  focusActive(wrap, nodes);
  console.assert(wrap.last.top === 3000 + 100 - 400, '应把 active 卡竖直居中, 实际 ' + wrap.last.top);
  console.assert(wrap.last.left === 600 + 150 - 500, '应把 active 卡水平居中, 实际 ' + wrap.last.left);
  // 无 active 时退到 check
  focusActive(wrap, nodes.filter(n => n.task.status !== 'active'));
  console.assert(wrap.last.top === 400 + 100 - 400, 'active 缺席应退到 check, 实际 ' + wrap.last.top);
  // 卡在画布左上角时不许滚出负值
  focusActive(wrap, [mk('a', 'active', 0, 0)]);
  console.assert(wrap.last.left === 0 && wrap.last.top === 0, '不许出现负滚动量');
  // 状态全不在优先级表里 → 退到第一张卡, 不能崩
  focusActive(wrap, [mk('x', 'unknown', 900, 900)]);
  console.assert(wrap.last.top === 900 + 100 - 400, '未知状态应退到第一张卡');
  focusActive(wrap, []);   // 空图不该抛
  console.log('13 自动定位 OK left=' + wrap.last.left + ' top=' + wrap.last.top);
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
