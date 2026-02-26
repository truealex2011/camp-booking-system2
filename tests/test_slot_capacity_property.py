"""Property-based tests for time slot capacity limits.

Feature: booking-system-improvements
"""
import pytest
import uuid
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from datetime import date, timedelta
from app.models import db, Booking, Service
from app.services.booking_service import BookingService


class TestSlotCapacityProperty:
    """Property-based tests for time slot capacity limits."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=2000, max_examples=50)
    @given(
        num_bookings=st.integers(min_value=0, max_value=5),
        time_slot=st.sampled_from(['09:00', '09:15', '09:30', '09:45', '10:00', '10:15', '10:30', '10:45'])
    )
    def test_property_slot_capacity_limit(self, app, app_context, num_bookings, time_slot):
        """Property 4: Time Slot Capacity Limit
        
        **Validates: Requirements 4.4**
        
        For any 15-minute time slot on any date, the system should allow exactly
        2 confirmed bookings before marking the slot as unavailable.
        """
        # Clean up any existing data
        Booking.query.delete()
        Service.query.delete()
        db.session.commit()
        
        # Create a test service with unique name using UUID
        service = Service(
            name=f'Test Service {uuid.uuid4()}',
            description='Test Description',
            active=True,
            display_order=1
        )
        db.session.add(service)
        db.session.commit()
        
        # Use a future date
        booking_date = date.today() + timedelta(days=1)
        
        # Create the specified number of bookings for this slot
        for i in range(num_bookings):
            booking = Booking(
                service_id=service.id,
                date=booking_date,
                time_slot=time_slot,
                last_name=f'TestLast{i}',
                first_name=f'TestFirst{i}',
                phone=f'+7 (900) 000-00-{i:02d}',
                camp='Test Camp',
                status='confirmed',
                reference_number=f'{uuid.uuid4().hex[:12].upper()}'
            )
            db.session.add(booking)
        db.session.commit()
        
        # Check availability
        is_available = BookingService.is_slot_available(booking_date, time_slot, max_bookings=2)
        
        # Verify capacity limit
        if num_bookings < 2:
            assert is_available, \
                f"Slot {time_slot} with {num_bookings} bookings should be available (limit is 2)"
        else:
            assert not is_available, \
                f"Slot {time_slot} with {num_bookings} bookings should be unavailable (limit is 2)"
        
        # Verify slot count
        slot_count = BookingService.get_slot_count(booking_date, time_slot)
        assert slot_count == num_bookings, \
            f"Slot count should be {num_bookings}, got {slot_count}"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=2000, max_examples=30)
    @given(
        num_confirmed=st.integers(min_value=0, max_value=3),
        num_cancelled=st.integers(min_value=0, max_value=3)
    )
    def test_property_capacity_only_counts_confirmed(self, app, app_context, num_confirmed, num_cancelled):
        """Property 4: Time Slot Capacity Limit - Only Confirmed Bookings Count
        
        **Validates: Requirements 4.4**
        
        For any time slot, only confirmed bookings should count toward the
        capacity limit. Cancelled bookings should not affect availability.
        """
        # Clean up any existing data
        Booking.query.delete()
        Service.query.delete()
        db.session.commit()
        
        # Create a test service with unique name using UUID
        service = Service(
            name=f'Test Service {uuid.uuid4()}',
            description='Test Description',
            active=True,
            display_order=1
        )
        db.session.add(service)
        db.session.commit()
        
        # Use a future date and fixed time slot
        booking_date = date.today() + timedelta(days=2)
        time_slot = '11:00'
        
        # Create confirmed bookings
        for i in range(num_confirmed):
            booking = Booking(
                service_id=service.id,
                date=booking_date,
                time_slot=time_slot,
                last_name=f'ConfirmedLast{i}',
                first_name=f'ConfirmedFirst{i}',
                phone=f'+7 (901) 000-00-{i:02d}',
                camp='Test Camp',
                status='confirmed',
                reference_number=f'{uuid.uuid4().hex[:12].upper()}'
            )
            db.session.add(booking)
        
        # Create cancelled bookings
        for i in range(num_cancelled):
            booking = Booking(
                service_id=service.id,
                date=booking_date,
                time_slot=time_slot,
                last_name=f'CancelledLast{i}',
                first_name=f'CancelledFirst{i}',
                phone=f'+7 (902) 000-00-{i:02d}',
                camp='Test Camp',
                status='cancelled',
                reference_number=f'{uuid.uuid4().hex[:12].upper()}'
            )
            db.session.add(booking)
        
        db.session.commit()
        
        # Check availability - should only consider confirmed bookings
        is_available = BookingService.is_slot_available(booking_date, time_slot, max_bookings=2)
        slot_count = BookingService.get_slot_count(booking_date, time_slot)
        
        # Verify only confirmed bookings count
        assert slot_count == num_confirmed, \
            f"Slot count should only include confirmed bookings: expected {num_confirmed}, got {slot_count}"
        
        # Verify availability based on confirmed bookings only
        if num_confirmed < 2:
            assert is_available, \
                f"Slot should be available with {num_confirmed} confirmed bookings (cancelled: {num_cancelled})"
        else:
            assert not is_available, \
                f"Slot should be unavailable with {num_confirmed} confirmed bookings (cancelled: {num_cancelled})"
