"""
Base window class for all application windows.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any
from abc import ABC, abstractmethod

from logic.utils.logger import get_logger


class BaseWindow(ABC):
    """Base class for all application windows."""
    
    def __init__(self, parent: Optional[tk.Widget] = None, title: str = "GroceryStorePro",
                 width: int = 800, height: int = 600, resizable: bool = True,
                 modal: bool = False):
        """
        Initialize base window.
        
        Args:
            parent: Parent widget
            title: Window title
            width: Window width
            height: Window height
            resizable: Whether window is resizable
            modal: Whether window is modal
        """
        self.logger = get_logger(self.__class__.__name__)
        self.parent = parent
        self.title = title
        self.width = width
        self.height = height
        self.resizable = resizable
        self.modal = modal
        
        # Create window
        if modal and parent:
            self.window = tk.Toplevel(parent)
            self.window.transient(parent)
            self.window.grab_set()
        else:
            self.window = tk.Toplevel(parent) if parent else tk.Tk()
        
        # Configure window
        self.window.title(title)
        self.window.geometry(f"{width}x{height}")
        
        if not resizable:
            self.window.resizable(False, False)
        
        # Center window
        self.center_window()
        
        # Setup UI
        self.setup_ui()
        
        # Setup event handlers
        self.setup_events()
        
        # Apply theme
        self.apply_theme()
    
    def center_window(self):
        """Center the window on screen or parent."""
        self.window.update_idletasks()
        
        if self.parent:
            # Center on parent
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            x = parent_x + (parent_width - self.width) // 2
            y = parent_y + (parent_height - self.height) // 2
        else:
            # Center on screen
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            x = (screen_width - self.width) // 2
            y = (screen_height - self.height) // 2
        
        self.window.geometry(f"{self.width}x{self.height}+{x}+{y}")
    
    @abstractmethod
    def setup_ui(self):
        """Setup the user interface. Must be implemented by subclasses."""
        pass
    
    def setup_events(self):
        """Setup event handlers. Can be overridden by subclasses."""
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Handle escape key for modal windows
        if self.modal:
            self.window.bind('<Escape>', lambda e: self.on_close())
    
    def apply_theme(self):
        """Apply theme to the window."""
        try:
            style = ttk.Style()
            
            # Configure modern theme
            style.theme_use('clam')
            
            # Configure custom styles
            style.configure('Title.TLabel', 
                          font=('Arial', 16, 'bold'),
                          foreground='#2c3e50')
            
            style.configure('Heading.TLabel', 
                          font=('Arial', 12, 'bold'),
                          foreground='#34495e')
            
            style.configure('Success.TLabel', 
                          foreground='#27ae60')
            
            style.configure('Error.TLabel', 
                          foreground='#e74c3c')
            
            style.configure('Warning.TLabel', 
                          foreground='#f39c12')
            
            # Button styles
            style.configure('Primary.TButton',
                          font=('Arial', 10, 'bold'))
            
            style.configure('Success.TButton',
                          foreground='white')
            
            style.configure('Danger.TButton',
                          foreground='white')
            
        except Exception as e:
            self.logger.warning(f"Failed to apply theme: {e}")
    
    def show(self):
        """Show the window."""
        self.window.deiconify()
        self.window.lift()
        self.window.focus_set()
        
        if self.modal:
            self.window.wait_window()
    
    def hide(self):
        """Hide the window."""
        self.window.withdraw()
    
    def close(self):
        """Close the window."""
        if self.modal and self.parent:
            self.window.grab_release()
        self.window.destroy()
    
    def on_close(self):
        """Handle window close event. Can be overridden by subclasses."""
        self.close()
    
    def show_error(self, title: str, message: str):
        """Show error message dialog."""
        messagebox.showerror(title, message, parent=self.window)
    
    def show_warning(self, title: str, message: str):
        """Show warning message dialog."""
        messagebox.showwarning(title, message, parent=self.window)
    
    def show_info(self, title: str, message: str):
        """Show information message dialog."""
        messagebox.showinfo(title, message, parent=self.window)
    
    def ask_yes_no(self, title: str, message: str) -> bool:
        """Show yes/no confirmation dialog."""
        return messagebox.askyesno(title, message, parent=self.window)
    
    def ask_ok_cancel(self, title: str, message: str) -> bool:
        """Show OK/Cancel confirmation dialog."""
        return messagebox.askokcancel(title, message, parent=self.window)
    
    def create_frame(self, parent: tk.Widget, **kwargs) -> ttk.Frame:
        """Create a themed frame."""
        return ttk.Frame(parent, **kwargs)
    
    def create_label(self, parent: tk.Widget, text: str, style: str = None, **kwargs) -> ttk.Label:
        """Create a themed label."""
        if style:
            return ttk.Label(parent, text=text, style=style, **kwargs)
        return ttk.Label(parent, text=text, **kwargs)
    
    def create_button(self, parent: tk.Widget, text: str, command: Callable = None,
                     style: str = None, **kwargs) -> ttk.Button:
        """Create a themed button."""
        if style:
            return ttk.Button(parent, text=text, command=command, style=style, **kwargs)
        return ttk.Button(parent, text=text, command=command, **kwargs)
    
    def create_entry(self, parent: tk.Widget, **kwargs) -> ttk.Entry:
        """Create a themed entry widget."""
        return ttk.Entry(parent, **kwargs)
    
    def create_text(self, parent: tk.Widget, **kwargs) -> tk.Text:
        """Create a text widget."""
        return tk.Text(parent, **kwargs)
    
    def create_listbox(self, parent: tk.Widget, **kwargs) -> tk.Listbox:
        """Create a listbox widget."""
        return tk.Listbox(parent, **kwargs)
    
    def create_treeview(self, parent: tk.Widget, columns: list = None, **kwargs) -> ttk.Treeview:
        """Create a treeview widget."""
        if columns:
            return ttk.Treeview(parent, columns=columns, **kwargs)
        return ttk.Treeview(parent, **kwargs)
    
    def create_combobox(self, parent: tk.Widget, values: list = None, **kwargs) -> ttk.Combobox:
        """Create a combobox widget."""
        combobox = ttk.Combobox(parent, **kwargs)
        if values:
            combobox['values'] = values
        return combobox
    
    def create_checkbutton(self, parent: tk.Widget, text: str, variable: tk.Variable = None,
                          **kwargs) -> ttk.Checkbutton:
        """Create a checkbutton widget."""
        return ttk.Checkbutton(parent, text=text, variable=variable, **kwargs)
    
    def create_radiobutton(self, parent: tk.Widget, text: str, variable: tk.Variable = None,
                          value: Any = None, **kwargs) -> ttk.Radiobutton:
        """Create a radiobutton widget."""
        return ttk.Radiobutton(parent, text=text, variable=variable, value=value, **kwargs)
    
    def create_scrollbar(self, parent: tk.Widget, **kwargs) -> ttk.Scrollbar:
        """Create a scrollbar widget."""
        return ttk.Scrollbar(parent, **kwargs)
    
    def create_separator(self, parent: tk.Widget, **kwargs) -> ttk.Separator:
        """Create a separator widget."""
        return ttk.Separator(parent, **kwargs)
    
    def create_progressbar(self, parent: tk.Widget, **kwargs) -> ttk.Progressbar:
        """Create a progressbar widget."""
        return ttk.Progressbar(parent, **kwargs)
    
    def create_notebook(self, parent: tk.Widget, **kwargs) -> ttk.Notebook:
        """Create a notebook widget."""
        return ttk.Notebook(parent, **kwargs)
    
    def create_panedwindow(self, parent: tk.Widget, **kwargs) -> ttk.PanedWindow:
        """Create a panedwindow widget."""
        return ttk.PanedWindow(parent, **kwargs)
    
    def bind_enter_key(self, widget: tk.Widget, command: Callable):
        """Bind Enter key to a command."""
        widget.bind('<Return>', lambda e: command())
    
    def bind_escape_key(self, widget: tk.Widget, command: Callable):
        """Bind Escape key to a command."""
        widget.bind('<Escape>', lambda e: command())
    
    def set_focus(self, widget: tk.Widget):
        """Set focus to a widget."""
        widget.focus_set()
    
    def disable_widget(self, widget: tk.Widget):
        """Disable a widget."""
        widget.configure(state='disabled')
    
    def enable_widget(self, widget: tk.Widget):
        """Enable a widget."""
        widget.configure(state='normal')
    
    def clear_entry(self, entry: ttk.Entry):
        """Clear an entry widget."""
        entry.delete(0, tk.END)
    
    def get_entry_text(self, entry: ttk.Entry) -> str:
        """Get text from an entry widget."""
        return entry.get().strip()
    
    def set_entry_text(self, entry: ttk.Entry, text: str):
        """Set text in an entry widget."""
        entry.delete(0, tk.END)
        entry.insert(0, text)
    
    def validate_required_fields(self, fields: Dict[str, tk.Widget]) -> bool:
        """
        Validate that required fields are not empty.
        
        Args:
            fields: Dictionary of field_name: widget pairs
            
        Returns:
            True if all fields are valid, False otherwise
        """
        for field_name, widget in fields.items():
            if isinstance(widget, ttk.Entry):
                if not self.get_entry_text(widget):
                    self.show_error("Validation Error", f"{field_name} is required")
                    widget.focus_set()
                    return False
            elif isinstance(widget, ttk.Combobox):
                if not widget.get().strip():
                    self.show_error("Validation Error", f"{field_name} is required")
                    widget.focus_set()
                    return False
        
        return True
