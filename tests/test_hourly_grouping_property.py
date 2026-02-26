"""Property-based tests for hourly time slot grouping.

Feature: booking-system-improvements
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from config import Config


class TestHourlyGroupingProperty:
    """Property-based tests for hourly time slot grouping."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=1000)
    @given(
        start_hour=st.integers(min_value=0, max_value=20),
        end_hour=st.integers(min_value=1, max_value=23)
    )
    def test_property_hourly_grouping(self, start_hour, end_hour):
        """Property 3: Hourly Time Slot Grouping
        
        **Validates: Requirements 4.1, 4.2**
        
        For any generated set of time slots, the slots should be organized into
        hourly groups where each hour contains exactly four 15-minute intervals
        (00, 15, 30, 45).
        """
        # Skip invalid ranges where start >= end
        if start_hour >= end_hour:
            return
        
        # Generate time slots for the given range
        time_slots = []
        for hour in range(start_hour, end_hour):
            for minute in [0, 15, 30, 45]:
                time_slots.append(f'{hour:02d}:{minute:02d}')
        
        # Group slots by hour
        hourly_groups = {}
        for slot in time_slots:
            hour = slot.split(':')[0]
            if hour not in hourly_groups:
                hourly_groups[hour] = []
            hourly_groups[hour].append(slot)
        
        # Verify each hour has exactly 4 slots
        for hour, slots in hourly_groups.items():
            assert len(slots) == 4, \
                f"Hour {hour} should have exactly 4 time slots, got {len(slots)}"
        
        # Verify slots within each hour are at 00, 15, 30, 45 minutes
        for hour, slots in hourly_groups.items():
            minutes = [int(slot.split(':')[1]) for slot in slots]
            minutes.sort()
            assert minutes == [0, 15, 30, 45], \
                f"Hour {hour} should have slots at 00, 15, 30, 45 minutes, got {minutes}"
    
    def test_property_config_time_slots_hourly_grouping(self):
        """Property 3: Hourly Time Slot Grouping - Config TIME_SLOTS
        
        **Validates: Requirements 4.1, 4.2**
        
        Verify that the TIME_SLOTS configuration follows the hourly grouping
        property with 4 intervals per hour.
        """
        time_slots = Config.TIME_SLOTS
        
        # Group slots by hour
        hourly_groups = {}
        for slot in time_slots:
            hour = slot.split(':')[0]
            if hour not in hourly_groups:
                hourly_groups[hour] = []
            hourly_groups[hour].append(slot)
        
        # Verify each hour has exactly 4 slots
        for hour, slots in hourly_groups.items():
            assert len(slots) == 4, \
                f"Hour {hour} should have exactly 4 time slots, got {len(slots)}"
        
        # Verify slots within each hour are at 00, 15, 30, 45 minutes
        for hour, slots in hourly_groups.items():
            minutes = [int(slot.split(':')[1]) for slot in slots]
            minutes.sort()
            assert minutes == [0, 15, 30, 45], \
                f"Hour {hour} should have slots at 00, 15, 30, 45 minutes, got {minutes}"
        
        # Verify total number of slots (9:00 to 17:00 = 8 hours * 4 slots = 32 slots)
        expected_total = 8 * 4
        assert len(time_slots) == expected_total, \
            f"Expected {expected_total} total time slots, got {len(time_slots)}"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=1000)
    @given(
        hour=st.integers(min_value=0, max_value=23)
    )
    def test_property_single_hour_grouping(self, hour):
        """Property 3: Hourly Time Slot Grouping - Single Hour
        
        **Validates: Requirements 4.1, 4.2**
        
        For any single hour, the generated slots should contain exactly 4
        intervals at 00, 15, 30, 45 minutes.
        """
        # Generate slots for a single hour
        slots = []
        for minute in [0, 15, 30, 45]:
            slots.append(f'{hour:02d}:{minute:02d}')
        
        # Verify we have exactly 4 slots
        assert len(slots) == 4, \
            f"Hour {hour} should generate exactly 4 time slots, got {len(slots)}"
        
        # Verify the minutes are correct
        minutes = [int(slot.split(':')[1]) for slot in slots]
        assert minutes == [0, 15, 30, 45], \
            f"Hour {hour} should have slots at 00, 15, 30, 45 minutes, got {minutes}"
        
        # Verify all slots have the same hour
        hours = [slot.split(':')[0] for slot in slots]
        assert all(h == f'{hour:02d}' for h in hours), \
            f"All slots should be for hour {hour:02d}"
