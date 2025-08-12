"""
Customer and supplier models.
"""

from peewee import (
    CharField, TextField, DecimalField, IntegerField, 
    BooleanField, DateField
)
from decimal import Decimal
from .base_model import BaseModel


class Customer(BaseModel):
    """Customer model."""
    
    # Customer types
    CUSTOMER_TYPES = [
        ('retail', 'Retail Customer'),
        ('wholesale', 'Wholesale Customer'),
        ('both', 'Both Retail & Wholesale'),
    ]
    
    # Basic information
    code = CharField(max_length=50, unique=True)
    name = CharField(max_length=200)
    name_ar = CharField(max_length=200, null=True)
    
    # Contact information
    phone = CharField(max_length=20, null=True)
    phone2 = CharField(max_length=20, null=True)
    email = CharField(max_length=100, null=True)
    
    # Address
    address = TextField(null=True)
    address_ar = TextField(null=True)
    city = CharField(max_length=100, null=True)
    postal_code = CharField(max_length=20, null=True)
    country = CharField(max_length=100, null=True)
    
    # Business information
    customer_type = CharField(max_length=20, choices=CUSTOMER_TYPES, default='retail')
    tax_number = CharField(max_length=50, null=True)
    commercial_registration = CharField(max_length=50, null=True)
    
    # Credit settings
    credit_limit = DecimalField(max_digits=12, decimal_places=3, default=0)
    current_balance = DecimalField(max_digits=12, decimal_places=3, default=0)
    payment_terms_days = IntegerField(default=0)  # 0 = cash only
    
    # Pricing settings
    default_pricing_mode = CharField(max_length=20, default='retail')
    discount_percentage = DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Status and settings
    is_active = BooleanField(default=True)
    allow_credit = BooleanField(default=False)
    send_statements = BooleanField(default=True)
    
    # Additional information
    notes = TextField(null=True)
    
    class Meta:
        table_name = 'customers'
    
    def get_credit_available(self) -> Decimal:
        """
        Get available credit amount.
        
        Returns:
            Available credit (credit_limit - current_balance)
        """
        return self.credit_limit - self.current_balance
    
    def is_credit_exceeded(self) -> bool:
        """
        Check if customer has exceeded credit limit.
        
        Returns:
            True if credit limit exceeded, False otherwise
        """
        return self.current_balance > self.credit_limit
    
    def can_purchase_on_credit(self, amount: Decimal) -> bool:
        """
        Check if customer can make a purchase on credit.
        
        Args:
            amount: Purchase amount to check
            
        Returns:
            True if purchase is allowed, False otherwise
        """
        if not self.allow_credit:
            return False
        
        if self.credit_limit == 0:
            return False
        
        return (self.current_balance + amount) <= self.credit_limit
    
    def add_to_balance(self, amount: Decimal):
        """
        Add amount to customer balance (for sales).
        
        Args:
            amount: Amount to add
        """
        self.current_balance += amount
        self.save()
    
    def subtract_from_balance(self, amount: Decimal):
        """
        Subtract amount from customer balance (for payments).
        
        Args:
            amount: Amount to subtract
        """
        self.current_balance -= amount
        self.save()
    
    def get_aging_balance(self):
        """
        Get aging analysis of customer balance.
        
        Returns:
            Dictionary with aging buckets
        """
        from datetime import date, timedelta
        from .invoice_models import Sale
        
        today = date.today()
        aging = {
            'current': Decimal('0'),      # 0-30 days
            'days_31_60': Decimal('0'),   # 31-60 days
            'days_61_90': Decimal('0'),   # 61-90 days
            'over_90': Decimal('0'),      # Over 90 days
        }
        
        # Get unpaid sales
        unpaid_sales = Sale.select().where(
            (Sale.customer == self) & 
            (Sale.status.in_(['partial', 'unpaid']))
        )
        
        for sale in unpaid_sales:
            outstanding = sale.total_amount - sale.paid_amount
            days_overdue = (today - sale.invoice_date).days - self.payment_terms_days
            
            if days_overdue <= 30:
                aging['current'] += outstanding
            elif days_overdue <= 60:
                aging['days_31_60'] += outstanding
            elif days_overdue <= 90:
                aging['days_61_90'] += outstanding
            else:
                aging['over_90'] += outstanding
        
        return aging
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Supplier(BaseModel):
    """Supplier model."""
    
    # Basic information
    code = CharField(max_length=50, unique=True)
    name = CharField(max_length=200)
    name_ar = CharField(max_length=200, null=True)
    
    # Contact information
    phone = CharField(max_length=20, null=True)
    phone2 = CharField(max_length=20, null=True)
    email = CharField(max_length=100, null=True)
    website = CharField(max_length=200, null=True)
    
    # Contact person
    contact_person = CharField(max_length=100, null=True)
    contact_person_ar = CharField(max_length=100, null=True)
    contact_phone = CharField(max_length=20, null=True)
    
    # Address
    address = TextField(null=True)
    address_ar = TextField(null=True)
    city = CharField(max_length=100, null=True)
    postal_code = CharField(max_length=20, null=True)
    country = CharField(max_length=100, null=True)
    
    # Business information
    tax_number = CharField(max_length=50, null=True)
    commercial_registration = CharField(max_length=50, null=True)
    
    # Payment settings
    current_balance = DecimalField(max_digits=12, decimal_places=3, default=0)
    payment_terms_days = IntegerField(default=30)
    
    # Status and settings
    is_active = BooleanField(default=True)
    is_preferred = BooleanField(default=False)
    
    # Additional information
    notes = TextField(null=True)
    
    class Meta:
        table_name = 'suppliers'
    
    def add_to_balance(self, amount: Decimal):
        """
        Add amount to supplier balance (for purchases).
        
        Args:
            amount: Amount to add
        """
        self.current_balance += amount
        self.save()
    
    def subtract_from_balance(self, amount: Decimal):
        """
        Subtract amount from supplier balance (for payments).
        
        Args:
            amount: Amount to subtract
        """
        self.current_balance -= amount
        self.save()
    
    def get_aging_balance(self):
        """
        Get aging analysis of supplier balance.
        
        Returns:
            Dictionary with aging buckets
        """
        from datetime import date, timedelta
        from .invoice_models import Purchase
        
        today = date.today()
        aging = {
            'current': Decimal('0'),      # 0-30 days
            'days_31_60': Decimal('0'),   # 31-60 days
            'days_61_90': Decimal('0'),   # 61-90 days
            'over_90': Decimal('0'),      # Over 90 days
        }
        
        # Get unpaid purchases
        unpaid_purchases = Purchase.select().where(
            (Purchase.supplier == self) & 
            (Purchase.status.in_(['partial', 'unpaid']))
        )
        
        for purchase in unpaid_purchases:
            outstanding = purchase.total_amount - purchase.paid_amount
            days_overdue = (today - purchase.invoice_date).days - self.payment_terms_days
            
            if days_overdue <= 30:
                aging['current'] += outstanding
            elif days_overdue <= 60:
                aging['days_31_60'] += outstanding
            elif days_overdue <= 90:
                aging['days_61_90'] += outstanding
            else:
                aging['over_90'] += outstanding
        
        return aging
    
    def get_total_purchases(self, start_date=None, end_date=None):
        """
        Get total purchase amount for a period.
        
        Args:
            start_date: Start date for calculation
            end_date: End date for calculation
            
        Returns:
            Total purchase amount
        """
        from .invoice_models import Purchase
        
        query = Purchase.select().where(Purchase.supplier == self)
        
        if start_date:
            query = query.where(Purchase.invoice_date >= start_date)
        if end_date:
            query = query.where(Purchase.invoice_date <= end_date)
        
        total = Decimal('0')
        for purchase in query:
            total += purchase.total_amount
        
        return total
    
    def __str__(self):
        return f"{self.code} - {self.name}"
