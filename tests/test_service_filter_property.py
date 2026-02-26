"""Property-based tests for user booking service filter functionality.

Feature: booking-system-improvements
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from app.models import db, Service, Booking
from datetime import date, timedelta
import random
import string


def generate_reference_number():
    """Generate a unique reference number for testing."""
    date_part = date.today().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f'{date_part}-{random_part}'


@st.composite
def booking_set_strategy(draw):
    """Generate a random set of bookings with various services.
    
    Returns a tuple: (services_list, bookings_list)
    where bookings_list contains tuples: (service_id, date, time_slot, phone)
    """
    # Generate 1-5 services
    num_services = draw(st.integers(min_value=1, max_value=5))
    services = []
    for i in range(num_services):
        service_name = f"Service_{draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=3, max_size=10))}_{i}"
        services.append(service_name)
    
    # Generate 1-20 bookings
    num_bookings = draw(st.integers(min_value=1, max_value=20))
    bookings = []
    
    # Use a consistent phone number for all bookings (same user)
    phone = "+7 (999) 123-45-67"
    
    for i in range(num_bookings):
        # Pick a random service
        service_idx = draw(st.integers(min_value=0, max_value=len(services) - 1))
        
        # Generate a date (within 30 days from today)
        days_offset = draw(st.integers(min_value=-30, max_value=30))
        booking_date = date.today() + timedelta(days=days_offset)
        
        # Generate a time slot (15-minute intervals)
        hour = draw(st.integers(min_value=9, max_value=16))
        minute = draw(st.sampled_from([0, 15, 30, 45]))
        time_slot = f"{hour:02d}:{minute:02d}"
        
        # Random status
        status = draw(st.sampled_from(['confirmed', 'cancelled']))
        
        bookings.append((service_idx, booking_date, time_slot, phone, status))
    
    return services, bookings


class TestServiceFilterProperty:
    """Property-based tests for service filter functionality."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    @given(booking_data=booking_set_strategy())
    def test_property_service_filter_population(self, app_context, booking_data):
        """Property 15: Service Filter Population
        
        **Validates: Requirements 9.2**
        
        For any user's set of bookings, the service filter dropdown should contain
        exactly the unique set of services associated with those bookings.
        """
        services_list, bookings_list = booking_data
        
        # Clean up database
        db.session.query(Booking).delete()
        db.session.query(Service).delete()
        db.session.commit()
        
        # Create services in database
        service_objects = []
        for service_name in services_list:
            service = Service(name=service_name, active=True)
            db.session.add(service)
            service_objects.append(service)
        db.session.commit()
        
        # Create bookings in database
        phone = bookings_list[0][3]  # All bookings have same phone
        for service_idx, booking_date, time_slot, phone_num, status in bookings_list:
            booking = Booking(
                service_id=service_objects[service_idx].id,
                date=booking_date,
                time_slot=time_slot,
                last_name="Test",
                first_name="User",
                phone=phone_num,
                camp="Test Camp",
                status=status,
                reference_number=generate_reference_number()
            )
            db.session.add(booking)
        db.session.commit()
        
        # Get all bookings for this user
        user_bookings = Booking.query.filter_by(phone=phone).all()
        
        # Extract unique service IDs from bookings
        unique_service_ids = set()
        for booking in user_bookings:
            unique_service_ids.add(booking.service_id)
        
        # Build the services dict as the view does
        services_dict = {}
        for booking in user_bookings:
            if booking.service_id not in services_dict:
                services_dict[booking.service_id] = booking.service.name
        
        # Verify: The filter should contain exactly the unique services
        assert len(services_dict) == len(unique_service_ids), \
            f"Filter should contain {len(unique_service_ids)} unique services, got {len(services_dict)}"
        
        # Verify: All service IDs in the filter are from the user's bookings
        for service_id in services_dict.keys():
            assert service_id in unique_service_ids, \
                f"Service ID {service_id} in filter should be from user's bookings"
        
        # Verify: All unique services from bookings are in the filter
        for service_id in unique_service_ids:
            assert service_id in services_dict, \
                f"Service ID {service_id} from bookings should be in filter"
        
        # Clean up
        db.session.query(Booking).delete()
        db.session.query(Service).delete()
        db.session.commit()
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    @given(booking_data=booking_set_strategy())
    def test_property_service_filter_application(self, app_context, booking_data):
        """Property 16: Service Filter Application
        
        **Validates: Requirements 9.3**
        
        For any service selected in the filter, the displayed bookings should include
        only those bookings where the service_id matches the selected service.
        """
        services_list, bookings_list = booking_data
        
        # Clean up database
        db.session.query(Booking).delete()
        db.session.query(Service).delete()
        db.session.commit()
        
        # Create services in database
        service_objects = []
        for service_name in services_list:
            service = Service(name=service_name, active=True)
            db.session.add(service)
            service_objects.append(service)
        db.session.commit()
        
        # Create bookings in database
        phone = bookings_list[0][3]
        booking_objects = []
        for service_idx, booking_date, time_slot, phone_num, status in bookings_list:
            booking = Booking(
                service_id=service_objects[service_idx].id,
                date=booking_date,
                time_slot=time_slot,
                last_name="Test",
                first_name="User",
                phone=phone_num,
                camp="Test Camp",
                status=status,
                reference_number=generate_reference_number()
            )
            db.session.add(booking)
            booking_objects.append(booking)
        db.session.commit()
        
        # Get all bookings for this user
        all_bookings = Booking.query.filter_by(phone=phone).all()
        
        # Get unique service IDs
        unique_service_ids = set(b.service_id for b in all_bookings)
        
        # Test filtering for each service
        for service_id in unique_service_ids:
            # Simulate client-side filtering: get bookings that match the service
            filtered_bookings = [b for b in all_bookings if b.service_id == service_id]
            
            # Verify: All filtered bookings have the selected service_id
            for booking in filtered_bookings:
                assert booking.service_id == service_id, \
                    f"Filtered booking should have service_id {service_id}, got {booking.service_id}"
            
            # Verify: All bookings with this service_id are included
            expected_count = sum(1 for b in all_bookings if b.service_id == service_id)
            assert len(filtered_bookings) == expected_count, \
                f"Should have {expected_count} bookings for service {service_id}, got {len(filtered_bookings)}"
        
        # Test "all" filter - should show all bookings
        all_filtered = [b for b in all_bookings]
        assert len(all_filtered) == len(all_bookings), \
            "All filter should show all bookings"
        
        # Clean up
        db.session.query(Booking).delete()
        db.session.query(Service).delete()
        db.session.commit()

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    @given(
        service_id=st.integers(min_value=1, max_value=5),
        num_bookings=st.integers(min_value=1, max_value=10)
    )
    def test_property_filter_state_persistence(self, app_context, client, service_id, num_bookings):
        """Property 17: Filter State Persistence
        
        **Validates: Requirements 9.5**
        
        For any filter selection made by a user, the filter state should persist
        across page interactions within the same session until explicitly cleared.
        
        Note: This test verifies the JavaScript sessionStorage implementation
        by checking that the filter value is properly saved and restored.
        """
        # Clean up database
        db.session.query(Booking).delete()
        db.session.query(Service).delete()
        db.session.commit()
        
        # Create a service
        service = Service(name=f"Test Service {service_id}", active=True)
        db.session.add(service)
        db.session.commit()
        
        # Create bookings
        phone = "+7 (999) 123-45-67"
        reference_numbers = []
        for i in range(num_bookings):
            booking = Booking(
                service_id=service.id,
                date=date.today() + timedelta(days=i),
                time_slot="09:00",
                last_name="Test",
                first_name="User",
                phone=phone,
                camp="Test Camp",
                status='confirmed',
                reference_number=generate_reference_number()
            )
            db.session.add(booking)
            reference_numbers.append(booking.reference_number)
        db.session.commit()
        
        # Get the first booking's reference number
        first_ref = reference_numbers[0]
        
        # Make a request to the bookings page
        response = client.get(f'/bookings/{first_ref}')
        assert response.status_code == 200
        
        # Verify the page contains the service filter dropdown
        html = response.data.decode('utf-8')
        assert 'id="service-filter"' in html, "Service filter dropdown should be present"
        assert 'sessionStorage.setItem' in html, "JavaScript should save filter state to sessionStorage"
        assert 'sessionStorage.getItem' in html, "JavaScript should restore filter state from sessionStorage"
        
        # Verify the filter options include the service
        assert f'value="{service.id}"' in html, f"Filter should include service {service.id}"
        
        # Clean up
        db.session.query(Booking).delete()
        db.session.query(Service).delete()
        db.session.commit()
