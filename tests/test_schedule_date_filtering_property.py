"""Property-based tests for schedule date filtering functionality.

Feature: booking-system-improvements
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import date, timedelta
from app.models import db, Service, Booking
from app.services.booking_service import BookingService


class TestScheduleDateFilteringProperty:
    """Property-based tests for schedule date filtering."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=2000, max_examples=50)
    @given(
        target_date_offset=st.integers(min_value=0, max_value=30),
        other_dates_offsets=st.lists(
            st.integers(min_value=0, max_value=30),
            min_size=0,
            max_size=5
        ),
        num_bookings_on_target=st.integers(min_value=1, max_value=5),
        random_seed=st.integers(min_value=0, max_value=999999)
    )
    def test_property_schedule_date_filtering(self, app_context, target_date_offset, 
                                              other_dates_offsets, num_bookings_on_target,
                                              random_seed):
        """Property 6: Schedule Date Filtering
        
        **Validates: Requirements 5.3**
        
        For any date selected for schedule printing, the generated schedule should
        contain only bookings that match that specific date.
        """
        # Clean up any existing data
        Booking.query.delete()
        Service.query.delete()
        db.session.commit()
        
        # Create a test service with unique name
        service = Service(
            name=f"Test Service {random_seed}",
            description="Test",
            active=True,
            display_order=1
        )
        db.session.add(service)
        db.session.commit()
        
        # Calculate target date
        target_date = date.today() + timedelta(days=target_date_offset)
        
        # Create bookings on the target date
        target_booking_ids = []
        for i in range(num_bookings_on_target):
            booking = Booking(
                service_id=service.id,
                date=target_date,
                time_slot=f"{9 + i}:00",
                last_name=f"Иванов{i}",
                first_name=f"Иван{i}",
                phone="+7 (999) 123-45-67",
                camp="Лагерь 1",
                status='confirmed',
                reference_number=f"TEST-{random_seed}-{target_date_offset}-{i}"
            )
            db.session.add(booking)
            db.session.flush()
            target_booking_ids.append(booking.id)
        
        # Create bookings on other dates (should not appear in results)
        other_booking_ids = []
        for idx, offset in enumerate(other_dates_offsets):
            # Skip if offset matches target date
            if offset == target_date_offset:
                continue
                
            other_date = date.today() + timedelta(days=offset)
            booking = Booking(
                service_id=service.id,
                date=other_date,
                time_slot="10:00",
                last_name="Петров",
                first_name="Петр",
                phone="+7 (999) 123-45-67",
                camp="Лагерь 2",
                status='confirmed',
                reference_number=f"OTHER-{random_seed}-{offset}-{idx}"
            )
            db.session.add(booking)
            db.session.flush()
            other_booking_ids.append(booking.id)
        
        db.session.commit()
        
        # Get bookings for the target date
        filtered_bookings = BookingService.get_bookings_by_date(target_date)
        
        # Verify all returned bookings match the target date
        for booking in filtered_bookings:
            assert booking.date == target_date, \
                f"Booking {booking.id} has date {booking.date}, expected {target_date}"
        
        # Verify all target bookings are included
        filtered_ids = [b.id for b in filtered_bookings]
        for booking_id in target_booking_ids:
            assert booking_id in filtered_ids, \
                f"Target booking {booking_id} should be in filtered results"
        
        # Verify no other-date bookings are included
        for booking_id in other_booking_ids:
            assert booking_id not in filtered_ids, \
                f"Other-date booking {booking_id} should not be in filtered results"
        
        # Verify count matches
        assert len(filtered_bookings) == num_bookings_on_target, \
            f"Expected {num_bookings_on_target} bookings, got {len(filtered_bookings)}"
