"""Tests for notification system functionality."""
import pytest
from datetime import datetime, date, timedelta
from app.models import db, Booking, Service, PushSubscription, Notification
from app.services.notification_service import NotificationService


def test_save_subscription(client):
    """Test saving push subscription for a booking."""
    # Create a service and booking
    service = Service(name='Test Service', active=True)
    db.session.add(service)
    db.session.commit()
    
    booking = Booking(
        service_id=service.id,
        date=date.today() + timedelta(days=1),
        time_slot='10:00',
        last_name='Test',
        first_name='User',
        phone='+79991234567',
        camp='Test Camp',
        reference_number='TEST123'
    )
    db.session.add(booking)
    db.session.commit()
    
    # Save subscription
    subscription_data = {
        'endpoint': 'https://fcm.googleapis.com/fcm/send/test',
        'keys': {
            'p256dh': 'test_p256dh_key',
            'auth': 'test_auth_key'
        }
    }
    
    result = NotificationService.save_subscription(booking.id, subscription_data)
    
    assert result is not None
    assert result.booking_id == booking.id
    assert result.endpoint == subscription_data['endpoint']
    assert result.p256dh_key == subscription_data['keys']['p256dh']
    assert result.auth_key == subscription_data['keys']['auth']


def test_create_notification_record(client):
    """Test creating notification record in database."""
    # Create a service and booking
    service = Service(name='Test Service', active=True)
    db.session.add(service)
    db.session.commit()
    
    booking = Booking(
        service_id=service.id,
        date=date.today() + timedelta(days=1),
        time_slot='10:00',
        last_name='Test',
        first_name='User',
        phone='+79991234567',
        camp='Test Camp',
        reference_number='TEST123'
    )
    db.session.add(booking)
    db.session.commit()
    
    # Create notification
    notification = NotificationService.create_notification_record(
        booking.id,
        'Test Title',
        'Test Message',
        'reminder'
    )
    
    assert notification is not None
    assert notification.booking_id == booking.id
    assert notification.title == 'Test Title'
    assert notification.message == 'Test Message'
    assert notification.notification_type == 'reminder'
    assert notification.is_read is False


def test_get_user_notifications(client):
    """Test retrieving notifications for a user by phone."""
    # Create a service
    service = Service(name='Test Service', active=True)
    db.session.add(service)
    db.session.commit()
    
    # Create multiple bookings for same phone
    phone = '+79991234567'
    bookings = []
    for i in range(3):
        booking = Booking(
            service_id=service.id,
            date=date.today() + timedelta(days=i+1),
            time_slot='10:00',
            last_name='Test',
            first_name='User',
            phone=phone,
            camp='Test Camp',
            reference_number=f'TEST{i}'
        )
        db.session.add(booking)
        bookings.append(booking)
    db.session.commit()
    
    # Create notifications for each booking
    for booking in bookings:
        NotificationService.create_notification_record(
            booking.id,
            f'Notification {booking.reference_number}',
            'Test message',
            'reminder'
        )
    
    # Get notifications
    notifications = NotificationService.get_user_notifications(phone)
    
    assert len(notifications) == 3
    assert all(n.booking_id in [b.id for b in bookings] for n in notifications)


def test_mark_notification_read(client):
    """Test marking notification as read."""
    # Create a service and booking
    service = Service(name='Test Service', active=True)
    db.session.add(service)
    db.session.commit()
    
    booking = Booking(
        service_id=service.id,
        date=date.today() + timedelta(days=1),
        time_slot='10:00',
        last_name='Test',
        first_name='User',
        phone='+79991234567',
        camp='Test Camp',
        reference_number='TEST123'
    )
    db.session.add(booking)
    db.session.commit()
    
    # Create notification
    notification = NotificationService.create_notification_record(
        booking.id,
        'Test Title',
        'Test Message',
        'reminder'
    )
    
    assert notification.is_read is False
    
    # Mark as read
    result = NotificationService.mark_notification_read(notification.id)
    
    assert result is True
    
    # Verify it's marked as read
    updated_notification = Notification.query.get(notification.id)
    assert updated_notification.is_read is True


def test_notification_to_dict(client):
    """Test notification serialization to dictionary."""
    # Create a service and booking
    service = Service(name='Test Service', active=True)
    db.session.add(service)
    db.session.commit()
    
    booking = Booking(
        service_id=service.id,
        date=date.today() + timedelta(days=1),
        time_slot='10:00',
        last_name='Test',
        first_name='User',
        phone='+79991234567',
        camp='Test Camp',
        reference_number='TEST123'
    )
    db.session.add(booking)
    db.session.commit()
    
    # Create notification
    notification = NotificationService.create_notification_record(
        booking.id,
        'Test Title',
        'Test Message',
        'reminder'
    )
    
    # Convert to dict
    notification_dict = notification.to_dict()
    
    assert notification_dict['id'] == notification.id
    assert notification_dict['booking_id'] == booking.id
    assert notification_dict['title'] == 'Test Title'
    assert notification_dict['message'] == 'Test Message'
    assert notification_dict['notification_type'] == 'reminder'
    assert notification_dict['is_read'] is False
    assert 'created_at' in notification_dict
