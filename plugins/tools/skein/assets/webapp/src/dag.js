// SKEIN webapp DAG 渲染共享模块: 从 pages/board.js 抽出的 dagHtml (Sugiyama 分层 + SVG 有向连接图)。
// ponytail: 逐字节移植自 board.js, 不改算法/像素常量。esc() 与 NODE_VAR/NODE_CLS 随 dagHtml 一起
//           搬到本模块 (board.js 内 esc 另有 30+ 处使用, 保留其独立副本不动)。

let NODE_VAR = {}, NODE_CLS = {};

// 由 board.js 在每次渲染前注入状态染色映射 (task 状态 -> CSS 变量 / class)。
export function setNodeMaps(varMap, clsMap) {
  NODE_VAR = varMap || {};
  NODE_CLS = clsMap || {};
}

function esc(s) {
  return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ── DAG (SVG 有向连接图, Sugiyama 重心分层) ── 像素常量与 board-render 逐字节对齐
export function dagHtml(nodes, tips, links, forceVertical) {
  if (!nodes || nodes.length < 2) return "";
  var ids = nodes.map(function (n) { return n[0]; });
  var idset = {}; ids.forEach(function (i) { idset[i] = true; });
  var dep = {}, smap = {}, order = {};
  nodes.forEach(function (n, k) {
    dep[n[0]] = (n[3] || []).filter(function (d) { return idset[d]; });
    smap[n[0]] = n;
    order[n[0]] = k;
  });
  var layer = {};
  function depth(i, seen) {
    if (i in layer) return layer[i];
    if (seen[i]) return 0;
    var seen2 = {}; for (var s in seen) seen2[s] = true; seen2[i] = true;
    var mx = -1, ns = dep[i];
    for (var k = 0; k < ns.length; k++) { var dd = depth(ns[k], seen2); if (dd > mx) mx = dd; }
    var d = 1 + mx; layer[i] = d; return d;
  }
  ids.forEach(function (i) { depth(i, {}); });
  (function () {
    var root = {}; ids.forEach(function (i) { root[i] = i; });
    function find(x) { while (root[x] !== x) { root[x] = root[root[x]]; x = root[x]; } return x; }
    ids.forEach(function (i) { dep[i].forEach(function (p) { root[find(i)] = find(p); }); });
    var compDone = {};
    ids.forEach(function (i) {
      var r = find(i), d = smap[i][2] === "已完成";
      compDone[r] = (r in compDone) ? (compDone[r] && d) : d;
    });
    var liveMax = -1;
    ids.forEach(function (i) { if (!compDone[find(i)] && layer[i] > liveMax) liveMax = layer[i]; });
    if (liveMax >= 0) {
      var shift = liveMax + 1;
      ids.forEach(function (i) { if (compDone[find(i)]) layer[i] += shift; });
    }
  })();
  var layers = {};
  Object.keys(layer).forEach(function (i) { var d = layer[i]; (layers[d] = layers[d] || []).push(i); });
  var sortedDepths = Object.keys(layers).map(Number).sort(function (a, b) { return a - b; });
  sortedDepths.forEach(function (d) { layers[d].sort(function (a, b) { return order[a] - order[b]; }); });

  function txtw(s, fs) {
    s = String(s == null ? "" : s);
    var w = 0;
    for (var k = 0; k < s.length; k++) w += (s.charCodeAt(k) > 0x2E80 ? fs : fs * 0.6);
    return w;
  }
  function wrap(s, fs, maxpx) {
    s = String(s == null ? "" : s);
    if (!s) return [];
    var out = [], cur = "";
    for (var k = 0; k < s.length; k++) {
      var ch = s[k];
      if (cur && txtw(cur + ch, fs) > maxpx) {
        var cut = cur.lastIndexOf(" ");
        if (cut > 0 && ch.charCodeAt(0) < 0x2E80) { out.push(cur.slice(0, cut)); cur = cur.slice(cut + 1) + ch; }
        else { out.push(cur); cur = ch; }
      } else cur += ch;
    }
    if (cur) out.push(cur);
    return out;
  }
  var PAD = 14, CAP = 272, need = 208.0;
  nodes.forEach(function (n) {
    var pct = n.length > 4 ? n[4] : null;
    var idrow = txtw(n[0], 13) + (pct != null ? txtw(pct + "%", 11) + 14 : 0);
    need = Math.max(need, idrow + PAD * 2);
  });
  var NW = Math.min(Math.trunc(need + 0.999), CAP);
  var inner = NW - PAD * 2 - 4;
  var wrapped = {};
  nodes.forEach(function (n) {
    var dsc = (n.length > 5 && n[5]) ? n[5] : "";
    var nm = wrap(n[1], 12, inner); if (!nm.length) nm = [""];
    wrapped[n[0]] = [nm, wrap(dsc, 10, inner)];
  });
  var nmMax = 0, dsMax = 0;
  ids.forEach(function (i) {
    nmMax = Math.max(nmMax, wrapped[i][0].length);
    dsMax = Math.max(dsMax, wrapped[i][1].length);
  });
  var NH = 30 + nmMax * 16 + (dsMax ? 6 + dsMax * 14 : 0) + 10;
  var COL = NW + 34, ROW = NH + 20;
  var nlayer = sortedDepths[sortedDepths.length - 1] + 1;
  var span = 0; sortedDepths.forEach(function (d) { span = Math.max(span, layers[d].length); });

  var kids = {}; ids.forEach(function (i) { kids[i] = []; });
  ids.forEach(function (i) { dep[i].forEach(function (p) { kids[p].push(i); }); });
  var colOf = {};
  sortedDepths.forEach(function (d) { layers[d].forEach(function (i, k) { colOf[i] = k; }); });
  function bary(i, nb) {
    var ns = nb[i];
    if (ns && ns.length) { var s = 0; ns.forEach(function (n) { s += colOf[n]; }); return s / ns.length; }
    return colOf[i];
  }
  for (var it = 0; it < 4; it++) {
    sortedDepths.slice(1).forEach(function (d) {
      layers[d].sort(function (a, b) { return bary(a, dep) - bary(b, dep); });
      layers[d].forEach(function (i, k) { colOf[i] = k; });
    });
    sortedDepths.slice().reverse().slice(0, -1).forEach(function (d) {
      layers[d].sort(function (a, b) { return bary(a, kids) - bary(b, kids); });
      layers[d].forEach(function (i, k) { colOf[i] = k; });
    });
  }

  var vertical = forceVertical || nlayer * COL + 10 > 1180;
  var pos = {}, W, H;
  if (vertical) {
    var PER = 4, maxcols = Math.min(span, PER), roff = 0;
    sortedDepths.forEach(function (d) {
      var idsD = layers[d];
      var nrow = Math.floor((idsD.length + PER - 1) / PER);
      for (var sub = 0; sub < nrow; sub++) {
        var chunk = idsD.slice(sub * PER, (sub + 1) * PER);
        var off = Math.floor((maxcols - chunk.length) * COL / 2);
        for (var col = 0; col < chunk.length; col++) {
          pos[chunk[col]] = [off + col * COL + 10, (roff + sub) * ROW + 10];
        }
      }
      roff += nrow;
    });
    W = maxcols * COL + 10; H = roff * ROW + 10;
  } else {
    sortedDepths.forEach(function (d) {
      var idsD = layers[d];
      var off = Math.floor((span - idsD.length) * ROW / 2);
      idsD.forEach(function (i, r) { pos[i] = [d * COL + 10, off + r * ROW + 10]; });
    });
    W = nlayer * COL + 10; H = span * ROW + 10;
  }

  var lines = [];
  ids.forEach(function (i) {
    var p2 = pos[i], x2 = p2[0], y2 = p2[1];
    dep[i].forEach(function (p) {
      var p1 = pos[p], x1 = p1[0], y1 = p1[1];
      if (vertical) {
        var sx = x1 + NW / 2, sy = y1 + NH, ex = x2 + NW / 2, ey = y2, my = (sy + ey) / 2;
        lines.push(
          '<path d="M' + sx + "," + sy + " C" + sx + "," + my + " " + ex + "," + my + " " + ex + "," + (ey - 2)
          + '" fill="none" stroke="var(--muted)" stroke-width="1.5"/>'
          + '<polygon points="' + (ex - 4) + "," + (ey - 8) + " " + ex + "," + ey + " " + (ex + 4) + "," + (ey - 8)
          + '" fill="var(--muted)"/>');
      } else {
        var ey2 = y2 + NH / 2, sx2 = x1 + NW, sy2 = y1 + NH / 2, mx = (sx2 + x2) / 2;
        lines.push(
          '<path d="M' + sx2 + "," + sy2 + " C" + mx + "," + sy2 + " " + mx + "," + ey2 + " " + (x2 - 2) + "," + ey2
          + '" fill="none" stroke="var(--muted)" stroke-width="1.5"/>'
          + '<polygon points="' + (x2 - 8) + "," + (ey2 - 4) + " " + x2 + "," + ey2 + " " + (x2 - 8) + "," + (ey2 + 4)
          + '" fill="var(--muted)"/>');
      }
    });
  });

  var boxes = [];
  ids.forEach(function (i) {
    var p = pos[i], x = p[0], y = p[1], node = smap[i];
    var _id = node[0], stt = node[2], pct = node.length > 4 ? node[4] : null;
    var nmLines = wrapped[_id][0], dsLines = wrapped[_id][1];
    var pctTxt = pct != null
      ? '<text x="' + (x + NW - 12) + '" y="' + (y + 22) + '" font-size="11" text-anchor="end" fill="var(--head)">' + pct + "%</text>"
      : "";
    var nmTxt = nmLines.map(function (ln, k) {
      return '<text x="' + (x + 14) + '" y="' + (y + 44 + k * 16) + '" font-size="12" fill="var(--fg)">' + esc(ln) + "</text>";
    }).join("");
    var dsTop = 44 + nmMax * 16;
    var descTxt = dsLines.map(function (ln, k) {
      return '<text x="' + (x + 14) + '" y="' + (y + dsTop + k * 14) + '" font-size="10" fill="var(--muted)">' + esc(ln) + "</text>";
    }).join("");
    var hasTip = !!(tips && (i in tips));
    var hasLink = !!(links && (i in links));
    var blob = esc([_id, node[1], node.length > 5 ? node[5] : ""].map(function (x) { return String(x || ""); }).join(" ").toLowerCase());
    var gAttr = (hasTip ? ' data-tip="' + esc(i) + '"' : "") + ' data-status="' + esc(stt) + '" data-search="' + blob + '"';
    var gCls = ((NODE_CLS[stt] || "") + (hasTip ? " has-tip" : "") + (hasLink ? " has-link" : "")).trim();
    var g =
      '<g class="' + gCls + '"' + gAttr + '><rect x="' + x + '" y="' + y + '" width="' + NW + '" height="' + NH
      + '" rx="6" fill="var(--bg)" stroke="var(--brd)"/>'
      + '<rect x="' + x + '" y="' + y + '" width="4" height="' + NH + '" rx="2" fill="var(' + (NODE_VAR[stt] || "--muted") + ')"/>'
      + '<text x="' + (x + 14) + '" y="' + (y + 22) + '" font-size="13" fill="var(--fg)">' + esc(_id) + "</text>"
      + pctTxt + nmTxt + descTxt + "</g>";
    if (hasLink) g = '<a href="' + esc(links[i]) + '">' + g + "</a>";
    boxes.push(g);
  });

  var svg = '<svg class="dag" viewBox="0 0 ' + W + " " + H + '" width="' + W + '" height="' + H
    + '" xmlns="http://www.w3.org/2000/svg">' + lines.join("") + boxes.join("") + "</svg>";
  var tipHtml = tips
    ? ids.filter(function (i) { return i in tips; })
      .map(function (i) { return '<div class="dag-tip" data-for="' + esc(i) + '">' + tips[i] + "</div>"; }).join("")
    : "";
  return '<div class="dag-wrap">' + svg + tipHtml + "</div>";
}
