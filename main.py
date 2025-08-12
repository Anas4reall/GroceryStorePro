#!/usr/bin/env python3
"""
GroceryStorePro - Main Application Entry Point

A comprehensive desktop application for managing grocery warehouse operations,
supporting both wholesale and retail business models with integrated accounting.

Author: GroceryStorePro Development Team
Version: 1.0.0
License: MIT
"""

import sys
import os
import logging
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import application modules
try:
    from config.app_config import AppConfig
    from database.init_db import initialize_database
    from ui.windows.login_window import LoginWindow
    from ui.windows.main_window import MainWindow
    from logic.services.auth_service import AuthService
    from logic.utils.logger import setup_logging
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


class GroceryStoreProApp:
    """Main application class for GroceryStorePro."""
    
    def __init__(self):
        """Initialize the application."""
        self.root = None
        self.current_user = None
        self.config = None
        self.auth_service = None
        
        # Setup logging
        self.logger = setup_logging()
        self.logger.info("Starting GroceryStorePro application")
        
        # Initialize configuration
        self._load_configuration()
        
        # Initialize database
        self._initialize_database()
        
        # Initialize services
        self._initialize_services()
        
        # Setup GUI
        self._setup_gui()
    
    def _load_configuration(self):
        """Load application configuration."""
        try:
            self.config = AppConfig()
            self.logger.info("Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            messagebox.showerror(
                "Configuration Error",
                f"Failed to load application configuration:\n{e}\n\n"
                "Please check your configuration files."
            )
            sys.exit(1)
    
    def _initialize_database(self):
        """Initialize the database."""
        try:
            initialize_database()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            messagebox.showerror(
                "Database Error",
                f"Failed to initialize database:\n{e}\n\n"
                "Please check your database configuration and permissions."
            )
            sys.exit(1)
    
    def _initialize_services(self):
        """Initialize business services."""
        try:
            self.auth_service = AuthService()
            self.logger.info("Services initialized successfully")
        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}")
            messagebox.showerror(
                "Service Error",
                f"Failed to initialize services:\n{e}"
            )
            sys.exit(1)
    
    def _setup_gui(self):
        """Setup the main GUI."""
        try:
            # Create root window (hidden initially)
            self.root = tk.Tk()
            self.root.withdraw()  # Hide main window initially
            
            # Configure root window
            self.root.title("GroceryStorePro")
            self.root.geometry("1200x800")
            self.root.minsize(1024, 768)
            
            # Set application icon
            self._set_application_icon()
            
            # Configure style for modern look
            self._configure_styles()
            
            # Show login window
            self._show_login()
            
        except Exception as e:
            self.logger.error(f"GUI setup failed: {e}")
            messagebox.showerror(
                "GUI Error",
                f"Failed to setup user interface:\n{e}"
            )
            sys.exit(1)
    
    def _set_application_icon(self):
        """Set the application icon."""
        try:
            icon_path = project_root / "assets" / "icons" / "app_icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception as e:
            self.logger.warning(f"Could not set application icon: {e}")
    
    def _configure_styles(self):
        """Configure TTK styles for modern appearance."""
        try:
            style = ttk.Style()
            
            # Use a modern theme
            available_themes = style.theme_names()
            if 'clam' in available_themes:
                style.theme_use('clam')
            elif 'alt' in available_themes:
                style.theme_use('alt')
            
            # Configure custom styles
            style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
            style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
            style.configure('Success.TLabel', foreground='green')
            style.configure('Error.TLabel', foreground='red')
            style.configure('Warning.TLabel', foreground='orange')
            
        except Exception as e:
            self.logger.warning(f"Could not configure styles: {e}")
    
    def _show_login(self):
        """Show the login window."""
        try:
            login_window = LoginWindow(
                parent=self.root,
                auth_service=self.auth_service,
                on_login_success=self._on_login_success,
                config=self.config
            )
            login_window.show()
            
        except Exception as e:
            self.logger.error(f"Failed to show login window: {e}")
            messagebox.showerror(
                "Login Error",
                f"Failed to show login window:\n{e}"
            )
            sys.exit(1)
    
    def _on_login_success(self, user):
        """Handle successful login."""
        try:
            self.current_user = user
            self.logger.info(f"User {user.username} logged in successfully")
            
            # Show main application window
            self._show_main_window()
            
        except Exception as e:
            self.logger.error(f"Failed to handle login success: {e}")
            messagebox.showerror(
                "Application Error",
                f"Failed to start main application:\n{e}"
            )
    
    def _show_main_window(self):
        """Show the main application window."""
        try:
            # Show the main window
            self.root.deiconify()
            
            # Create main window content
            main_window = MainWindow(
                parent=self.root,
                current_user=self.current_user,
                config=self.config
            )
            
            # Center the window
            self._center_window()
            
            self.logger.info("Main window displayed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to show main window: {e}")
            messagebox.showerror(
                "Application Error",
                f"Failed to show main window:\n{e}"
            )
    
    def _center_window(self):
        """Center the main window on screen."""
        try:
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        except Exception as e:
            self.logger.warning(f"Could not center window: {e}")
    
    def run(self):
        """Run the application main loop."""
        try:
            self.logger.info("Starting application main loop")
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            messagebox.showerror(
                "Application Error",
                f"An unexpected error occurred:\n{e}"
            )
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Cleanup resources before exit."""
        try:
            self.logger.info("Cleaning up application resources")
            
            # Close database connections
            from database.models import database
            if not database.is_closed():
                database.close()
            
            self.logger.info("Application shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def main():
    """Main entry point."""
    try:
        # Create and run the application
        app = GroceryStoreProApp()
        app.run()
        
    except Exception as e:
        # Last resort error handling
        print(f"Fatal error: {e}")
        try:
            messagebox.showerror(
                "Fatal Error",
                f"A fatal error occurred:\n{e}\n\n"
                "Please check the log files for more details."
            )
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
