"""Property-based tests for schedule content completeness.

Feature: booking-system-improvements
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import date, timedelta
from app.models import db, Service, Booking
from app.services.booking_service import BookingService


class TestScheduleContentProperty:
    """Property-based tests for schedule content completeness."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=2000, max_examples=50)
    @given(
        date_offset=st.integers(min_value=0, max_value=30),
        num_bookings=st.integers(min_value=1, max_value=5),
        random_seed=st.integers(min_value=0, max_value=999999)
    )
    def test_property_schedule_content_completeness(self, app_context, date_offset, 
                                                    num_bookings, random_seed):
        """Property 7: Schedule Content Completeness
        
        **Validates: Requirements 5.4**
        
        For any booking included in a printed schedule, the schedule should display
        the booking's time slot, user name (first and last), service name, and
        contact phone number.
        """
        # Clean up any existing data
        Booking.query.delete()
        Service.query.delete()
        db.session.commit()
        
        # Create a test service
        service = Service(
            name=f"Test Service {random_seed}",
            description="Test Description",
            active=True,
            display_order=1
        )
        db.session.add(service)
        db.session.commit()
        
        # Calculate booking date
        booking_date = date.today() + timedelta(days=date_offset)
        
        # Create bookings with various data
        created_bookings = []
        for i in range(num_bookings):
            booking = Booking(
                service_id=service.id,
                date=booking_date,
                time_slot=f"{9 + i}:00",
                last_name=f"Фамилия{i}",
                first_name=f"Имя{i}",
                phone=f"+7 (999) {100 + i:03d}-45-67",
                camp=f"Лагерь {i % 3 + 1}",
                status='confirmed',
                reference_number=f"REF-{random_seed}-{i}"
            )
            db.session.add(booking)
            db.session.flush()
            created_bookings.append({
                'id': booking.id,
                'time_slot': booking.time_slot,
                'last_name': booking.last_name,
                'first_name': booking.first_name,
                'phone': booking.phone,
                'service_name': service.name
            })
        
        db.session.commit()
        
        # Get bookings for the date (this is what the print schedule uses)
        schedule_bookings = BookingService.get_bookings_by_date(booking_date)
        
        # Filter only confirmed bookings (as the print route does)
        confirmed_bookings = [b for b in schedule_bookings if b.status == 'confirmed']
        
        # Verify all required fields are present for each booking
        assert len(confirmed_bookings) == num_bookings, \
            f"Expected {num_bookings} bookings in schedule, got {len(confirmed_bookings)}"
        
        for booking in confirmed_bookings:
            # Verify time slot is present and not empty
            assert booking.time_slot is not None, \
                f"Booking {booking.id} missing time_slot"
            assert booking.time_slot != "", \
                f"Booking {booking.id} has empty time_slot"
            
            # Verify last name is present and not empty
            assert booking.last_name is not None, \
                f"Booking {booking.id} missing last_name"
            assert booking.last_name != "", \
                f"Booking {booking.id} has empty last_name"
            
            # Verify first name is present and not empty
            assert booking.first_name is not None, \
                f"Booking {booking.id} missing first_name"
            assert booking.first_name != "", \
                f"Booking {booking.id} has empty first_name"
            
            # Verify phone is present and not empty
            assert booking.phone is not None, \
                f"Booking {booking.id} missing phone"
            assert booking.phone != "", \
                f"Booking {booking.id} has empty phone"
            
            # Verify service relationship exists and has a name
            assert booking.service is not None, \
                f"Booking {booking.id} missing service relationship"
            assert booking.service.name is not None, \
                f"Booking {booking.id} service missing name"
            assert booking.service.name != "", \
                f"Booking {booking.id} service has empty name"
            
            # Verify the values match what we created
            matching_created = [b for b in created_bookings if b['id'] == booking.id]
            assert len(matching_created) == 1, \
                f"Could not find created booking with id {booking.id}"
            
            created = matching_created[0]
            assert booking.time_slot == created['time_slot'], \
                f"Time slot mismatch for booking {booking.id}"
            assert booking.last_name == created['last_name'], \
                f"Last name mismatch for booking {booking.id}"
            assert booking.first_name == created['first_name'], \
                f"First name mismatch for booking {booking.id}"
            assert booking.phone == created['phone'], \
                f"Phone mismatch for booking {booking.id}"
            assert booking.service.name == created['service_name'], \
                f"Service name mismatch for booking {booking.id}"
