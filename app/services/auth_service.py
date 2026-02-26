"""Authentication service for admin users."""
import bcrypt
from flask import session
from app.models import db, AdminUser


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password as string
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            password_hash: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    
    @staticmethod
    def login(username, password):
        """Authenticate a user and create a session.
        
        Args:
            username: Admin username
            password: Admin password
            
        Returns:
            True if authentication successful, False otherwise
        """
        user = AdminUser.query.filter_by(username=username).first()
        
        if user and AuthService.verify_password(password, user.password_hash):
            session['admin_id'] = user.id
            session['admin_username'] = user.username
            session.permanent = True
            return True
        
        return False
    
    @staticmethod
    def logout():
        """Destroy the current admin session."""
        session.pop('admin_id', None)
        session.pop('admin_username', None)
    
    @staticmethod
    def is_authenticated():
        """Check if the current user is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return 'admin_id' in session
    
    @staticmethod
    def get_current_user():
        """Get the currently authenticated admin user.
        
        Returns:
            AdminUser object or None
        """
        if 'admin_id' in session:
            return AdminUser.query.get(session['admin_id'])
        return None
    
    @staticmethod
    def create_admin(username, password):
        """Create a new admin user.
        
        Args:
            username: Admin username
            password: Admin password
            
        Returns:
            AdminUser object or None if username exists
        """
        # Check if username already exists
        existing_user = AdminUser.query.filter_by(username=username).first()
        if existing_user:
            return None
        
        # Create new admin user
        password_hash = AuthService.hash_password(password)
        admin = AdminUser(username=username, password_hash=password_hash)
        
        db.session.add(admin)
        db.session.commit()
        
        return admin
    
    @staticmethod
    def update_password(user_id, new_password):
        """Update an admin user's password.
        
        Args:
            user_id: Admin user ID
            new_password: New password
            
        Returns:
            True if successful, False otherwise
        """
        user = AdminUser.query.get(user_id)
        if not user:
            return False
        
        user.password_hash = AuthService.hash_password(new_password)
        db.session.commit()
        
        return True
