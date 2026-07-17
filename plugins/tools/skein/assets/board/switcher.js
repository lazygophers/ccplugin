// SKEIN 看板主题切换器: 读/写 <html> data 属性 + localStorage, 无依赖。
(function(){
  var html=document.documentElement;
  // 实测 topbar 高 (含换行) + body 上内边距 → 写 --topbar, 左卡片据此定 top/height,
  // 保证 card 上下边界都在视口内、随 topbar 高变化自适应、无追赶滑动
  function syncTopbar(){
    var tb=document.querySelector('.topbar');
    if(!tb)return;
    var padTop=parseFloat(getComputedStyle(document.body).paddingTop)||0;
    html.style.setProperty('--topbar',(tb.offsetHeight+padTop)+'px');
  }
  syncTopbar();
  window.addEventListener('resize',syncTopbar);
  // 浮动按钮开合: 点圆钮 toggle 面板, 点面板外收起
  var fabWrap=document.querySelector('.fab-wrap'),fab=document.getElementById('sw-fab');
  if(fabWrap&&fab){
    fab.addEventListener('click',function(e){
      e.stopPropagation();
      var open=fabWrap.classList.toggle('open');
      fab.setAttribute('aria-expanded',open?'true':'false');
    });
    document.addEventListener('click',function(e){
      if(!fabWrap.contains(e.target)){fabWrap.classList.remove('open');fab.setAttribute('aria-expanded','false');}
    });
  }
  // 状态筛选(#sw-filter, 现居任务进展卡) + 搜索(#sw-search, 居 topbar) 统一决定右栏卡显隐:
  // 卡显 iff 状态命中 且 (搜索空 或 data-search 含关键词); 搜索还高亮命中卡关键词 + 左栏 DAG 命中节点高亮/其余变灰
  // 激活的状态过滤集 (空=全部); 取自 .stat.on 卡 (排除总计卡 .stat-all)
  // 状态筛选默认三态 (进行中/检查中/待处理), 仅内存不持久化: 软刷新走同一 JS 模块 → filterSet 存活, 整页刷新回默认
  var filterSet=['进行中','检查中','待处理'];
  function curFilters(){var b=document.getElementById('sw-filter');if(!b)return [];
    return Array.prototype.filter.call(b.querySelectorAll('.stat.on'),function(s){return !s.classList.contains('stat-all');})
      .map(function(s){return s.getAttribute('data-filter');});}
  // 总计卡激活态 = 无任何状态卡激活 (视觉表「全部」)
  function syncTotalState(b){var all=b.querySelector('.stat-all');if(all)all.classList.toggle('on',!b.querySelector('.stat.on:not(.stat-all)'));}
  function curQuery(){var s=document.getElementById('sw-search');return s?s.value.trim().toLowerCase():'';}
  // 卡内高亮: 先拆旧 mark.hl, 再对含关键词文本节点包 <mark class=hl> (跳过 SVG 子树, 免污染卡内 DAG)
  function highlightCard(card,q){
    card.querySelectorAll('mark.hl').forEach(function(m){
      m.parentNode.replaceChild(document.createTextNode(m.textContent),m);});
    card.normalize();
    if(!q)return;
    var walker=document.createTreeWalker(card,NodeFilter.SHOW_TEXT,{acceptNode:function(nd){
      if(!nd.nodeValue||nd.nodeValue.toLowerCase().indexOf(q)<0)return NodeFilter.FILTER_REJECT;
      for(var p=nd.parentNode;p&&p!==card;p=p.parentNode){
        if(p.tagName&&p.tagName.toLowerCase()==='svg')return NodeFilter.FILTER_REJECT;}
      return NodeFilter.FILTER_ACCEPT;}});
    var nodes=[],n; while(n=walker.nextNode())nodes.push(n);
    nodes.forEach(function(node){
      var txt=node.nodeValue,low=txt.toLowerCase(),idx=low.indexOf(q),last=0;
      var frag=document.createDocumentFragment();
      while(idx>=0){
        if(idx>last)frag.appendChild(document.createTextNode(txt.slice(last,idx)));
        var mk=document.createElement('mark');mk.className='hl';mk.textContent=txt.slice(idx,idx+q.length);
        frag.appendChild(mk); last=idx+q.length; idx=low.indexOf(q,last);
      }
      if(last<txt.length)frag.appendChild(document.createTextNode(txt.slice(last)));
      node.parentNode.replaceChild(frag,node);
    });
  }
  function applyCards(){
    var fs=curFilters(),q=curQuery(),all=fs.length===0;
    document.querySelectorAll('section.card[data-status]').forEach(function(c){
      var okS=(all||fs.indexOf(c.getAttribute('data-status'))>=0);
      var okQ=(!q||(c.getAttribute('data-search')||'').indexOf(q)>=0);
      c.style.display=(okS&&okQ)?'':'none';
      highlightCard(c,okQ?q:'');
    });
    // 左栏 DAG: 搜索命中节点高亮 (dag-hit); 状态筛选外 + 搜索未命中节点变灰 (dag-dim)
    document.querySelectorAll('.dag-wrap svg g[data-search]').forEach(function(g){
      var hitQ=!!q&&g.getAttribute('data-search').indexOf(q)>=0;
      var st=g.getAttribute('data-status');
      var dimS=!all&&!!st&&fs.indexOf(st)<0&&!!g.closest('.col-side');
      g.classList.toggle('dag-hit',hitQ);
      g.classList.toggle('dag-dim',(!!q&&!hitQ)||dimS);
    });
  }
  var ssel=document.getElementById('sw-search');
  if(ssel)ssel.addEventListener('input',applyCards);
  // 进度条动画视口门控 observer (单例, 每次软刷新 disconnect + 重新 observe 新卡片 bar)
  var io=('IntersectionObserver' in window)?new IntersectionObserver(function(es){
    es.forEach(function(e){e.target.classList.toggle('voff',!e.isIntersecting);});
  },{rootMargin:'120px'}):null;
  // 内容区 (.layout) 绑定: 首次 + 每次软刷新 swap .layout 后重跑
  // (DAG 切换/悬浮浮层/进度条门控绑在卡片元素上, swap 即失效; doc-link 走 document 委托不用管)
  function bindContent(){
    // stat 卡多选筛选: board-render 每次重渲染新 #sw-filter 节点, 故每次恢复保存态; click 委托一次性绑
    var fbox=document.getElementById('sw-filter');
    if(fbox){
      fbox.querySelectorAll('.stat').forEach(function(s){var f=s.getAttribute('data-filter');
        s.classList.toggle('on',!!f&&filterSet.indexOf(f)>=0);});
      syncTotalState(fbox);
      if(!fbox.__skBound){
        fbox.__skBound=true;
        fbox.addEventListener('click',function(e){
          var b=e.target.closest('.stat'); if(!b||!fbox.contains(b))return;
          if(b.classList.contains('stat-all'))fbox.querySelectorAll('.stat').forEach(function(s){s.classList.remove('on');});
          else b.classList.toggle('on');
          syncTotalState(fbox);
          filterSet=curFilters();  // 内存态, 不落 localStorage
          applyCards();
        });
      }
    }
    applyCards();  // 依 topbar 未 swap 的筛选/搜索态, 重新套用到新卡片
    // DAG 维度切换: 按钮切 task / task+subtask 视图 (localStorage 记忆), 非 tab
    document.querySelectorAll('.dag-switch').forEach(function(sw){
      var card=sw.closest('.card');
      function show(v){
        sw.querySelectorAll('button').forEach(function(b){b.classList.toggle('on',b.getAttribute('data-dag')===v);});
        card.querySelectorAll('.dag-view').forEach(function(vw){vw.hidden=vw.getAttribute('data-dag')!==v;});
        localStorage.setItem('skein-dagview',v);
      }
      sw.querySelectorAll('button').forEach(function(b){
        b.addEventListener('click',function(){if(!b.disabled)show(b.getAttribute('data-dag'));});
      });
      var saved=localStorage.getItem('skein-dagview');
      if(saved&&card.querySelector('.dag-view[data-dag="'+saved+'"]'))show(saved);
    });
    // DAG 节点悬浮浮层: hover 有 data-tip 的节点 → 同 .dag-wrap 内对应 .dag-tip 定位显示
    document.querySelectorAll('.dag-wrap').forEach(function(wrap){
      wrap.querySelectorAll('svg .has-tip[data-tip]').forEach(function(g){
        var tip=wrap.querySelector('.dag-tip[data-for="'+g.getAttribute('data-tip')+'"]');
        if(!tip)return;
        g.addEventListener('mouseenter',function(){
          // tip 是 position:fixed → 用视口坐标定位, 逃逸 .dag-wrap 的 overflow 裁剪
          tip.style.display='block';
          var gb=g.getBoundingClientRect(),tb=tip.getBoundingClientRect();
          var vw=window.innerWidth,vh=window.innerHeight;
          var left=Math.min(gb.left,vw-tb.width-8);
          // 下方放不下则翻到节点上方
          var top=gb.bottom+6+tb.height>vh?gb.top-tb.height-6:gb.bottom+6;
          tip.style.left=Math.max(8,left)+'px';
          tip.style.top=Math.max(8,top)+'px';
        });
        g.addEventListener('mouseleave',function(){tip.style.display='none';});
      });
    });
    // 只门控右栏卡片 bar (百+条才 churn GPU); 左栏总览"整体进度"单条常驻不门控
    if(io){io.disconnect();document.querySelectorAll('.col-main .bar').forEach(function(b){io.observe(b);});}
  }
  // serve 软刷新: 拉 /__skein__/data 新 JSON → renderBoard 前端重渲染 .layout (不取 HTML)
  // — 免闪白 + 保滚动态 (renderBoard 内会调 bindContent 复原筛选/搜索/展开)。file:// 无端点 或 fetch 失败 → reload 兜底。
  function softRefresh(){
    if(location.protocol==='file:'){location.reload();return;}
    fetch('/__skein__/data',{cache:'no-store'}).then(function(r){
      if(!r.ok)throw new Error(r.status);return r.json();
    }).then(function(data){
      if(window.renderBoard){window.renderBoard(data);}else{location.reload();}
    }).catch(function(){location.reload();});
  }
  window.__skeinRefresh=softRefresh;  // 供热重载 WS inline script 调用同一软刷新路径
  window.__skeinBindContent=bindContent;  // board-render 每次渲染 .layout 后调, 重绑卡片交互 (DAG 切换/浮层/门控)
  // 首屏: board-render 已定义 renderBoard → 用内联 window.__SKEIN__ 渲染 (内部调 bindContent); 否则直接 bindContent 兜底
  if(window.renderBoard&&window.__SKEIN__)window.renderBoard(window.__SKEIN__);
  else bindContent();
  // 顶栏/图钉动作: 软刷新数据 (不整页 reload) / 回到顶部
  ['sw-refresh','sw-refresh-top'].forEach(function(id){
    var b=document.getElementById(id);if(b)b.addEventListener('click',softRefresh);
  });
  var tBtn=document.getElementById('sw-top');
  if(tBtn)tBtn.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'});});
})();
