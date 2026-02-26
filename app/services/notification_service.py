"""Notification service for managing push notifications and notification records."""
import os
import json
from datetime import datetime
from pywebpush import webpush, WebPushException
from app.models import db, PushSubscription, Notification, Booking


class NotificationService:
    """Service for managing notifications and push subscriptions."""
    
    @staticmethod
    def save_subscription(booking_id, subscription_data):
        """Save push subscription for a booking.
        
        Args:
            booking_id: Booking ID
            subscription_data: Dict with endpoint, keys (p256dh, auth)
            
        Returns:
            PushSubscription object or None
        """
        try:
            # Check if subscription already exists
            existing = PushSubscription.query.filter_by(booking_id=booking_id).first()
            
            if existing:
                # Update existing subscription
                existing.endpoint = subscription_data['endpoint']
                existing.p256dh_key = subscription_data['keys']['p256dh']
                existing.auth_key = subscription_data['keys']['auth']
            else:
                # Create new subscription
                subscription = PushSubscription(
                    booking_id=booking_id,
                    endpoint=subscription_data['endpoint'],
                    p256dh_key=subscription_data['keys']['p256dh'],
                    auth_key=subscription_data['keys']['auth']
                )
                db.session.add(subscription)
            
            db.session.commit()
            return existing if existing else subscription
            
        except Exception as e:
            print(f"Error saving subscription: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def send_push_notification(subscription, title, message):
        """Send push notification using pywebpush.
        
        Args:
            subscription: PushSubscription object
            title: Notification title
            message: Notification message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from flask import current_app
            
            # Get VAPID keys from config
            vapid_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
            vapid_claims_email = current_app.config.get('VAPID_CLAIMS_EMAIL', 'mailto:admin@example.com')
            
            if not vapid_private_key:
                print("VAPID_PRIVATE_KEY not configured")
                return False
            
            # Prepare notification payload
            payload = json.dumps({
                'title': title,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Send push notification
            webpush(
                subscription_info={
                    'endpoint': subscription.endpoint,
                    'keys': {
                        'p256dh': subscription.p256dh_key,
                        'auth': subscription.auth_key
                    }
                },
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims={'sub': vapid_claims_email}
            )
            
            return True
            
        except WebPushException as e:
            print(f"Web Push failed: {e}")
            # If subscription is invalid, delete it
            if e.response and e.response.status_code in [404, 410]:
                try:
                    db.session.delete(subscription)
                    db.session.commit()
                except:
                    db.session.rollback()
            return False
            
        except Exception as e:
            print(f"Error sending push notification: {e}")
            return False
    
    @staticmethod
    def create_notification_record(booking_id, title, message, notification_type):
        """Create notification record in database.
        
        Args:
            booking_id: Booking ID
            title: Notification title
            message: Notification message
            notification_type: Type ('reminder', 'cancellation')
            
        Returns:
            Notification object or None
        """
        try:
            notification = Notification(
                booking_id=booking_id,
                title=title,
                message=message,
                notification_type=notification_type,
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()
            return notification
            
        except Exception as e:
            print(f"Error creating notification record: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_user_notifications(phone):
        """Get all notifications for a user by phone number.
        
        Args:
            phone: User's phone number
            
        Returns:
            List of Notification objects
        """
        try:
            # Get all bookings for this phone
            bookings = Booking.query.filter_by(phone=phone).all()
            booking_ids = [b.id for b in bookings]
            
            # Get notifications for these bookings
            notifications = Notification.query.filter(
                Notification.booking_id.in_(booking_ids)
            ).order_by(Notification.created_at.desc()).all()
            
            return notifications
            
        except Exception as e:
            print(f"Error getting user notifications: {e}")
            return []
    
    @staticmethod
    def mark_notification_read(notification_id):
        """Mark notification as read.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            notification = Notification.query.get(notification_id)
            if notification:
                notification.is_read = True
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def send_cancellation_notification(booking):
        """Send cancellation notification to user.
        
        Args:
            booking: Booking object that was cancelled
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create notification message
            title = "Бронирование отменено"
            message = (
                f"Ваше бронирование {booking.reference_number} "
                f"на {booking.date.strftime('%d.%m.%Y')} в {booking.time_slot} "
                f"было отменено администратором."
            )
            
            # Create notification record
            notification = NotificationService.create_notification_record(
                booking.id,
                title,
                message,
                'cancellation'
            )
            
            if not notification:
                return False
            
            # Try to send push notification
            subscription = PushSubscription.query.filter_by(booking_id=booking.id).first()
            if subscription:
                NotificationService.send_push_notification(subscription, title, message)
                notification.sent_at = datetime.utcnow()
                db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"Error sending cancellation notification: {e}")
            return False
    
    @staticmethod
    def send_reminder_notification(booking):
        """Send 24-hour reminder notification to user.
        
        Args:
            booking: Booking object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create notification message
            title = "Напоминание о записи"
            message = (
                f"Напоминаем, что завтра {booking.date.strftime('%d.%m.%Y')} "
                f"в {booking.time_slot} у вас запись на услугу '{booking.service.name}'. "
                f"Номер бронирования: {booking.reference_number}"
            )
            
            # Create notification record
            notification = NotificationService.create_notification_record(
                booking.id,
                title,
                message,
                'reminder'
            )
            
            if not notification:
                return False
            
            # Try to send push notification
            subscription = PushSubscription.query.filter_by(booking_id=booking.id).first()
            if subscription:
                NotificationService.send_push_notification(subscription, title, message)
                notification.sent_at = datetime.utcnow()
                db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"Error sending reminder notification: {e}")
            return False
    
    @staticmethod
    def get_unread_count(phone):
        """Get count of unread notifications for a user.
        
        Args:
            phone: User's phone number
            
        Returns:
            Count of unread notifications
        """
        try:
            # Get all bookings for this phone
            bookings = Booking.query.filter_by(phone=phone).all()
            booking_ids = [b.id for b in bookings]
            
            # Count unread notifications for these bookings
            count = Notification.query.filter(
                Notification.booking_id.in_(booking_ids),
                Notification.is_read == False
            ).count()
            
            return count
            
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0
