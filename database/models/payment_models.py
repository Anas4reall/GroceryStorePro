"""
Payment models.
"""

from peewee import (
    CharField, DecimalField, IntegerField, DateField,
    ForeignKeyField, TextField, DeferredForeignKey
)
from decimal import Decimal
from datetime import date
from .base_model import BaseModel


class Payment(BaseModel):
    """Payment model for tracking all payments (customer and supplier)."""
    
    # Payment types
    PAYMENT_TYPES = [
        ('customer_payment', 'Customer Payment'),
        ('supplier_payment', 'Supplier Payment'),
        ('expense', 'Expense Payment'),
        ('refund', 'Refund'),
    ]
    
    # Payment methods
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('mobile_payment', 'Mobile Payment'),
        ('other', 'Other'),
    ]
    
    # Payment statuses
    STATUSES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic payment information
    payment_no = CharField(max_length=50, unique=True)
    payment_type = CharField(max_length=20, choices=PAYMENT_TYPES)
    payment_date = DateField(default=date.today)
    amount = DecimalField(max_digits=12, decimal_places=3)
    
    # Payment method details
    payment_method = CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_no = CharField(max_length=100, null=True)  # Check number, transaction ID, etc.
    
    # Linked entity (polymorphic relationship)
    linked_to_type = CharField(max_length=20)  # 'sale', 'purchase', 'customer', 'supplier'
    linked_to_id = IntegerField()
    
    # Status
    status = CharField(max_length=20, choices=STATUSES, default='completed')
    
    # Additional information
    notes = TextField(null=True)
    internal_notes = TextField(null=True)
    
    # User who recorded the payment
    user = DeferredForeignKey('User', backref='payments', null=True, on_delete='SET NULL')
    
    class Meta:
        table_name = 'payments'
    
    def get_linked_entity(self):
        """
        Get the linked entity (sale, purchase, customer, or supplier).
        
        Returns:
            The linked model instance
        """
        if self.linked_to_type == 'sale':
            from .invoice_models import Sale
            return Sale.get_or_none_by_id(self.linked_to_id)
        elif self.linked_to_type == 'purchase':
            from .invoice_models import Purchase
            return Purchase.get_or_none_by_id(self.linked_to_id)
        elif self.linked_to_type == 'customer':
            from .customer_supplier_models import Customer
            return Customer.get_or_none_by_id(self.linked_to_id)
        elif self.linked_to_type == 'supplier':
            from .customer_supplier_models import Supplier
            return Supplier.get_or_none_by_id(self.linked_to_id)
        return None
    
    def get_linked_entity_name(self) -> str:
        """
        Get the name of the linked entity.
        
        Returns:
            Name of the linked entity
        """
        entity = self.get_linked_entity()
        if entity:
            if hasattr(entity, 'name'):
                return entity.name
            elif hasattr(entity, 'invoice_no'):
                return entity.invoice_no
        return "Unknown"
    
    @classmethod
    def create_customer_payment(cls, customer, amount, payment_method, 
                              reference_no=None, notes=None, user=None, 
                              linked_sale=None):
        """
        Create a customer payment record.
        
        Args:
            customer: Customer instance
            amount: Payment amount
            payment_method: Payment method
            reference_no: Reference number (optional)
            notes: Payment notes (optional)
            user: User who recorded the payment
            linked_sale: Specific sale this payment is for (optional)
            
        Returns:
            Payment instance
        """
        # Generate payment number
        payment_no = cls._generate_payment_number('CP')
        
        # Determine what to link to
        if linked_sale:
            linked_to_type = 'sale'
            linked_to_id = linked_sale.id
        else:
            linked_to_type = 'customer'
            linked_to_id = customer.id
        
        return cls.create(
            payment_no=payment_no,
            payment_type='customer_payment',
            amount=amount,
            payment_method=payment_method,
            reference_no=reference_no,
            linked_to_type=linked_to_type,
            linked_to_id=linked_to_id,
            notes=notes,
            user=user
        )
    
    @classmethod
    def create_supplier_payment(cls, supplier, amount, payment_method,
                              reference_no=None, notes=None, user=None,
                              linked_purchase=None):
        """
        Create a supplier payment record.
        
        Args:
            supplier: Supplier instance
            amount: Payment amount
            payment_method: Payment method
            reference_no: Reference number (optional)
            notes: Payment notes (optional)
            user: User who recorded the payment
            linked_purchase: Specific purchase this payment is for (optional)
            
        Returns:
            Payment instance
        """
        # Generate payment number
        payment_no = cls._generate_payment_number('SP')
        
        # Determine what to link to
        if linked_purchase:
            linked_to_type = 'purchase'
            linked_to_id = linked_purchase.id
        else:
            linked_to_type = 'supplier'
            linked_to_id = supplier.id
        
        return cls.create(
            payment_no=payment_no,
            payment_type='supplier_payment',
            amount=amount,
            payment_method=payment_method,
            reference_no=reference_no,
            linked_to_type=linked_to_type,
            linked_to_id=linked_to_id,
            notes=notes,
            user=user
        )
    
    @classmethod
    def _generate_payment_number(cls, prefix='PAY'):
        """
        Generate a unique payment number.
        
        Args:
            prefix: Prefix for the payment number
            
        Returns:
            Unique payment number
        """
        from datetime import datetime
        
        # Get current date
        today = datetime.now()
        date_str = today.strftime('%Y%m%d')
        
        # Find the next sequence number for today
        pattern = f"{prefix}-{date_str}-%"
        last_payment = cls.select().where(
            cls.payment_no.startswith(f"{prefix}-{date_str}-")
        ).order_by(cls.payment_no.desc()).first()
        
        if last_payment:
            # Extract sequence number from last payment
            try:
                last_seq = int(last_payment.payment_no.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1
        
        return f"{prefix}-{date_str}-{next_seq:04d}"
    
    def process_payment(self):
        """
        Process the payment and update related records.
        """
        if self.status != 'pending':
            return
        
        try:
            entity = self.get_linked_entity()
            
            if self.payment_type == 'customer_payment':
                if self.linked_to_type == 'sale':
                    # Payment for specific sale
                    entity.paid_amount += self.amount
                    entity.update_status()
                    entity.save()
                    
                    # Update customer balance
                    if entity.customer:
                        entity.customer.subtract_from_balance(self.amount)
                
                elif self.linked_to_type == 'customer':
                    # General customer payment
                    entity.subtract_from_balance(self.amount)
            
            elif self.payment_type == 'supplier_payment':
                if self.linked_to_type == 'purchase':
                    # Payment for specific purchase
                    entity.paid_amount += self.amount
                    entity.update_status()
                    entity.save()
                    
                    # Update supplier balance
                    if entity.supplier:
                        entity.supplier.subtract_from_balance(self.amount)
                
                elif self.linked_to_type == 'supplier':
                    # General supplier payment
                    entity.subtract_from_balance(self.amount)
            
            # Mark payment as completed
            self.status = 'completed'
            self.save()
            
        except Exception as e:
            # Mark payment as failed
            self.status = 'failed'
            self.internal_notes = f"Processing failed: {str(e)}"
            self.save()
            raise
    
    def reverse_payment(self):
        """
        Reverse the payment and update related records.
        """
        if self.status != 'completed':
            return
        
        try:
            entity = self.get_linked_entity()
            
            if self.payment_type == 'customer_payment':
                if self.linked_to_type == 'sale':
                    # Reverse payment for specific sale
                    entity.paid_amount -= self.amount
                    entity.update_status()
                    entity.save()
                    
                    # Update customer balance
                    if entity.customer:
                        entity.customer.add_to_balance(self.amount)
                
                elif self.linked_to_type == 'customer':
                    # Reverse general customer payment
                    entity.add_to_balance(self.amount)
            
            elif self.payment_type == 'supplier_payment':
                if self.linked_to_type == 'purchase':
                    # Reverse payment for specific purchase
                    entity.paid_amount -= self.amount
                    entity.update_status()
                    entity.save()
                    
                    # Update supplier balance
                    if entity.supplier:
                        entity.supplier.add_to_balance(self.amount)
                
                elif self.linked_to_type == 'supplier':
                    # Reverse general supplier payment
                    entity.add_to_balance(self.amount)
            
            # Mark payment as cancelled
            self.status = 'cancelled'
            self.save()
            
        except Exception as e:
            self.internal_notes = f"Reversal failed: {str(e)}"
            self.save()
            raise
    
    def __str__(self):
        return f"Payment {self.payment_no} - {self.amount} ({self.payment_method})"
