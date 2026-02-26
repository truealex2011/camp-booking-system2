"""Flask application factory."""
import os
from flask import Flask
from flask_session import Session
from flask_wtf.csrf import CSRFProtect

from app.models import db
from config import config


csrf = CSRFProtect()
sess = Session()


def create_app(config_name=None):
    """Create and configure the Flask application.
    
    Args:
        config_name: Configuration name ('development', 'production', 'testing')
        
    Returns:
        Flask application instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')
    
    # Ensure config_name is valid
    if config_name not in config:
        config_name = 'production'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    sess.init_app(app)
    
    # Create database tables
    with app.app_context():
        os.makedirs('/tmp', exist_ok=True)
        db.create_all()
    
    # Register blueprints
    from app.routes import public, admin
    app.register_blueprint(public.bp)
    app.register_blueprint(admin.bp, url_prefix='/admin')
    
    # Initialize scheduler for notifications (only in production/development, not testing)
    if config_name != 'testing':
        try:
            from app.scheduler import init_scheduler
            init_scheduler(app)
        except Exception as e:
            print(f"Failed to initialize scheduler: {e}")
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': True, 'message': 'Страница не найдена', 'code': 'NOT_FOUND'}, 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return {'error': True, 'message': 'Доступ запрещен', 'code': 'FORBIDDEN'}, 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': True, 'message': 'Произошла ошибка. Пожалуйста, попробуйте позже.', 'code': 'INTERNAL_ERROR'}, 500
