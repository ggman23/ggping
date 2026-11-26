/* CVTT Vaires, version 2 : service worker. Toujours le réseau d'abord (pages et données à jour) ; sans
   réseau (salle mal couverte), la dernière version gardée. Les données restent chiffrées dans le cache. */
const CACHE = "cvtt-v2-__VERSION__";
const COQUILLE = ["./", "commun.css", "commun.js", "equipes/", "rencontre/", "joueurs/", "agenda/", "club/", "indivs/", "77/", "tournois/",
                  "manifest.webmanifest", "icones/icone-192.png"];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => Promise.allSettled(COQUILLE.map((u) => c.add(u)))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((cles) => Promise.all(cles.filter((k) => k.startsWith("cvtt-v2-") && k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;  // compteurs de visites, liens extérieurs : non gardés
  e.respondWith(fetch(e.request).then((r) => {
    if (r.ok) { const copie = r.clone(); caches.open(CACHE).then((c) => c.put(e.request, copie)); }
    return r;
  }).catch(() => caches.match(e.request, { ignoreSearch: true }).then((r) => r || caches.match(e.request))));
});
