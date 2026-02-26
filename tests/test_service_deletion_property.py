"""Property-based tests for service deletion functionality.

Feature: booking-system-improvements
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from app.models import db, Service, Booking
from app.services.service_manager import ServiceManager
from datetime import date, timedelta


# Strategy for generating valid booking data
@st.composite
def booking_data(draw):
    """Generate valid booking data."""
    return {
        'date': draw(st.dates(
            min_value=date.today(),
            max_value=date.today() + timedelta(days=365)
        )),
        'time_slot': draw(st.sampled_from([
            "09:00", "10:00", "11:00", "12:00", "13:00", 
            "14:00", "15:00", "16:00", "17:00"
        ])),
        'last_name': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll'), min_codepoint=65, max_codepoint=122
        ))),
        'first_name': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll'), min_codepoint=65, max_codepoint=122
        ))),
        'phone': draw(st.text(min_size=10, max_size=20, alphabet=st.characters(
            whitelist_characters='0123456789+-() '
        ))),
        'camp': draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll'), min_codepoint=65, max_codepoint=122
        ))),
        'status': draw(st.sampled_from(['confirmed', 'cancelled'])),
    }


@given(
    num_bookings=st.integers(min_value=0, max_value=10)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_21_service_deletion_booking_check(app_context, num_bookings):
    """Property 21: Service Deletion Booking Check
    
    **Validates: Requirements 12.1**
    
    For any service deletion attempt, the system should query the database
    to count all bookings (regardless of status) associated with that service
    before allowing deletion.
    
    This property verifies that the system always checks booking count before
    attempting deletion.
    """
    # Create a service
    service = Service(name=f"Test Service {num_bookings}", active=True)
    db.session.add(service)
    db.session.commit()
    service_id = service.id
    
    # Create the specified number of bookings with random statuses
    for i in range(num_bookings):
        status = 'confirmed' if i % 2 == 0 else 'cancelled'
        booking = Booking(
            service_id=service_id,
            date=date.today() + timedelta(days=i),
            time_slot="10:00",
            last_name=f"LastName{i}",
            first_name=f"FirstName{i}",
            phone=f"123456789{i}",
            camp=f"Camp{i}",
            status=status,
            reference_number=f"REF{service_id}{i:04d}"
        )
        db.session.add(booking)
    db.session.commit()
    
    # Query the actual booking count
    actual_count = Booking.query.filter_by(service_id=service_id).count()
    
    # Verify the count matches what we created
    assert actual_count == num_bookings
    
    # Check if service can be deleted
    can_delete = ServiceManager.can_delete_service(service_id)
    
    # Property: can_delete should be True if and only if booking count is 0
    assert can_delete == (num_bookings == 0)
    
    # Verify deletion attempt respects the booking check
    deletion_result = ServiceManager.delete_service(service_id)
    assert deletion_result == (num_bookings == 0)
    
    # Cleanup
    if num_bookings > 0:
        # Service should still exist
        assert Service.query.get(service_id) is not None
        # Clean up for next iteration
        Booking.query.filter_by(service_id=service_id).delete()
        db.session.delete(service)
        db.session.commit()
    else:
        # Service should be deleted
        assert Service.query.get(service_id) is None


@given(
    num_bookings=st.integers(min_value=0, max_value=20)
)
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None  # Disable deadline for database operations
)
def test_property_22_service_deletion_rules(app_context, num_bookings):
    """Property 22: Service Deletion Rules
    
    **Validates: Requirements 12.2, 12.3**
    
    For any service, the service should be deletable if and only if it has
    zero associated bookings (counting both confirmed and cancelled bookings).
    
    This property verifies the deletion rules are correctly enforced.
    """
    # Create a service
    service = Service(name=f"Service Rules Test {num_bookings}", active=True)
    db.session.add(service)
    db.session.commit()
    service_id = service.id
    
    # Create bookings with mixed statuses
    for i in range(num_bookings):
        # Alternate between confirmed and cancelled
        status = 'confirmed' if i % 2 == 0 else 'cancelled'
        booking = Booking(
            service_id=service_id,
            date=date.today() + timedelta(days=i),
            time_slot=f"{9 + (i % 8):02d}:00",
            last_name=f"Last{i}",
            first_name=f"First{i}",
            phone=f"555000{i:04d}",
            camp=f"TestCamp{i}",
            status=status,
            reference_number=f"RULE{service_id}{i:05d}"
        )
        db.session.add(booking)
    db.session.commit()
    
    # Test the deletion rule
    can_delete = ServiceManager.can_delete_service(service_id)
    
    # Property: Service is deletable IFF it has zero bookings
    if num_bookings == 0:
        assert can_delete is True
        assert ServiceManager.delete_service(service_id) is True
        assert Service.query.get(service_id) is None
    else:
        assert can_delete is False
        assert ServiceManager.delete_service(service_id) is False
        assert Service.query.get(service_id) is not None
        
        # Cleanup
        Booking.query.filter_by(service_id=service_id).delete()
        db.session.delete(service)
        db.session.commit()


@given(
    num_confirmed=st.integers(min_value=0, max_value=10),
    num_cancelled=st.integers(min_value=0, max_value=10)
)
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=1000,  # Increase deadline for database operations with many bookings
    max_examples=50  # Reduce examples to speed up test
)
def test_property_23_booking_count_accuracy(app_context, num_confirmed, num_cancelled):
    """Property 23: Booking Count Accuracy
    
    **Validates: Requirements 12.4**
    
    For any service, the booking count used for deletion checks should include
    all bookings with that service_id, regardless of whether the booking status
    is 'confirmed' or 'cancelled'.
    
    This property verifies that the count is accurate and includes all statuses.
    """
    import time
    import random
    
    # Create a unique service name to avoid conflicts
    unique_id = int(time.time() * 1000000) + random.randint(0, 999999)
    service = Service(name=f"Count Test {unique_id}", active=True)
    db.session.add(service)
    db.session.commit()
    service_id = service.id
    
    try:
        # Create confirmed bookings
        for i in range(num_confirmed):
            booking = Booking(
                service_id=service_id,
                date=date.today() + timedelta(days=i),
                time_slot="10:00",
                last_name=f"ConfirmedLast{i}",
                first_name=f"ConfirmedFirst{i}",
                phone=f"111{i:07d}",
                camp=f"Camp{i}",
                status="confirmed",
                reference_number=f"CONF{unique_id}{i:05d}"
            )
            db.session.add(booking)
        
        # Create cancelled bookings
        for i in range(num_cancelled):
            booking = Booking(
                service_id=service_id,
                date=date.today() + timedelta(days=num_confirmed + i),
                time_slot="11:00",
                last_name=f"CancelledLast{i}",
                first_name=f"CancelledFirst{i}",
                phone=f"222{i:07d}",
                camp=f"Camp{i}",
                status="cancelled",
                reference_number=f"CANC{unique_id}{i:05d}"
            )
            db.session.add(booking)
        
        db.session.commit()
        
        # Count bookings by status
        confirmed_count = Booking.query.filter_by(
            service_id=service_id, status='confirmed'
        ).count()
        cancelled_count = Booking.query.filter_by(
            service_id=service_id, status='cancelled'
        ).count()
        total_count = Booking.query.filter_by(service_id=service_id).count()
        
        # Verify counts match what we created
        assert confirmed_count == num_confirmed
        assert cancelled_count == num_cancelled
        assert total_count == num_confirmed + num_cancelled
        
        # Property: can_delete should consider TOTAL count, not just confirmed
        can_delete = ServiceManager.can_delete_service(service_id)
        expected_can_delete = (num_confirmed + num_cancelled) == 0
        assert can_delete == expected_can_delete
        
        # Verify deletion respects total count
        deletion_result = ServiceManager.delete_service(service_id)
        assert deletion_result == expected_can_delete
        
    finally:
        # Cleanup - always clean up regardless of test outcome
        try:
            Booking.query.filter_by(service_id=service_id).delete()
            service_obj = Service.query.get(service_id)
            if service_obj:
                db.session.delete(service_obj)
            db.session.commit()
        except:
            db.session.rollback()


@given(
    initial_bookings=st.integers(min_value=1, max_value=5)
)
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=2000  # Increase deadline significantly for multiple deletions
)
def test_property_24_post_deletion_consistency(app_context, initial_bookings):
    """Property 24: Post-Deletion State Consistency
    
    **Validates: Requirements 12.5**
    
    For any service, after all its associated bookings are deleted, the service
    should immediately become deletable without requiring cache refresh or page reload.
    
    This property verifies there are no caching or state consistency issues.
    """
    # Create a service
    service = Service(name=f"Consistency Test {initial_bookings}", active=True)
    db.session.add(service)
    db.session.commit()
    service_id = service.id
    
    # Create initial bookings
    booking_ids = []
    for i in range(initial_bookings):
        status = 'confirmed' if i % 2 == 0 else 'cancelled'
        booking = Booking(
            service_id=service_id,
            date=date.today() + timedelta(days=i),
            time_slot=f"{9 + (i % 8):02d}:00",
            last_name=f"ConsistLast{i}",
            first_name=f"ConsistFirst{i}",
            phone=f"333{i:07d}",
            camp=f"Camp{i}",
            status=status,
            reference_number=f"CONS{service_id}{i:05d}"
        )
        db.session.add(booking)
        db.session.flush()
        booking_ids.append(booking.id)
    
    db.session.commit()
    
    # Verify service is not deletable with bookings
    assert ServiceManager.can_delete_service(service_id) is False
    assert ServiceManager.delete_service(service_id) is False
    
    # Delete bookings one by one
    for i, booking_id in enumerate(booking_ids):
        booking = Booking.query.get(booking_id)
        db.session.delete(booking)
        db.session.commit()
        
        remaining = initial_bookings - (i + 1)
        
        # Check state consistency after each deletion
        can_delete = ServiceManager.can_delete_service(service_id)
        
        if remaining == 0:
            # Property: Service should be IMMEDIATELY deletable when last booking removed
            assert can_delete is True, \
                f"Service should be deletable after all {initial_bookings} bookings deleted"
            
            # Verify deletion succeeds
            assert ServiceManager.delete_service(service_id) is True
            assert Service.query.get(service_id) is None
            break
        else:
            # Still has bookings, should not be deletable
            assert can_delete is False, \
                f"Service should not be deletable with {remaining} bookings remaining"
