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
    
    # Create database tables and seed default data
    with app.app_context():
        os.makedirs('/tmp', exist_ok=True)
        db.create_all()
        
        # Seed default admin user if none exist
        from app.models import AdminUser, Service
        if AdminUser.query.count() == 0:
            _seed_default_admin()
        
        # Seed default services if none exist
        if Service.query.count() == 0:
            _seed_default_services()
    
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


def _seed_default_services():
    """Seed default services into database."""
    import json
    from app.models import Service
    
    services_data = [
        {
            'name': 'Получить путевку',
            'description': 'Получение путевки в лагерь',
            'display_order': 1,
            'documents': [
                'Оригинал и копия свидетельства о рождении ребенка (даже если ребенок получил паспорт)',
                'Распечатанная квитанция об оплате (полная, где видны все суммы и реквизиты)',
                'Оригинал паспорта родителя для заполнения договора об оказании услуги летнего отдыха'
            ]
        },
        {
            'name': 'Возврат денежных средств',
            'description': 'Возврат денежных средств за путевку',
            'display_order': 2,
            'documents': [
                'Оригинал путевки',
                'Паспорт родителя',
                'Реквизиты для возврата средств'
            ]
        },
        {
            'name': 'Возврат путевки',
            'description': 'Возврат неиспользованной путевки',
            'display_order': 3,
            'documents': [
                'Оригинал путевки',
                'Паспорт родителя'
            ]
        }
    ]
    
    for service_data in services_data:
        service = Service(
            name=service_data['name'],
            description=service_data['description'],
            display_order=service_data['display_order'],
            required_documents=json.dumps(service_data['documents'], ensure_ascii=False),
            active=True
        )
        db.session.add(service)
    
    db.session.commit()
    print("✓ Default services created")


def _seed_default_admin():
    """Seed default admin user into database."""
    from app.models import AdminUser
    from app.services.auth_service import AuthService
    
    admin_exists = AdminUser.query.filter_by(username='admin').first()
    
    if not admin_exists:
        admin = AuthService.create_admin('admin', 'admin123')
        if admin:
            print("✓ Default admin user created: admin / admin123")
    else:
        print("✓ Admin user already exists")


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
