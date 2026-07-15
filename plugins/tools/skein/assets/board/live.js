// SKEIN 看板热重载: serve 连 WS — "data"→软刷 (拉 JSON 重渲染), "reload"→整页刷;
// onopen 重连=服务端重启→整页刷。file:// 无 WS 端点, 直接退出 (被拷进 .skein/board/ 也不生效)。
(function(){
  if(location.protocol==="file:")return;
  var seen=false;
  function conn(){
    var ws=new WebSocket((location.protocol==="https:"?"wss://":"ws://")+location.host+"/__skein__/live");
    ws.onopen=function(){if(seen)location.reload();else seen=true;};
    ws.onmessage=function(e){
      if(e.data==="data"){window.__skeinRefresh?window.__skeinRefresh():location.reload();}
      else if(e.data==="reload"){location.reload();}
    };
    ws.onclose=function(){setTimeout(conn,2000);};
    ws.onerror=function(){try{ws.close();}catch(_){}};
  }
  conn();
})();
