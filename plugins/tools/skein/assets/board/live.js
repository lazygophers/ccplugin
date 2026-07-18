// SKEIN 看板热重载: serve 连 WS — "data"→软刷 (拉 JSON 重渲染), "reload"→整页刷;
// onopen 重连=服务端重启→整页刷。file:// 无 WS 端点, 直接退出 (被拷进 .skein/board/ 也不生效)。
// 后端挂: WS 断后每 2s 重连; 5 分钟内未重连成功 → 判定服务已停, 自动关页 (window.close 被浏览器拦则整页遮罩提示)。
(function(){
  if(location.protocol==="file:")return;
  var seen=false,deadTimer=null,GRACE=5*60*1000;
  function giveUp(){
    try{window.close();}catch(_){}  // 仅能关脚本自开的窗; 拦住不抛错, 落遮罩兜底
    document.documentElement.innerHTML='<div style="display:flex;align-items:center;justify-content:center;height:100vh;font:16px/1.6 system-ui;color:#666;text-align:center">SKEIN 看板服务已停止<br>(5 分钟未恢复, 请重开 <code>skein serve</code>)</div>';
  }
  function conn(){
    var ws=new WebSocket((location.protocol==="https:"?"wss://":"ws://")+location.host+"/__skein__/live");
    ws.onopen=function(){if(deadTimer){clearTimeout(deadTimer);deadTimer=null;}if(seen)location.reload();else seen=true;};
    ws.onmessage=function(e){
      if(e.data==="data"){window.__skeinRefresh?window.__skeinRefresh():location.reload();}
      else if(e.data==="reload"){location.reload();}
    };
    ws.onclose=function(){if(!deadTimer)deadTimer=setTimeout(giveUp,GRACE);setTimeout(conn,2000);};
    ws.onerror=function(){try{ws.close();}catch(_){}};
  }
  conn();
})();
