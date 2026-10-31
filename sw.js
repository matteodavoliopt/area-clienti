/* Area clienti – funzionamento senza connessione.
   Pagine: prima la rete, se manca usa la copia salvata. File statici: copia salvata, aggiornata in background. */
var C='area-clienti-v2';
self.addEventListener('install',function(e){ self.skipWaiting(); });
self.addEventListener('activate',function(e){ e.waitUntil(caches.keys().then(function(ks){ return Promise.all(ks.filter(function(k){ return k!==C; }).map(function(k){ return caches.delete(k); })); }).then(function(){ return self.clients.claim(); })); });
self.addEventListener('fetch',function(e){
  var r=e.request; if(r.method!=='GET') return;
  var u=new URL(r.url);
  if(u.hostname==='docs.google.com' || u.hostname.indexOf('youtube')>=0) return;
  var page = r.mode==='navigate' || (u.origin===location.origin && /\/$|\.html$/.test(u.pathname));
  if(page){
    var net=fetch(r).then(function(res){ if(res && res.ok){ var cp=res.clone(); caches.open(C).then(function(c){ c.put(r,cp); }); } return res; });
    var cached=caches.match(r,{ignoreSearch:true});
    var slow=new Promise(function(ok){ setTimeout(ok,3500); }).then(function(){ return cached.then(function(c){ return c || net; }); });
    e.respondWith(Promise.race([net, slow]).catch(function(){ return cached.then(function(c){ return c || Response.error(); }); }));
    return;
  }
  if(u.origin===location.origin || /fonts\.(googleapis|gstatic)\.com$/.test(u.hostname) || u.hostname==='i.ytimg.com'){
    e.respondWith(caches.match(r).then(function(hit){
      var net=fetch(r).then(function(res){ if(res && (res.ok || res.type==='opaque')){ var cp=res.clone(); caches.open(C).then(function(c){ c.put(r,cp); }); } return res; }).catch(function(){ return hit; });
      return hit || net;
    }));
  }
});
