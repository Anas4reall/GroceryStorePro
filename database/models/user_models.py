"""
User management models.
"""

from peewee import (
    CharField, TextField, BooleanField, DateTimeField, 
    ForeignKeyField, IntegerField
)
from datetime import datetime
import bcrypt
from .base_model import BaseModel


class Role(BaseModel):
    """User role model."""
    
    name = CharField(max_length=50, unique=True)
    name_ar = CharField(max_length=50, null=True)
    description = TextField(null=True)
    description_ar = TextField(null=True)
    is_active = BooleanField(default=True)
    
    class Meta:
        table_name = 'roles'
    
    def __str__(self):
        return self.name


class Permission(BaseModel):
    """Permission model."""
    
    name = CharField(max_length=100, unique=True)
    description = TextField(null=True)
    module = CharField(max_length=50)  # e.g., 'sales', 'inventory', 'reports'
    action = CharField(max_length=50)  # e.g., 'create', 'read', 'update', 'delete'
    
    class Meta:
        table_name = 'permissions'
    
    def __str__(self):
        return f"{self.module}.{self.action}"


class User(BaseModel):
    """User model."""
    
    username = CharField(max_length=50, unique=True)
    password_hash = CharField(max_length=255)
    full_name = CharField(max_length=100)
    full_name_ar = CharField(max_length=100, null=True)
    email = CharField(max_length=100, null=True)
    phone = CharField(max_length=20, null=True)
    is_active = BooleanField(default=True)
    is_admin = BooleanField(default=False)
    last_login = DateTimeField(null=True)
    failed_login_attempts = IntegerField(default=0)
    locked_until = DateTimeField(null=True)
    password_changed_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'users'
    
    def set_password(self, password: str):
        """
        Set user password with bcrypt hashing.
        
        Args:
            password: Plain text password
        """
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        self.password_changed_at = datetime.now()
    
    def check_password(self, password: str) -> bool:
        """
        Check if provided password matches the stored hash.
        
        Args:
            password: Plain text password to check
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                self.password_hash.encode('utf-8')
            )
        except Exception:
            return False
    
    def is_locked(self) -> bool:
        """
        Check if user account is locked.
        
        Returns:
            True if account is locked, False otherwise
        """
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until
    
    def lock_account(self, duration_minutes: int = 15):
        """
        Lock user account for specified duration.
        
        Args:
            duration_minutes: Duration to lock account in minutes
        """
        from datetime import timedelta
        self.locked_until = datetime.now() + timedelta(minutes=duration_minutes)
        self.save()
    
    def unlock_account(self):
        """Unlock user account."""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save()
    
    def increment_failed_login(self):
        """Increment failed login attempts counter."""
        self.failed_login_attempts += 1
        self.save()
    
    def reset_failed_login(self):
        """Reset failed login attempts counter."""
        self.failed_login_attempts = 0
        self.save()
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.now()
        self.reset_failed_login()
        self.save()
    
    def get_roles(self):
        """
        Get all roles assigned to this user.
        
        Returns:
            List of Role objects
        """
        return [ur.role for ur in self.user_roles]
    
    def has_role(self, role_name: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            role_name: Name of the role to check
            
        Returns:
            True if user has the role, False otherwise
        """
        return any(role.name == role_name for role in self.get_roles())
    
    def has_permission(self, module: str, action: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            module: Module name (e.g., 'sales', 'inventory')
            action: Action name (e.g., 'create', 'read', 'update', 'delete')
            
        Returns:
            True if user has the permission, False otherwise
        """
        # Admin users have all permissions
        if self.is_admin:
            return True
        
        # Check role-based permissions
        for role in self.get_roles():
            for role_permission in role.role_permissions:
                permission = role_permission.permission
                if permission.module == module and permission.action == action:
                    return True
        
        return False
    
    def to_dict(self, exclude_fields=None):
        """Convert to dictionary, excluding sensitive fields by default."""
        if exclude_fields is None:
            exclude_fields = ['password_hash']
        else:
            exclude_fields.append('password_hash')
        
        return super().to_dict(exclude_fields)
    
    def __str__(self):
        return self.username


class UserRole(BaseModel):
    """Many-to-many relationship between users and roles."""
    
    user = ForeignKeyField(User, backref='user_roles', on_delete='CASCADE')
    role = ForeignKeyField(Role, backref='user_roles', on_delete='CASCADE')
    assigned_by = ForeignKeyField(User, null=True, on_delete='SET NULL')
    assigned_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'user_roles'
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class RolePermission(BaseModel):
    """Many-to-many relationship between roles and permissions."""
    
    role = ForeignKeyField(Role, backref='role_permissions', on_delete='CASCADE')
    permission = ForeignKeyField(Permission, backref='role_permissions', on_delete='CASCADE')
    
    class Meta:
        table_name = 'role_permissions'
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"
