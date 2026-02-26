"""Application configuration."""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load VAPID keys from .env.vapid file
vapid_env_path = os.path.join(os.path.dirname(__file__), '.env.vapid')
if os.path.exists(vapid_env_path):
    load_dotenv(vapid_env_path)


class Config:
    """Base configuration."""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # VAPID keys for push notifications
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')
    VAPID_CLAIMS_EMAIL = os.environ.get('VAPID_CLAIMS_EMAIL', 'mailto:admin@example.com')
    
    # Database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:////tmp/database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Booking settings
    MAX_BOOKINGS_PER_SLOT = 2
    CALENDAR_DAYS_AHEAD = 30
    
    # Generate 15-minute time slots from 9:00 to 17:00
    TIME_SLOTS = []
    for hour in range(9, 17):
        for minute in [0, 15, 30, 45]:
            TIME_SLOTS.append(f'{hour:02d}:{minute:02d}')
    
    # Camp options
    CAMPS = [
        'Таежный 6 – Республика Чародеев',
        'Таежный 9 – Дружный',
        'Таежный 10 – Звездный'
    ]
    
    # Required documents
    REQUIRED_DOCUMENTS = [
        'Оригинал и копия свидетельства о рождении ребенка (даже если ребенок получил паспорт)',
        'Распечатанная квитанция об оплате (полная, где видны все суммы и реквизиты)',
        'Оригинал паспорта родителя для заполнения договора об оказании услуги летнего отдыха'
    ]


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    # Ensure these are set in production
    def __init__(self):
        super().__init__()
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production")


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
