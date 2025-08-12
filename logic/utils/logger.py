"""
Logging utility for GroceryStorePro.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys


def setup_logging(log_level=logging.INFO, log_to_file=True, log_to_console=True):
    """
    Setup application logging.
    
    Args:
        log_level: Logging level (default: INFO)
        log_to_file: Whether to log to file (default: True)
        log_to_console: Whether to log to console (default: True)
        
    Returns:
        Logger instance
    """
    # Create logs directory
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('GroceryStorePro')
    logger.setLevel(log_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation
    if log_to_file:
        log_file = log_dir / "grocerystorepro.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Error log file
        error_log_file = log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name=None):
    """
    Get a logger instance.
    
    Args:
        name: Logger name (default: calling module name)
        
    Returns:
        Logger instance
    """
    if name is None:
        # Get the calling module name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return logging.getLogger(f'GroceryStorePro.{name}')


class DatabaseLogHandler(logging.Handler):
    """Custom log handler that writes to database."""
    
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.user = None
    
    def set_user(self, user):
        """Set the current user for logging."""
        self.user = user
    
    def emit(self, record):
        """Emit a log record to the database."""
        try:
            from database.models import AuditLog
            
            # Map log levels to severity
            severity_map = {
                logging.DEBUG: 'info',
                logging.INFO: 'info',
                logging.WARNING: 'warning',
                logging.ERROR: 'error',
                logging.CRITICAL: 'critical'
            }
            
            severity = severity_map.get(record.levelno, 'info')
            
            # Create audit log entry
            AuditLog.create(
                user=self.user,
                action='system_log',
                description=record.getMessage(),
                severity=severity,
                table_name=getattr(record, 'table_name', None),
                record_id=getattr(record, 'record_id', None)
            )
            
        except Exception:
            # Don't let logging errors break the application
            pass


def log_database_operation(user, action, table_name, record_id=None, 
                         old_values=None, new_values=None, description=None):
    """
    Log a database operation to the audit log.
    
    Args:
        user: User who performed the operation
        action: Action performed ('create', 'update', 'delete')
        table_name: Name of the table
        record_id: ID of the affected record
        old_values: Dictionary of old values (for updates/deletes)
        new_values: Dictionary of new values (for creates/updates)
        description: Optional description
    """
    try:
        from database.models import AuditLog
        
        if action == 'create':
            AuditLog.log_create(user, table_name, record_id, new_values, description)
        elif action == 'update':
            AuditLog.log_update(user, table_name, record_id, old_values, new_values, description)
        elif action == 'delete':
            AuditLog.log_delete(user, table_name, record_id, old_values, description)
        
    except Exception as e:
        # Log the error but don't break the application
        logger = get_logger(__name__)
        logger.error(f"Failed to log database operation: {e}")


def log_user_action(user, action, description, severity='info', **kwargs):
    """
    Log a user action.
    
    Args:
        user: User who performed the action
        action: Action performed
        description: Description of the action
        severity: Severity level
        **kwargs: Additional fields
    """
    try:
        from database.models import AuditLog
        
        AuditLog.log_system_event(
            user=user,
            action=action,
            description=description,
            severity=severity,
            **kwargs
        )
        
    except Exception as e:
        # Log the error but don't break the application
        logger = get_logger(__name__)
        logger.error(f"Failed to log user action: {e}")


def log_security_event(event_type, username=None, ip_address=None, 
                      user_agent=None, description=None):
    """
    Log a security-related event.
    
    Args:
        event_type: Type of security event
        username: Username involved (if any)
        ip_address: IP address
        user_agent: User agent string
        description: Event description
    """
    try:
        from database.models import AuditLog
        
        if event_type == 'failed_login':
            AuditLog.log_failed_login(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                reason=description
            )
        else:
            AuditLog.log_system_event(
                user=None,
                action=event_type,
                description=description or f"Security event: {event_type}",
                severity='warning',
                ip_address=ip_address,
                user_agent=user_agent
            )
        
    except Exception as e:
        # Log the error but don't break the application
        logger = get_logger(__name__)
        logger.error(f"Failed to log security event: {e}")


class ContextFilter(logging.Filter):
    """Filter to add context information to log records."""
    
    def __init__(self):
        super().__init__()
        self.user = None
        self.session_id = None
    
    def set_context(self, user=None, session_id=None):
        """Set context information."""
        self.user = user
        self.session_id = session_id
    
    def filter(self, record):
        """Add context information to the record."""
        record.username = self.user.username if self.user else 'system'
        record.session_id = self.session_id or 'unknown'
        return True


# Global context filter instance
context_filter = ContextFilter()


def set_logging_context(user=None, session_id=None):
    """
    Set logging context for the current session.
    
    Args:
        user: Current user
        session_id: Current session ID
    """
    context_filter.set_context(user, session_id)


def cleanup_old_logs(days_to_keep=30):
    """
    Clean up old log files.
    
    Args:
        days_to_keep: Number of days to keep log files
    """
    try:
        from datetime import timedelta
        
        log_dir = Path(__file__).parent.parent.parent / "logs"
        if not log_dir.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
        
        logger = get_logger(__name__)
        logger.info(f"Cleaned up log files older than {days_to_keep} days")
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to cleanup old logs: {e}")


# Initialize logging when module is imported
if not logging.getLogger('GroceryStorePro').handlers:
    setup_logging()
