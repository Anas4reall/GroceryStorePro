"""
Base model for all database models.
"""

from peewee import Model, DateTimeField, IntegerField
from datetime import datetime
from . import database


class BaseModel(Model):
    """Base model class with common fields and functionality."""
    
    id = IntegerField(primary_key=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        database = database
    
    def save(self, *args, **kwargs):
        """Override save to update the updated_at timestamp."""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
    def to_dict(self, exclude_fields=None):
        """
        Convert model instance to dictionary.
        
        Args:
            exclude_fields: List of fields to exclude from the dictionary
            
        Returns:
            Dictionary representation of the model
        """
        if exclude_fields is None:
            exclude_fields = []
        
        data = {}
        for field_name in self._meta.fields:
            if field_name not in exclude_fields:
                field_value = getattr(self, field_name)
                
                # Handle datetime fields
                if isinstance(field_value, datetime):
                    data[field_name] = field_value.isoformat()
                # Handle foreign key fields
                elif hasattr(field_value, 'id'):
                    data[field_name] = field_value.id
                else:
                    data[field_name] = field_value
        
        return data
    
    @classmethod
    def get_or_none_by_id(cls, model_id):
        """
        Get model instance by ID or return None if not found.
        
        Args:
            model_id: The ID to search for
            
        Returns:
            Model instance or None
        """
        try:
            return cls.get_by_id(model_id)
        except cls.DoesNotExist:
            return None
    
    def __str__(self):
        """String representation of the model."""
        return f"{self.__class__.__name__}(id={self.id})"
    
    def __repr__(self):
        """Detailed string representation of the model."""
        return f"<{self.__class__.__name__}: {self.id}>"
