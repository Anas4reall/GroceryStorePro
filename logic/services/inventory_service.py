"""
Inventory management service for stock operations.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from database.models import (
    Product, Batch, StockTransaction, User
)
from logic.utils.logger import get_logger, log_database_operation


@dataclass
class StockAlert:
    """Data class for stock alerts."""
    product: Product
    alert_type: str  # 'low_stock', 'expired', 'near_expiry'
    current_stock: int
    reorder_point: int
    message: str
    severity: str  # 'info', 'warning', 'critical'


class InventoryService:
    """Service for managing inventory operations."""
    
    def __init__(self):
        """Initialize the inventory service."""
        self.logger = get_logger(__name__)
    
    def add_stock(self, product: Product, quantity: int, cost_per_unit: Decimal,
                  batch_no: str = None, expiry_date: date = None,
                  source_type: str = 'purchase', source_id: int = None,
                  user: User = None) -> Tuple[bool, str, Optional[Batch]]:
        """
        Add stock to inventory.
        
        Args:
            product: Product to add stock for
            quantity: Quantity to add
            cost_per_unit: Cost per unit
            batch_no: Batch number (required if product tracks batches)
            expiry_date: Expiry date (for perishable items)
            source_type: Source of stock ('purchase', 'adjustment', 'return')
            source_id: ID of source document
            user: User performing the operation
            
        Returns:
            Tuple of (success, message, batch_object)
        """
        try:
            if quantity <= 0:
                return False, "Quantity must be positive", None
            
            if cost_per_unit < 0:
                return False, "Cost per unit cannot be negative", None
            
            batch = None
            
            if product.track_batches:
                if not batch_no:
                    return False, "Batch number is required for this product", None
                
                # Create or update batch
                batch, created = Batch.get_or_create(
                    product=product,
                    batch_no=batch_no,
                    defaults={
                        'expiry_date': expiry_date,
                        'initial_qty': quantity,
                        'current_qty': quantity,
                        'cost_per_unit': cost_per_unit,
                        'source_type': source_type,
                        'source_id': source_id or 0
                    }
                )
                
                if not created:
                    # Update existing batch
                    batch.current_qty += quantity
                    batch.save()
            
            # Create stock transaction
            transaction = StockTransaction.create(
                product=product,
                batch=batch,
                transaction_type=source_type,
                quantity=quantity,
                unit_cost=cost_per_unit,
                reference_type=source_type,
                reference_id=source_id,
                user=user,
                reason=f"Stock added via {source_type}"
            )
            
            # Log the operation
            log_database_operation(
                user=user,
                action='create',
                table_name='stock_transaction',
                record_id=transaction.id,
                new_values={
                    'product_id': product.id,
                    'quantity': quantity,
                    'transaction_type': source_type
                },
                description=f"Added {quantity} units of {product.name}"
            )
            
            self.logger.info(f"Added {quantity} units of {product.sku} to inventory")
            
            return True, "Stock added successfully", batch
            
        except Exception as e:
            self.logger.error(f"Failed to add stock: {e}")
            return False, f"Failed to add stock: {str(e)}", None
    
    def remove_stock(self, product: Product, quantity: int,
                     batch: Batch = None, reason: str = 'sale',
                     reference_type: str = None, reference_id: int = None,
                     user: User = None, allow_negative: bool = False) -> Tuple[bool, str, List[Batch]]:
        """
        Remove stock from inventory using FIFO method.
        
        Args:
            product: Product to remove stock from
            quantity: Quantity to remove
            batch: Specific batch to remove from (optional)
            reason: Reason for removal
            reference_type: Type of reference document
            reference_id: ID of reference document
            user: User performing the operation
            allow_negative: Allow negative stock
            
        Returns:
            Tuple of (success, message, list_of_affected_batches)
        """
        try:
            if quantity <= 0:
                return False, "Quantity must be positive", []
            
            # Check available stock
            available_stock = product.get_available_stock()
            if not allow_negative and quantity > available_stock:
                return False, f"Insufficient stock. Available: {available_stock}, Required: {quantity}", []
            
            affected_batches = []
            remaining_qty = quantity
            
            if product.track_batches:
                if batch:
                    # Remove from specific batch
                    if batch.current_qty < remaining_qty and not allow_negative:
                        return False, f"Insufficient stock in batch {batch.batch_no}", []
                    
                    # Create transaction
                    StockTransaction.create(
                        product=product,
                        batch=batch,
                        transaction_type='sale' if reason == 'sale' else 'adjustment_out',
                        quantity=remaining_qty,
                        unit_cost=batch.cost_per_unit,
                        reference_type=reference_type,
                        reference_id=reference_id,
                        user=user,
                        reason=reason
                    )
                    
                    batch.current_qty -= remaining_qty
                    batch.save()
                    affected_batches.append(batch)
                    
                else:
                    # Use FIFO - oldest batches first
                    batches = (Batch.select()
                             .where((Batch.product == product) & (Batch.current_qty > 0))
                             .order_by(Batch.created_at))
                    
                    for batch in batches:
                        if remaining_qty <= 0:
                            break
                        
                        # Skip expired batches unless allowing negative stock
                        if batch.is_expired() and not allow_negative:
                            continue
                        
                        qty_to_remove = min(remaining_qty, batch.current_qty)
                        
                        # Create transaction
                        StockTransaction.create(
                            product=product,
                            batch=batch,
                            transaction_type='sale' if reason == 'sale' else 'adjustment_out',
                            quantity=qty_to_remove,
                            unit_cost=batch.cost_per_unit,
                            reference_type=reference_type,
                            reference_id=reference_id,
                            user=user,
                            reason=reason
                        )
                        
                        batch.current_qty -= qty_to_remove
                        batch.save()
                        affected_batches.append(batch)
                        remaining_qty -= qty_to_remove
                    
                    if remaining_qty > 0 and not allow_negative:
                        return False, f"Could not remove {remaining_qty} units - insufficient non-expired stock", affected_batches
            
            else:
                # Non-batch tracked product
                StockTransaction.create(
                    product=product,
                    transaction_type='sale' if reason == 'sale' else 'adjustment_out',
                    quantity=quantity,
                    unit_cost=product.buy_price,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    user=user,
                    reason=reason
                )
            
            # Log the operation
            log_database_operation(
                user=user,
                action='create',
                table_name='stock_transaction',
                new_values={
                    'product_id': product.id,
                    'quantity': -quantity,
                    'transaction_type': 'sale' if reason == 'sale' else 'adjustment_out'
                },
                description=f"Removed {quantity} units of {product.name}"
            )
            
            self.logger.info(f"Removed {quantity} units of {product.sku} from inventory")
            
            return True, "Stock removed successfully", affected_batches
            
        except Exception as e:
            self.logger.error(f"Failed to remove stock: {e}")
            return False, f"Failed to remove stock: {str(e)}", []
    
    def adjust_stock(self, product: Product, adjustment_qty: int, reason: str,
                     batch: Batch = None, user: User = None) -> Tuple[bool, str]:
        """
        Adjust stock levels (positive or negative adjustment).
        
        Args:
            product: Product to adjust
            adjustment_qty: Adjustment quantity (positive for increase, negative for decrease)
            reason: Reason for adjustment
            batch: Specific batch to adjust (optional)
            user: User performing the adjustment
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if adjustment_qty == 0:
                return False, "Adjustment quantity cannot be zero", 
            
            if adjustment_qty > 0:
                # Positive adjustment - add stock
                if product.track_batches and not batch:
                    return False, "Batch is required for batch-tracked products"
                
                if batch:
                    batch.current_qty += adjustment_qty
                    batch.save()
                
                StockTransaction.create(
                    product=product,
                    batch=batch,
                    transaction_type='adjustment_in',
                    quantity=adjustment_qty,
                    unit_cost=batch.cost_per_unit if batch else product.buy_price,
                    reference_type='adjustment',
                    user=user,
                    reason=reason
                )
                
            else:
                # Negative adjustment - remove stock
                adjustment_qty = abs(adjustment_qty)
                
                if batch:
                    if batch.current_qty < adjustment_qty:
                        return False, f"Insufficient stock in batch {batch.batch_no}"
                    
                    batch.current_qty -= adjustment_qty
                    batch.save()
                
                StockTransaction.create(
                    product=product,
                    batch=batch,
                    transaction_type='adjustment_out',
                    quantity=adjustment_qty,
                    unit_cost=batch.cost_per_unit if batch else product.buy_price,
                    reference_type='adjustment',
                    user=user,
                    reason=reason
                )
            
            # Log the operation
            log_database_operation(
                user=user,
                action='create',
                table_name='stock_transaction',
                new_values={
                    'product_id': product.id,
                    'quantity': adjustment_qty if adjustment_qty > 0 else -adjustment_qty,
                    'transaction_type': 'adjustment_in' if adjustment_qty > 0 else 'adjustment_out',
                    'reason': reason
                },
                description=f"Stock adjustment for {product.name}: {reason}"
            )
            
            self.logger.info(f"Stock adjusted for {product.sku}: {adjustment_qty} units - {reason}")
            
            return True, "Stock adjusted successfully"
            
        except Exception as e:
            self.logger.error(f"Failed to adjust stock: {e}")
            return False, f"Failed to adjust stock: {str(e)}"
    
    def get_stock_alerts(self, days_ahead: int = 7) -> List[StockAlert]:
        """
        Get stock alerts for low stock, expired, and near-expiry items.
        
        Args:
            days_ahead: Days ahead to check for near-expiry items
            
        Returns:
            List of stock alerts
        """
        alerts = []
        
        try:
            # Get all active products
            products = Product.select().where(Product.is_active == True)
            
            for product in products:
                current_stock = product.get_available_stock()
                
                # Low stock alert
                if product.is_low_stock():
                    alerts.append(StockAlert(
                        product=product,
                        alert_type='low_stock',
                        current_stock=current_stock,
                        reorder_point=product.reorder_point,
                        message=f"Stock is below reorder point ({product.reorder_point})",
                        severity='warning'
                    ))
                
                # Check batches for expiry alerts
                if product.track_batches:
                    future_date = date.today() + timedelta(days=days_ahead)
                    
                    for batch in product.batches:
                        if batch.current_qty <= 0:
                            continue
                        
                        if batch.is_expired():
                            alerts.append(StockAlert(
                                product=product,
                                alert_type='expired',
                                current_stock=batch.current_qty,
                                reorder_point=0,
                                message=f"Batch {batch.batch_no} has expired",
                                severity='critical'
                            ))
                        
                        elif batch.expiry_date and batch.expiry_date <= future_date:
                            days_to_expiry = (batch.expiry_date - date.today()).days
                            alerts.append(StockAlert(
                                product=product,
                                alert_type='near_expiry',
                                current_stock=batch.current_qty,
                                reorder_point=0,
                                message=f"Batch {batch.batch_no} expires in {days_to_expiry} days",
                                severity='warning'
                            ))
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to get stock alerts: {e}")
            return []
    
    def get_stock_valuation(self, as_of_date: date = None) -> Dict[str, Decimal]:
        """
        Calculate stock valuation using FIFO method.
        
        Args:
            as_of_date: Date to calculate valuation (None for current)
            
        Returns:
            Dictionary with valuation details
        """
        try:
            if as_of_date is None:
                as_of_date = date.today()
            
            total_value = Decimal('0')
            product_values = {}
            
            products = Product.select().where(Product.is_active == True)
            
            for product in products:
                product_value = Decimal('0')
                
                if product.track_batches:
                    for batch in product.batches:
                        if batch.current_qty > 0:
                            product_value += batch.get_total_value()
                else:
                    # For non-batch tracked items, use current stock * buy price
                    current_stock = product.get_current_stock()
                    product_value = Decimal(str(current_stock)) * product.buy_price
                
                product_values[product.sku] = product_value
                total_value += product_value
            
            return {
                'total_value': total_value,
                'product_values': product_values,
                'valuation_date': as_of_date
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate stock valuation: {e}")
            return {'total_value': Decimal('0'), 'product_values': {}, 'valuation_date': as_of_date}
