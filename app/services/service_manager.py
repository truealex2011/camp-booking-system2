"""Service management logic."""
import json
from app.models import db, Service, Booking


class ServiceManager:
    """Manager for service CRUD operations."""
    
    @staticmethod
    def get_active_services():
        """Get all active services ordered by display priority.
        
        Returns:
            List of active Service objects ordered by display_order, then name
        """
        return Service.query.filter_by(active=True).order_by(Service.display_order, Service.name).all()
    
    @staticmethod
    def get_all_services():
        """Get all services regardless of status.
        
        Returns:
            List of all Service objects
        """
        return Service.query.order_by(Service.name).all()
    
    @staticmethod
    def get_service_by_id(service_id):
        """Get a service by ID.
        
        Args:
            service_id: Service ID
            
        Returns:
            Service object or None
        """
        return Service.query.get(service_id)
    
    @staticmethod
    def create_service(name, description='', required_documents=None):
        """Create a new service.
        
        Args:
            name: Service name
            description: Service description
            required_documents: List of required documents
            
        Returns:
            Service object or None if name already exists
        """
        # Check if service with this name already exists
        existing = Service.query.filter_by(name=name).first()
        if existing:
            return None
        
        # Convert required_documents list to JSON string
        if required_documents is None:
            required_documents = []
        
        documents_json = json.dumps(required_documents, ensure_ascii=False)
        
        service = Service(
            name=name,
            description=description,
            required_documents=documents_json,
            active=True
        )
        
        db.session.add(service)
        db.session.commit()
        
        return service
    
    @staticmethod
    def update_service(service_id, name=None, description=None, required_documents=None):
        """Update an existing service.
        
        Args:
            service_id: Service ID
            name: New service name (optional)
            description: New description (optional)
            required_documents: New list of required documents (optional)
            
        Returns:
            True if successful, False otherwise
        """
        service = Service.query.get(service_id)
        if not service:
            return False
        
        # Check if new name conflicts with existing service
        if name and name != service.name:
            existing = Service.query.filter_by(name=name).first()
            if existing:
                return False
            service.name = name
        
        if description is not None:
            service.description = description
        
        if required_documents is not None:
            service.required_documents = json.dumps(required_documents, ensure_ascii=False)
        
        db.session.commit()
        return True
    
    @staticmethod
    def toggle_service_status(service_id):
        """Toggle service active status.
        
        Args:
            service_id: Service ID
            
        Returns:
            True if successful, False otherwise
        """
        service = Service.query.get(service_id)
        if not service:
            return False
        
        service.active = not service.active
        db.session.commit()
        return True
    
    @staticmethod
    def deactivate_service(service_id):
        """Deactivate a service.
        
        Args:
            service_id: Service ID
            
        Returns:
            True if successful, False otherwise
        """
        service = Service.query.get(service_id)
        if not service:
            return False
        
        service.active = False
        db.session.commit()
        return True
    
    @staticmethod
    def can_delete_service(service_id):
        """Check if a service can be deleted (has no active bookings).
        
        Only counts active (not cancelled) bookings. Cancelled bookings don't
        prevent deletion since they're no longer active.
        
        Args:
            service_id: Service ID
            
        Returns:
            True if can be deleted (zero active bookings), False otherwise
        """
        # Count only active bookings (status != 'cancelled')
        booking_count = Booking.query.filter(
            Booking.service_id == service_id,
            Booking.status != 'cancelled'
        ).count()
        return booking_count == 0
    
    @staticmethod
    def delete_service(service_id):
        """Delete a service if it has no active bookings.
        
        Performs an explicit check before deletion to ensure no active bookings exist.
        This double-check prevents race conditions and ensures data consistency.
        
        Args:
            service_id: Service ID
            
        Returns:
            True if successful, False otherwise
        """
        # Explicit check before deletion - prevents race conditions
        if not ServiceManager.can_delete_service(service_id):
            return False
        
        service = Service.query.get(service_id)
        if not service:
            return False
        
        # Double-check immediately before deletion to prevent race conditions
        # Only count active bookings (not cancelled)
        booking_count = Booking.query.filter(
            Booking.service_id == service.id,
            Booking.status != 'cancelled'
        ).count()
        if booking_count > 0:
            return False
        
        # Delete all bookings (including cancelled ones) associated with this service
        Booking.query.filter_by(service_id=service.id).delete()
        
        db.session.delete(service)
        db.session.commit()
        return True
    
    @staticmethod
    def get_required_documents(service_id):
        """Get required documents for a service.
        
        Args:
            service_id: Service ID
            
        Returns:
            List of required documents or empty list
        """
        service = Service.query.get(service_id)
        if not service or not service.required_documents:
            return []
        
        try:
            return json.loads(service.required_documents)
        except json.JSONDecodeError:
            return []
