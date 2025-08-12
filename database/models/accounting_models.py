"""
Accounting models for integrated accounting system.
"""

from peewee import (
    CharField, DecimalField, IntegerField, DateField,
    ForeignKeyField, TextField, BooleanField, DeferredForeignKey
)
from decimal import Decimal
from datetime import date
from .base_model import BaseModel


class Account(BaseModel):
    """Chart of accounts model."""
    
    # Account types
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
        ('cogs', 'Cost of Goods Sold'),
    ]
    
    # Account subtypes
    ACCOUNT_SUBTYPES = [
        # Assets
        ('current_asset', 'Current Asset'),
        ('fixed_asset', 'Fixed Asset'),
        ('other_asset', 'Other Asset'),
        
        # Liabilities
        ('current_liability', 'Current Liability'),
        ('long_term_liability', 'Long Term Liability'),
        
        # Equity
        ('owner_equity', 'Owner Equity'),
        ('retained_earnings', 'Retained Earnings'),
        
        # Revenue
        ('sales_revenue', 'Sales Revenue'),
        ('other_revenue', 'Other Revenue'),
        
        # Expenses
        ('operating_expense', 'Operating Expense'),
        ('administrative_expense', 'Administrative Expense'),
        ('financial_expense', 'Financial Expense'),
        
        # COGS
        ('direct_cost', 'Direct Cost'),
        ('indirect_cost', 'Indirect Cost'),
    ]
    
    # Account information
    code = CharField(max_length=20, unique=True)
    name = CharField(max_length=200)
    name_ar = CharField(max_length=200, null=True)
    description = TextField(null=True)
    description_ar = TextField(null=True)
    
    # Account classification
    account_type = CharField(max_length=20, choices=ACCOUNT_TYPES)
    account_subtype = CharField(max_length=30, choices=ACCOUNT_SUBTYPES, null=True)
    
    # Hierarchy
    parent_account = ForeignKeyField('self', null=True, backref='sub_accounts')
    level = IntegerField(default=0)
    
    # Settings
    is_active = BooleanField(default=True)
    is_system_account = BooleanField(default=False)  # Cannot be deleted
    allow_posting = BooleanField(default=True)  # Allow direct posting
    
    # Balance tracking
    current_balance = DecimalField(max_digits=15, decimal_places=3, default=0)
    
    class Meta:
        table_name = 'accounts'
    
    def get_full_code(self) -> str:
        """Get full account code including parent codes."""
        if self.parent_account:
            return f"{self.parent_account.get_full_code()}.{self.code}"
        return self.code
    
    def get_full_name(self) -> str:
        """Get full account name including parent names."""
        if self.parent_account:
            return f"{self.parent_account.get_full_name()} > {self.name}"
        return self.name
    
    def is_debit_account(self) -> bool:
        """Check if this is a debit account (increases with debits)."""
        return self.account_type in ['asset', 'expense', 'cogs']
    
    def is_credit_account(self) -> bool:
        """Check if this is a credit account (increases with credits)."""
        return self.account_type in ['liability', 'equity', 'revenue']
    
    def get_balance(self, as_of_date=None) -> Decimal:
        """
        Get account balance as of a specific date.
        
        Args:
            as_of_date: Date to calculate balance (None for current)
            
        Returns:
            Account balance
        """
        from .accounting_models import JournalEntryLine
        
        query = JournalEntryLine.select().join(JournalEntry).where(
            JournalEntryLine.account == self
        )
        
        if as_of_date:
            query = query.where(JournalEntry.entry_date <= as_of_date)
        
        total_debits = Decimal('0')
        total_credits = Decimal('0')
        
        for line in query:
            total_debits += line.debit_amount
            total_credits += line.credit_amount
        
        # Calculate balance based on account type
        if self.is_debit_account():
            return total_debits - total_credits
        else:
            return total_credits - total_debits
    
    def update_balance(self):
        """Update the current balance field."""
        self.current_balance = self.get_balance()
        self.save()
    
    @classmethod
    def get_system_accounts(cls):
        """Get dictionary of system accounts."""
        accounts = {}
        system_accounts = cls.select().where(cls.is_system_account == True)
        
        for account in system_accounts:
            # Use a simplified key based on account purpose
            if 'cash' in account.name.lower():
                accounts['cash'] = account
            elif 'inventory' in account.name.lower():
                accounts['inventory'] = account
            elif 'accounts_receivable' in account.code.lower():
                accounts['accounts_receivable'] = account
            elif 'accounts_payable' in account.code.lower():
                accounts['accounts_payable'] = account
            elif 'sales' in account.name.lower() and account.account_type == 'revenue':
                accounts['sales'] = account
            elif 'cogs' in account.name.lower() or account.account_type == 'cogs':
                accounts['cogs'] = account
        
        return accounts
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(BaseModel):
    """Journal entry model."""
    
    # Entry types
    ENTRY_TYPES = [
        ('manual', 'Manual Entry'),
        ('sale', 'Sales Transaction'),
        ('purchase', 'Purchase Transaction'),
        ('payment', 'Payment Transaction'),
        ('adjustment', 'Adjustment Entry'),
        ('closing', 'Closing Entry'),
    ]
    
    # Entry information
    entry_no = CharField(max_length=50, unique=True)
    entry_date = DateField(default=date.today)
    entry_type = CharField(max_length=20, choices=ENTRY_TYPES, default='manual')
    
    # Description
    description = CharField(max_length=500)
    description_ar = CharField(max_length=500, null=True)
    
    # Reference to source transaction
    reference_type = CharField(max_length=20, null=True)  # 'sale', 'purchase', 'payment'
    reference_id = IntegerField(null=True)
    reference_no = CharField(max_length=100, null=True)
    
    # Totals (for validation)
    total_debit = DecimalField(max_digits=15, decimal_places=3, default=0)
    total_credit = DecimalField(max_digits=15, decimal_places=3, default=0)
    
    # Status
    is_posted = BooleanField(default=False)
    is_reversed = BooleanField(default=False)
    reversed_by = ForeignKeyField('self', null=True, backref='reversed_entries')
    
    # User who created the entry
    user = DeferredForeignKey('User', backref='journal_entries', null=True, on_delete='SET NULL')
    
    class Meta:
        table_name = 'journal_entries'
    
    def calculate_totals(self):
        """Calculate and update total debits and credits."""
        self.total_debit = sum(line.debit_amount for line in self.journal_lines)
        self.total_credit = sum(line.credit_amount for line in self.journal_lines)
        self.save()
    
    def is_balanced(self) -> bool:
        """Check if journal entry is balanced (debits = credits)."""
        return abs(self.total_debit - self.total_credit) < Decimal('0.001')
    
    def post(self):
        """Post the journal entry and update account balances."""
        if self.is_posted:
            return
        
        if not self.is_balanced():
            raise ValueError("Journal entry is not balanced")
        
        # Update account balances
        for line in self.journal_lines:
            line.account.update_balance()
        
        self.is_posted = True
        self.save()
    
    def reverse(self, user=None, description=None):
        """
        Create a reversing journal entry.
        
        Args:
            user: User creating the reversal
            description: Description for the reversal entry
            
        Returns:
            Reversing journal entry
        """
        if self.is_reversed:
            raise ValueError("Entry is already reversed")
        
        if not self.is_posted:
            raise ValueError("Cannot reverse unposted entry")
        
        # Create reversing entry
        reversing_entry = JournalEntry.create(
            entry_no=self._generate_entry_number(),
            entry_date=date.today(),
            entry_type=self.entry_type,
            description=description or f"Reversal of {self.entry_no}",
            reference_type=self.reference_type,
            reference_id=self.reference_id,
            reference_no=self.reference_no,
            user=user
        )
        
        # Create reversing lines
        for line in self.journal_lines:
            JournalEntryLine.create(
                journal_entry=reversing_entry,
                account=line.account,
                debit_amount=line.credit_amount,  # Swap debits and credits
                credit_amount=line.debit_amount,
                description=f"Reversal: {line.description}"
            )
        
        # Update totals and post
        reversing_entry.calculate_totals()
        reversing_entry.post()
        
        # Mark original as reversed
        self.is_reversed = True
        self.reversed_by = reversing_entry
        self.save()
        
        return reversing_entry
    
    @classmethod
    def _generate_entry_number(cls, prefix='JE'):
        """Generate unique journal entry number."""
        from datetime import datetime
        
        today = datetime.now()
        date_str = today.strftime('%Y%m%d')
        
        # Find next sequence number
        pattern = f"{prefix}-{date_str}-%"
        last_entry = cls.select().where(
            cls.entry_no.startswith(f"{prefix}-{date_str}-")
        ).order_by(cls.entry_no.desc()).first()
        
        if last_entry:
            try:
                last_seq = int(last_entry.entry_no.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1
        
        return f"{prefix}-{date_str}-{next_seq:04d}"
    
    def __str__(self):
        return f"JE {self.entry_no} - {self.description}"


class JournalEntryLine(BaseModel):
    """Journal entry line item."""
    
    journal_entry = ForeignKeyField(JournalEntry, backref='journal_lines', on_delete='CASCADE')
    account = ForeignKeyField(Account, backref='journal_lines', on_delete='RESTRICT')
    
    # Amounts
    debit_amount = DecimalField(max_digits=15, decimal_places=3, default=0)
    credit_amount = DecimalField(max_digits=15, decimal_places=3, default=0)
    
    # Description
    description = CharField(max_length=500, null=True)
    description_ar = CharField(max_length=500, null=True)
    
    class Meta:
        table_name = 'journal_entry_lines'
    
    def save(self, *args, **kwargs):
        """Override save to ensure only debit OR credit has value."""
        # Ensure only one of debit or credit has a value
        if self.debit_amount > 0:
            self.credit_amount = 0
        elif self.credit_amount > 0:
            self.debit_amount = 0
        
        super().save(*args, **kwargs)
    
    def get_amount(self) -> Decimal:
        """Get the line amount (debit or credit)."""
        return self.debit_amount if self.debit_amount > 0 else self.credit_amount
    
    def is_debit(self) -> bool:
        """Check if this is a debit line."""
        return self.debit_amount > 0
    
    def is_credit(self) -> bool:
        """Check if this is a credit line."""
        return self.credit_amount > 0
    
    def __str__(self):
        amount = self.debit_amount if self.debit_amount > 0 else self.credit_amount
        side = "Dr" if self.debit_amount > 0 else "Cr"
        return f"{self.account.code} - {amount} {side}"
