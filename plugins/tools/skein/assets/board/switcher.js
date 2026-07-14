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
  var keys={theme:'data-theme',palette:'data-palette',mode:'data-mode'};
  function apply(k,v){
    if(!v)return;
    html.setAttribute(keys[k],v);
    localStorage.setItem('skein-'+k,v);
    var sel=document.getElementById('sw-'+k);
    if(sel)sel.value=v;
  }
  Object.keys(keys).forEach(function(k){
    var saved=localStorage.getItem('skein-'+k);
    if(saved)apply(k,saved);
    var sel=document.getElementById('sw-'+k);
    if(sel)sel.addEventListener('change',function(){apply(k,sel.value);});
  });
  // 状态筛选: 按 data-status 显隐 task card ('all'=全显); 概览 banner 无 data-status → 恒显
  function applyFilter(v){
    if(!v)v='all';
    localStorage.setItem('skein-filter',v);
    var sel=document.getElementById('sw-filter');
    if(sel)sel.value=v;
    document.querySelectorAll('section.card[data-status]').forEach(function(c){
      c.style.display=(v==='all'||c.getAttribute('data-status')===v)?'':'none';
    });
  }
  applyFilter(localStorage.getItem('skein-filter'));
  var fsel=document.getElementById('sw-filter');
  if(fsel)fsel.addEventListener('change',function(){applyFilter(fsel.value);});
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
})();
