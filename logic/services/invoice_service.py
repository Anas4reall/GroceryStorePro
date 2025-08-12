"""
Invoice service for managing sales and purchase invoices.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from database.models import (
    Sale, SaleItem, Purchase, PurchaseItem, Product, Batch,
    Customer, Supplier, User, Account, JournalEntry, JournalEntryLine
)
from logic.services.inventory_service import InventoryService
from logic.utils.logger import get_logger, log_database_operation


@dataclass
class InvoiceLineItem:
    """Data class for invoice line items."""
    product_id: int
    quantity: int
    unit_price: Decimal
    batch_id: Optional[int] = None
    discount_percentage: Decimal = Decimal('0')
    notes: Optional[str] = None


class InvoiceService:
    """Service for managing invoices and related operations."""
    
    def __init__(self):
        """Initialize the invoice service."""
        self.logger = get_logger(__name__)
        self.inventory_service = InventoryService()
    
    def create_sale_invoice(self, customer_id: Optional[int], pricing_mode: str,
                           line_items: List[InvoiceLineItem], discount_percentage: Decimal = Decimal('0'),
                           tax_rate: Decimal = Decimal('15'), notes: str = None,
                           user: User = None) -> Tuple[bool, str, Optional[Sale]]:
        """
        Create a sales invoice.
        
        Args:
            customer_id: Customer ID (None for walk-in customers)
            pricing_mode: 'retail' or 'wholesale'
            line_items: List of invoice line items
            discount_percentage: Overall discount percentage
            tax_rate: Tax rate percentage
            notes: Invoice notes
            user: User creating the invoice
            
        Returns:
            Tuple of (success, message, sale_object)
        """
        try:
            if not line_items:
                return False, "Invoice must have at least one line item", None
            
            # Get customer if specified
            customer = None
            if customer_id:
                try:
                    customer = Customer.get_by_id(customer_id)
                    if not customer.is_active:
                        return False, "Customer account is inactive", None
                except Customer.DoesNotExist:
                    return False, "Customer not found", None
            
            # Generate invoice number
            invoice_no = self._generate_invoice_number('INV')
            
            # Create sale record
            sale = Sale.create(
                invoice_no=invoice_no,
                customer=customer,
                pricing_mode=pricing_mode,
                discount_percentage=discount_percentage,
                tax_rate=tax_rate,
                notes=notes,
                user=user
            )
            
            # Process line items
            total_cogs = Decimal('0')
            
            for item in line_items:
                success, message, affected_batches = self._add_sale_item(
                    sale, item, pricing_mode, user
                )
                
                if not success:
                    # Rollback - delete the sale
                    sale.delete_instance()
                    return False, message, None
                
                # Calculate COGS for this item
                if affected_batches:
                    for batch in affected_batches:
                        total_cogs += batch.cost_per_unit * Decimal(str(item.quantity))
                else:
                    # Non-batch tracked item
                    product = Product.get_by_id(item.product_id)
                    total_cogs += product.buy_price * Decimal(str(item.quantity))
            
            # Calculate totals
            sale.calculate_totals()
            
            # Create accounting entries
            self._create_sale_accounting_entries(sale, total_cogs, user)
            
            # Update customer balance if credit sale
            if customer and sale.paid_amount < sale.total_amount:
                customer.add_to_balance(sale.total_amount - sale.paid_amount)
            
            # Log the operation
            log_database_operation(
                user=user,
                action='create',
                table_name='sales',
                record_id=sale.id,
                new_values={
                    'invoice_no': sale.invoice_no,
                    'customer_id': customer_id,
                    'total_amount': float(sale.total_amount)
                },
                description=f"Created sales invoice {sale.invoice_no}"
            )
            
            self.logger.info(f"Created sales invoice {sale.invoice_no} for {sale.total_amount}")
            
            return True, "Sales invoice created successfully", sale
            
        except Exception as e:
            self.logger.error(f"Failed to create sales invoice: {e}")
            return False, f"Failed to create sales invoice: {str(e)}", None
    
    def create_purchase_invoice(self, supplier_id: int, supplier_invoice_no: str,
                               line_items: List[InvoiceLineItem], discount_percentage: Decimal = Decimal('0'),
                               tax_rate: Decimal = Decimal('15'), notes: str = None,
                               user: User = None) -> Tuple[bool, str, Optional[Purchase]]:
        """
        Create a purchase invoice.
        
        Args:
            supplier_id: Supplier ID
            supplier_invoice_no: Supplier's invoice number
            line_items: List of invoice line items
            discount_percentage: Overall discount percentage
            tax_rate: Tax rate percentage
            notes: Invoice notes
            user: User creating the invoice
            
        Returns:
            Tuple of (success, message, purchase_object)
        """
        try:
            if not line_items:
                return False, "Invoice must have at least one line item", None
            
            # Get supplier
            try:
                supplier = Supplier.get_by_id(supplier_id)
                if not supplier.is_active:
                    return False, "Supplier account is inactive", None
            except Supplier.DoesNotExist:
                return False, "Supplier not found", None
            
            # Generate invoice number
            invoice_no = self._generate_invoice_number('PUR')
            
            # Create purchase record
            purchase = Purchase.create(
                invoice_no=invoice_no,
                supplier_invoice_no=supplier_invoice_no,
                supplier=supplier,
                discount_percentage=discount_percentage,
                tax_rate=tax_rate,
                notes=notes,
                user=user
            )
            
            # Process line items
            for item in line_items:
                success, message = self._add_purchase_item(purchase, item, user)
                
                if not success:
                    # Rollback - delete the purchase
                    purchase.delete_instance()
                    return False, message, None
            
            # Calculate totals
            purchase.calculate_totals()
            
            # Create accounting entries
            self._create_purchase_accounting_entries(purchase, user)
            
            # Update supplier balance
            supplier.add_to_balance(purchase.total_amount - purchase.paid_amount)
            
            # Log the operation
            log_database_operation(
                user=user,
                action='create',
                table_name='purchases',
                record_id=purchase.id,
                new_values={
                    'invoice_no': purchase.invoice_no,
                    'supplier_id': supplier_id,
                    'total_amount': float(purchase.total_amount)
                },
                description=f"Created purchase invoice {purchase.invoice_no}"
            )
            
            self.logger.info(f"Created purchase invoice {purchase.invoice_no} for {purchase.total_amount}")
            
            return True, "Purchase invoice created successfully", purchase
            
        except Exception as e:
            self.logger.error(f"Failed to create purchase invoice: {e}")
            return False, f"Failed to create purchase invoice: {str(e)}", None
    
    def _add_sale_item(self, sale: Sale, item: InvoiceLineItem, pricing_mode: str,
                       user: User) -> Tuple[bool, str, List[Batch]]:
        """Add a line item to a sales invoice."""
        try:
            # Get product
            product = Product.get_by_id(item.product_id)
            
            # Get price based on pricing mode
            unit_price = product.get_price(pricing_mode)
            if item.unit_price != unit_price:
                # Allow price override but log it
                self.logger.info(f"Price override for {product.sku}: {unit_price} -> {item.unit_price}")
            
            # Check stock availability
            available_stock = product.get_available_stock()
            if item.quantity > available_stock:
                return False, f"Insufficient stock for {product.name}. Available: {available_stock}", []
            
            # Remove stock from inventory
            success, message, affected_batches = self.inventory_service.remove_stock(
                product=product,
                quantity=item.quantity,
                batch=Batch.get_by_id(item.batch_id) if item.batch_id else None,
                reason='sale',
                reference_type='sale',
                reference_id=sale.id,
                user=user
            )
            
            if not success:
                return False, message, []
            
            # Create sale item
            sale_item = SaleItem.create(
                sale=sale,
                product=product,
                batch=Batch.get_by_id(item.batch_id) if item.batch_id else None,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_discount_percentage=item.discount_percentage,
                notes=item.notes
            )
            
            # Calculate line total
            sale_item.calculate_line_total()
            
            return True, "Sale item added successfully", affected_batches
            
        except Exception as e:
            self.logger.error(f"Failed to add sale item: {e}")
            return False, f"Failed to add sale item: {str(e)}", []
    
    def _add_purchase_item(self, purchase: Purchase, item: InvoiceLineItem,
                          user: User) -> Tuple[bool, str]:
        """Add a line item to a purchase invoice."""
        try:
            # Get product
            product = Product.get_by_id(item.product_id)
            
            # Create purchase item
            purchase_item = PurchaseItem.create(
                purchase=purchase,
                product=product,
                batch_no=item.notes,  # Using notes field for batch number
                quantity=item.quantity,
                unit_cost=item.unit_price
            )
            
            # Calculate line total
            purchase_item.calculate_line_total()
            
            # Add stock to inventory
            success, message, batch = self.inventory_service.add_stock(
                product=product,
                quantity=item.quantity,
                cost_per_unit=item.unit_price,
                batch_no=item.notes,  # Using notes field for batch number
                source_type='purchase',
                source_id=purchase.id,
                user=user
            )
            
            if not success:
                return False, message
            
            return True, "Purchase item added successfully"
            
        except Exception as e:
            self.logger.error(f"Failed to add purchase item: {e}")
            return False, f"Failed to add purchase item: {str(e)}"
    
    def _create_sale_accounting_entries(self, sale: Sale, total_cogs: Decimal, user: User):
        """Create accounting entries for a sale."""
        try:
            # Get system accounts
            accounts = Account.get_system_accounts()
            
            # Create journal entry
            entry = JournalEntry.create(
                entry_no=JournalEntry._generate_entry_number('SALE'),
                entry_type='sale',
                description=f"Sale invoice {sale.invoice_no}",
                reference_type='sale',
                reference_id=sale.id,
                reference_no=sale.invoice_no,
                user=user
            )
            
            # Debit: Cash/Accounts Receivable
            if sale.customer and sale.paid_amount < sale.total_amount:
                # Partial payment - split between cash and AR
                if sale.paid_amount > 0:
                    JournalEntryLine.create(
                        journal_entry=entry,
                        account=accounts['cash'],
                        debit_amount=sale.paid_amount,
                        description=f"Cash received for invoice {sale.invoice_no}"
                    )
                
                ar_amount = sale.total_amount - sale.paid_amount
                JournalEntryLine.create(
                    journal_entry=entry,
                    account=accounts['accounts_receivable'],
                    debit_amount=ar_amount,
                    description=f"Accounts receivable for invoice {sale.invoice_no}"
                )
            else:
                # Full cash payment
                JournalEntryLine.create(
                    journal_entry=entry,
                    account=accounts['cash'],
                    debit_amount=sale.total_amount,
                    description=f"Cash received for invoice {sale.invoice_no}"
                )
            
            # Credit: Sales Revenue
            JournalEntryLine.create(
                journal_entry=entry,
                account=accounts['sales'],
                credit_amount=sale.total_amount,
                description=f"Sales revenue for invoice {sale.invoice_no}"
            )
            
            # COGS Entry
            if total_cogs > 0:
                # Debit: Cost of Goods Sold
                JournalEntryLine.create(
                    journal_entry=entry,
                    account=accounts['cogs'],
                    debit_amount=total_cogs,
                    description=f"Cost of goods sold for invoice {sale.invoice_no}"
                )
                
                # Credit: Inventory
                JournalEntryLine.create(
                    journal_entry=entry,
                    account=accounts['inventory'],
                    credit_amount=total_cogs,
                    description=f"Inventory reduction for invoice {sale.invoice_no}"
                )
            
            # Calculate totals and post
            entry.calculate_totals()
            entry.post()
            
        except Exception as e:
            self.logger.error(f"Failed to create sale accounting entries: {e}")
    
    def _create_purchase_accounting_entries(self, purchase: Purchase, user: User):
        """Create accounting entries for a purchase."""
        try:
            # Get system accounts
            accounts = Account.get_system_accounts()
            
            # Create journal entry
            entry = JournalEntry.create(
                entry_no=JournalEntry._generate_entry_number('PUR'),
                entry_type='purchase',
                description=f"Purchase invoice {purchase.invoice_no}",
                reference_type='purchase',
                reference_id=purchase.id,
                reference_no=purchase.invoice_no,
                user=user
            )
            
            # Debit: Inventory
            JournalEntryLine.create(
                journal_entry=entry,
                account=accounts['inventory'],
                debit_amount=purchase.total_amount,
                description=f"Inventory purchase for invoice {purchase.invoice_no}"
            )
            
            # Credit: Cash/Accounts Payable
            if purchase.paid_amount < purchase.total_amount:
                # Partial payment - split between cash and AP
                if purchase.paid_amount > 0:
                    JournalEntryLine.create(
                        journal_entry=entry,
                        account=accounts['cash'],
                        credit_amount=purchase.paid_amount,
                        description=f"Cash paid for invoice {purchase.invoice_no}"
                    )
                
                ap_amount = purchase.total_amount - purchase.paid_amount
                JournalEntryLine.create(
                    journal_entry=entry,
                    account=accounts['accounts_payable'],
                    credit_amount=ap_amount,
                    description=f"Accounts payable for invoice {purchase.invoice_no}"
                )
            else:
                # Full cash payment
                JournalEntryLine.create(
                    journal_entry=entry,
                    account=accounts['cash'],
                    credit_amount=purchase.total_amount,
                    description=f"Cash paid for invoice {purchase.invoice_no}"
                )
            
            # Calculate totals and post
            entry.calculate_totals()
            entry.post()
            
        except Exception as e:
            self.logger.error(f"Failed to create purchase accounting entries: {e}")
    
    def _generate_invoice_number(self, prefix: str) -> str:
        """Generate a unique invoice number."""
        today = datetime.now()
        date_str = today.strftime('%Y%m%d')
        
        # Find the next sequence number for today
        if prefix == 'INV':
            pattern = f"{prefix}-{date_str}-%"
            last_invoice = Sale.select().where(
                Sale.invoice_no.startswith(f"{prefix}-{date_str}-")
            ).order_by(Sale.invoice_no.desc()).first()
        else:  # PUR
            pattern = f"{prefix}-{date_str}-%"
            last_invoice = Purchase.select().where(
                Purchase.invoice_no.startswith(f"{prefix}-{date_str}-")
            ).order_by(Purchase.invoice_no.desc()).first()
        
        if last_invoice:
            try:
                last_seq = int(last_invoice.invoice_no.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1
        
        return f"{prefix}-{date_str}-{next_seq:04d}"
