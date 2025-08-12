"""
Invoice models for purchases and sales.
"""

from peewee import (
    CharField, DecimalField, IntegerField, DateField,
    ForeignKeyField, TextField, BooleanField, DeferredForeignKey
)
from decimal import Decimal
from datetime import date
from .base_model import BaseModel


class Purchase(BaseModel):
    """Purchase invoice model."""
    
    # Invoice statuses
    STATUSES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Invoice details
    invoice_no = CharField(max_length=50, unique=True)
    supplier_invoice_no = CharField(max_length=50, null=True)
    supplier = DeferredForeignKey('Supplier', backref='purchases', on_delete='RESTRICT')
    invoice_date = DateField(default=date.today)
    due_date = DateField(null=True)
    
    # Amounts
    subtotal = DecimalField(max_digits=12, decimal_places=3, default=0)
    discount_amount = DecimalField(max_digits=12, decimal_places=3, default=0)
    discount_percentage = DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = DecimalField(max_digits=12, decimal_places=3, default=0)
    tax_rate = DecimalField(max_digits=5, decimal_places=2, default=0)
    total_amount = DecimalField(max_digits=12, decimal_places=3, default=0)
    paid_amount = DecimalField(max_digits=12, decimal_places=3, default=0)
    
    # Status and settings
    status = CharField(max_length=20, choices=STATUSES, default='draft')
    is_received = BooleanField(default=False)  # Stock received
    
    # Additional information
    notes = TextField(null=True)
    internal_notes = TextField(null=True)
    
    # User who created the invoice
    user = DeferredForeignKey('User', backref='purchases', null=True, on_delete='SET NULL')
    
    class Meta:
        table_name = 'purchases'
    
    def calculate_totals(self):
        """Calculate and update invoice totals."""
        # Calculate subtotal from items
        self.subtotal = sum(item.line_total for item in self.purchase_items)
        
        # Apply discount
        if self.discount_percentage > 0:
            self.discount_amount = (self.subtotal * self.discount_percentage) / 100
        
        # Calculate tax
        taxable_amount = self.subtotal - self.discount_amount
        if self.tax_rate > 0:
            self.tax_amount = (taxable_amount * self.tax_rate) / 100
        
        # Calculate total
        self.total_amount = taxable_amount + self.tax_amount
        
        self.save()
    
    def get_outstanding_amount(self) -> Decimal:
        """Get outstanding amount to be paid."""
        return self.total_amount - self.paid_amount
    
    def is_fully_paid(self) -> bool:
        """Check if invoice is fully paid."""
        return self.paid_amount >= self.total_amount
    
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if not self.due_date:
            return False
        return date.today() > self.due_date and not self.is_fully_paid()
    
    def update_status(self):
        """Update invoice status based on payment amount."""
        if self.paid_amount == 0:
            self.status = 'confirmed' if self.status != 'draft' else 'draft'
        elif self.paid_amount >= self.total_amount:
            self.status = 'paid'
        else:
            self.status = 'partial'
        self.save()
    
    def __str__(self):
        return f"Purchase {self.invoice_no} - {self.supplier.name}"


class PurchaseItem(BaseModel):
    """Purchase invoice line item."""
    
    purchase = ForeignKeyField(Purchase, backref='purchase_items', on_delete='CASCADE')
    product = DeferredForeignKey('Product', backref='purchase_items', on_delete='RESTRICT')
    
    # Batch information
    batch_no = CharField(max_length=100, null=True)
    expiry_date = DateField(null=True)
    
    # Quantities and pricing
    quantity = IntegerField()
    unit_cost = DecimalField(max_digits=10, decimal_places=3)
    line_total = DecimalField(max_digits=12, decimal_places=3)
    
    # Additional information
    notes = TextField(null=True)
    
    class Meta:
        table_name = 'purchase_items'
    
    def calculate_line_total(self):
        """Calculate and update line total."""
        self.line_total = Decimal(str(self.quantity)) * self.unit_cost
        self.save()
    
    def __str__(self):
        return f"{self.purchase.invoice_no} - {self.product.name} x {self.quantity}"


class Sale(BaseModel):
    """Sales invoice model."""
    
    # Invoice statuses
    STATUSES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    # Pricing modes
    PRICING_MODES = [
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
    ]
    
    # Invoice details
    invoice_no = CharField(max_length=50, unique=True)
    customer = DeferredForeignKey('Customer', backref='sales', null=True, on_delete='RESTRICT')
    invoice_date = DateField(default=date.today)
    due_date = DateField(null=True)
    
    # Pricing
    pricing_mode = CharField(max_length=20, choices=PRICING_MODES, default='retail')
    
    # Amounts
    subtotal = DecimalField(max_digits=12, decimal_places=3, default=0)
    discount_amount = DecimalField(max_digits=12, decimal_places=3, default=0)
    discount_percentage = DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = DecimalField(max_digits=12, decimal_places=3, default=0)
    tax_rate = DecimalField(max_digits=5, decimal_places=2, default=0)
    total_amount = DecimalField(max_digits=12, decimal_places=3, default=0)
    paid_amount = DecimalField(max_digits=12, decimal_places=3, default=0)
    
    # Status and settings
    status = CharField(max_length=20, choices=STATUSES, default='draft')
    
    # Additional information
    notes = TextField(null=True)
    internal_notes = TextField(null=True)
    
    # User who created the invoice
    user = DeferredForeignKey('User', backref='sales', null=True, on_delete='SET NULL')
    
    class Meta:
        table_name = 'sales'
    
    def calculate_totals(self):
        """Calculate and update invoice totals."""
        # Calculate subtotal from items
        self.subtotal = sum(item.line_total for item in self.sale_items)
        
        # Apply discount
        if self.discount_percentage > 0:
            self.discount_amount = (self.subtotal * self.discount_percentage) / 100
        
        # Calculate tax
        taxable_amount = self.subtotal - self.discount_amount
        if self.tax_rate > 0:
            self.tax_amount = (taxable_amount * self.tax_rate) / 100
        
        # Calculate total
        self.total_amount = taxable_amount + self.tax_amount
        
        self.save()
    
    def get_outstanding_amount(self) -> Decimal:
        """Get outstanding amount to be paid."""
        return self.total_amount - self.paid_amount
    
    def is_fully_paid(self) -> bool:
        """Check if invoice is fully paid."""
        return self.paid_amount >= self.total_amount
    
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if not self.due_date:
            return False
        return date.today() > self.due_date and not self.is_fully_paid()
    
    def update_status(self):
        """Update invoice status based on payment amount."""
        if self.paid_amount == 0:
            self.status = 'confirmed' if self.status != 'draft' else 'draft'
        elif self.paid_amount >= self.total_amount:
            self.status = 'paid'
        else:
            self.status = 'partial'
        self.save()
    
    def get_cost_of_goods_sold(self) -> Decimal:
        """Calculate total cost of goods sold for this sale."""
        total_cogs = Decimal('0')
        for item in self.sale_items:
            if item.batch:
                total_cogs += item.batch.cost_per_unit * Decimal(str(item.quantity))
            else:
                # For non-batch tracked items, use product buy price
                total_cogs += item.product.buy_price * Decimal(str(item.quantity))
        return total_cogs
    
    def get_gross_profit(self) -> Decimal:
        """Calculate gross profit for this sale."""
        return self.total_amount - self.get_cost_of_goods_sold()
    
    def get_profit_margin(self) -> Decimal:
        """Calculate profit margin percentage."""
        if self.total_amount == 0:
            return Decimal('0')
        return (self.get_gross_profit() / self.total_amount) * 100
    
    def __str__(self):
        customer_name = self.customer.name if self.customer else "Walk-in Customer"
        return f"Sale {self.invoice_no} - {customer_name}"


class SaleItem(BaseModel):
    """Sales invoice line item."""
    
    sale = ForeignKeyField(Sale, backref='sale_items', on_delete='CASCADE')
    product = DeferredForeignKey('Product', backref='sale_items', on_delete='RESTRICT')
    batch = DeferredForeignKey('Batch', backref='sale_items', null=True, on_delete='RESTRICT')
    
    # Quantities and pricing
    quantity = IntegerField()
    unit_price = DecimalField(max_digits=10, decimal_places=3)
    line_discount_percentage = DecimalField(max_digits=5, decimal_places=2, default=0)
    line_discount_amount = DecimalField(max_digits=10, decimal_places=3, default=0)
    line_total = DecimalField(max_digits=12, decimal_places=3)
    
    # Additional information
    notes = TextField(null=True)
    
    class Meta:
        table_name = 'sale_items'
    
    def calculate_line_total(self):
        """Calculate and update line total."""
        subtotal = Decimal(str(self.quantity)) * self.unit_price
        
        # Apply line discount
        if self.line_discount_percentage > 0:
            self.line_discount_amount = (subtotal * self.line_discount_percentage) / 100
        
        self.line_total = subtotal - self.line_discount_amount
        self.save()
    
    def get_cost_of_goods_sold(self) -> Decimal:
        """Get cost of goods sold for this line item."""
        if self.batch:
            return self.batch.cost_per_unit * Decimal(str(self.quantity))
        else:
            return self.product.buy_price * Decimal(str(self.quantity))
    
    def get_gross_profit(self) -> Decimal:
        """Get gross profit for this line item."""
        return self.line_total - self.get_cost_of_goods_sold()
    
    def __str__(self):
        return f"{self.sale.invoice_no} - {self.product.name} x {self.quantity}"
