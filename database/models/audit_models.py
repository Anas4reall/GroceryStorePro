"""
Audit and logging models.
"""

from peewee import (
    CharField, TextField, IntegerField, DateTimeField,
    ForeignKeyField, BooleanField, DeferredForeignKey
)
from datetime import datetime
import json
from .base_model import BaseModel


class AuditLog(BaseModel):
    """Audit log model for tracking all critical operations."""
    
    # Action types
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('failed_login', 'Failed Login'),
        ('password_change', 'Password Change'),
        ('permission_change', 'Permission Change'),
        ('system_setting', 'System Setting Change'),
        ('backup', 'Backup Operation'),
        ('restore', 'Restore Operation'),
        ('export', 'Data Export'),
        ('import', 'Data Import'),
    ]
    
    # Severity levels
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    # Audit information
    user = DeferredForeignKey('User', backref='audit_logs', null=True, on_delete='SET NULL')
    action = CharField(max_length=20, choices=ACTION_TYPES)
    table_name = CharField(max_length=100, null=True)
    record_id = IntegerField(null=True)
    
    # Change details
    old_values = TextField(null=True)  # JSON string of old values
    new_values = TextField(null=True)  # JSON string of new values
    
    # Additional information
    description = CharField(max_length=500, null=True)
    severity = CharField(max_length=10, choices=SEVERITY_LEVELS, default='info')
    
    # System information
    ip_address = CharField(max_length=45, null=True)  # IPv6 compatible
    user_agent = CharField(max_length=500, null=True)
    session_id = CharField(max_length=100, null=True)
    
    # Timestamp
    timestamp = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'audit_logs'
    
    def set_old_values(self, values_dict):
        """
        Set old values as JSON string.
        
        Args:
            values_dict: Dictionary of old values
        """
        if values_dict:
            self.old_values = json.dumps(values_dict, default=str, ensure_ascii=False)
    
    def set_new_values(self, values_dict):
        """
        Set new values as JSON string.
        
        Args:
            values_dict: Dictionary of new values
        """
        if values_dict:
            self.new_values = json.dumps(values_dict, default=str, ensure_ascii=False)
    
    def get_old_values(self):
        """
        Get old values as dictionary.
        
        Returns:
            Dictionary of old values or None
        """
        if self.old_values:
            try:
                return json.loads(self.old_values)
            except json.JSONDecodeError:
                return None
        return None
    
    def get_new_values(self):
        """
        Get new values as dictionary.
        
        Returns:
            Dictionary of new values or None
        """
        if self.new_values:
            try:
                return json.loads(self.new_values)
            except json.JSONDecodeError:
                return None
        return None
    
    def get_changes(self):
        """
        Get a summary of changes made.
        
        Returns:
            Dictionary of changed fields with old and new values
        """
        old_vals = self.get_old_values()
        new_vals = self.get_new_values()
        
        if not old_vals or not new_vals:
            return {}
        
        changes = {}
        for key in new_vals:
            if key in old_vals and old_vals[key] != new_vals[key]:
                changes[key] = {
                    'old': old_vals[key],
                    'new': new_vals[key]
                }
        
        return changes
    
    @classmethod
    def log_create(cls, user, table_name, record_id, new_values, description=None):
        """
        Log a create operation.
        
        Args:
            user: User who performed the action
            table_name: Name of the table
            record_id: ID of the created record
            new_values: Dictionary of new values
            description: Optional description
        """
        audit_log = cls.create(
            user=user,
            action='create',
            table_name=table_name,
            record_id=record_id,
            description=description or f"Created {table_name} record"
        )
        audit_log.set_new_values(new_values)
        audit_log.save()
        return audit_log
    
    @classmethod
    def log_update(cls, user, table_name, record_id, old_values, new_values, description=None):
        """
        Log an update operation.
        
        Args:
            user: User who performed the action
            table_name: Name of the table
            record_id: ID of the updated record
            old_values: Dictionary of old values
            new_values: Dictionary of new values
            description: Optional description
        """
        audit_log = cls.create(
            user=user,
            action='update',
            table_name=table_name,
            record_id=record_id,
            description=description or f"Updated {table_name} record"
        )
        audit_log.set_old_values(old_values)
        audit_log.set_new_values(new_values)
        audit_log.save()
        return audit_log
    
    @classmethod
    def log_delete(cls, user, table_name, record_id, old_values, description=None):
        """
        Log a delete operation.
        
        Args:
            user: User who performed the action
            table_name: Name of the table
            record_id: ID of the deleted record
            old_values: Dictionary of old values
            description: Optional description
        """
        audit_log = cls.create(
            user=user,
            action='delete',
            table_name=table_name,
            record_id=record_id,
            description=description or f"Deleted {table_name} record",
            severity='warning'
        )
        audit_log.set_old_values(old_values)
        audit_log.save()
        return audit_log
    
    @classmethod
    def log_login(cls, user, ip_address=None, user_agent=None, session_id=None):
        """
        Log a successful login.
        
        Args:
            user: User who logged in
            ip_address: IP address of the user
            user_agent: User agent string
            session_id: Session ID
        """
        return cls.create(
            user=user,
            action='login',
            description=f"User {user.username} logged in",
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
    
    @classmethod
    def log_failed_login(cls, username, ip_address=None, user_agent=None, reason=None):
        """
        Log a failed login attempt.
        
        Args:
            username: Username that was attempted
            ip_address: IP address of the attempt
            user_agent: User agent string
            reason: Reason for failure
        """
        return cls.create(
            action='failed_login',
            description=f"Failed login attempt for username: {username}. Reason: {reason}",
            severity='warning',
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_logout(cls, user, session_id=None):
        """
        Log a logout.
        
        Args:
            user: User who logged out
            session_id: Session ID
        """
        return cls.create(
            user=user,
            action='logout',
            description=f"User {user.username} logged out",
            session_id=session_id
        )
    
    @classmethod
    def log_system_event(cls, user, action, description, severity='info', **kwargs):
        """
        Log a general system event.
        
        Args:
            user: User who performed the action (can be None for system events)
            action: Action type
            description: Description of the event
            severity: Severity level
            **kwargs: Additional fields
        """
        return cls.create(
            user=user,
            action=action,
            description=description,
            severity=severity,
            **kwargs
        )
    
    @classmethod
    def cleanup_old_logs(cls, days_to_keep=90):
        """
        Clean up old audit logs.
        
        Args:
            days_to_keep: Number of days to keep logs
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Delete old logs except critical ones
        deleted_count = cls.delete().where(
            (cls.timestamp < cutoff_date) & 
            (cls.severity != 'critical')
        ).execute()
        
        return deleted_count
    
    def __str__(self):
        user_name = self.user.username if self.user else "System"
        return f"{self.timestamp} - {user_name} - {self.action} - {self.description}"
