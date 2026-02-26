"""Custom decorators for the application."""
from functools import wraps
from flask import redirect, url_for, flash
from app.services.auth_service import AuthService


def login_required(f):
    """Decorator to require admin authentication for a route.
    
    Usage:
        @app.route('/admin/dashboard')
        @login_required
        def dashboard():
            return render_template('admin/dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_authenticated():
            flash('Пожалуйста, войдите в систему для доступа к этой странице.', 'warning')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function
