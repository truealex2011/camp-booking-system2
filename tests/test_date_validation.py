"""Unit tests for date validation functionality."""
import pytest
from datetime import date, timedelta
from app.utils.validators import DateValidator


class TestDateValidation:
    """Test date validation edge cases."""
    
    def test_current_date_acceptance(self):
        """Test that today's date passes validation.
        
        Requirements: 2.1
        """
        today = date.today()
        
        # Validate today's date
        is_valid, error_msg = DateValidator.validate_date(today)
        
        # Should be accepted
        assert is_valid, f"Current date {today} should be accepted"
        assert error_msg is None, f"Error message should be None for valid date, got '{error_msg}'"
    
    def test_future_date_acceptance(self):
        """Test that future dates pass validation."""
        tomorrow = date.today() + timedelta(days=1)
        next_week = date.today() + timedelta(days=7)
        
        # Validate future dates
        is_valid_tomorrow, error_msg_tomorrow = DateValidator.validate_date(tomorrow)
        is_valid_next_week, error_msg_next_week = DateValidator.validate_date(next_week)
        
        # Should be accepted
        assert is_valid_tomorrow, f"Future date {tomorrow} should be accepted"
        assert error_msg_tomorrow is None
        assert is_valid_next_week, f"Future date {next_week} should be accepted"
        assert error_msg_next_week is None
    
    def test_yesterday_rejection(self):
        """Test that yesterday's date is rejected.
        
        Requirements: 2.2
        """
        yesterday = date.today() - timedelta(days=1)
        
        # Validate yesterday's date
        is_valid, error_msg = DateValidator.validate_date(yesterday)
        
        # Should be rejected
        assert not is_valid, f"Yesterday's date {yesterday} should be rejected"
        assert error_msg == "Date cannot be in the past"
    
    def test_string_date_format(self):
        """Test validation with string date format."""
        today_str = date.today().strftime('%Y-%m-%d')
        
        # Validate string date
        is_valid, error_msg = DateValidator.validate_date(today_str)
        
        # Should be accepted
        assert is_valid, f"Current date string {today_str} should be accepted"
        assert error_msg is None
    
    def test_invalid_date_format(self):
        """Test validation with invalid date format."""
        invalid_dates = [
            "2024-13-01",  # Invalid month
            "2024-02-30",  # Invalid day
            "not-a-date",  # Invalid format
            "01/01/2024",  # Wrong format
        ]
        
        for invalid_date in invalid_dates:
            is_valid, error_msg = DateValidator.validate_date(invalid_date)
            assert not is_valid, f"Invalid date {invalid_date} should be rejected"
            assert error_msg == "Invalid date format"
    
    def test_allow_past_parameter(self):
        """Test that allow_past parameter works correctly."""
        yesterday = date.today() - timedelta(days=1)
        
        # With allow_past=True
        is_valid, error_msg = DateValidator.validate_date(yesterday, allow_past=True)
        assert is_valid, "Past date should be accepted when allow_past=True"
        assert error_msg is None
        
        # With allow_past=False (default)
        is_valid, error_msg = DateValidator.validate_date(yesterday, allow_past=False)
        assert not is_valid, "Past date should be rejected when allow_past=False"
        assert error_msg == "Date cannot be in the past"
