// SKEIN 看板前端渲染器: 消费 window.__SKEIN__ (Python _board_data() 出的结构化数据),
// 建 .layout innerHTML (总览 + 卡片 + SVG DAG)。业务数字/节点/边 Python 已算好, 此处只做呈现。
// 忠实移植原 _board_html 的 esc/mdInline/badge/fmtDur/bar/dagHtml(Sugiyama)/概览/prd/卡片。
// 暴露 window.renderBoard(data); 不在 load 时自动渲染 (switcher.js 用内联数据驱动首屏)。
(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function mdInline(s) {
    // 行内 md → HTML: 先 esc 防注入, 再套 代码/粗/斜/链接 (与 Python md_inline 逐条对齐)
    s = esc(s);
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    s = s.replace(/\*\*([^*]+?)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/(?<![*\w])[*_]([^*_]+?)[*_](?![*\w])/g, "<em>$1</em>");
    s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (m, txt, url) {
      if (/^(?:https?:|\/|\.|#)/.test(url) && url.indexOf('"') < 0 && url.indexOf(" ") < 0) {
        return '<a href="' + url + '" target="_blank" rel="noopener">' + txt + "</a>";
      }
      return m;
    });
    return s;
  }

  function badge(text, clsmap) {
    return '<span class="badge ' + (clsmap[text] || "") + '">' + esc(text) + "</span>";
  }

  function fmtDur(mins) {
    if (mins == null) return "-";
    return mins < 60 ? mins + "m"
      : Math.floor(mins / 60) + "h" + String(mins % 60).padStart(2, "0") + "m";
  }

  function bar(pct, sub, cls) {
    // width + label 均封顶 100%; prog 条带 --p 供 CSS 在 palette 内插值上色
    var p = Math.min(pct, 100);
    var kind = cls || "prog";
    // 仅 100% (已完成) 打 done → CSS 只给完成条流光; 未完成条静止
    var c = "bar " + kind + (sub ? " sub" : "") + (p >= 100 ? " done" : "");
    var style = "width:" + p + "%" + (kind === "prog" ? ";--p:" + p : "");
    return '<div class="' + c + '"><div class="fill" style="' + style
      + '"></div><span class="pct">' + p + "%</span></div>";
  }

  // ── DAG (SVG 有向连接图, Sugiyama 重心分层) ── 像素常量与 Python dag_html 逐字节对齐
  function dagHtml(nodes, tips, links, forceVertical) {
    // nodes: [[id, name, status, deps(id 数组), pct, desc]]; tips: {id: htmlString}; links: {id: href}
    if (!nodes || nodes.length < 2) return "";
    var NODE_VAR = dagHtml._nodeVar, NODE_CLS = dagHtml._nodeCls;
    var ids = nodes.map(function (n) { return n[0]; });
    var idset = {}; ids.forEach(function (i) { idset[i] = true; });
    var dep = {}, smap = {}, order = {};
    nodes.forEach(function (n, k) {
      dep[n[0]] = (n[3] || []).filter(function (d) { return idset[d]; });
      smap[n[0]] = n;
      order[n[0]] = k;
    });
    // 分层: layer = 最长依赖深度 (列 = 执行波次)
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
    // 完成子图下沉: 整条链/孤点全 已完成 的弱连通分量, 深度整体下移到活跃节点之下 (读区留给活跃工作)
    (function () {
      var root = {}; ids.forEach(function (i) { root[i] = i; });
      function find(x) { while (root[x] !== x) { root[x] = root[root[x]]; x = root[x]; } return x; }
      ids.forEach(function (i) { dep[i].forEach(function (p) { root[find(i)] = find(p); }); });
      var compDone = {};  // 分量根 → 是否全 done
      ids.forEach(function (i) {
        var r = find(i), d = smap[i][2] === "已完成";
        compDone[r] = (r in compDone) ? (compDone[r] && d) : d;
      });
      var liveMax = -1;
      ids.forEach(function (i) { if (!compDone[find(i)] && layer[i] > liveMax) liveMax = layer[i]; });
      if (liveMax >= 0) {  // 有活跃分量才下沉; 全 done 时不动
        var shift = liveMax + 1;
        ids.forEach(function (i) { if (compDone[find(i)]) layer[i] += shift; });
      }
    })();
    var layers = {};
    Object.keys(layer).forEach(function (i) {
      var d = layer[i]; (layers[d] = layers[d] || []).push(i);
    });
    var sortedDepths = Object.keys(layers).map(Number).sort(function (a, b) { return a - b; });
    sortedDepths.forEach(function (d) {
      layers[d].sort(function (a, b) { return order[a] - order[b]; });
    });

    // 估文本像素宽 (CJK 全宽 1em, 其余约 0.6em)
    function txtw(s, fs) {
      s = String(s == null ? "" : s);
      var w = 0;
      for (var k = 0; k < s.length; k++) w += (s.charCodeAt(k) > 0x2E80 ? fs : fs * 0.6);
      return w;
    }
    function wrap(s, fs, maxpx) {  // 贪心断行 (CJK 逐字断; 拉丁尽量空格断)
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

    // 交叉削减 (Sugiyama 重心法): 上行看子、下行看父, 往返 4 轮
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
      sortedDepths.slice(1).forEach(function (d) {          // 下行: 按父重心排
        layers[d].sort(function (a, b) { return bary(a, dep) - bary(b, dep); });
        layers[d].forEach(function (i, k) { colOf[i] = k; });
      });
      sortedDepths.slice().reverse().slice(0, -1).forEach(function (d) {  // 上行: 按子重心排
        layers[d].sort(function (a, b) { return bary(a, kids) - bary(b, kids); });
        layers[d].forEach(function (i, k) { colOf[i] = k; });
      });
    }

    // 朝向: 默认左右向; 宽 > 1180 或 force → 纵向 (上往下)
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

  // 概览 task 节点悬浮浮层: 总进度条 + subtask DAG (>=2 画图, 否则列表兜底)
  function buildTip(tip) {
    var subDag = tip.subNodes ? dagHtml(tip.subNodes, null, null, false) : "";
    if (!subDag) {
      subDag = tip.subs
        ? '<p class="meta">' + tip.subs.map(function (s) { return esc(s.name) + " " + s.pct + "%"; }).join(" · ") + "</p>"
        : '<p class="empty">无 subtask</p>';
    }
    return '<p class="meta">' + esc(tip.name) + " · 总进度</p>" + bar(tip.pct, true, "") + subDag;
  }

  function prdBlock(prd) {
    if (!prd || !prd.length) return "";
    var parts = prd.map(function (sec) {
      var b = sec.badge ? '<span class="prd-p">' + sec.badge[0] + "/" + sec.badge[1] + "</span>" : "";
      var lis = sec.items.map(function (it) {
        var cls = it.kind === "check" ? (it.done ? "done" : "") : it.proseCls;
        return '<li class="' + cls + '">' + mdInline(it.text) + "</li>";
      }).join("");
      return '<div class="prd-sec"><div class="prd-h">' + esc(sec.name) + b + '</div><ul class="prd-list">' + lis + "</ul></div>";
    }).join("");
    return '<div class="prd">' + parts + "</div>";
  }

  function docRow(links) {
    if (!links || !links.length) return "";
    var dl = links.map(function (l) {
      return '<button type="button" class="doc-link" data-doc="' + esc(l.doc) + '" data-title="' + esc(l.title) + '">' + esc(l.label) + "</button>";
    }).join("");
    return '<p class="doc-links">' + dl + "</p>";
  }

  function subtable(rows, ssCls) {
    if (!rows || !rows.length) return '<p class="empty">无 subtask</p>';
    var srows = rows.map(function (s) {
      return "<tr><td>" + esc(s.sid) + "</td><td>" + esc(s.name) + "</td>"
        + "<td>" + badge(s.status, ssCls) + "</td>"
        + "<td>" + bar(s.pct, true, "") + "</td>"
        + "<td>" + esc(fmtDur(s.est == null ? null : s.est)) + "</td>"
        + "<td>" + esc(s.agent) + "</td>"
        + "<td>" + esc((s.skills || []).join(",") || "-") + "</td>"
        + "<td>" + esc((s.depNames || []).join(", ") || "-") + "</td>"
        + "<td>" + esc((s.acc || []).join("; ") || "-") + "</td></tr>";
    }).join("");
    return "<table><thead><tr><th>sid</th><th>名称</th><th>状态</th><th>进度</th>"
      + "<th>预期</th><th>agent</th><th>skills</th><th>依赖</th><th>验收标准</th></tr></thead>"
      + "<tbody>" + srows + "</tbody></table>";
  }

  function renderBoard(data) {
    dagHtml._nodeVar = data.nodeVar;
    dagHtml._nodeCls = data.nodeCls;
    var ov = data.overview;
    // filterOpts 顺序: [all, active, check, pending, done] → 拿状态字面值给 statcard
    var fo = data.filterOpts;
    var S_ACTIVE = fo[1][0], S_CHECK = fo[2][0], S_PENDING = fo[3][0], S_DONE = fo[4][0];
    // stat 卡 = 可点击多选筛选器: 总计(清空) + 4 状态; 点击激活状态过滤 (switcher.js 绑定)
    function statcard(label, key, filter, cls) {
      return '<button type="button" class="stat' + (cls ? " " + cls : "") + '" data-filter="' + esc(filter) + '">'
        + '<span class="stat-n">' + (key === "__total__" ? ov.taskCount : (ov.stats[key] || 0))
        + '</span><span class="stat-l">' + esc(label) + "</span></button>";
    }
    var stats = '<div class="stats" id="sw-filter">'
      + statcard("总计", "__total__", "", "stat-all")
      + statcard("已完成", S_DONE, S_DONE) + statcard("进行中", S_ACTIVE, S_ACTIVE)
      + statcard("检查中", S_CHECK, S_CHECK) + statcard("待处理", S_PENDING, S_PENDING) + "</div>";
    var sw = '<div class="dag-switch" role="group">'
      + '<button type="button" data-dag="task" class="on">task 维度</button>'
      + '<button type="button" data-dag="full"' + (ov.hasSub ? "" : " disabled") + ">subtask 维度</button></div>";

    // task 维度 DAG: 结构化 tips → html 串
    var td = ov.taskDag;
    var tipMap = {};
    Object.keys(td.tips || {}).forEach(function (id) { tipMap[id] = buildTip(td.tips[id]); });
    var taskView = '<div class="dag-view" data-dag="task">' + dagHtml(td.nodes, tipMap, td.links, true) + "</div>";
    var fullView = ov.fullDag
      ? '<div class="dag-view" data-dag="full" hidden>' + dagHtml(ov.fullDag.nodes, null, null, true) + "</div>"
      : "";

    // 待执行 subtask 队列 (全部未完成 task, 同实际调度序: task 序 → 就绪优先 + 关键路径权重降序)
    var queue = "";
    var pq = ov.pendingQueue || [];
    if (pq.length) {
      var qrows = pq.map(function (q, k) {
        var chip = q.ready
          ? '<span class="q-chip q-ready">就绪</span>'
          : '<span class="q-chip q-block">排队中</span>';
        return '<li class="q-item">'
          + '<span class="q-ord">' + (k + 1) + "</span>" + chip
          + '<span class="q-name">' + esc(q.tid) + "/" + esc(q.sid) + " · " + esc(q.name) + "</span>"
          + '<span class="q-agent">' + esc(q.agent) + "</span></li>";
      }).join("");
      queue = '<div class="queue"><p class="meta">待执行队列 · 调度序 · ' + pq.length + "</p>"
        + '<ol class="q-list">' + qrows + "</ol></div>";
    }

    var overview = '<section class="card"><h2>任务进展</h2>' + sw + stats
      + '<p class="meta">' + ov.taskCount + " task · " + esc(ov.estMeta) + "</p>"
      + '<p class="meta">当前进度</p>' + bar(ov.combinedPct, false, "")
      + queue + taskView + fullView + "</section>";

    var cards = data.cards.map(function (c) {
      var h2 = "<h2>" + esc(c.id) + " " + badge(c.status, data.stClsMap)
        + (c.nextUp ? "<span class=next-up-chip>▶ 下一个</span>" : "") + "</h2>";
      var meta1 = '<p class="meta">前置: ' + esc((c.depNames || []).join(", ") || "-") + " · "
        + (c.worktree ? "worktree: " + esc(c.worktree) + " · " : "")
        + "耗时 " + fmtDur(c.elapsed) + " / 预期 " + fmtDur(c.est == null ? null : c.est) + "</p>";
      return '<section class="card' + (c.nextUp ? " next-up" : "") + '" id="task-' + esc(c.id)
        + '" data-status="' + esc(c.status) + '" data-search="' + esc(c.search) + '">'
        + h2
        + '<p class="name">' + esc(c.name) + "</p>"
        + docRow(c.docLinks)
        + prdBlock(c.prd)
        + meta1
        + '<p class="meta">子任务 ' + c.sdone + "/" + c.stotal + "</p>" + bar(c.spct, true, "")
        + '<details class="detail" open><summary>明细 · DAG + 子任务表</summary>'
        + dagHtml(c.subNodes, null, null, (c.subNodes || []).length > 4)
        + subtable(c.subtable, data.ssClsMap) + "</details></section>";
    }).join("");
    var main = data.cards.length ? cards : '<p class="empty">无 task</p>';

    // 软刷新保滚动位: 换 innerHTML 前记左栏 DAG 各视图滚动位 + 窗口滚动, 渲染后复原
    // (同一 renderBoard 调用内读旧 DOM→写新 DOM; 整页 reload 时 DOM 全新, 无旧值→自然回置顶)
    // 选择器必须用 dag-view 直接子 .dag-wrap: 节点 hover tip 内嵌 mini-DAG 也是 .dag-wrap,
    // 后代选择器会连带命中它们并按 data-dag 覆盖, 把真滚动容器的位置冲成 0。
    var savedScroll = {}, savedWin = window.pageYOffset;
    document.querySelectorAll(".col-side .dag-view > .dag-wrap").forEach(function (w) {
      var v = w.closest(".dag-view");
      if (v) savedScroll[v.getAttribute("data-dag")] = { t: w.scrollTop, l: w.scrollLeft };
    });

    var layout = document.querySelector(".layout");
    if (layout) layout.innerHTML = '<aside class="col-side">' + overview + '</aside><main class="col-main">' + main + "</main>";
    if (window.__skeinBindContent) window.__skeinBindContent();  // 恢复可见 dag-view (task/subtask 维度)

    document.querySelectorAll(".col-side .dag-view > .dag-wrap").forEach(function (w) {
      var v = w.closest(".dag-view"), s = v && savedScroll[v.getAttribute("data-dag")];
      if (s) { w.scrollTop = s.t; w.scrollLeft = s.l; return; }
      // 首屏无存位: 居中到进行中节点 (.n-active 优先, 退 .n-check)。SVG 被缩放,
      // 像素坐标不 1:1, 用 getBoundingClientRect 算实际偏移。
      var node = w.querySelector(".n-active") || w.querySelector(".n-check");
      if (!node) return;
      var nr = node.getBoundingClientRect(), wr = w.getBoundingClientRect();
      w.scrollTop += (nr.top - wr.top) - (w.clientHeight - nr.height) / 2;
      w.scrollLeft += (nr.left - wr.left) - (w.clientWidth - nr.width) / 2;
    });
    window.scrollTo({ top: savedWin, behavior: "instant" });
  }

  window.renderBoard = renderBoard;
})();
