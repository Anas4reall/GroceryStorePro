"""
Login window for user authentication.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ui.components.base_window import BaseWindow
from logic.services.auth_service import AuthService
from config.app_config import AppConfig
from database.models import User


class LoginWindow(BaseWindow):
    """Login window for user authentication."""
    
    def __init__(self, parent: Optional[tk.Widget], auth_service: AuthService,
                 on_login_success: Callable[[User], None], config: AppConfig):
        """
        Initialize login window.
        
        Args:
            parent: Parent widget
            auth_service: Authentication service
            on_login_success: Callback for successful login
            config: Application configuration
        """
        self.auth_service = auth_service
        self.on_login_success = on_login_success
        self.config = config
        
        # Initialize variables
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.language_var = tk.StringVar(value=config.get_language())
        self.remember_var = tk.BooleanVar()
        
        # UI elements
        self.username_entry = None
        self.password_entry = None
        self.login_button = None
        self.status_label = None
        
        super().__init__(
            parent=parent,
            title="GroceryStorePro - Login",
            width=400,
            height=500,
            resizable=False,
            modal=True
        )
    
    def setup_ui(self):
        """Setup the login user interface."""
        # Main container
        main_frame = self.create_frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo/Title section
        self.create_title_section(main_frame)
        
        # Login form section
        self.create_login_form(main_frame)
        
        # Language selection
        self.create_language_section(main_frame)
        
        # Remember me option
        self.create_remember_section(main_frame)
        
        # Buttons section
        self.create_buttons_section(main_frame)
        
        # Status section
        self.create_status_section(main_frame)
        
        # Footer
        self.create_footer_section(main_frame)
        
        # Set initial focus
        self.username_entry.focus_set()
    
    def create_title_section(self, parent):
        """Create the title section."""
        title_frame = self.create_frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Application title
        title_label = self.create_label(
            title_frame,
            text="GroceryStorePro",
            style="Title.TLabel"
        )
        title_label.pack()
        
        # Subtitle
        subtitle_label = self.create_label(
            title_frame,
            text="Professional Grocery Store Management",
            font=('Arial', 10)
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Arabic subtitle
        arabic_subtitle = self.create_label(
            title_frame,
            text="نظام إدارة متجر البقالة المحترف",
            font=('Arial', 10)
        )
        arabic_subtitle.pack(pady=(2, 0))
    
    def create_login_form(self, parent):
        """Create the login form."""
        form_frame = self.create_frame(parent)
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Username field
        username_label = self.create_label(form_frame, text="Username / اسم المستخدم:")
        username_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.username_entry = self.create_entry(
            form_frame,
            textvariable=self.username_var,
            font=('Arial', 12),
            width=30
        )
        self.username_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Password field
        password_label = self.create_label(form_frame, text="Password / كلمة المرور:")
        password_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.password_entry = self.create_entry(
            form_frame,
            textvariable=self.password_var,
            show="*",
            font=('Arial', 12),
            width=30
        )
        self.password_entry.pack(fill=tk.X)
        
        # Bind Enter key to login
        self.bind_enter_key(self.username_entry, self.login)
        self.bind_enter_key(self.password_entry, self.login)
    
    def create_language_section(self, parent):
        """Create the language selection section."""
        lang_frame = self.create_frame(parent)
        lang_frame.pack(fill=tk.X, pady=(20, 10))
        
        lang_label = self.create_label(lang_frame, text="Language / اللغة:")
        lang_label.pack(anchor=tk.W, pady=(0, 5))
        
        lang_combobox = self.create_combobox(
            lang_frame,
            textvariable=self.language_var,
            values=["العربية (Arabic)", "English"],
            state="readonly",
            width=25
        )
        lang_combobox.pack(anchor=tk.W)
        
        # Set default selection
        if self.config.get_language() == 'ar':
            lang_combobox.set("العربية (Arabic)")
        else:
            lang_combobox.set("English")
    
    def create_remember_section(self, parent):
        """Create the remember me section."""
        remember_frame = self.create_frame(parent)
        remember_frame.pack(fill=tk.X, pady=(10, 20))
        
        remember_check = self.create_checkbutton(
            remember_frame,
            text="Remember me / تذكرني",
            variable=self.remember_var
        )
        remember_check.pack(anchor=tk.W)
    
    def create_buttons_section(self, parent):
        """Create the buttons section."""
        buttons_frame = self.create_frame(parent)
        buttons_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Create a sub-frame for button alignment
        button_container = self.create_frame(buttons_frame)
        button_container.pack()
        
        # Login button
        self.login_button = self.create_button(
            button_container,
            text="Login / دخول",
            command=self.login,
            style="Primary.TButton",
            width=15
        )
        self.login_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Exit button
        exit_button = self.create_button(
            button_container,
            text="Exit / خروج",
            command=self.on_close,
            width=15
        )
        exit_button.pack(side=tk.LEFT)
    
    def create_status_section(self, parent):
        """Create the status section."""
        status_frame = self.create_frame(parent)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.status_label = self.create_label(
            status_frame,
            text="",
            font=('Arial', 9),
            foreground="red"
        )
        self.status_label.pack()
    
    def create_footer_section(self, parent):
        """Create the footer section."""
        footer_frame = self.create_frame(parent)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Version info
        version_label = self.create_label(
            footer_frame,
            text="Version 1.0.0",
            font=('Arial', 8),
            foreground="gray"
        )
        version_label.pack(side=tk.LEFT)
        
        # Copyright
        copyright_label = self.create_label(
            footer_frame,
            text="© 2024 GroceryStorePro",
            font=('Arial', 8),
            foreground="gray"
        )
        copyright_label.pack(side=tk.RIGHT)
    
    def login(self):
        """Handle login attempt."""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        # Clear previous status
        self.status_label.config(text="")
        
        # Validate input
        if not username:
            self.show_status("Please enter username / يرجى إدخال اسم المستخدم", "error")
            self.username_entry.focus_set()
            return
        
        if not password:
            self.show_status("Please enter password / يرجى إدخال كلمة المرور", "error")
            self.password_entry.focus_set()
            return
        
        # Disable login button during authentication
        self.login_button.config(state='disabled', text="Logging in... / جاري الدخول...")
        self.window.update()
        
        try:
            # Attempt authentication
            success, user, message = self.auth_service.authenticate(
                username=username,
                password=password,
                ip_address="127.0.0.1",  # Local login
                user_agent="GroceryStorePro Desktop"
            )
            
            if success:
                self.show_status("Login successful / تم الدخول بنجاح", "success")
                
                # Update language setting if changed
                selected_lang = "ar" if "Arabic" in self.language_var.get() else "en"
                if selected_lang != self.config.get_language():
                    self.config.set('APPLICATION', 'language', selected_lang)
                    self.config.save()
                
                # Close login window and call success callback
                self.window.after(500, lambda: self._handle_login_success(user))
            else:
                self.show_status(f"Login failed: {message} / فشل الدخول: {message}", "error")
                self.password_entry.delete(0, tk.END)
                self.password_entry.focus_set()
        
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            self.show_status("Login system error / خطأ في نظام الدخول", "error")
        
        finally:
            # Re-enable login button
            self.login_button.config(state='normal', text="Login / دخول")
    
    def _handle_login_success(self, user: User):
        """Handle successful login."""
        try:
            # Create session
            session_id = self.auth_service.create_session(user, "127.0.0.1")
            
            # Call success callback
            self.on_login_success(user)
            
            # Close login window
            self.close()
            
        except Exception as e:
            self.logger.error(f"Error handling login success: {e}")
            self.show_status("Error starting session / خطأ في بدء الجلسة", "error")
    
    def show_status(self, message: str, status_type: str = "info"):
        """
        Show status message.
        
        Args:
            message: Status message
            status_type: Type of status ('info', 'success', 'error', 'warning')
        """
        colors = {
            'info': '#2c3e50',
            'success': '#27ae60',
            'error': '#e74c3c',
            'warning': '#f39c12'
        }
        
        self.status_label.config(
            text=message,
            foreground=colors.get(status_type, colors['info'])
        )
    
    def on_close(self):
        """Handle window close event."""
        # Exit the application
        if self.parent:
            self.parent.quit()
        else:
            self.window.quit()
        
        self.close()
    
    def setup_events(self):
        """Setup additional event handlers."""
        super().setup_events()
        
        # Handle window focus
        self.window.bind('<FocusIn>', self.on_focus_in)
    
    def on_focus_in(self, event):
        """Handle window focus event."""
        # Set focus to username entry if it's empty, otherwise password entry
        if not self.username_var.get().strip():
            self.username_entry.focus_set()
        elif not self.password_var.get():
            self.password_entry.focus_set()
