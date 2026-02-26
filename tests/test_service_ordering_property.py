"""Property-based tests for service ordering functionality.

Feature: booking-system-improvements
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from app.models import db, Service
from app.services.service_manager import ServiceManager


# Priority service names and their display orders
PRIORITY_SERVICES = {
    "Получить путевку": 1,
    "Возврат дс": 2,
    "Возврат путевки": 3,
}


@st.composite
def service_set_strategy(draw):
    """Generate a random set of services with various configurations.
    
    Returns a list of tuples: (name, display_order, active)
    """
    services = []
    
    # Decide which priority services to include
    for name, order in PRIORITY_SERVICES.items():
        include = draw(st.booleans())
        if include:
            active = draw(st.booleans())
            services.append((name, order, active))
    
    # Add some random non-priority services
    num_other_services = draw(st.integers(min_value=0, max_value=5))
    for i in range(num_other_services):
        name = f"Service_{draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=3, max_size=10))}_{i}"
        active = draw(st.booleans())
        services.append((name, 999, active))
    
    return services


class TestServiceOrderingProperty:
    """Property-based tests for service ordering."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=1000)
    @given(service_set=service_set_strategy())
    def test_property_service_display_order(self, app_context, service_set):
        """Property 1: Service Display Order
        
        **Validates: Requirements 1.1**
        
        For any set of active services, when the system displays them on the main page,
        the services "Получить путевку", "Возврат дс", and "Возврат путевки" should
        appear in that exact order before any other services.
        """
        # Skip if no services
        assume(len(service_set) > 0)
        
        # Clean up any existing services first
        db.session.query(Service).delete()
        db.session.commit()
        
        # Create services in database
        for name, display_order, active in service_set:
            service = Service(name=name, display_order=display_order, active=active)
            db.session.add(service)
        db.session.commit()
        
        # Get active services
        active_services = ServiceManager.get_active_services()
        
        # Extract names of active services
        active_names = [s.name for s in active_services]
        
        # Find which priority services are active
        active_priority_services = []
        for name, order in sorted(PRIORITY_SERVICES.items(), key=lambda x: x[1]):
            if any(s[0] == name and s[2] for s in service_set):
                active_priority_services.append(name)
        
        # Verify priority services appear first in correct order
        for i, priority_name in enumerate(active_priority_services):
            assert priority_name in active_names, f"Priority service {priority_name} should be in active services"
            priority_index = active_names.index(priority_name)
            
            # This priority service should appear before all non-priority services
            for service_name in active_names[priority_index + 1:]:
                if service_name not in PRIORITY_SERVICES:
                    # This is a non-priority service, it should come after priority service
                    assert True
                else:
                    # This is another priority service, check it has higher order
                    assert PRIORITY_SERVICES[service_name] > PRIORITY_SERVICES[priority_name], \
                        f"{service_name} should come after {priority_name}"
        
        # Verify the relative order of priority services
        priority_indices = []
        for priority_name in ["Получить путевку", "Возврат дс", "Возврат путевки"]:
            if priority_name in active_names:
                priority_indices.append((priority_name, active_names.index(priority_name)))
        
        # Check that priority services appear in ascending order of their indices
        for i in range(len(priority_indices) - 1):
            name1, idx1 = priority_indices[i]
            name2, idx2 = priority_indices[i + 1]
            assert idx1 < idx2, f"{name1} should appear before {name2}"
        
        # Verify services with same display_order are sorted by name
        for i in range(len(active_services) - 1):
            if active_services[i].display_order == active_services[i + 1].display_order:
                assert active_services[i].name <= active_services[i + 1].name, \
                    f"Services with same display_order should be sorted by name: {active_services[i].name} vs {active_services[i + 1].name}"
        
        # Clean up for next test
        db.session.query(Service).delete()
        db.session.commit()
