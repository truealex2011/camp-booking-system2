"""Validation utilities for form inputs."""
import re
from datetime import date, datetime


class PhoneValidator:
    """Validator and formatter for phone numbers."""
    
    PHONE_PATTERN = re.compile(r'^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$')
    DIGITS_PATTERN = re.compile(r'\d')
    
    @staticmethod
    def format_phone(phone):
        """Format phone number to +7 (XXX) XXX-XX-XX.
        
        Args:
            phone: Phone number string (can be any format)
            
        Returns:
            Formatted phone number or None if invalid
        """
        # Extract only digits
        digits = ''.join(PhoneValidator.DIGITS_PATTERN.findall(phone))
        
        # Remove leading 7 or 8 if present
        if digits.startswith('7') or digits.startswith('8'):
            digits = digits[1:]
        
        # Check if we have exactly 10 digits
        if len(digits) != 10:
            return None
        
        # Format as +7 (XXX) XXX-XX-XX
        return f'+7 ({digits[0:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:10]}'
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format.
        
        Args:
            phone: Phone number string
            
        Returns:
            True if valid, False otherwise
        """
        if not phone:
            return False
        
        # Check if already in correct format
        if PhoneValidator.PHONE_PATTERN.match(phone):
            return True
        
        # Try to format and check if successful
        formatted = PhoneValidator.format_phone(phone)
        return formatted is not None


class DateValidator:
    """Validator for dates."""
    
    @staticmethod
    def validate_date(date_value, allow_past=False):
        """Validate that date is not in the past.
        
        Args:
            date_value: Date object or string (YYYY-MM-DD)
            allow_past: Whether to allow past dates
            
        Returns:
            tuple: (is_valid, error_message) where is_valid is bool and error_message is str or None
        """
        if isinstance(date_value, str):
            try:
                date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
            except ValueError:
                return (False, "Invalid date format")
        
        if not isinstance(date_value, date):
            return (False, "Invalid date format")
        
        if not allow_past and date_value < date.today():
            return (False, "Date cannot be in the past")
        
        return (True, None)
    
    @staticmethod
    def validate_date_range(date_value, max_days_ahead=30):
        """Validate that date is within allowed range.
        
        Args:
            date_value: Date object
            max_days_ahead: Maximum days in the future
            
        Returns:
            True if valid, False otherwise
        """
        is_valid, _ = DateValidator.validate_date(date_value)
        if not is_valid:
            return False
        
        from datetime import timedelta
        max_date = date.today() + timedelta(days=max_days_ahead)
        
        return date_value <= max_date


class TimeSlotValidator:
    """Validator for time slots."""
    
    TIME_PATTERN = re.compile(r'^\d{2}:\d{2}$')
    
    @staticmethod
    def validate_time_slot(time_slot):
        """Validate time slot format (HH:MM) with 15-minute intervals.
        
        Args:
            time_slot: Time slot string
            
        Returns:
            True if valid, False otherwise
        """
        if not time_slot or not TimeSlotValidator.TIME_PATTERN.match(time_slot):
            return False
        
        try:
            hours, minutes = map(int, time_slot.split(':'))
            # Validate hours are in valid range
            if not (0 <= hours < 24):
                return False
            # Validate minutes are on 15-minute intervals (00, 15, 30, 45)
            if minutes not in [0, 15, 30, 45]:
                return False
            return True
        except ValueError:
            return False


class NameValidator:
    """Validator for names (Cyrillic only)."""
    
    CYRILLIC_PATTERN = re.compile(r'^[А-Яа-яЁё\s\-]+$')
    
    @staticmethod
    def validate_name(name, min_length=2, max_length=50):
        """Validate name (Cyrillic letters only).
        
        Args:
            name: Name string
            min_length: Minimum length
            max_length: Maximum length
            
        Returns:
            True if valid, False otherwise
        """
        if not name:
            return False
        
        name = name.strip()
        
        if len(name) < min_length or len(name) > max_length:
            return False
        
        return bool(NameValidator.CYRILLIC_PATTERN.match(name))


class CampValidator:
    """Validator for camp selection."""
    
    @staticmethod
    def validate_camp(camp, valid_camps):
        """Validate camp selection.
        
        Args:
            camp: Camp name string
            valid_camps: List of valid camp names
            
        Returns:
            True if valid, False otherwise
        """
        return camp in valid_camps
