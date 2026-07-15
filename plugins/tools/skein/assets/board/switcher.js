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
  var keys={theme:'data-theme'};  // 唯一外观选项; 配色/明暗烘焙进主题预设 css
  // serve(http): config.yaml 是主题真值源 (服务端已渲染 data-theme), 改动 POST 回落盘; file://: 用 localStorage
  var served=/^https?:$/.test(location.protocol);
  function apply(k,v){
    if(!v)return;
    html.setAttribute(keys[k],v);
    if(!served)localStorage.setItem('skein-'+k,v);  // serve 下不写 localStorage, 免下次覆盖服务端配置
    var sel=document.getElementById('sw-'+k);
    if(sel)sel.value=v;
  }
  Object.keys(keys).forEach(function(k){
    if(!served){var saved=localStorage.getItem('skein-'+k);if(saved)apply(k,saved);}  // serve 下不覆盖服务端主题
    var sel=document.getElementById('sw-'+k);
    if(sel)sel.addEventListener('change',function(){
      apply(k,sel.value);
      if(served&&k==='theme')  // 持久化到 config.yaml
        fetch('/__skein__/config',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({board_theme:sel.value})}).catch(function(){});
    });
  });
  // 状态筛选(#sw-filter, 现居任务进展卡) + 搜索(#sw-search, 居 topbar) 统一决定右栏卡显隐:
  // 卡显 iff 状态命中 且 (搜索空 或 data-search 含关键词); 搜索还高亮命中卡关键词 + 左栏 DAG 命中节点高亮/其余变灰
  function curFilter(){var s=document.getElementById('sw-filter');return s?s.value:'all';}
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
    var f=curFilter(),q=curQuery();
    document.querySelectorAll('section.card[data-status]').forEach(function(c){
      var okS=(f==='all'||c.getAttribute('data-status')===f);
      var okQ=(!q||(c.getAttribute('data-search')||'').indexOf(q)>=0);
      c.style.display=(okS&&okQ)?'':'none';
      highlightCard(c,okQ?q:'');
    });
    // 左栏 DAG: 搜索时命中节点高亮 (dag-hit)、其余变灰 (dag-dim); 状态筛选不动 DAG
    document.querySelectorAll('.dag-wrap svg g[data-search]').forEach(function(g){
      var hit=!!q&&g.getAttribute('data-search').indexOf(q)>=0;
      g.classList.toggle('dag-hit',hit);
      g.classList.toggle('dag-dim',!!q&&!hit);
    });
  }
  var fsel=document.getElementById('sw-filter');
  if(fsel){
    var savedF=localStorage.getItem('skein-filter'); if(savedF)fsel.value=savedF;
    fsel.addEventListener('change',function(){localStorage.setItem('skein-filter',fsel.value);applyCards();});
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
  // serve 软刷新: fetch 后端 live 渲染 (GET 当前页, 同 task 变更自动刷新的接口) → 只 swap .layout, 不整页 reload
  // — 免闪白 + 保滚动/筛选/展开态。file:// 无实时端点 或 fetch 失败 → 退 location.reload 兜底。
  function softRefresh(){
    if(location.protocol==='file:'){location.reload();return;}
    fetch(location.pathname,{cache:'no-store'}).then(function(r){
      if(!r.ok)throw new Error(r.status);return r.text();
    }).then(function(t){
      var fresh=new DOMParser().parseFromString(t,'text/html').querySelector('.layout');
      var cur=document.querySelector('.layout');
      if(fresh&&cur){cur.replaceWith(fresh);bindContent();}else{location.reload();}
    }).catch(function(){location.reload();});
  }
  window.__skeinRefresh=softRefresh;  // 供热重载 WS inline script 调用同一软刷新路径
  bindContent();
  // 顶栏/图钉动作: 软刷新数据 (不整页 reload) / 回到顶部
  ['sw-refresh','sw-refresh-top'].forEach(function(id){
    var b=document.getElementById(id);if(b)b.addEventListener('click',softRefresh);
  });
  var tBtn=document.getElementById('sw-top');
  if(tBtn)tBtn.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'});});
})();
