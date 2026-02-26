"""Public user-facing routes."""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, flash
from datetime import datetime, timedelta, date
from app.services.service_manager import ServiceManager
from app.services.booking_service import BookingService
from flask import current_app
from app import csrf

bp = Blueprint('public', __name__)


@bp.route('/')
def index():
    """Main page - service selection."""
    services = ServiceManager.get_active_services()
    return render_template('public/index.html', services=services)


@bp.route('/calendar/<int:service_id>')
def calendar(service_id):
    """Calendar page - date and time selection."""
    service = ServiceManager.get_service_by_id(service_id)
    
    if not service or not service.active:
        flash('Услуга не найдена или недоступна', 'error')
        return redirect(url_for('public.index'))
    
    # Store service_id in session
    session['selected_service_id'] = service_id
    
    time_slots = current_app.config['TIME_SLOTS']
    camps = current_app.config['CAMPS']
    
    return render_template('public/calendar.html', service=service, time_slots=time_slots, camps=camps)


@bp.route('/api/slots')
def get_slots():
    """API endpoint to get available slots for a date."""
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({'error': 'Date parameter required'}), 400
    
    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Check if date is valid
    if booking_date < date.today():
        return jsonify({'error': 'Date cannot be in the past'}), 400
    
    max_date = date.today() + timedelta(days=current_app.config['CALENDAR_DAYS_AHEAD'])
    if booking_date > max_date:
        return jsonify({'error': 'Date is too far in the future'}), 400
    
    time_slots = current_app.config['TIME_SLOTS']
    max_bookings = current_app.config['MAX_BOOKINGS_PER_SLOT']
    
    # Get availability for each slot
    slots_data = []
    for slot in time_slots:
        count = BookingService.get_slot_count(booking_date, slot)
        slots_data.append({
            'time': slot,
            'available': count < max_bookings,
            'count': count,
            'max': max_bookings
        })
    
    return jsonify({'slots': slots_data})


@bp.route('/booking', methods=['POST'])
def create_booking():
    """Create a new booking."""
    # Get form data
    service_id = session.get('selected_service_id')
    if not service_id:
        return jsonify({'error': True, 'message': 'Услуга не выбрана'}), 400
    
    date_str = request.form.get('date')
    time_slot = request.form.get('time_slot')
    last_name = request.form.get('last_name')
    first_name = request.form.get('first_name')
    phone = request.form.get('phone')
    camp = request.form.get('camp')
    
    # Validate required fields
    if not all([date_str, time_slot, last_name, first_name, phone, camp]):
        return jsonify({
            'error': True,
            'message': 'Все поля обязательны для заполнения',
            'field_errors': {}
        }), 400
    
    # Parse date
    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': True, 'message': 'Неверный формат даты'}), 400
    
    # Create booking
    valid_camps = current_app.config['CAMPS']
    max_bookings = current_app.config['MAX_BOOKINGS_PER_SLOT']
    
    booking, errors = BookingService.create_booking(
        service_id=service_id,
        booking_date=booking_date,
        time_slot=time_slot,
        last_name=last_name,
        first_name=first_name,
        phone=phone,
        camp=camp,
        valid_camps=valid_camps,
        max_bookings=max_bookings
    )
    
    if errors:
        return jsonify({
            'error': True,
            'message': 'Пожалуйста, проверьте правильность введенных данных',
            'field_errors': errors
        }), 400
    
    # Clear session
    session.pop('selected_service_id', None)
    
    # Return success with reference number
    return jsonify({
        'success': True,
        'reference_number': booking.reference_number,
        'redirect_url': url_for('public.confirmation', reference_number=booking.reference_number)
    })


@bp.route('/confirmation/<reference_number>')
def confirmation(reference_number):
    """Booking confirmation page."""
    booking = BookingService.get_booking_by_reference(reference_number)
    
    if not booking:
        flash('Бронирование не найдено', 'error')
        return redirect(url_for('public.index'))
    
    # Get required documents for the service
    required_documents = ServiceManager.get_required_documents(booking.service_id)
    if not required_documents:
        required_documents = current_app.config['REQUIRED_DOCUMENTS']
    
    return render_template('public/confirmation.html', booking=booking, required_documents=required_documents)


@bp.route('/bookings/<reference_number>')
def my_bookings(reference_number):
    """User bookings view page."""
    # Get the first booking by reference number to identify the user
    booking = BookingService.get_booking_by_reference(reference_number)
    
    if not booking:
        flash('Бронирование не найдено', 'error')
        return redirect(url_for('public.index'))
    
    # Get all bookings for this user (by phone number)
    from app.models import Booking
    bookings = Booking.query.filter_by(phone=booking.phone).order_by(Booking.date.desc(), Booking.time_slot).all()
    
    # Get unique services for filter
    services = {}
    for b in bookings:
        if b.service_id not in services:
            services[b.service_id] = b.service.name
    
    return render_template('public/my_bookings.html', bookings=bookings, services=services, reference_number=reference_number)


@bp.route('/notifications/<phone>')
def notifications(phone):
    """User notifications page."""
    # Verify phone belongs to a real booking
    from app.models import Booking
    booking = Booking.query.filter_by(phone=phone).first()
    
    if not booking:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('public.index'))
    
    return render_template('public/notifications.html', phone=phone)


# Notification API endpoints

@bp.route('/api/subscribe', methods=['POST'])
def subscribe_push():
    """Save push notification subscription."""
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        subscription = data.get('subscription')
        
        if not booking_id or not subscription:
            return jsonify({'success': False, 'message': 'Missing data'}), 400
        
        from app.services.notification_service import NotificationService
        result = NotificationService.save_subscription(booking_id, subscription)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Failed to save subscription'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/notifications/<phone>', methods=['GET'])
def get_notifications(phone):
    """Get notifications for a user by phone number."""
    try:
        from app.services.notification_service import NotificationService
        notifications = NotificationService.get_user_notifications(phone)
        
        return jsonify({
            'success': True,
            'notifications': [n.to_dict() for n in notifications]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@csrf.exempt
def mark_notification_read(notification_id):
    """Mark notification as read."""
    try:
        print(f"Marking notification {notification_id} as read")
        from app.services.notification_service import NotificationService
        result = NotificationService.mark_notification_read(notification_id)
        
        print(f"Result: {result}")
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Notification not found'}), 404
            
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/notifications/<phone>/unread-count', methods=['GET'])
def get_unread_count(phone):
    """Get count of unread notifications for a user."""
    try:
        from app.services.notification_service import NotificationService
        count = NotificationService.get_unread_count(phone)
        
        return jsonify({
            'success': True,
            'count': count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
