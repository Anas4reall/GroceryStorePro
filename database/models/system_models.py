"""
System configuration and settings models.
"""

from peewee import (
    CharField, TextField, BooleanField, IntegerField, 
    DecimalField, DateTimeField
)
from datetime import datetime
import json
from .base_model import BaseModel


class SystemSetting(BaseModel):
    """System settings model for configurable application settings."""
    
    # Setting categories
    CATEGORIES = [
        ('general', 'General Settings'),
        ('business', 'Business Settings'),
        ('accounting', 'Accounting Settings'),
        ('inventory', 'Inventory Settings'),
        ('security', 'Security Settings'),
        ('ui', 'User Interface Settings'),
        ('reports', 'Reports Settings'),
        ('backup', 'Backup Settings'),
        ('integration', 'Integration Settings'),
    ]
    
    # Data types
    DATA_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('decimal', 'Decimal'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
    ]
    
    # Setting information
    key = CharField(max_length=100, unique=True)
    category = CharField(max_length=20, choices=CATEGORIES, default='general')
    data_type = CharField(max_length=10, choices=DATA_TYPES, default='string')
    
    # Value storage
    value = TextField()
    default_value = TextField(null=True)
    
    # Metadata
    name = CharField(max_length=200)
    name_ar = CharField(max_length=200, null=True)
    description = TextField(null=True)
    description_ar = TextField(null=True)
    
    # Validation
    validation_rules = TextField(null=True)  # JSON string with validation rules
    possible_values = TextField(null=True)   # JSON array of possible values
    
    # Settings
    is_system_setting = BooleanField(default=False)  # Cannot be deleted
    is_user_editable = BooleanField(default=True)
    requires_restart = BooleanField(default=False)
    
    # Tracking
    last_modified_by = CharField(max_length=100, null=True)
    last_modified_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'system_settings'
    
    def get_typed_value(self):
        """
        Get the value converted to the appropriate data type.
        
        Returns:
            Value converted to the specified data type
        """
        if not self.value:
            return self.get_typed_default_value()
        
        try:
            if self.data_type == 'integer':
                return int(self.value)
            elif self.data_type == 'decimal':
                from decimal import Decimal
                return Decimal(self.value)
            elif self.data_type == 'boolean':
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.data_type == 'json':
                return json.loads(self.value)
            elif self.data_type == 'date':
                from datetime import datetime
                return datetime.strptime(self.value, '%Y-%m-%d').date()
            elif self.data_type == 'datetime':
                from datetime import datetime
                return datetime.fromisoformat(self.value)
            else:  # string
                return self.value
        except (ValueError, json.JSONDecodeError):
            return self.get_typed_default_value()
    
    def get_typed_default_value(self):
        """
        Get the default value converted to the appropriate data type.
        
        Returns:
            Default value converted to the specified data type
        """
        if not self.default_value:
            if self.data_type == 'integer':
                return 0
            elif self.data_type == 'decimal':
                from decimal import Decimal
                return Decimal('0')
            elif self.data_type == 'boolean':
                return False
            elif self.data_type == 'json':
                return {}
            elif self.data_type in ('date', 'datetime'):
                return None
            else:
                return ''
        
        try:
            if self.data_type == 'integer':
                return int(self.default_value)
            elif self.data_type == 'decimal':
                from decimal import Decimal
                return Decimal(self.default_value)
            elif self.data_type == 'boolean':
                return self.default_value.lower() in ('true', '1', 'yes', 'on')
            elif self.data_type == 'json':
                return json.loads(self.default_value)
            elif self.data_type == 'date':
                from datetime import datetime
                return datetime.strptime(self.default_value, '%Y-%m-%d').date()
            elif self.data_type == 'datetime':
                from datetime import datetime
                return datetime.fromisoformat(self.default_value)
            else:  # string
                return self.default_value
        except (ValueError, json.JSONDecodeError):
            return self.get_typed_default_value()
    
    def set_typed_value(self, value, modified_by=None):
        """
        Set the value with automatic type conversion.
        
        Args:
            value: Value to set
            modified_by: User who modified the setting
        """
        if value is None:
            self.value = ''
        elif self.data_type == 'json':
            self.value = json.dumps(value, ensure_ascii=False)
        elif self.data_type in ('date', 'datetime'):
            if hasattr(value, 'isoformat'):
                self.value = value.isoformat()
            else:
                self.value = str(value)
        else:
            self.value = str(value)
        
        self.last_modified_by = modified_by
        self.last_modified_at = datetime.now()
        self.save()
    
    def validate_value(self, value):
        """
        Validate a value against the setting's validation rules.
        
        Args:
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check possible values
        if self.possible_values:
            try:
                possible = json.loads(self.possible_values)
                if isinstance(possible, list) and value not in possible:
                    return False, f"Value must be one of: {', '.join(map(str, possible))}"
            except json.JSONDecodeError:
                pass
        
        # Check validation rules
        if self.validation_rules:
            try:
                rules = json.loads(self.validation_rules)
                
                # Min/max for numeric values
                if self.data_type in ('integer', 'decimal'):
                    if 'min' in rules and value < rules['min']:
                        return False, f"Value must be at least {rules['min']}"
                    if 'max' in rules and value > rules['max']:
                        return False, f"Value must be at most {rules['max']}"
                
                # Length for strings
                elif self.data_type == 'string':
                    if 'min_length' in rules and len(str(value)) < rules['min_length']:
                        return False, f"Value must be at least {rules['min_length']} characters"
                    if 'max_length' in rules and len(str(value)) > rules['max_length']:
                        return False, f"Value must be at most {rules['max_length']} characters"
                    if 'pattern' in rules:
                        import re
                        if not re.match(rules['pattern'], str(value)):
                            return False, f"Value does not match required pattern"
                
            except (json.JSONDecodeError, KeyError):
                pass
        
        return True, None
    
    @classmethod
    def get_setting(cls, key, default=None):
        """
        Get a setting value by key.
        
        Args:
            key: Setting key
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        try:
            setting = cls.get(cls.key == key)
            return setting.get_typed_value()
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, key, value, modified_by=None):
        """
        Set a setting value by key.
        
        Args:
            key: Setting key
            value: Value to set
            modified_by: User who modified the setting
        """
        try:
            setting = cls.get(cls.key == key)
            setting.set_typed_value(value, modified_by)
        except cls.DoesNotExist:
            # Create new setting if it doesn't exist
            cls.create(
                key=key,
                value=str(value),
                name=key.replace('_', ' ').title(),
                last_modified_by=modified_by
            )
    
    @classmethod
    def get_settings_by_category(cls, category):
        """
        Get all settings in a category.
        
        Args:
            category: Category name
            
        Returns:
            Dictionary of key-value pairs
        """
        settings = {}
        for setting in cls.select().where(cls.category == category):
            settings[setting.key] = setting.get_typed_value()
        return settings
    
    @classmethod
    def initialize_default_settings(cls):
        """Initialize default system settings."""
        default_settings = [
            # General settings
            {
                'key': 'company_name',
                'category': 'general',
                'data_type': 'string',
                'value': 'متجر البقالة المحترف',
                'name': 'Company Name',
                'name_ar': 'اسم الشركة',
                'description': 'Company name displayed on invoices and reports',
                'is_system_setting': True
            },
            {
                'key': 'company_name_en',
                'category': 'general',
                'data_type': 'string',
                'value': 'Professional Grocery Store',
                'name': 'Company Name (English)',
                'name_ar': 'اسم الشركة (إنجليزي)',
                'description': 'Company name in English',
                'is_system_setting': True
            },
            {
                'key': 'default_currency',
                'category': 'business',
                'data_type': 'string',
                'value': 'SAR',
                'name': 'Default Currency',
                'name_ar': 'العملة الافتراضية',
                'description': 'Default currency for transactions',
                'possible_values': '["SAR", "USD", "EUR", "AED"]',
                'is_system_setting': True
            },
            {
                'key': 'default_tax_rate',
                'category': 'business',
                'data_type': 'decimal',
                'value': '15.00',
                'name': 'Default Tax Rate (%)',
                'name_ar': 'معدل الضريبة الافتراضي (%)',
                'description': 'Default tax rate percentage',
                'validation_rules': '{"min": 0, "max": 100}',
                'is_system_setting': True
            },
            {
                'key': 'allow_negative_stock',
                'category': 'inventory',
                'data_type': 'boolean',
                'value': 'false',
                'name': 'Allow Negative Stock',
                'name_ar': 'السماح بالمخزون السالب',
                'description': 'Allow selling products with negative stock',
                'is_system_setting': True
            },
            {
                'key': 'backup_retention_days',
                'category': 'backup',
                'data_type': 'integer',
                'value': '14',
                'name': 'Backup Retention (Days)',
                'name_ar': 'مدة الاحتفاظ بالنسخ الاحتياطية (أيام)',
                'description': 'Number of days to keep backup files',
                'validation_rules': '{"min": 1, "max": 365}',
                'is_system_setting': True
            }
        ]
        
        for setting_data in default_settings:
            try:
                cls.get(cls.key == setting_data['key'])
            except cls.DoesNotExist:
                cls.create(**setting_data)
    
    def __str__(self):
        return f"{self.key} = {self.value}"
