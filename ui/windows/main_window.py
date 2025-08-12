"""
Main application window (dashboard).
"""

import tkinter as tk
from tkinter import ttk
from datetime import date, datetime
from typing import Optional

from ui.components.base_window import BaseWindow
from database.models import User, Sale, Product
from config.app_config import AppConfig
from logic.services.inventory_service import InventoryService
from logic.services.reports_service import ReportsService


class MainWindow:
    """Main application window with dashboard."""
    
    def __init__(self, parent: tk.Widget, current_user: User, config: AppConfig):
        """
        Initialize main window.
        
        Args:
            parent: Parent widget (root window)
            current_user: Currently logged in user
            config: Application configuration
        """
        self.parent = parent
        self.current_user = current_user
        self.config = config
        
        # Services
        self.inventory_service = InventoryService()
        self.reports_service = ReportsService()
        
        # UI elements
        self.main_frame = None
        self.status_bar = None
        self.kpi_frame = None
        self.alerts_frame = None
        self.recent_transactions_frame = None
        
        # Data refresh timer
        self.refresh_timer = None
        
        # Setup UI
        self.setup_ui()
        self.setup_menu()
        self.load_dashboard_data()
        
        # Start auto-refresh
        self.start_auto_refresh()
    
    def setup_ui(self):
        """Setup the main user interface."""
        # Configure parent window
        self.parent.title("GroceryStorePro - Dashboard")
        
        # Create main container
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create header
        self.create_header()
        
        # Create KPI section
        self.create_kpi_section()
        
        # Create quick actions
        self.create_quick_actions()
        
        # Create main content area
        self.create_main_content()
        
        # Create status bar
        self.create_status_bar()
    
    def create_header(self):
        """Create the header section."""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Welcome message
        welcome_text = f"Welcome, {self.current_user.full_name} | مرحباً، {self.current_user.full_name_ar or self.current_user.full_name}"
        welcome_label = ttk.Label(
            header_frame,
            text=welcome_text,
            font=('Arial', 12, 'bold')
        )
        welcome_label.pack(side=tk.LEFT)
        
        # User info and logout
        user_frame = ttk.Frame(header_frame)
        user_frame.pack(side=tk.RIGHT)
        
        # Current date/time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        time_label = ttk.Label(
            user_frame,
            text=current_time,
            font=('Arial', 10)
        )
        time_label.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Logout button
        logout_button = ttk.Button(
            user_frame,
            text="Logout / خروج",
            command=self.logout,
            width=12
        )
        logout_button.pack(side=tk.RIGHT)
    
    def create_kpi_section(self):
        """Create the KPI (Key Performance Indicators) section."""
        kpi_label = ttk.Label(
            self.main_frame,
            text="Key Performance Indicators / المؤشرات الرئيسية",
            font=('Arial', 12, 'bold')
        )
        kpi_label.pack(anchor=tk.W, pady=(10, 5))
        
        self.kpi_frame = ttk.Frame(self.main_frame)
        self.kpi_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Create KPI cards
        self.create_kpi_card("Today Sales\nمبيعات اليوم", "0.00 SAR", "#27ae60")
        self.create_kpi_card("Low Stock\nمخزون منخفض", "0 Items", "#e74c3c")
        self.create_kpi_card("Cash Balance\nرصيد النقدية", "0.00 SAR", "#3498db")
        self.create_kpi_card("Pending Payments\nمدفوعات معلقة", "0", "#f39c12")
    
    def create_kpi_card(self, title: str, value: str, color: str):
        """Create a KPI card."""
        card_frame = ttk.LabelFrame(self.kpi_frame, text="", padding="10")
        card_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Title
        title_label = ttk.Label(
            card_frame,
            text=title,
            font=('Arial', 10, 'bold'),
            foreground=color,
            justify=tk.CENTER
        )
        title_label.pack()
        
        # Value
        value_label = ttk.Label(
            card_frame,
            text=value,
            font=('Arial', 14, 'bold'),
            justify=tk.CENTER
        )
        value_label.pack(pady=(5, 0))
        
        # Store reference for updates
        setattr(self, f"kpi_{title.split()[0].lower()}_label", value_label)
    
    def create_quick_actions(self):
        """Create quick actions section."""
        actions_label = ttk.Label(
            self.main_frame,
            text="Quick Actions / إجراءات سريعة",
            font=('Arial', 12, 'bold')
        )
        actions_label.pack(anchor=tk.W, pady=(10, 5))
        
        actions_frame = ttk.Frame(self.main_frame)
        actions_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Action buttons
        buttons = [
            ("New Sale\nمبيعة جديدة", self.new_sale, "#27ae60"),
            ("New Purchase\nمشتريات جديدة", self.new_purchase, "#3498db"),
            ("Add Product\nإضافة منتج", self.add_product, "#9b59b6"),
            ("Customer Payment\nدفعة عميل", self.customer_payment, "#e67e22"),
            ("Stock Adjust\nتعديل مخزون", self.stock_adjust, "#34495e")
        ]
        
        for text, command, color in buttons:
            button = ttk.Button(
                actions_frame,
                text=text,
                command=command,
                width=15
            )
            button.pack(side=tk.LEFT, padx=(0, 10))
    
    def create_main_content(self):
        """Create main content area with tabs."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Recent Transactions tab
        self.create_recent_transactions_tab(notebook)
        
        # Alerts & Notifications tab
        self.create_alerts_tab(notebook)
    
    def create_recent_transactions_tab(self, parent):
        """Create recent transactions tab."""
        transactions_frame = ttk.Frame(parent)
        parent.add(transactions_frame, text="Recent Transactions / المعاملات الأخيرة")
        
        # Create treeview for transactions
        columns = ('Date', 'Type', 'Customer/Supplier', 'Amount', 'Status')
        self.transactions_tree = ttk.Treeview(
            transactions_frame,
            columns=columns,
            show='headings',
            height=10
        )
        
        # Configure columns
        self.transactions_tree.heading('Date', text='Date / التاريخ')
        self.transactions_tree.heading('Type', text='Type / النوع')
        self.transactions_tree.heading('Customer/Supplier', text='Customer/Supplier / العميل/المورد')
        self.transactions_tree.heading('Amount', text='Amount / المبلغ')
        self.transactions_tree.heading('Status', text='Status / الحالة')
        
        # Configure column widths
        self.transactions_tree.column('Date', width=100)
        self.transactions_tree.column('Type', width=80)
        self.transactions_tree.column('Customer/Supplier', width=200)
        self.transactions_tree.column('Amount', width=100)
        self.transactions_tree.column('Status', width=80)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(transactions_frame, orient=tk.VERTICAL, command=self.transactions_tree.yview)
        self.transactions_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.transactions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_alerts_tab(self, parent):
        """Create alerts and notifications tab."""
        alerts_frame = ttk.Frame(parent)
        parent.add(alerts_frame, text="Alerts & Notifications / التنبيهات والإشعارات")
        
        # Create text widget for alerts
        self.alerts_text = tk.Text(
            alerts_frame,
            height=12,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        
        # Add scrollbar
        alerts_scrollbar = ttk.Scrollbar(alerts_frame, orient=tk.VERTICAL, command=self.alerts_text.yview)
        self.alerts_text.configure(yscrollcommand=alerts_scrollbar.set)
        
        # Pack widgets
        self.alerts_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alerts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_status_bar(self):
        """Create status bar."""
        self.status_bar = ttk.Frame(self.main_frame)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Status label
        self.status_label = ttk.Label(
            self.status_bar,
            text="Ready / جاهز",
            font=('Arial', 9)
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Current date
        current_date = date.today().strftime("%Y-%m-%d")
        date_label = ttk.Label(
            self.status_bar,
            text=f"Date: {current_date}",
            font=('Arial', 9)
        )
        date_label.pack(side=tk.RIGHT)
    
    def setup_menu(self):
        """Setup application menu."""
        menubar = tk.Menu(self.parent)
        self.parent.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File / ملف", menu=file_menu)
        file_menu.add_command(label="New Sale / مبيعة جديدة", command=self.new_sale)
        file_menu.add_command(label="New Purchase / مشتريات جديدة", command=self.new_purchase)
        file_menu.add_separator()
        file_menu.add_command(label="Exit / خروج", command=self.parent.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit / تحرير", menu=edit_menu)
        edit_menu.add_command(label="Products / المنتجات", command=self.manage_products)
        edit_menu.add_command(label="Customers / العملاء", command=self.manage_customers)
        edit_menu.add_command(label="Suppliers / الموردين", command=self.manage_suppliers)
        
        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports / التقارير", menu=reports_menu)
        reports_menu.add_command(label="Sales Report / تقرير المبيعات", command=self.sales_report)
        reports_menu.add_command(label="Inventory Report / تقرير المخزون", command=self.inventory_report)
        reports_menu.add_command(label="Financial Report / التقرير المالي", command=self.financial_report)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools / أدوات", menu=tools_menu)
        tools_menu.add_command(label="Settings / الإعدادات", command=self.settings)
        tools_menu.add_command(label="Backup / نسخ احتياطي", command=self.backup)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help / مساعدة", menu=help_menu)
        help_menu.add_command(label="About / حول", command=self.about)
    
    def load_dashboard_data(self):
        """Load dashboard data."""
        try:
            # Update KPIs
            self.update_kpis()
            
            # Load recent transactions
            self.load_recent_transactions()
            
            # Load alerts
            self.load_alerts()
            
            # Update status
            self.status_label.config(text="Data loaded / تم تحميل البيانات")
            
        except Exception as e:
            self.status_label.config(text=f"Error loading data / خطأ في تحميل البيانات: {str(e)}")
    
    def update_kpis(self):
        """Update KPI values."""
        try:
            # Today's sales
            today = date.today()
            today_sales = Sale.select().where(Sale.invoice_date == today)
            total_sales = sum(sale.total_amount for sale in today_sales)
            
            if hasattr(self, 'kpi_today_label'):
                self.kpi_today_label.config(text=f"{total_sales:.2f} SAR")
            
            # Low stock items
            alerts = self.inventory_service.get_stock_alerts()
            low_stock_count = len([alert for alert in alerts if alert.alert_type == 'low_stock'])
            
            if hasattr(self, 'kpi_low_label'):
                self.kpi_low_label.config(text=f"{low_stock_count} Items")
            
            # Cash balance (placeholder - would need actual cash account balance)
            if hasattr(self, 'kpi_cash_label'):
                self.kpi_cash_label.config(text="0.00 SAR")
            
            # Pending payments (placeholder)
            if hasattr(self, 'kpi_pending_label'):
                self.kpi_pending_label.config(text="0")
                
        except Exception as e:
            print(f"Error updating KPIs: {e}")
    
    def load_recent_transactions(self):
        """Load recent transactions."""
        try:
            # Clear existing items
            for item in self.transactions_tree.get_children():
                self.transactions_tree.delete(item)
            
            # Get recent sales (last 10)
            recent_sales = Sale.select().order_by(Sale.created_at.desc()).limit(10)
            
            for sale in recent_sales:
                customer_name = sale.customer.name if sale.customer else "Walk-in Customer"
                self.transactions_tree.insert('', 'end', values=(
                    sale.invoice_date.strftime('%Y-%m-%d'),
                    'Sale',
                    customer_name,
                    f"{sale.total_amount:.2f} SAR",
                    sale.status.title()
                ))
                
        except Exception as e:
            print(f"Error loading recent transactions: {e}")
    
    def load_alerts(self):
        """Load alerts and notifications."""
        try:
            # Clear existing alerts
            self.alerts_text.delete(1.0, tk.END)
            
            # Get stock alerts
            alerts = self.inventory_service.get_stock_alerts()
            
            if alerts:
                self.alerts_text.insert(tk.END, "Stock Alerts / تنبيهات المخزون:\n\n")
                
                for alert in alerts:
                    severity_icon = "⚠️" if alert.severity == "warning" else "🔴"
                    alert_text = f"{severity_icon} {alert.product.name}: {alert.message}\n"
                    self.alerts_text.insert(tk.END, alert_text)
            else:
                self.alerts_text.insert(tk.END, "No alerts / لا توجد تنبيهات\n")
            
            # Add system notifications
            self.alerts_text.insert(tk.END, "\nSystem Notifications / إشعارات النظام:\n")
            self.alerts_text.insert(tk.END, "ℹ️ System is running normally / النظام يعمل بشكل طبيعي\n")
            
        except Exception as e:
            self.alerts_text.insert(tk.END, f"Error loading alerts / خطأ في تحميل التنبيهات: {str(e)}\n")
    
    def start_auto_refresh(self):
        """Start auto-refresh timer."""
        # Refresh every 5 minutes
        self.refresh_timer = self.parent.after(300000, self.auto_refresh)
    
    def auto_refresh(self):
        """Auto-refresh dashboard data."""
        self.load_dashboard_data()
        self.start_auto_refresh()
    
    # Menu command handlers (placeholders)
    def new_sale(self):
        """Open new sale window."""
        self.status_label.config(text="Opening new sale window... / فتح نافذة مبيعة جديدة...")
    
    def new_purchase(self):
        """Open new purchase window."""
        self.status_label.config(text="Opening new purchase window... / فتح نافذة مشتريات جديدة...")
    
    def add_product(self):
        """Open add product dialog."""
        self.status_label.config(text="Opening add product dialog... / فتح حوار إضافة منتج...")
    
    def customer_payment(self):
        """Open customer payment dialog."""
        self.status_label.config(text="Opening customer payment dialog... / فتح حوار دفعة عميل...")
    
    def stock_adjust(self):
        """Open stock adjustment dialog."""
        self.status_label.config(text="Opening stock adjustment dialog... / فتح حوار تعديل مخزون...")
    
    def manage_products(self):
        """Open products management window."""
        self.status_label.config(text="Opening products management... / فتح إدارة المنتجات...")
    
    def manage_customers(self):
        """Open customers management window."""
        self.status_label.config(text="Opening customers management... / فتح إدارة العملاء...")
    
    def manage_suppliers(self):
        """Open suppliers management window."""
        self.status_label.config(text="Opening suppliers management... / فتح إدارة الموردين...")
    
    def sales_report(self):
        """Open sales report."""
        self.status_label.config(text="Opening sales report... / فتح تقرير المبيعات...")
    
    def inventory_report(self):
        """Open inventory report."""
        self.status_label.config(text="Opening inventory report... / فتح تقرير المخزون...")
    
    def financial_report(self):
        """Open financial report."""
        self.status_label.config(text="Opening financial report... / فتح التقرير المالي...")
    
    def settings(self):
        """Open settings window."""
        self.status_label.config(text="Opening settings... / فتح الإعدادات...")
    
    def backup(self):
        """Open backup dialog."""
        self.status_label.config(text="Opening backup dialog... / فتح حوار النسخ الاحتياطي...")
    
    def about(self):
        """Show about dialog."""
        about_text = """GroceryStorePro v1.0.0
Professional Grocery Store Management System
نظام إدارة متجر البقالة المحترف

© 2024 GroceryStorePro
All rights reserved."""
        
        tk.messagebox.showinfo("About / حول", about_text)
    
    def logout(self):
        """Logout current user."""
        if tk.messagebox.askyesno("Logout / خروج", "Are you sure you want to logout? / هل أنت متأكد من الخروج؟"):
            # Cancel refresh timer
            if self.refresh_timer:
                self.parent.after_cancel(self.refresh_timer)
            
            # Close application
            self.parent.quit()
