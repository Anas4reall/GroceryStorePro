"""
Stock transaction models.
"""

from peewee import (
    CharField, IntegerField, DecimalField,
    ForeignKeyField, DateTimeField, TextField, DeferredForeignKey
)
from datetime import datetime
from .base_model import BaseModel


class StockTransaction(BaseModel):
    """Stock transaction model for tracking all inventory movements."""
    
    # Transaction types
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('adjustment_in', 'Stock Adjustment In'),
        ('adjustment_out', 'Stock Adjustment Out'),
        ('return_in', 'Return In'),
        ('return_out', 'Return Out'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
        ('damage', 'Damage/Loss'),
        ('expired', 'Expired Stock'),
    ]
    
    # References - using DeferredForeignKey for forward references
    product = DeferredForeignKey('Product', backref='stock_transactions', on_delete='CASCADE')
    batch = DeferredForeignKey('Batch', backref='stock_transactions', null=True, on_delete='CASCADE')
    
    # Transaction details
    transaction_type = CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = IntegerField()  # Positive for in, negative for out
    unit_cost = DecimalField(max_digits=10, decimal_places=3, null=True)
    
    # Reference to source document
    reference_type = CharField(max_length=20, null=True)  # 'purchase', 'sale', 'adjustment'
    reference_id = IntegerField(null=True)
    reference_no = CharField(max_length=100, null=True)  # Invoice number, etc.
    
    # Additional information
    reason = CharField(max_length=200, null=True)
    notes = TextField(null=True)
    
    # User who performed the transaction
    user = DeferredForeignKey('User', backref='stock_transactions', null=True, on_delete='SET NULL')
    
    # Transaction timestamp
    transaction_date = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'stock_transactions'
    
    def is_inbound(self) -> bool:
        """
        Check if this is an inbound transaction (increases stock).
        
        Returns:
            True if inbound, False if outbound
        """
        inbound_types = ['purchase', 'adjustment_in', 'return_in', 'transfer_in']
        return self.transaction_type in inbound_types
    
    def is_outbound(self) -> bool:
        """
        Check if this is an outbound transaction (decreases stock).
        
        Returns:
            True if outbound, False if inbound
        """
        return not self.is_inbound()
    
    def get_signed_quantity(self) -> int:
        """
        Get quantity with appropriate sign (positive for in, negative for out).
        
        Returns:
            Signed quantity
        """
        if self.is_inbound():
            return abs(self.quantity)
        else:
            return -abs(self.quantity)
    
    def get_total_value(self) -> DecimalField:
        """
        Get total value of this transaction.
        
        Returns:
            Total value (quantity * unit_cost)
        """
        if self.unit_cost is None:
            return DecimalField('0')
        
        return DecimalField(str(abs(self.quantity))) * self.unit_cost
    
    @classmethod
    def create_purchase_transaction(cls, product, batch, quantity, unit_cost, 
                                  purchase_id, user=None):
        """
        Create a purchase stock transaction.
        
        Args:
            product: Product instance
            batch: Batch instance
            quantity: Quantity purchased
            unit_cost: Cost per unit
            purchase_id: Purchase record ID
            user: User who performed the transaction
            
        Returns:
            StockTransaction instance
        """
        return cls.create(
            product=product,
            batch=batch,
            transaction_type='purchase',
            quantity=abs(quantity),
            unit_cost=unit_cost,
            reference_type='purchase',
            reference_id=purchase_id,
            user=user,
            reason='Stock received from purchase'
        )
    
    @classmethod
    def create_sale_transaction(cls, product, batch, quantity, unit_cost, 
                              sale_id, user=None):
        """
        Create a sale stock transaction.
        
        Args:
            product: Product instance
            batch: Batch instance (can be None for non-batch tracked items)
            quantity: Quantity sold
            unit_cost: Cost per unit (for COGS calculation)
            sale_id: Sale record ID
            user: User who performed the transaction
            
        Returns:
            StockTransaction instance
        """
        return cls.create(
            product=product,
            batch=batch,
            transaction_type='sale',
            quantity=abs(quantity),
            unit_cost=unit_cost,
            reference_type='sale',
            reference_id=sale_id,
            user=user,
            reason='Stock sold to customer'
        )
    
    @classmethod
    def create_adjustment_transaction(cls, product, batch, quantity, reason, 
                                    user=None, notes=None):
        """
        Create a stock adjustment transaction.
        
        Args:
            product: Product instance
            batch: Batch instance (can be None)
            quantity: Adjustment quantity (positive for in, negative for out)
            reason: Reason for adjustment
            user: User who performed the adjustment
            notes: Additional notes
            
        Returns:
            StockTransaction instance
        """
        transaction_type = 'adjustment_in' if quantity > 0 else 'adjustment_out'
        
        return cls.create(
            product=product,
            batch=batch,
            transaction_type=transaction_type,
            quantity=abs(quantity),
            reference_type='adjustment',
            reason=reason,
            notes=notes,
            user=user
        )
    
    @classmethod
    def get_product_balance(cls, product, as_of_date=None):
        """
        Get current stock balance for a product.
        
        Args:
            product: Product instance
            as_of_date: Calculate balance as of this date (None for current)
            
        Returns:
            Current stock balance
        """
        query = cls.select().where(cls.product == product)
        
        if as_of_date:
            query = query.where(cls.transaction_date <= as_of_date)
        
        balance = 0
        for transaction in query:
            balance += transaction.get_signed_quantity()
        
        return max(0, balance)  # Don't allow negative stock in reporting
    
    @classmethod
    def get_batch_balance(cls, batch, as_of_date=None):
        """
        Get current stock balance for a specific batch.
        
        Args:
            batch: Batch instance
            as_of_date: Calculate balance as of this date (None for current)
            
        Returns:
            Current batch stock balance
        """
        query = cls.select().where(cls.batch == batch)
        
        if as_of_date:
            query = query.where(cls.transaction_date <= as_of_date)
        
        balance = 0
        for transaction in query:
            balance += transaction.get_signed_quantity()
        
        return max(0, balance)
    
    def __str__(self):
        direction = "IN" if self.is_inbound() else "OUT"
        return f"{self.product.sku} - {self.transaction_type.upper()} {direction} - {self.quantity}"
