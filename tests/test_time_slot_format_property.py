"""Property-based tests for time slot format validation.

Feature: booking-system-improvements
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.utils.validators import TimeSlotValidator


class TestTimeSlotFormatProperty:
    """Property-based tests for time slot format validation."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=1000)
    @given(
        hours=st.integers(min_value=0, max_value=23),
        minutes=st.integers(min_value=0, max_value=59)
    )
    def test_property_time_slot_format_validation(self, hours, minutes):
        """Property 5: Time Slot Format Validation
        
        **Validates: Requirements 4.6**
        
        For any time slot string submitted for booking, the system should only
        accept values in HH:MM format where MM is one of {00, 15, 30, 45}.
        """
        # Generate time slot string
        time_slot = f"{hours:02d}:{minutes:02d}"
        
        # Validate the time slot
        is_valid = TimeSlotValidator.validate_time_slot(time_slot)
        
        # Should only be valid if minutes are 00, 15, 30, or 45
        expected_valid = minutes in [0, 15, 30, 45]
        
        assert is_valid == expected_valid, \
            f"Time slot {time_slot} validation should be {expected_valid}, got {is_valid}"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=1000)
    @given(time_string=st.text(min_size=1, max_size=10))
    def test_property_invalid_format_rejection(self, time_string):
        """Property 5: Time Slot Format Validation - Invalid Formats
        
        **Validates: Requirements 4.6**
        
        For any random string that doesn't match HH:MM format with valid
        15-minute intervals, the system should reject it.
        """
        # Skip strings that happen to be valid time slots
        if len(time_string) == 5 and time_string[2] == ':':
            try:
                hours, minutes = map(int, time_string.split(':'))
                if 0 <= hours < 24 and minutes in [0, 15, 30, 45]:
                    return  # Skip valid time slots
            except (ValueError, IndexError):
                pass
        
        # Validate the time string
        is_valid = TimeSlotValidator.validate_time_slot(time_string)
        
        # Should be invalid for random strings
        assert not is_valid, \
            f"Random string '{time_string}' should be rejected as invalid time slot"
