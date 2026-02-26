"""Unit tests for service ordering functionality."""
import pytest
from app.models import db, Service
from app.services.service_manager import ServiceManager


class TestServiceOrdering:
    """Test service ordering edge cases."""
    
    def test_with_inactive_priority_services(self, app_context):
        """Test ordering with inactive priority services.
        
        Requirements: 1.3
        """
        # Create priority services with one inactive
        service1 = Service(name="Test Получить путевку", display_order=1, active=False)
        service2 = Service(name="Test Возврат дс", display_order=2, active=True)
        service3 = Service(name="Test Возврат путевки", display_order=3, active=True)
        service4 = Service(name="Test Other Service", display_order=999, active=True)
        
        db.session.add_all([service1, service2, service3, service4])
        db.session.commit()
        
        # Get active services
        services = ServiceManager.get_active_services()
        
        # Should skip inactive service1 and show service2, service3, service4
        assert len(services) == 3
        assert services[0].name == "Test Возврат дс"
        assert services[1].name == "Test Возврат путевки"
        assert services[2].name == "Test Other Service"
    
    def test_with_missing_priority_services(self, app_context):
        """Test ordering with missing priority services.
        
        Requirements: 1.3
        """
        # Create only one priority service and other services
        service1 = Service(name="Test Missing Возврат путевки", display_order=3, active=True)
        service2 = Service(name="Test Service A", display_order=999, active=True)
        service3 = Service(name="Test Service B", display_order=999, active=True)
        
        db.session.add_all([service1, service2, service3])
        db.session.commit()
        
        # Get active services
        services = ServiceManager.get_active_services()
        
        # Should show priority service first, then others alphabetically
        assert len(services) == 3
        assert services[0].name == "Test Missing Возврат путевки"
        # Services with same display_order should be sorted by name
        assert services[1].name == "Test Service A"
        assert services[2].name == "Test Service B"
    
    def test_with_only_non_priority_services(self, app_context):
        """Test ordering with only non-priority services.
        
        Requirements: 1.3
        """
        # Create only non-priority services
        service1 = Service(name="Test Zebra Service", display_order=999, active=True)
        service2 = Service(name="Test Alpha Service", display_order=999, active=True)
        service3 = Service(name="Test Beta Service", display_order=999, active=True)
        
        db.session.add_all([service1, service2, service3])
        db.session.commit()
        
        # Get active services
        services = ServiceManager.get_active_services()
        
        # Should be sorted alphabetically by name
        assert len(services) == 3
        assert services[0].name == "Test Alpha Service"
        assert services[1].name == "Test Beta Service"
        assert services[2].name == "Test Zebra Service"
    
    def test_all_priority_services_active(self, app_context):
        """Test ordering with all priority services active."""
        # Create all priority services
        service1 = Service(name="Test All Получить путевку", display_order=1, active=True)
        service2 = Service(name="Test All Возврат дс", display_order=2, active=True)
        service3 = Service(name="Test All Возврат путевки", display_order=3, active=True)
        service4 = Service(name="Test All Other Service", display_order=999, active=True)
        
        db.session.add_all([service1, service2, service3, service4])
        db.session.commit()
        
        # Get active services
        services = ServiceManager.get_active_services()
        
        # Should be in priority order
        assert len(services) == 4
        assert services[0].name == "Test All Получить путевку"
        assert services[1].name == "Test All Возврат дс"
        assert services[2].name == "Test All Возврат путевки"
        assert services[3].name == "Test All Other Service"
    
    def test_empty_services(self, app_context):
        """Test with no services in database."""
        # Get active services
        services = ServiceManager.get_active_services()
        
        # Should return empty list
        assert len(services) == 0
