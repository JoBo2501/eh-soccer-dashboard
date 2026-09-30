const CACHE_NAME = "eh-soccer-2026-v3";
const APP_SHELL = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./manifest.webmanifest",
  "./assets/team-2026.webp",
  "./assets/niklas-borck.webp",
  "./assets/icon-192.png",
  "./assets/icon-512.png",
  "./assets/icon-maskable-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  const url = new URL(event.request.url);
  if (url.pathname.endsWith("/data/season.json")) {
    const canonical = new URL("data/season.json", self.registration.scope).href;
    event.respondWith(
      fetch(event.request, { cache: "no-store" })
        .then((response) => {
          if (!response.ok) throw new Error("Season refresh failed");
          const copy = response.clone();
          event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.put(canonical, copy)));
          return response;
        })
        .catch(async () => {
          const saved = await caches.match(canonical);
          if (!saved) throw new Error("No offline season data available");
          const headers = new Headers(saved.headers);
          headers.set("X-EH-Offline", "1");
          return new Response(await saved.arrayBuffer(), { status: saved.status, headers });
        })
    );
    return;
  }

  if (url.origin === self.location.origin) {
    event.respondWith(
      fetch(event.request, { cache: "no-cache" }).then((response) => {
        if (!response.ok) throw new Error("App refresh failed");
        const copy = response.clone();
        event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy)));
        return response;
      }).catch(() => caches.match(event.request))
    );
  }
});
