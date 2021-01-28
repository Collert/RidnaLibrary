const CACHE_NAME = 'static-cache v3';

const FILES_TO_CACHE = [
  "/static/pwa/offline.html",
  "https://kit.fontawesome.com/a076d05399.js"
];

// Installation
self.addEventListener('install', (evt) => {
    console.log('[ServiceWorker] Install');
    evt.waitUntil(
      caches.open(CACHE_NAME).then((cache) => {
        console.log('[ServiceWorker] Pre-caching offline page');
        return cache.addAll(FILES_TO_CACHE);
      })
    );
  
    self.skipWaiting();
});

// Activation
self.addEventListener('activate', (evt) => {
console.log('[ServiceWorker] Activate');
evt.waitUntil(
    caches.keys().then((keyList) => {
    return Promise.all(keyList.map((key) => {
        if (key !== CACHE_NAME) {
        console.log('[ServiceWorker] Removing old cache', key);
        return caches.delete(key);
        }
    }));
    })
);
self.clients.claim();
});

// Fetch
self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {
        return response || fetch(event.request);
        })
    )
});

// Notifications

self.addEventListener('push', function(event) {
    console.log('[Service Worker] Push Received.');
  
    const title = "Ridna Library";
    const options = {
      body: event.data.text(),
      icon: "/static/pwa/icons/icon-72x72.png",
      vibrate: [50, 50, 50]
    };
  
    event.waitUntil(self.registration.showNotification(title, options));
});

// Background sync

//self.addEventListener('sync', function(event) {
//   if (event.tag == 'example-tag') {
//      event.waitUntil(
//      // Actions to be performed go here.
//      );
//    }
//  });