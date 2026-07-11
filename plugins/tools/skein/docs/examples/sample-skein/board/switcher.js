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
})();
