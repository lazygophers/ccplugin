// SKEIN 看板主题切换器: 读/写 <html> data 属性 + localStorage, 无依赖。
(function(){
  var html=document.documentElement;
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
})();
