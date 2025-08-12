"""
Authentication service for user login and session management.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import uuid

from database.models import User, AuditLog
from logic.utils.logger import get_logger, log_security_event, log_user_action


class AuthService:
    """Service for handling user authentication and authorization."""
    
    def __init__(self):
        """Initialize the authentication service."""
        self.logger = get_logger(__name__)
        self.active_sessions = {}  # In-memory session storage
        self.max_login_attempts = 3
        self.lockout_duration_minutes = 15
    
    def authenticate(self, username: str, password: str, 
                    ip_address: str = None, user_agent: str = None) -> Tuple[bool, Optional[User], str]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Tuple of (success, user_object, message)
        """
        try:
            # Find user
            try:
                user = User.get(User.username == username)
            except User.DoesNotExist:
                self.logger.warning(f"Login attempt with non-existent username: {username}")
                log_security_event(
                    'failed_login',
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    description="Username not found"
                )
                return False, None, "Invalid username or password"
            
            # Check if user is active
            if not user.is_active:
                self.logger.warning(f"Login attempt with inactive user: {username}")
                log_security_event(
                    'failed_login',
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    description="User account is inactive"
                )
                return False, None, "User account is inactive"
            
            # Check if account is locked
            if user.is_locked():
                self.logger.warning(f"Login attempt with locked account: {username}")
                log_security_event(
                    'failed_login',
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    description="Account is locked"
                )
                return False, None, f"Account is locked. Try again later."
            
            # Verify password
            if not user.check_password(password):
                self.logger.warning(f"Failed login attempt for user: {username}")
                
                # Increment failed attempts
                user.increment_failed_login()
                
                # Lock account if too many attempts
                if user.failed_login_attempts >= self.max_login_attempts:
                    user.lock_account(self.lockout_duration_minutes)
                    self.logger.warning(f"Account locked due to too many failed attempts: {username}")
                    
                    log_security_event(
                        'account_locked',
                        username=username,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        description=f"Account locked after {self.max_login_attempts} failed attempts"
                    )
                    
                    return False, None, f"Too many failed attempts. Account locked for {self.lockout_duration_minutes} minutes."
                
                log_security_event(
                    'failed_login',
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    description="Invalid password"
                )
                
                remaining_attempts = self.max_login_attempts - user.failed_login_attempts
                return False, None, f"Invalid username or password. {remaining_attempts} attempts remaining."
            
            # Successful authentication
            user.update_last_login()
            
            self.logger.info(f"Successful login for user: {username}")
            
            # Log successful login
            AuditLog.log_login(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return True, user, "Login successful"
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False, None, "Authentication system error"
    
    def create_session(self, user: User, ip_address: str = None) -> str:
        """
        Create a new session for the authenticated user.
        
        Args:
            user: Authenticated user
            ip_address: Client IP address
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            'user_id': user.id,
            'username': user.username,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'ip_address': ip_address,
            'is_active': True
        }
        
        self.active_sessions[session_id] = session_data
        
        self.logger.info(f"Session created for user {user.username}: {session_id}")
        
        return session_id
    
    def validate_session(self, session_id: str, timeout_minutes: int = 60) -> Tuple[bool, Optional[User]]:
        """
        Validate a session and check for timeout.
        
        Args:
            session_id: Session ID to validate
            timeout_minutes: Session timeout in minutes
            
        Returns:
            Tuple of (is_valid, user_object)
        """
        if session_id not in self.active_sessions:
            return False, None
        
        session_data = self.active_sessions[session_id]
        
        # Check if session is active
        if not session_data.get('is_active', False):
            return False, None
        
        # Check timeout
        last_activity = session_data['last_activity']
        if datetime.now() - last_activity > timedelta(minutes=timeout_minutes):
            self.logger.info(f"Session expired: {session_id}")
            self.end_session(session_id)
            return False, None
        
        # Update last activity
        session_data['last_activity'] = datetime.now()
        
        # Get user
        try:
            user = User.get_by_id(session_data['user_id'])
            if not user.is_active:
                self.end_session(session_id)
                return False, None
            
            return True, user
        except User.DoesNotExist:
            self.end_session(session_id)
            return False, None
    
    def end_session(self, session_id: str) -> bool:
        """
        End a user session.
        
        Args:
            session_id: Session ID to end
            
        Returns:
            True if session was ended, False if session not found
        """
        if session_id not in self.active_sessions:
            return False
        
        session_data = self.active_sessions[session_id]
        session_data['is_active'] = False
        
        # Log logout
        try:
            user = User.get_by_id(session_data['user_id'])
            AuditLog.log_logout(user=user, session_id=session_id)
            self.logger.info(f"Session ended for user {user.username}: {session_id}")
        except User.DoesNotExist:
            pass
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        return True
    
    def get_active_sessions(self) -> dict:
        """
        Get all active sessions.
        
        Returns:
            Dictionary of active sessions
        """
        return {sid: data for sid, data in self.active_sessions.items() 
                if data.get('is_active', False)}
    
    def cleanup_expired_sessions(self, timeout_minutes: int = 60):
        """
        Clean up expired sessions.
        
        Args:
            timeout_minutes: Session timeout in minutes
        """
        expired_sessions = []
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        
        for session_id, session_data in self.active_sessions.items():
            if session_data['last_activity'] < cutoff_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.end_session(session_id)
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def change_password(self, user: User, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change user password.
        
        Args:
            user: User object
            old_password: Current password
            new_password: New password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Verify old password
            if not user.check_password(old_password):
                log_security_event(
                    'password_change_failed',
                    username=user.username,
                    description="Invalid old password"
                )
                return False, "Current password is incorrect"
            
            # Validate new password
            is_valid, message = self.validate_password(new_password)
            if not is_valid:
                return False, message
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Log password change
            log_user_action(
                user=user,
                action='password_change',
                description="Password changed successfully",
                severity='info'
            )
            
            self.logger.info(f"Password changed for user: {user.username}")
            
            return True, "Password changed successfully"
            
        except Exception as e:
            self.logger.error(f"Password change error: {e}")
            return False, "Password change failed"
    
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
        if len(password) > 128:
            return False, "Password must be less than 128 characters"
        
        # Add more validation rules as needed
        # - Must contain uppercase and lowercase
        # - Must contain numbers
        # - Must contain special characters
        
        return True, "Password is valid"
    
    def unlock_user_account(self, username: str, admin_user: User) -> Tuple[bool, str]:
        """
        Unlock a user account (admin function).
        
        Args:
            username: Username to unlock
            admin_user: Admin user performing the action
            
        Returns:
            Tuple of (success, message)
        """
        try:
            user = User.get(User.username == username)
            
            if not user.is_locked():
                return False, "Account is not locked"
            
            user.unlock_account()
            
            log_user_action(
                user=admin_user,
                action='account_unlock',
                description=f"Unlocked account for user: {username}",
                severity='warning'
            )
            
            self.logger.info(f"Account unlocked by admin {admin_user.username} for user: {username}")
            
            return True, "Account unlocked successfully"
            
        except User.DoesNotExist:
            return False, "User not found"
        except Exception as e:
            self.logger.error(f"Account unlock error: {e}")
            return False, "Failed to unlock account"
