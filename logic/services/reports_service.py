"""
Reports service for generating business reports.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import csv
import io

from database.models import (
    Sale, Purchase, Product, Customer, Supplier, StockTransaction,
    Account, JournalEntry, JournalEntryLine, Batch
)
from logic.utils.logger import get_logger


@dataclass
class ReportData:
    """Data class for report results."""
    title: str
    subtitle: str
    data: List[Dict[str, Any]]
    totals: Dict[str, Any]
    parameters: Dict[str, Any]
    generated_at: datetime


class ReportsService:
    """Service for generating various business reports."""
    
    def __init__(self):
        """Initialize the reports service."""
        self.logger = get_logger(__name__)
    
    def generate_sales_summary_report(self, start_date: date, end_date: date,
                                    customer_id: Optional[int] = None,
                                    product_id: Optional[int] = None) -> ReportData:
        """
        Generate sales summary report.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            customer_id: Filter by customer (optional)
            product_id: Filter by product (optional)
            
        Returns:
            ReportData object
        """
        try:
            # Build query
            query = Sale.select().where(
                (Sale.invoice_date >= start_date) & 
                (Sale.invoice_date <= end_date) &
                (Sale.status != 'cancelled')
            )
            
            if customer_id:
                query = query.where(Sale.customer_id == customer_id)
            
            # Get sales data
            sales_data = []
            total_sales = Decimal('0')
            total_cost = Decimal('0')
            total_profit = Decimal('0')
            
            for sale in query:
                # Filter by product if specified
                if product_id:
                    sale_items = sale.sale_items.where(SaleItem.product_id == product_id)
                    if not sale_items.exists():
                        continue
                else:
                    sale_items = sale.sale_items
                
                sale_total = sum(item.line_total for item in sale_items)
                sale_cost = sum(item.get_cost_of_goods_sold() for item in sale_items)
                sale_profit = sale_total - sale_cost
                
                sales_data.append({
                    'invoice_no': sale.invoice_no,
                    'date': sale.invoice_date.strftime('%Y-%m-%d'),
                    'customer': sale.customer.name if sale.customer else 'Walk-in Customer',
                    'total_amount': float(sale_total),
                    'cost_of_goods': float(sale_cost),
                    'gross_profit': float(sale_profit),
                    'profit_margin': float((sale_profit / sale_total * 100) if sale_total > 0 else 0),
                    'status': sale.status
                })
                
                total_sales += sale_total
                total_cost += sale_cost
                total_profit += sale_profit
            
            # Calculate totals
            totals = {
                'total_sales': float(total_sales),
                'total_cost': float(total_cost),
                'total_profit': float(total_profit),
                'profit_margin': float((total_profit / total_sales * 100) if total_sales > 0 else 0),
                'transaction_count': len(sales_data)
            }
            
            # Parameters
            parameters = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'customer_id': customer_id,
                'product_id': product_id
            }
            
            return ReportData(
                title="Sales Summary Report",
                subtitle=f"From {start_date} to {end_date}",
                data=sales_data,
                totals=totals,
                parameters=parameters,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate sales summary report: {e}")
            return ReportData(
                title="Sales Summary Report",
                subtitle="Error generating report",
                data=[],
                totals={},
                parameters={},
                generated_at=datetime.now()
            )
    
    def generate_inventory_report(self, include_zero_stock: bool = False,
                                category_id: Optional[int] = None) -> ReportData:
        """
        Generate inventory status report.
        
        Args:
            include_zero_stock: Include products with zero stock
            category_id: Filter by category (optional)
            
        Returns:
            ReportData object
        """
        try:
            # Build query
            query = Product.select().where(Product.is_active == True)
            
            if category_id:
                query = query.where(Product.category_id == category_id)
            
            inventory_data = []
            total_value = Decimal('0')
            low_stock_count = 0
            
            for product in query:
                current_stock = product.get_current_stock()
                available_stock = product.get_available_stock()
                
                if not include_zero_stock and current_stock == 0:
                    continue
                
                # Calculate stock value
                if product.track_batches:
                    stock_value = sum(batch.get_total_value() for batch in product.batches 
                                    if batch.current_qty > 0)
                else:
                    stock_value = Decimal(str(current_stock)) * product.buy_price
                
                is_low_stock = product.is_low_stock()
                if is_low_stock:
                    low_stock_count += 1
                
                inventory_data.append({
                    'sku': product.sku,
                    'name': product.name,
                    'category': product.category.name if product.category else 'Uncategorized',
                    'unit': product.unit.name,
                    'current_stock': current_stock,
                    'available_stock': available_stock,
                    'reorder_point': product.reorder_point,
                    'buy_price': float(product.buy_price),
                    'retail_price': float(product.sell_price_retail),
                    'wholesale_price': float(product.sell_price_wholesale),
                    'stock_value': float(stock_value),
                    'is_low_stock': is_low_stock,
                    'track_batches': product.track_batches
                })
                
                total_value += stock_value
            
            # Calculate totals
            totals = {
                'total_products': len(inventory_data),
                'total_value': float(total_value),
                'low_stock_count': low_stock_count
            }
            
            # Parameters
            parameters = {
                'include_zero_stock': include_zero_stock,
                'category_id': category_id
            }
            
            return ReportData(
                title="Inventory Status Report",
                subtitle=f"As of {date.today()}",
                data=inventory_data,
                totals=totals,
                parameters=parameters,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate inventory report: {e}")
            return ReportData(
                title="Inventory Status Report",
                subtitle="Error generating report",
                data=[],
                totals={},
                parameters={},
                generated_at=datetime.now()
            )
    
    def generate_customer_statement(self, customer_id: int, start_date: date,
                                  end_date: date) -> ReportData:
        """
        Generate customer account statement.
        
        Args:
            customer_id: Customer ID
            start_date: Statement start date
            end_date: Statement end date
            
        Returns:
            ReportData object
        """
        try:
            # Get customer
            customer = Customer.get_by_id(customer_id)
            
            # Get transactions
            sales = Sale.select().where(
                (Sale.customer == customer) &
                (Sale.invoice_date >= start_date) &
                (Sale.invoice_date <= end_date)
            ).order_by(Sale.invoice_date)
            
            # Get payments
            from database.models import Payment
            payments = Payment.select().where(
                (Payment.linked_to_type == 'customer') &
                (Payment.linked_to_id == customer_id) &
                (Payment.payment_date >= start_date) &
                (Payment.payment_date <= end_date)
            ).order_by(Payment.payment_date)
            
            # Combine and sort transactions
            transactions = []
            
            for sale in sales:
                transactions.append({
                    'date': sale.invoice_date.strftime('%Y-%m-%d'),
                    'type': 'Sale',
                    'reference': sale.invoice_no,
                    'debit': float(sale.total_amount),
                    'credit': 0,
                    'balance': 0,  # Will be calculated later
                    'description': f"Sale invoice {sale.invoice_no}"
                })
            
            for payment in payments:
                transactions.append({
                    'date': payment.payment_date.strftime('%Y-%m-%d'),
                    'type': 'Payment',
                    'reference': payment.payment_no,
                    'debit': 0,
                    'credit': float(payment.amount),
                    'balance': 0,  # Will be calculated later
                    'description': f"Payment {payment.payment_no}"
                })
            
            # Sort by date
            transactions.sort(key=lambda x: x['date'])
            
            # Calculate running balance
            running_balance = Decimal('0')
            for transaction in transactions:
                running_balance += Decimal(str(transaction['debit'])) - Decimal(str(transaction['credit']))
                transaction['balance'] = float(running_balance)
            
            # Calculate totals
            total_debits = sum(t['debit'] for t in transactions)
            total_credits = sum(t['credit'] for t in transactions)
            
            totals = {
                'total_debits': total_debits,
                'total_credits': total_credits,
                'ending_balance': float(running_balance),
                'transaction_count': len(transactions)
            }
            
            # Parameters
            parameters = {
                'customer_id': customer_id,
                'customer_name': customer.name,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
            
            return ReportData(
                title="Customer Account Statement",
                subtitle=f"{customer.name} - {start_date} to {end_date}",
                data=transactions,
                totals=totals,
                parameters=parameters,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate customer statement: {e}")
            return ReportData(
                title="Customer Account Statement",
                subtitle="Error generating report",
                data=[],
                totals={},
                parameters={},
                generated_at=datetime.now()
            )
    
    def generate_profit_loss_report(self, start_date: date, end_date: date) -> ReportData:
        """
        Generate profit and loss report.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            ReportData object
        """
        try:
            # Get revenue accounts
            revenue_accounts = Account.select().where(Account.account_type == 'revenue')
            expense_accounts = Account.select().where(Account.account_type == 'expense')
            cogs_accounts = Account.select().where(Account.account_type == 'cogs')
            
            report_data = []
            total_revenue = Decimal('0')
            total_cogs = Decimal('0')
            total_expenses = Decimal('0')
            
            # Revenue section
            report_data.append({
                'account_type': 'REVENUE',
                'account_name': 'REVENUE',
                'amount': 0,
                'is_header': True
            })
            
            for account in revenue_accounts:
                balance = account.get_balance(end_date)
                total_revenue += balance
                
                report_data.append({
                    'account_type': 'revenue',
                    'account_name': account.name,
                    'amount': float(balance),
                    'is_header': False
                })
            
            # COGS section
            report_data.append({
                'account_type': 'COGS',
                'account_name': 'COST OF GOODS SOLD',
                'amount': 0,
                'is_header': True
            })
            
            for account in cogs_accounts:
                balance = account.get_balance(end_date)
                total_cogs += balance
                
                report_data.append({
                    'account_type': 'cogs',
                    'account_name': account.name,
                    'amount': float(balance),
                    'is_header': False
                })
            
            # Expenses section
            report_data.append({
                'account_type': 'EXPENSES',
                'account_name': 'EXPENSES',
                'amount': 0,
                'is_header': True
            })
            
            for account in expense_accounts:
                balance = account.get_balance(end_date)
                total_expenses += balance
                
                report_data.append({
                    'account_type': 'expense',
                    'account_name': account.name,
                    'amount': float(balance),
                    'is_header': False
                })
            
            # Calculate totals
            gross_profit = total_revenue - total_cogs
            net_profit = gross_profit - total_expenses
            
            totals = {
                'total_revenue': float(total_revenue),
                'total_cogs': float(total_cogs),
                'gross_profit': float(gross_profit),
                'total_expenses': float(total_expenses),
                'net_profit': float(net_profit),
                'gross_margin': float((gross_profit / total_revenue * 100) if total_revenue > 0 else 0),
                'net_margin': float((net_profit / total_revenue * 100) if total_revenue > 0 else 0)
            }
            
            # Parameters
            parameters = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
            
            return ReportData(
                title="Profit & Loss Statement",
                subtitle=f"From {start_date} to {end_date}",
                data=report_data,
                totals=totals,
                parameters=parameters,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate P&L report: {e}")
            return ReportData(
                title="Profit & Loss Statement",
                subtitle="Error generating report",
                data=[],
                totals={},
                parameters={},
                generated_at=datetime.now()
            )
    
    def export_to_csv(self, report_data: ReportData) -> str:
        """
        Export report data to CSV format.
        
        Args:
            report_data: Report data to export
            
        Returns:
            CSV content as string
        """
        try:
            output = io.StringIO()
            
            if not report_data.data:
                return ""
            
            # Get field names from first row
            fieldnames = list(report_data.data[0].keys())
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report_data.data)
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Failed to export to CSV: {e}")
            return ""
