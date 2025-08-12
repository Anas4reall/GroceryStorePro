"""
Application Configuration Module

Handles loading and managing application configuration settings.
"""

import os
import configparser
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class AppConfig:
    """Application configuration manager."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to configuration file. If None, uses default.
        """
        self.logger = logging.getLogger(__name__)
        
        # Set default config file path
        if config_file is None:
            config_file = Path(__file__).parent / "app_config.ini"
        
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            # Create default config if it doesn't exist
            if not self.config_file.exists():
                self._create_default_config()
            
            # Read configuration
            self.config.read(self.config_file, encoding='utf-8')
            self.logger.info(f"Configuration loaded from {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Create default configuration in memory
            self._create_default_config_in_memory()
    
    def _create_default_config(self):
        """Create default configuration file."""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create default configuration
            default_config = self._get_default_config()
            
            # Write to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                default_config.write(f)
            
            self.logger.info(f"Default configuration created at {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to create default configuration: {e}")
            raise
    
    def _create_default_config_in_memory(self):
        """Create default configuration in memory."""
        self.config = self._get_default_config()
    
    def _get_default_config(self) -> configparser.ConfigParser:
        """Get default configuration."""
        config = configparser.ConfigParser()
        
        # Application settings
        config['APPLICATION'] = {
            'name': 'GroceryStorePro',
            'version': '1.0.0',
            'language': 'ar',  # Arabic default
            'theme': 'modern',
            'debug': 'false',
            'log_level': 'INFO'
        }
        
        # Database settings
        config['DATABASE'] = {
            'type': 'sqlite',
            'path': 'data/grocerystore.db',
            'backup_enabled': 'true',
            'backup_retention_days': '14',
            'auto_backup_time': '00:00'
        }
        
        # UI settings
        config['UI'] = {
            'window_width': '1200',
            'window_height': '800',
            'min_width': '1024',
            'min_height': '768',
            'font_family': 'Arial',
            'font_size': '10',
            'rtl_support': 'true'
        }
        
        # Business settings
        config['BUSINESS'] = {
            'company_name': 'متجر البقالة المحترف',
            'company_name_en': 'Professional Grocery Store',
            'currency': 'SAR',
            'currency_symbol': 'ر.س',
            'tax_rate': '15.0',
            'allow_negative_stock': 'false',
            'default_pricing_mode': 'retail'
        }
        
        # Security settings
        config['SECURITY'] = {
            'session_timeout_minutes': '60',
            'password_min_length': '6',
            'max_login_attempts': '3',
            'lockout_duration_minutes': '15'
        }
        
        # Barcode settings
        config['BARCODE'] = {
            'enabled': 'true',
            'prefix': '',
            'suffix': '\r\n',
            'min_length': '8',
            'max_length': '20'
        }
        
        # Reports settings
        config['REPORTS'] = {
            'default_format': 'pdf',
            'output_directory': 'reports/output',
            'template_directory': 'reports/templates',
            'company_logo': 'assets/images/logo.png'
        }
        
        return config
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """
        Get configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            fallback: Default value if key not found
            
        Returns:
            Configuration value
        """
        try:
            return self.config.get(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value."""
        try:
            return self.config.getint(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get float configuration value."""
        try:
            return self.config.getfloat(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value."""
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def set(self, section: str, key: str, value: str):
        """
        Set configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            value: Configuration value
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))
    
    def save(self):
        """Save configuration to file."""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write configuration
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise
    
    def get_database_path(self) -> Path:
        """Get database file path."""
        db_path = self.get('DATABASE', 'path', 'data/grocerystore.db')
        return Path(db_path)
    
    def get_backup_directory(self) -> Path:
        """Get backup directory path."""
        return Path('data/backups')
    
    def get_reports_directory(self) -> Path:
        """Get reports output directory path."""
        reports_dir = self.get('REPORTS', 'output_directory', 'reports/output')
        return Path(reports_dir)
    
    def is_rtl_enabled(self) -> bool:
        """Check if RTL (Right-to-Left) support is enabled."""
        return self.getboolean('UI', 'rtl_support', True)
    
    def get_language(self) -> str:
        """Get current language setting."""
        return self.get('APPLICATION', 'language', 'ar')
    
    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self.getboolean('APPLICATION', 'debug', False)
    
    def get_tax_rate(self) -> float:
        """Get tax rate as decimal (e.g., 0.15 for 15%)."""
        return self.getfloat('BUSINESS', 'tax_rate', 15.0) / 100.0
    
    def allow_negative_stock(self) -> bool:
        """Check if negative stock is allowed."""
        return self.getboolean('BUSINESS', 'allow_negative_stock', False)
    
    def get_session_timeout(self) -> int:
        """Get session timeout in minutes."""
        return self.getint('SECURITY', 'session_timeout_minutes', 60)
