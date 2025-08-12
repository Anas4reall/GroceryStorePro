"""Database models package."""

from peewee import SqliteDatabase
from pathlib import Path
import os

# Database configuration
DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "grocerystore.db"

# Ensure data directory exists
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Initialize database
database = SqliteDatabase(
    str(DATABASE_PATH),
    pragmas={
        'journal_mode': 'wal',
        'cache_size': -1024 * 64,  # 64MB cache
        'foreign_keys': 1,
        'ignore_check_constraints': 0,
        'synchronous': 0
    }
)

# Import all models
from .base_model import BaseModel
from .user_models import User, Role, Permission, UserRole, RolePermission
from .product_models import Product, Category, Unit, Batch
from .transaction_models import StockTransaction
from .customer_supplier_models import Customer, Supplier
from .invoice_models import Purchase, PurchaseItem, Sale, SaleItem
from .payment_models import Payment
from .accounting_models import Account, JournalEntry, JournalEntryLine
from .audit_models import AuditLog
from .system_models import SystemSetting

# List of all models for database operations
ALL_MODELS = [
    # User management
    Role, Permission, User, UserRole, RolePermission,
    
    # Product management
    Category, Unit, Product, Batch,
    
    # Transactions
    StockTransaction,
    
    # Customers and suppliers
    Customer, Supplier,
    
    # Invoices
    Purchase, PurchaseItem, Sale, SaleItem,
    
    # Payments
    Payment,
    
    # Accounting
    Account, JournalEntry, JournalEntryLine,
    
    # System
    AuditLog, SystemSetting
]

__all__ = [
    'database',
    'BaseModel',
    'User', 'Role', 'Permission', 'UserRole', 'RolePermission',
    'Product', 'Category', 'Unit', 'Batch',
    'StockTransaction',
    'Customer', 'Supplier',
    'Purchase', 'PurchaseItem', 'Sale', 'SaleItem',
    'Payment',
    'Account', 'JournalEntry', 'JournalEntryLine',
    'AuditLog', 'SystemSetting',
    'ALL_MODELS'
]
