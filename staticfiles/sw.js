// Имя кэша — меняй при обновлении приложения
const CACHE_NAME = 'wisp-v1';
const OFFLINE_URL = '/static/offline.html';

// Файлы для кэширования (будут работать офлайн)
const urlsToCache = [
    '/',
    '/static/manifest.json',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
    '/static/offline.html',
    '/static/gerb.png'
];

// Установка Service Worker
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('Кэширование файлов...');
                return cache.addAll(urlsToCache);
            })
    );
});

// Активация Service Worker
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Удаление старого кэша:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Перехват запросов
self.addEventListener('fetch', function(event) {
    // Если запрос к нашему API — не кэшируем
    if (event.request.url.includes('/send_message/') ||
        event.request.url.includes('/get_new_messages/') ||
        event.request.url.includes('/login/') ||
        event.request.url.includes('/register/')) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // Если файл в кэше — возвращаем из кэша
                if (response) {
                    return response;
                }
                // Иначе — идём в сеть
                return fetch(event.request).catch(function() {
                    // Если нет интернета — показываем offline-страницу
                    if (event.request.mode === 'navigate') {
                        return caches.match(OFFLINE_URL);
                    }
                });
            })
    );
});