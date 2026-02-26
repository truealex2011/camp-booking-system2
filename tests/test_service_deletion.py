"""Unit tests for service deletion functionality."""
import pytest
from app.models import db, Service, Booking
from app.services.service_manager import ServiceManager
from datetime import date


def test_service_deletion_with_no_bookings(app_context):
    """Test that a service with no bookings can be deleted."""
    # Create a service
    service = Service(name="Test Service", active=True)
    db.session.add(service)
    db.session.commit()
    service_id = service.id
    
    # Verify it can be deleted
    assert ServiceManager.can_delete_service(service_id) is True
    
    # Delete the service
    result = ServiceManager.delete_service(service_id)
    assert result is True
    
    # Verify it's gone
    assert Service.query.get(service_id) is None


def test_service_deletion_with_confirmed_booking(app_context):
    """Test that a service with confirmed bookings cannot be deleted."""
    # Create a service
    service = Service(name="Test Service", active=True)
    db.session.add(service)
    db.session.commit()
    service_id = service.id
    
    # Create a confirmed booking
    booking = Booking(
        service_id=service_id,
        date=date(2024, 12, 25),
        time_slot="10:00",
        last_name="Doe",
        first_name="John",
        phone="1234567890",
        camp="Test Camp",
        status="confirmed",
        reference_number="TEST001"
    )
    db.session.add(booking)
    db.session.commit()
    
    # Verify it cannot be deleted
    assert ServiceManager.can_delete_service(service_id) is False
    
    # Attempt to delete should fail
    result = ServiceManager.delete_service(service_id)
    assert result is False
    
    # Verify service still exists
    assert Service.query.get(service_id) is not None


def test_service_deletion_with_cancelled_booking(app_context):
    """Test that a service with cancelled bookings cannot be deleted."""
    # Create a service
    service = Service(name="Test Service", active=True)
    db.session.add(service)
    db.session.commit()
    service_id = service.id
    
    # Create a cancelled booking
    booking = Booking(
        service_id=service_id,
        date=date(2024, 12, 25),
        time_slot="10:00",
        last_name="Doe",
        first_name="John",
        phone="1234567890",
        camp="Test Camp",
        status="cancelled",
        reference_number="TEST002"
    )
    db.session.add(booking)
    db.session.commit()
    
    # Verify it cannot be deleted (cancelled bookings count too)
    assert ServiceManager.can_delete_service(service_id) is False
    
    # Attempt to delete should fail
    result = ServiceManager.delete_service(service_id)
    assert result is False
    
    # Verify service still exists
    assert Service.query.get(service_id) is not None


def test_service_deletion_state_consistency(app_context):
    """Test that service becomes deletable immediately after all bookings deleted.
    
    This test verifies Requirement 12.5: no caching issues, immediate state update.
    """
    # Create a service
    service = Service(name="Test Service", active=True)
    db.session.add(service)
    db.session.commit()
    service_id = service.id
    
    # Create multiple bookings with different statuses
    booking1 = Booking(
        service_id=service_id,
        date=date(2024, 12, 25),
        time_slot="10:00",
        last_name="Doe",
        first_name="John",
        phone="1234567890",
        camp="Test Camp",
        status="confirmed",
        reference_number="TEST003"
    )
    booking2 = Booking(
        service_id=service_id,
        date=date(2024, 12, 26),
        time_slot="11:00",
        last_name="Smith",
        first_name="Jane",
        phone="0987654321",
        camp="Test Camp",
        status="cancelled",
        reference_number="TEST004"
    )
    db.session.add_all([booking1, booking2])
    db.session.commit()
    
    # Verify service cannot be deleted with bookings
    assert ServiceManager.can_delete_service(service_id) is False
    
    # Delete first booking
    db.session.delete(booking1)
    db.session.commit()
    
    # Should still not be deletable (one booking remains)
    assert ServiceManager.can_delete_service(service_id) is False
    
    # Delete second booking
    db.session.delete(booking2)
    db.session.commit()
    
    # NOW it should be immediately deletable (no caching issues)
    assert ServiceManager.can_delete_service(service_id) is True
    
    # And deletion should succeed
    result = ServiceManager.delete_service(service_id)
    assert result is True
    
    # Verify service is gone
    assert Service.query.get(service_id) is None


def test_booking_count_includes_all_statuses(app_context):
    """Test that booking count includes both confirmed and cancelled bookings."""
    # Create a service
    service = Service(name="Test Service", active=True)
    db.session.add(service)
    db.session.commit()
    service_id = service.id
    
    # Initially should be deletable
    assert ServiceManager.can_delete_service(service_id) is True
    
    # Add a confirmed booking
    booking1 = Booking(
        service_id=service_id,
        date=date(2024, 12, 25),
        time_slot="10:00",
        last_name="Doe",
        first_name="John",
        phone="1234567890",
        camp="Test Camp",
        status="confirmed",
        reference_number="TEST005"
    )
    db.session.add(booking1)
    db.session.commit()
    
    # Should not be deletable
    assert ServiceManager.can_delete_service(service_id) is False
    
    # Add a cancelled booking
    booking2 = Booking(
        service_id=service_id,
        date=date(2024, 12, 26),
        time_slot="11:00",
        last_name="Smith",
        first_name="Jane",
        phone="0987654321",
        camp="Test Camp",
        status="cancelled",
        reference_number="TEST006"
    )
    db.session.add(booking2)
    db.session.commit()
    
    # Should still not be deletable (count includes both)
    assert ServiceManager.can_delete_service(service_id) is False
    
    # Verify the count is 2
    booking_count = Booking.query.filter_by(service_id=service_id).count()
    assert booking_count == 2


def test_service_deletion_nonexistent_service(app_context):
    """Test that deleting a nonexistent service returns False."""
    result = ServiceManager.delete_service(99999)
    assert result is False


def test_can_delete_service_nonexistent_service(app_context):
    """Test that checking deletion for nonexistent service returns True (no bookings)."""
    # A nonexistent service has no bookings, so technically can be "deleted"
    # (though the actual deletion will fail when service is not found)
    result = ServiceManager.can_delete_service(99999)
    assert result is True
