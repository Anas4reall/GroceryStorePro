# GroceryStorePro - Functional Specification

## 1. Project Overview

**GroceryStorePro** is a comprehensive desktop application for managing grocery warehouse operations, supporting both wholesale and retail business models with integrated accounting functionality. The system operates entirely offline with local data storage.

### 1.1 Key Features
- Inventory management with batch tracking and expiry dates
- Dual pricing (wholesale/retail) with customer-based pricing
- Purchase and sales invoice management
- Integrated accounting with automatic journal entries
- Customer and supplier relationship management
- Comprehensive reporting and analytics
- Multi-user support with role-based access control
- Barcode scanning support
- Arabic/English language support
- Automated backup and restore functionality

## 2. User Roles and Permissions

### 2.1 Admin
- Full system access
- User management
- System configuration
- Database backup/restore
- All business operations

### 2.2 Manager
- All business operations (sales, purchases, inventory)
- Customer and supplier management
- Reports generation
- Cannot manage users or system settings

### 2.3 Cashier
- Sales transactions only
- Customer lookup
- Basic inventory inquiry
- Cannot access purchases, reports, or management functions

### 2.4 Warehouse Staff
- Inventory management (stock adjustments, receiving)
- Purchase order processing
- Cannot access sales or financial reports

## 3. Core Business Workflows

### 3.1 Purchase Workflow
1. Create purchase order or direct purchase invoice
2. Select supplier and add products with quantities
3. Specify batch information (batch number, expiry date)
4. Calculate totals with taxes and discounts
5. Record payment (full/partial)
6. Update inventory levels
7. Generate accounting entries (Inventory Dr, Accounts Payable Cr)

### 3.2 Sales Workflow
1. Create sales invoice
2. Select customer and pricing mode (retail/wholesale)
3. Add products via barcode scan or manual selection
4. System checks stock availability and expiry dates
5. Apply discounts and calculate taxes
6. Process payment (cash/credit)
7. Update inventory (FIFO method)
8. Generate accounting entries (Cash/AR Dr, Sales Cr, COGS Dr, Inventory Cr)

### 3.3 Inventory Management Workflow
1. Receive stock from purchases
2. Track batches with expiry dates
3. Monitor stock levels and reorder points
4. Handle stock adjustments (damage, theft, count corrections)
5. Generate stock movement reports
6. Alert for expired or near-expiry items

## 4. Database Schema Overview

### 4.1 Core Entities
- **Product**: SKU, name, category, unit, pricing, reorder levels
- **Batch**: Product batches with expiry tracking
- **StockTransaction**: All inventory movements
- **Customer/Supplier**: Contact and credit information
- **Purchase/Sale**: Transaction headers
- **PurchaseItem/SaleItem**: Transaction line items
- **Payment**: Payment records linked to transactions
- **User**: System users with roles
- **AuditLog**: Change tracking for compliance

### 4.2 Accounting Integration
- **Account**: Chart of accounts
- **JournalEntry**: Accounting transactions
- **JournalEntryLine**: Journal entry details

## 5. Business Rules

### 5.1 Inventory Rules
- FIFO (First In, First Out) for stock consumption
- Prevent sales of expired batches
- Configurable negative stock allowance
- Automatic reorder point alerts
- Batch tracking mandatory for perishable items

### 5.2 Pricing Rules
- Dual pricing structure (wholesale/retail)
- Customer-specific pricing overrides
- Discount application at line and invoice level
- Tax calculation based on configurable rates
- Currency support (SAR default, configurable)

### 5.3 Payment Rules
- Support for partial payments
- Automatic AR/AP balance updates
- Multiple payment methods (cash, card, bank transfer)
- Payment terms tracking for credit customers

### 5.4 Security Rules
- Role-based access control
- Password complexity requirements
- Session timeout for security
- Audit trail for all critical operations
- Data encryption for sensitive information

## 6. User Interface Requirements

### 6.1 Main Dashboard
- Key performance indicators (daily sales, low stock alerts, cash balance)
- Quick access to common functions
- Recent transactions summary
- System notifications and alerts

### 6.2 Product Management
- Product catalog with search and filtering
- Batch management interface
- Stock level monitoring
- Price management (retail/wholesale)
- Category and unit management

### 6.3 Transaction Processing
- Intuitive invoice creation interface
- Barcode scanning integration
- Real-time stock checking
- Payment processing interface
- Print/email invoice capability

### 6.4 Reporting Interface
- Pre-built report templates
- Custom date range selection
- Export options (PDF, Excel, CSV)
- Print preview functionality
- Report scheduling (future enhancement)

## 7. Technical Requirements

### 7.1 Performance
- Support for 10,000+ products
- Handle 1,000+ daily transactions
- Response time < 2 seconds for common operations
- Database size up to 1GB without performance degradation

### 7.2 Reliability
- Data integrity validation
- Automatic backup scheduling
- Error handling and recovery
- Transaction rollback capability

### 7.3 Usability
- Arabic language support (RTL)
- Keyboard shortcuts for power users
- Consistent UI design patterns
- Context-sensitive help system

## 8. Acceptance Criteria

### 8.1 Inventory Management
- ✅ Creating purchase invoice increases stock correctly
- ✅ Sales invoice decreases stock using FIFO method
- ✅ System prevents sale of expired batches
- ✅ Stock adjustments are properly recorded and audited
- ✅ Reorder alerts trigger at configured levels

### 8.2 Financial Management
- ✅ All transactions generate correct accounting entries
- ✅ Partial payments update customer balances accurately
- ✅ Tax calculations are correct and configurable
- ✅ Reports show accurate financial positions

### 8.3 System Operations
- ✅ User authentication and authorization work correctly
- ✅ Backup and restore functions preserve data integrity
- ✅ System handles concurrent users without data corruption
- ✅ Audit logs capture all critical operations

## 9. Future Enhancements (Post-MVP)
- Multi-location support
- Integration with external accounting systems
- Mobile app for inventory management
- E-commerce integration
- Advanced analytics and forecasting
- Cloud synchronization option
