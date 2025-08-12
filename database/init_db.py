"""
Database initialization script.

This script creates all database tables and populates them with initial data.
"""

import logging
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime

# Import all models
from .models import (
    database, ALL_MODELS,
    # User models
    User, Role, Permission, UserRole, RolePermission,
    # Product models
    Product, Category, Unit, Batch,
    # Transaction models
    StockTransaction,
    # Customer/Supplier models
    Customer, Supplier,
    # Invoice models
    Purchase, PurchaseItem, Sale, SaleItem,
    # Payment models
    Payment,
    # Accounting models
    Account, JournalEntry, JournalEntryLine,
    # System models
    AuditLog, SystemSetting
)


def initialize_database():
    """Initialize the database with tables and default data."""
    logger = logging.getLogger(__name__)
    
    try:
        # Connect to database
        database.connect()
        logger.info("Connected to database")
        
        # Create tables
        create_tables()
        logger.info("Database tables created successfully")
        
        # Initialize default data
        initialize_default_data()
        logger.info("Default data initialized successfully")
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        if not database.is_closed():
            database.close()


def create_tables():
    """Create all database tables."""
    logger = logging.getLogger(__name__)
    
    try:
        # Drop existing tables if they exist (for development)
        # In production, you might want to use migrations instead
        database.drop_tables(ALL_MODELS, safe=True)
        logger.info("Existing tables dropped")
        
        # Create all tables
        database.create_tables(ALL_MODELS, safe=True)
        logger.info("All tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


def initialize_default_data():
    """Initialize database with default data."""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize in order of dependencies
        initialize_system_settings()
        initialize_roles_and_permissions()
        initialize_default_user()
        initialize_chart_of_accounts()
        initialize_default_categories_and_units()
        
        logger.info("Default data initialization completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize default data: {e}")
        raise


def initialize_system_settings():
    """Initialize system settings."""
    logger = logging.getLogger(__name__)
    
    try:
        SystemSetting.initialize_default_settings()
        logger.info("System settings initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize system settings: {e}")
        raise


def initialize_roles_and_permissions():
    """Initialize roles and permissions."""
    logger = logging.getLogger(__name__)
    
    try:
        # Create permissions
        permissions_data = [
            # User management
            ('users.create', 'Create Users', 'users', 'create'),
            ('users.read', 'View Users', 'users', 'read'),
            ('users.update', 'Update Users', 'users', 'update'),
            ('users.delete', 'Delete Users', 'users', 'delete'),
            
            # Product management
            ('products.create', 'Create Products', 'products', 'create'),
            ('products.read', 'View Products', 'products', 'read'),
            ('products.update', 'Update Products', 'products', 'update'),
            ('products.delete', 'Delete Products', 'products', 'delete'),
            
            # Inventory management
            ('inventory.create', 'Create Inventory Transactions', 'inventory', 'create'),
            ('inventory.read', 'View Inventory', 'inventory', 'read'),
            ('inventory.update', 'Update Inventory', 'inventory', 'update'),
            ('inventory.adjust', 'Adjust Inventory', 'inventory', 'adjust'),
            
            # Sales
            ('sales.create', 'Create Sales', 'sales', 'create'),
            ('sales.read', 'View Sales', 'sales', 'read'),
            ('sales.update', 'Update Sales', 'sales', 'update'),
            ('sales.delete', 'Delete Sales', 'sales', 'delete'),
            
            # Purchases
            ('purchases.create', 'Create Purchases', 'purchases', 'create'),
            ('purchases.read', 'View Purchases', 'purchases', 'read'),
            ('purchases.update', 'Update Purchases', 'purchases', 'update'),
            ('purchases.delete', 'Delete Purchases', 'purchases', 'delete'),
            
            # Customers
            ('customers.create', 'Create Customers', 'customers', 'create'),
            ('customers.read', 'View Customers', 'customers', 'read'),
            ('customers.update', 'Update Customers', 'customers', 'update'),
            ('customers.delete', 'Delete Customers', 'customers', 'delete'),
            
            # Suppliers
            ('suppliers.create', 'Create Suppliers', 'suppliers', 'create'),
            ('suppliers.read', 'View Suppliers', 'suppliers', 'read'),
            ('suppliers.update', 'Update Suppliers', 'suppliers', 'update'),
            ('suppliers.delete', 'Delete Suppliers', 'suppliers', 'delete'),
            
            # Payments
            ('payments.create', 'Create Payments', 'payments', 'create'),
            ('payments.read', 'View Payments', 'payments', 'read'),
            ('payments.update', 'Update Payments', 'payments', 'update'),
            ('payments.delete', 'Delete Payments', 'payments', 'delete'),
            
            # Reports
            ('reports.sales', 'View Sales Reports', 'reports', 'sales'),
            ('reports.inventory', 'View Inventory Reports', 'reports', 'inventory'),
            ('reports.financial', 'View Financial Reports', 'reports', 'financial'),
            ('reports.export', 'Export Reports', 'reports', 'export'),
            
            # System
            ('system.settings', 'Manage System Settings', 'system', 'settings'),
            ('system.backup', 'Manage Backups', 'system', 'backup'),
            ('system.audit', 'View Audit Logs', 'system', 'audit'),
        ]
        
        for perm_name, description, module, action in permissions_data:
            Permission.get_or_create(
                name=perm_name,
                defaults={
                    'description': description,
                    'module': module,
                    'action': action
                }
            )
        
        # Create roles
        roles_data = [
            ('admin', 'Administrator', 'Full system access'),
            ('manager', 'Manager', 'Business operations and reports'),
            ('cashier', 'Cashier', 'Sales transactions only'),
            ('warehouse', 'Warehouse Staff', 'Inventory management'),
        ]
        
        for role_name, description, desc_ar in roles_data:
            Role.get_or_create(
                name=role_name,
                defaults={
                    'description': description,
                    'description_ar': desc_ar
                }
            )
        
        # Assign permissions to roles
        assign_role_permissions()
        
        logger.info("Roles and permissions initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize roles and permissions: {e}")
        raise


def assign_role_permissions():
    """Assign permissions to roles."""
    
    # Admin gets all permissions
    admin_role = Role.get(Role.name == 'admin')
    all_permissions = Permission.select()
    for permission in all_permissions:
        RolePermission.get_or_create(
            role=admin_role,
            permission=permission
        )
    
    # Manager permissions
    manager_role = Role.get(Role.name == 'manager')
    manager_permissions = [
        'products.create', 'products.read', 'products.update', 'products.delete',
        'inventory.create', 'inventory.read', 'inventory.update', 'inventory.adjust',
        'sales.create', 'sales.read', 'sales.update', 'sales.delete',
        'purchases.create', 'purchases.read', 'purchases.update', 'purchases.delete',
        'customers.create', 'customers.read', 'customers.update', 'customers.delete',
        'suppliers.create', 'suppliers.read', 'suppliers.update', 'suppliers.delete',
        'payments.create', 'payments.read', 'payments.update', 'payments.delete',
        'reports.sales', 'reports.inventory', 'reports.financial', 'reports.export',
    ]
    
    for perm_name in manager_permissions:
        try:
            permission = Permission.get(Permission.name == perm_name)
            RolePermission.get_or_create(
                role=manager_role,
                permission=permission
            )
        except Permission.DoesNotExist:
            continue
    
    # Cashier permissions
    cashier_role = Role.get(Role.name == 'cashier')
    cashier_permissions = [
        'products.read',
        'inventory.read',
        'sales.create', 'sales.read',
        'customers.read',
        'payments.create', 'payments.read',
    ]
    
    for perm_name in cashier_permissions:
        try:
            permission = Permission.get(Permission.name == perm_name)
            RolePermission.get_or_create(
                role=cashier_role,
                permission=permission
            )
        except Permission.DoesNotExist:
            continue
    
    # Warehouse permissions
    warehouse_role = Role.get(Role.name == 'warehouse')
    warehouse_permissions = [
        'products.create', 'products.read', 'products.update',
        'inventory.create', 'inventory.read', 'inventory.update', 'inventory.adjust',
        'purchases.create', 'purchases.read', 'purchases.update',
        'suppliers.read',
        'reports.inventory',
    ]
    
    for perm_name in warehouse_permissions:
        try:
            permission = Permission.get(Permission.name == perm_name)
            RolePermission.get_or_create(
                role=warehouse_role,
                permission=permission
            )
        except Permission.DoesNotExist:
            continue


def initialize_default_user():
    """Create default admin user."""
    logger = logging.getLogger(__name__)
    
    try:
        # Create default admin user
        try:
            admin_user = User.get(User.username == 'admin')
            logger.info("Default admin user already exists")
        except User.DoesNotExist:
            admin_user = User.create(
                username='admin',
                full_name='System Administrator',
                full_name_ar='مدير النظام',
                email='admin@grocerystorepro.com',
                is_admin=True,
                is_active=True,
                password_hash=''  # Temporary, will be set below
            )
            admin_user.set_password('admin123')
            admin_user.save()
            logger.info("Default admin user created (username: admin, password: admin123)")

            # Assign admin role
            admin_role = Role.get(Role.name == 'admin')
            UserRole.create(
                user=admin_user,
                role=admin_role
            )
        
    except Exception as e:
        logger.error(f"Failed to create default user: {e}")
        raise


def initialize_chart_of_accounts():
    """Initialize default chart of accounts."""
    logger = logging.getLogger(__name__)
    
    try:
        accounts_data = [
            # Assets
            ('1000', 'Assets', 'الأصول', 'asset', None, True, False),
            ('1100', 'Current Assets', 'الأصول المتداولة', 'asset', '1000', True, False),
            ('1110', 'Cash', 'النقدية', 'asset', '1100', True, True),
            ('1120', 'Accounts Receivable', 'الذمم المدينة', 'asset', '1100', True, True),
            ('1130', 'Inventory', 'المخزون', 'asset', '1100', True, True),
            
            # Liabilities
            ('2000', 'Liabilities', 'الخصوم', 'liability', None, True, False),
            ('2100', 'Current Liabilities', 'الخصوم المتداولة', 'liability', '2000', True, False),
            ('2110', 'Accounts Payable', 'الذمم الدائنة', 'liability', '2100', True, True),
            ('2120', 'Tax Payable', 'الضرائب المستحقة', 'liability', '2100', True, True),
            
            # Equity
            ('3000', 'Equity', 'حقوق الملكية', 'equity', None, True, False),
            ('3100', 'Owner Equity', 'رأس المال', 'equity', '3000', True, True),
            ('3200', 'Retained Earnings', 'الأرباح المحتجزة', 'equity', '3000', True, True),
            
            # Revenue
            ('4000', 'Revenue', 'الإيرادات', 'revenue', None, True, False),
            ('4100', 'Sales Revenue', 'إيرادات المبيعات', 'revenue', '4000', True, True),
            ('4200', 'Other Revenue', 'إيرادات أخرى', 'revenue', '4000', True, True),
            
            # Cost of Goods Sold
            ('5000', 'Cost of Goods Sold', 'تكلفة البضاعة المباعة', 'cogs', None, True, False),
            ('5100', 'Direct Costs', 'التكاليف المباشرة', 'cogs', '5000', True, True),
            
            # Expenses
            ('6000', 'Expenses', 'المصروفات', 'expense', None, True, False),
            ('6100', 'Operating Expenses', 'مصروفات التشغيل', 'expense', '6000', True, False),
            ('6110', 'Rent Expense', 'مصروف الإيجار', 'expense', '6100', True, True),
            ('6120', 'Utilities Expense', 'مصروف المرافق', 'expense', '6100', True, True),
            ('6130', 'Salaries Expense', 'مصروف الرواتب', 'expense', '6100', True, True),
        ]
        
        for code, name, name_ar, acc_type, parent_code, is_active, allow_posting in accounts_data:
            parent_account = None
            if parent_code:
                try:
                    parent_account = Account.get(Account.code == parent_code)
                except Account.DoesNotExist:
                    continue
            
            Account.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'name_ar': name_ar,
                    'account_type': acc_type,
                    'parent_account': parent_account,
                    'is_active': is_active,
                    'allow_posting': allow_posting,
                    'is_system_account': True
                }
            )
        
        logger.info("Chart of accounts initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize chart of accounts: {e}")
        raise


def initialize_default_categories_and_units():
    """Initialize default product categories and units."""
    logger = logging.getLogger(__name__)
    
    try:
        # Create default categories
        categories_data = [
            ('Food & Beverages', 'الأطعمة والمشروبات'),
            ('Dairy Products', 'منتجات الألبان'),
            ('Fruits & Vegetables', 'الفواكه والخضروات'),
            ('Meat & Poultry', 'اللحوم والدواجن'),
            ('Bakery', 'المخبوزات'),
            ('Beverages', 'المشروبات'),
            ('Household Items', 'المواد المنزلية'),
            ('Personal Care', 'العناية الشخصية'),
        ]
        
        for name, name_ar in categories_data:
            Category.get_or_create(
                name=name,
                defaults={'name_ar': name_ar}
            )
        
        # Create default units
        units_data = [
            ('Piece', 'قطعة', 'PC', 'قطعة'),
            ('Kilogram', 'كيلوغرام', 'KG', 'كغ'),
            ('Gram', 'غرام', 'G', 'غ'),
            ('Liter', 'لتر', 'L', 'ل'),
            ('Milliliter', 'مليلتر', 'ML', 'مل'),
            ('Box', 'صندوق', 'BOX', 'صندوق'),
            ('Pack', 'علبة', 'PACK', 'علبة'),
            ('Bottle', 'زجاجة', 'BTL', 'زجاجة'),
        ]
        
        for name, name_ar, abbr, abbr_ar in units_data:
            Unit.get_or_create(
                name=name,
                defaults={
                    'name_ar': name_ar,
                    'abbreviation': abbr,
                    'abbreviation_ar': abbr_ar
                }
            )
        
        logger.info("Default categories and units initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize categories and units: {e}")
        raise


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize database
    initialize_database()
    print("Database initialization completed successfully!")
