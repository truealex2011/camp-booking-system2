"""Background scheduler for sending reminder notifications."""
from datetime import date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app.models import Booking
from app.services.notification_service import NotificationService


def check_upcoming_bookings():
    """Check for bookings 24 hours away and send reminders.
    
    This function runs periodically to find bookings scheduled for tomorrow
    and sends reminder notifications to users.
    """
    try:
        # Calculate tomorrow's date
        tomorrow = date.today() + timedelta(days=1)
        
        # Find all confirmed bookings for tomorrow
        bookings = Booking.query.filter_by(
            date=tomorrow,
            status='confirmed'
        ).all()
        
        print(f"Found {len(bookings)} bookings for {tomorrow}")
        
        # Send reminder for each booking
        for booking in bookings:
            try:
                NotificationService.send_reminder_notification(booking)
                print(f"Sent reminder for booking {booking.reference_number}")
            except Exception as e:
                print(f"Failed to send reminder for {booking.reference_number}: {e}")
                
    except Exception as e:
        print(f"Error in check_upcoming_bookings: {e}")


def init_scheduler(app):
    """Initialize and start the background scheduler.
    
    Args:
        app: Flask application instance
    """
    scheduler = BackgroundScheduler()
    
    # Add job to check for upcoming bookings every hour
    scheduler.add_job(
        func=lambda: app.app_context().push() or check_upcoming_bookings(),
        trigger="interval",
        hours=1,
        id='check_upcoming_bookings',
        name='Check for bookings 24 hours away',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    
    print("Scheduler started - checking for upcoming bookings every hour")
    
    # Shutdown scheduler when app exits
    import atexit
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler
