"""Property-based tests for date validation functionality.

Feature: booking-system-improvements
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import date, timedelta
from app.utils.validators import DateValidator


class TestDateValidationProperty:
    """Property-based tests for date validation."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=1000)
    @given(days_ago=st.integers(min_value=1, max_value=365))
    def test_property_past_date_rejection(self, days_ago):
        """Property 2: Past Date Rejection
        
        **Validates: Requirements 2.2**
        
        For any date that is before the current server date, when a user attempts
        to create a booking, the system should reject the booking with the error
        message "Date cannot be in the past".
        """
        # Generate a past date
        past_date = date.today() - timedelta(days=days_ago)
        
        # Validate the past date
        is_valid, error_msg = DateValidator.validate_date(past_date)
        
        # Should be rejected
        assert not is_valid, f"Past date {past_date} should be rejected"
        assert error_msg == "Date cannot be in the past", \
            f"Error message should be 'Date cannot be in the past', got '{error_msg}'"
