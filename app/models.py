"""Database models for the camp booking system."""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Service(db.Model):
    """Service model for bookable camp services."""
    
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    required_documents = db.Column(db.Text)  # JSON array as string
    active = db.Column(db.Boolean, default=True, nullable=False)
    display_order = db.Column(db.Integer, default=999)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    bookings = db.relationship('Booking', backref='service', lazy=True)
    
    def __repr__(self):
        return f'<Service {self.name}>'
    
    def to_dict(self):
        """Convert service to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'required_documents': self.required_documents,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Booking(db.Model):
    """Booking model for service reservations."""
    
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='RESTRICT'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(5), nullable=False)  # Format: "HH:MM"
    last_name = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    camp = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='confirmed', nullable=False)  # 'confirmed', 'cancelled'
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_bookings_date', 'date'),
        db.Index('idx_bookings_service', 'service_id'),
        db.Index('idx_bookings_status', 'status'),
        db.Index('idx_bookings_slot', 'date', 'time_slot'),
    )
    
    def __repr__(self):
        return f'<Booking {self.reference_number}>'
    
    def to_dict(self):
        """Convert booking to dictionary."""
        return {
            'id': self.id,
            'service_id': self.service_id,
            'service_name': self.service.name if self.service else None,
            'date': self.date.isoformat() if self.date else None,
            'time_slot': self.time_slot,
            'last_name': self.last_name,
            'first_name': self.first_name,
            'phone': self.phone,
            'camp': self.camp,
            'status': self.status,
            'reference_number': self.reference_number,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AdminUser(db.Model):
    """Admin user model for authentication."""
    
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<AdminUser {self.username}>'


class PushSubscription(db.Model):
    """Stores push notification subscriptions."""
    
    __tablename__ = 'push_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False, unique=True)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh_key = db.Column(db.Text, nullable=False)
    auth_key = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    booking = db.relationship('Booking', backref='push_subscription')
    
    def __repr__(self):
        return f'<PushSubscription {self.id} for Booking {self.booking_id}>'


class Notification(db.Model):
    """Stores notification records for user viewing."""
    
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 'reminder', 'cancellation'
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    sent_at = db.Column(db.DateTime)
    
    # Relationships
    booking = db.relationship('Booking', backref='notifications')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_notifications_booking', 'booking_id'),
        db.Index('idx_notifications_read', 'is_read'),
    )
    
    def __repr__(self):
        return f'<Notification {self.id} for Booking {self.booking_id}>'
    
    def to_dict(self):
        """Convert notification to dictionary."""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }

