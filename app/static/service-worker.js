// Service Worker for handling push notifications

self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    event.waitUntil(clients.claim());
});

self.addEventListener('push', (event) => {
    console.log('Push notification received');
    
    let data = {
        title: 'Уведомление',
        message: 'У вас новое уведомление'
    };
    
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            console.error('Failed to parse push data:', e);
        }
    }
    
    const options = {
        body: data.message,
        icon: '/static/images/notification-icon.png',
        badge: '/static/images/badge-icon.png',
        vibrate: [200, 100, 200],
        tag: 'booking-notification',
        requireInteraction: true,
        data: {
            timestamp: data.timestamp || new Date().toISOString()
        }
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked');
    event.notification.close();
    
    // Open the app when notification is clicked
    event.waitUntil(
        clients.openWindow('/')
    );
});
