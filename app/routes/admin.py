"""Admin routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import date, datetime
from app.services.auth_service import AuthService
from app.services.service_manager import ServiceManager
from app.services.booking_service import BookingService
from app.utils.decorators import login_required
from flask import current_app

bp = Blueprint('admin', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if AuthService.login(username, password):
            flash('Вход выполнен успешно', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('admin/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Admin logout."""
    AuthService.logout()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('admin.login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard."""
    # Get today's bookings count
    todays_bookings = BookingService.get_todays_bookings()
    
    # Get total statistics
    stats = BookingService.get_statistics()
    
    return render_template('admin/dashboard.html', 
                         todays_count=len(todays_bookings),
                         stats=stats,
                         date=date)


@bp.route('/services')
@login_required
def services():
    """Service management page."""
    all_services = ServiceManager.get_all_services()
    return render_template('admin/services.html', services=all_services)


@bp.route('/services/create', methods=['POST'])
@login_required
def create_service():
    """Create a new service."""
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    if not name:
        flash('Название услуги обязательно', 'error')
        return redirect(url_for('admin.services'))
    
    service = ServiceManager.create_service(name, description)
    
    if service:
        flash('Услуга создана успешно', 'success')
    else:
        flash('Услуга с таким названием уже существует', 'error')
    
    return redirect(url_for('admin.services'))


@bp.route('/services/<int:service_id>/toggle', methods=['POST'])
@login_required
def toggle_service(service_id):
    """Toggle service active status."""
    if ServiceManager.toggle_service_status(service_id):
        flash('Статус услуги изменен', 'success')
    else:
        flash('Услуга не найдена', 'error')
    
    return redirect(url_for('admin.services'))


@bp.route('/services/<int:service_id>/delete', methods=['POST'])
@login_required
def delete_service(service_id):
    """Delete a service."""
    if not ServiceManager.can_delete_service(service_id):
        flash('Невозможно удалить услугу с существующими бронированиями', 'error')
    elif ServiceManager.delete_service(service_id):
        flash('Услуга удалена', 'success')
    else:
        flash('Услуга не найдена', 'error')
    
    return redirect(url_for('admin.services'))


@bp.route('/bookings')
@login_required
def bookings():
    """Booking management page."""
    # Get filter parameters
    service_id = request.args.get('service_id', type=int)
    date_str = request.args.get('date')
    camp = request.args.get('camp')
    status = request.args.get('status')
    
    # Parse date if provided
    booking_date = None
    if date_str:
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Get filtered bookings
    all_bookings = BookingService.get_bookings_by_filter(
        service_id=service_id,
        booking_date=booking_date,
        camp=camp,
        status=status
    )
    
    # Get all services for filter dropdown
    all_services = ServiceManager.get_all_services()
    camps = current_app.config['CAMPS']
    
    return render_template('admin/bookings.html', 
                         bookings=all_bookings,
                         services=all_services,
                         camps=camps,
                         filters={
                             'service_id': service_id,
                             'date': date_str,
                             'camp': camp,
                             'status': status
                         })


@bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Cancel a booking."""
    if BookingService.cancel_booking(booking_id, cancelled_by_admin=True):
        flash('Бронирование отменено', 'success')
    else:
        flash('Бронирование не найдено', 'error')
    
    return redirect(url_for('admin.bookings'))


@bp.route('/schedule/print')
@login_required
def print_schedule():
    """Print schedule for a selected date."""
    # Get date parameter from query string, default to today
    date_str = request.args.get('date')
    
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    # Get bookings for the selected date
    bookings = BookingService.get_bookings_by_date(selected_date)
    # Filter only confirmed bookings
    confirmed_bookings = [b for b in bookings if b.status == 'confirmed']
    
    return render_template('admin/print_schedule.html', 
                         bookings=confirmed_bookings,
                         date=selected_date,
                         datetime=datetime)


@bp.route('/statistics')
@login_required
def statistics():
    """Statistics page."""
    # Get date range from query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    stats = BookingService.get_statistics(start_date, end_date)
    
    return render_template('admin/statistics.html', 
                         stats=stats,
                         start_date=start_date,
                         end_date=end_date)
