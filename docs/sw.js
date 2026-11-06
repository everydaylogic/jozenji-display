// ネットを優先し、つながらないときだけ前回の内容を使う
const CACHE = 'jozenji-display-v2';
const SHELL = ['./', 'index.html', 'calendar.html', 'manifest.webmanifest', 'icon-192.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  const key = new URL(req.url); key.search = '';
  e.respondWith(
    fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(key.href, copy)); }
      return res;
    }).catch(() => caches.match(key.href).then(r => r || caches.match('index.html')))
  );
});
