"""
Product management models.
"""

from peewee import (
    CharField, TextField, DecimalField, IntegerField, 
    BooleanField, DateField, ForeignKeyField
)
from decimal import Decimal
from datetime import date
from .base_model import BaseModel


class Category(BaseModel):
    """Product category model."""
    
    name = CharField(max_length=100, unique=True)
    name_ar = CharField(max_length=100, null=True)
    description = TextField(null=True)
    description_ar = TextField(null=True)
    parent_category = ForeignKeyField('self', null=True, backref='subcategories')
    is_active = BooleanField(default=True)
    
    class Meta:
        table_name = 'categories'
    
    def __str__(self):
        return self.name
    
    def get_full_path(self) -> str:
        """Get full category path (e.g., 'Food > Dairy > Milk')."""
        if self.parent_category:
            return f"{self.parent_category.get_full_path()} > {self.name}"
        return self.name


class Unit(BaseModel):
    """Unit of measurement model."""
    
    name = CharField(max_length=50, unique=True)
    name_ar = CharField(max_length=50, null=True)
    abbreviation = CharField(max_length=10, unique=True)
    abbreviation_ar = CharField(max_length=10, null=True)
    is_active = BooleanField(default=True)
    
    class Meta:
        table_name = 'units'
    
    def __str__(self):
        return self.name


class Product(BaseModel):
    """Product model."""
    
    sku = CharField(max_length=50, unique=True)
    name = CharField(max_length=200)
    name_ar = CharField(max_length=200, null=True)
    description = TextField(null=True)
    description_ar = TextField(null=True)
    
    # Categorization
    category = ForeignKeyField(Category, backref='products', null=True)
    unit = ForeignKeyField(Unit, backref='products')
    
    # Pricing
    buy_price = DecimalField(max_digits=10, decimal_places=3, default=0)
    sell_price_retail = DecimalField(max_digits=10, decimal_places=3, default=0)
    sell_price_wholesale = DecimalField(max_digits=10, decimal_places=3, default=0)
    
    # Inventory settings
    track_batches = BooleanField(default=True)
    reorder_point = IntegerField(default=0)
    max_stock_level = IntegerField(null=True)
    
    # Product attributes
    barcode = CharField(max_length=50, null=True, unique=True)
    brand = CharField(max_length=100, null=True)
    brand_ar = CharField(max_length=100, null=True)
    
    # Status
    is_active = BooleanField(default=True)
    is_perishable = BooleanField(default=False)
    
    # Tax settings
    is_taxable = BooleanField(default=True)
    tax_rate = DecimalField(max_digits=5, decimal_places=2, null=True)  # Override default tax rate
    
    class Meta:
        table_name = 'products'
    
    def get_current_stock(self) -> int:
        """
        Get current total stock quantity.
        
        Returns:
            Total stock quantity across all batches
        """
        if self.track_batches:
            return sum(batch.current_qty for batch in self.batches if batch.current_qty > 0)
        else:
            # For non-batch tracked items, sum from stock transactions
            from .transaction_models import StockTransaction
            transactions = StockTransaction.select().where(
                StockTransaction.product == self
            )
            
            total = 0
            for transaction in transactions:
                if transaction.transaction_type in ['purchase', 'adjustment_in', 'return_in']:
                    total += transaction.quantity
                elif transaction.transaction_type in ['sale', 'adjustment_out', 'return_out']:
                    total -= transaction.quantity
            
            return max(0, total)
    
    def get_available_stock(self) -> int:
        """
        Get available stock (excluding expired batches).
        
        Returns:
            Available stock quantity
        """
        if not self.track_batches:
            return self.get_current_stock()
        
        today = date.today()
        available = 0
        
        for batch in self.batches:
            if batch.current_qty > 0:
                if not batch.expiry_date or batch.expiry_date > today:
                    available += batch.current_qty
        
        return available
    
    def is_low_stock(self) -> bool:
        """
        Check if product is below reorder point.
        
        Returns:
            True if stock is low, False otherwise
        """
        return self.get_available_stock() <= self.reorder_point
    
    def get_price(self, pricing_mode: str = 'retail') -> Decimal:
        """
        Get product price based on pricing mode.
        
        Args:
            pricing_mode: 'retail' or 'wholesale'
            
        Returns:
            Product price
        """
        if pricing_mode == 'wholesale':
            return self.sell_price_wholesale
        return self.sell_price_retail
    
    def get_profit_margin(self, pricing_mode: str = 'retail') -> Decimal:
        """
        Calculate profit margin percentage.
        
        Args:
            pricing_mode: 'retail' or 'wholesale'
            
        Returns:
            Profit margin as percentage
        """
        sell_price = self.get_price(pricing_mode)
        if self.buy_price == 0:
            return Decimal('0')
        
        profit = sell_price - self.buy_price
        return (profit / self.buy_price) * 100
    
    def __str__(self):
        return f"{self.sku} - {self.name}"


class Batch(BaseModel):
    """Product batch model for tracking expiry dates and FIFO."""
    
    product = ForeignKeyField(Product, backref='batches', on_delete='CASCADE')
    batch_no = CharField(max_length=100)
    expiry_date = DateField(null=True)
    initial_qty = IntegerField()
    current_qty = IntegerField()
    cost_per_unit = DecimalField(max_digits=10, decimal_places=3)
    
    # Reference to source transaction
    source_type = CharField(max_length=20)  # 'purchase', 'adjustment'
    source_id = IntegerField()
    
    class Meta:
        table_name = 'batches'
    
    def is_expired(self) -> bool:
        """
        Check if batch is expired.
        
        Returns:
            True if expired, False otherwise
        """
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date
    
    def days_to_expiry(self) -> int:
        """
        Get number of days until expiry.
        
        Returns:
            Days to expiry (negative if expired)
        """
        if not self.expiry_date:
            return 999999  # Never expires
        
        delta = self.expiry_date - date.today()
        return delta.days
    
    def is_near_expiry(self, days_threshold: int = 7) -> bool:
        """
        Check if batch is near expiry.
        
        Args:
            days_threshold: Number of days to consider as "near expiry"
            
        Returns:
            True if near expiry, False otherwise
        """
        return 0 <= self.days_to_expiry() <= days_threshold
    
    def get_total_value(self) -> Decimal:
        """
        Get total value of current stock in this batch.
        
        Returns:
            Total value (current_qty * cost_per_unit)
        """
        return Decimal(str(self.current_qty)) * self.cost_per_unit
    
    def __str__(self):
        return f"{self.product.sku} - Batch {self.batch_no}"
