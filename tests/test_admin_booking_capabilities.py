"""Tests for admin booking capabilities (Requirement 7)."""
import pytest
from datetime import date, timedelta
from app.models import db, Service, Booking, AdminUser
from app.services.booking_service import BookingService
from app.services.auth_service import AuthService


@pytest.fixture
def admin_user(app_context):
    """Create an admin user for testing."""
    admin = AuthService.create_admin('testadmin', 'testpass123')
    return admin


@pytest.fixture
def test_service(app_context):
    """Create a test service."""
    service = Service(
        name='Test Service',
        description='Test Description',
        active=True
    )
    db.session.add(service)
    db.session.commit()
    return service


@pytest.fixture
def test_booking(app_context, test_service):
    """Create a test booking."""
    booking = Booking(
        service_id=test_service.id,
        date=date.today() + timedelta(days=1),
        time_slot='10:00',
        last_name='Иванов',
        first_name='Иван',
        phone='+7 (999) 123-45-67',
        camp='Лагерь 1',
        status='confirmed',
        reference_number='TEST123456'
    )
    db.session.add(booking)
    db.session.commit()
    return booking


def test_admin_can_cancel_bookings(app_context, test_booking):
    """
    Test that admin can cancel bookings.
    
    Validates: Requirements 7.3
    """
    # Verify booking is initially confirmed
    assert test_booking.status == 'confirmed'
    
    # Admin cancels the booking
    result = BookingService.cancel_booking(test_booking.id)
    
    # Verify cancellation was successful
    assert result is True
    
    # Verify booking status is now cancelled
    db.session.refresh(test_booking)
    assert test_booking.status == 'cancelled'


def test_admin_can_view_all_booking_details(app_context, test_booking):
    """
    Test that admin can view all booking details.
    
    Validates: Requirements 7.4
    """
    # Retrieve booking by ID
    booking = Booking.query.get(test_booking.id)
    
    # Verify all booking details are accessible
    assert booking is not None
    assert booking.reference_number == 'TEST123456'
    assert booking.date == date.today() + timedelta(days=1)
    assert booking.time_slot == '10:00'
    assert booking.last_name == 'Иванов'
    assert booking.first_name == 'Иван'
    assert booking.phone == '+7 (999) 123-45-67'
    assert booking.camp == 'Лагерь 1'
    assert booking.status == 'confirmed'
    assert booking.service_id == test_booking.service_id


def test_admin_cannot_edit_bookings_via_route(client, admin_user, test_booking):
    """
    Test that admin cannot edit bookings through the update route.
    
    Validates: Requirements 7.1
    """
    # Login as admin
    with client.session_transaction() as sess:
        sess['admin_id'] = admin_user.id
        sess['admin_username'] = admin_user.username
    
    # Attempt to access the update route (should not exist)
    response = client.post(
        f'/admin/bookings/{test_booking.id}/update',
        data={
            'date': '2024-12-31',
            'time_slot': '11:00',
            'last_name': 'Петров',
            'first_name': 'Петр',
            'phone': '+7 (999) 999-99-99',
            'camp': 'Лагерь 2'
        },
        follow_redirects=False
    )
    
    # Verify the route returns 404 (not found)
    assert response.status_code == 404
    
    # Verify booking was not modified
    db.session.refresh(test_booking)
    assert test_booking.last_name == 'Иванов'
    assert test_booking.first_name == 'Иван'
    assert test_booking.time_slot == '10:00'


def test_admin_bookings_page_has_no_edit_buttons(client, admin_user, test_booking):
    """
    Test that the admin bookings page does not display edit buttons.
    
    Validates: Requirements 7.1, 7.2
    """
    # Login as admin
    with client.session_transaction() as sess:
        sess['admin_id'] = admin_user.id
        sess['admin_username'] = admin_user.username
    
    # Access the bookings page
    response = client.get('/admin/bookings')
    
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    
    # Verify no edit button exists (the pencil emoji was used for edit)
    assert '✏️' not in html
    assert 'showEditForm' not in html
    assert 'Редактировать' not in html
    
    # Verify cancel button still exists
    assert '❌' in html
    assert 'Отменить' in html


def test_admin_can_view_booking_details_read_only(client, admin_user, test_booking):
    """
    Test that admin can view booking details in read-only mode.
    
    Validates: Requirements 7.2
    """
    # Login as admin
    with client.session_transaction() as sess:
        sess['admin_id'] = admin_user.id
        sess['admin_username'] = admin_user.username
    
    # Access the bookings page
    response = client.get('/admin/bookings')
    
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    
    # Verify booking details are displayed
    assert test_booking.reference_number in html
    assert 'Иванов' in html
    assert 'Иван' in html
    assert test_booking.phone in html
    assert test_booking.camp in html
    assert test_booking.time_slot in html


def test_admin_cancel_nonexistent_booking(app_context):
    """
    Test that cancelling a non-existent booking returns False.
    
    Validates: Requirements 7.3
    """
    # Attempt to cancel a booking that doesn't exist
    result = BookingService.cancel_booking(99999)
    
    # Verify cancellation failed
    assert result is False


def test_admin_can_cancel_only_confirmed_bookings(app_context, test_booking):
    """
    Test that admin can cancel confirmed bookings and the operation is idempotent.
    
    Validates: Requirements 7.3
    """
    # Cancel the booking
    result = BookingService.cancel_booking(test_booking.id)
    assert result is True
    
    db.session.refresh(test_booking)
    assert test_booking.status == 'cancelled'
    
    # Attempt to cancel again (should still succeed but no change)
    result = BookingService.cancel_booking(test_booking.id)
    assert result is True
    
    db.session.refresh(test_booking)
    assert test_booking.status == 'cancelled'


def test_admin_can_view_cancelled_bookings(app_context, test_booking):
    """
    Test that admin can view cancelled bookings.
    
    Validates: Requirements 7.4
    """
    # Cancel the booking
    BookingService.cancel_booking(test_booking.id)
    
    # Retrieve the booking
    booking = Booking.query.get(test_booking.id)
    
    # Verify all details are still accessible
    assert booking is not None
    assert booking.status == 'cancelled'
    assert booking.reference_number == 'TEST123456'
    assert booking.last_name == 'Иванов'


def test_admin_can_filter_and_view_bookings(client, admin_user, test_service, test_booking):
    """
    Test that admin can filter and view bookings by various criteria.
    
    Validates: Requirements 7.4
    """
    # Login as admin
    with client.session_transaction() as sess:
        sess['admin_id'] = admin_user.id
        sess['admin_username'] = admin_user.username
    
    # Filter by service
    response = client.get(f'/admin/bookings?service_id={test_service.id}')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert test_booking.reference_number in html
    
    # Filter by date
    booking_date = test_booking.date.strftime('%Y-%m-%d')
    response = client.get(f'/admin/bookings?date={booking_date}')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert test_booking.reference_number in html
    
    # Filter by status
    response = client.get('/admin/bookings?status=confirmed')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert test_booking.reference_number in html
