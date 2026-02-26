// Push Notifications Handler

class PushNotifications {
    constructor() {
        this.vapidPublicKey = null;
        this.registration = null;
    }
    
    /**
     * Initialize push notifications
     * @param {string} vapidPublicKey - VAPID public key from server
     */
    async init(vapidPublicKey) {
        this.vapidPublicKey = vapidPublicKey;
        
        // Check if service workers are supported
        if (!('serviceWorker' in navigator)) {
            console.log('Service Workers not supported');
            return false;
        }
        
        // Check if push notifications are supported
        if (!('PushManager' in window)) {
            console.log('Push notifications not supported');
            return false;
        }
        
        try {
            // Register service worker
            this.registration = await navigator.serviceWorker.register('/static/service-worker.js');
            console.log('Service Worker registered');
            return true;
        } catch (error) {
            console.error('Service Worker registration failed:', error);
            return false;
        }
    }
    
    /**
     * Subscribe to push notifications for a booking
     * @param {number} bookingId - Booking ID
     */
    async subscribeToPush(bookingId) {
        if (!this.registration) {
            console.error('Service Worker not registered');
            return false;
        }
        
        try {
            // Request notification permission
            const permission = await Notification.requestPermission();
            
            if (permission !== 'granted') {
                console.log('Notification permission denied');
                return false;
            }
            
            // Convert VAPID key to Uint8Array
            const applicationServerKey = this.urlBase64ToUint8Array(this.vapidPublicKey);
            
            // Subscribe to push notifications
            const subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: applicationServerKey
            });
            
            // Send subscription to server
            const response = await fetch('/api/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    booking_id: bookingId,
                    subscription: subscription.toJSON()
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('Successfully subscribed to push notifications');
                return true;
            } else {
                console.error('Failed to save subscription:', data.message);
                return false;
            }
            
        } catch (error) {
            console.error('Error subscribing to push notifications:', error);
            return false;
        }
    }
    
    /**
     * Convert VAPID key from base64 to Uint8Array
     * @param {string} base64String - Base64 encoded VAPID key
     * @returns {Uint8Array}
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        
        return outputArray;
    }
    
    /**
     * Check if user is subscribed to push notifications
     * @returns {Promise<boolean>}
     */
    async isSubscribed() {
        if (!this.registration) {
            return false;
        }
        
        try {
            const subscription = await this.registration.pushManager.getSubscription();
            return subscription !== null;
        } catch (error) {
            console.error('Error checking subscription:', error);
            return false;
        }
    }
}

// Create global instance
window.pushNotifications = new PushNotifications();
