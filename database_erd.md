# GroceryStorePro - Database Entity Relationship Diagram

## Database Schema Design

### Core Entities and Relationships

```mermaid
erDiagram
    User ||--o{ AuditLog : creates
    User {
        int id PK
        string username UK
        string password_hash
        string full_name
        string email
        string role
        boolean is_active
        datetime created_at
        datetime last_login
    }

    Product ||--o{ Batch : has
    Product ||--o{ PurchaseItem : contains
    Product ||--o{ SaleItem : contains
    Product ||--o{ StockTransaction : affects
    Product {
        int id PK
        string sku UK
        string name
        string name_ar
        string category
        string unit
        decimal buy_price
        decimal sell_price_retail
        decimal sell_price_wholesale
        int reorder_point
        boolean is_active
        boolean track_batches
        datetime created_at
        datetime updated_at
    }

    Batch ||--o{ StockTransaction : involves
    Batch ||--o{ SaleItem : uses
    Batch {
        int id PK
        int product_id FK
        string batch_no
        date expiry_date
        int current_qty
        decimal cost_per_unit
        datetime created_at
    }

    StockTransaction {
        int id PK
        int product_id FK
        int batch_id FK
        string transaction_type
        int quantity
        string reason
        int reference_id
        string reference_type
        int user_id FK
        datetime timestamp
    }

    Customer ||--o{ Sale : places
    Customer ||--o{ Payment : makes
    Customer {
        int id PK
        string code UK
        string name
        string name_ar
        string phone
        string email
        string address
        string customer_type
        decimal credit_limit
        decimal current_balance
        int payment_terms_days
        boolean is_active
        datetime created_at
    }

    Supplier ||--o{ Purchase : receives
    Supplier ||--o{ Payment : receives
    Supplier {
        int id PK
        string code UK
        string name
        string name_ar
        string phone
        string email
        string address
        decimal current_balance
        int payment_terms_days
        boolean is_active
        datetime created_at
    }

    Purchase ||--o{ PurchaseItem : contains
    Purchase ||--o{ Payment : has
    Purchase {
        int id PK
        string invoice_no UK
        int supplier_id FK
        date invoice_date
        decimal subtotal
        decimal discount_amount
        decimal tax_amount
        decimal total_amount
        decimal paid_amount
        string status
        string notes
        int user_id FK
        datetime created_at
    }

    PurchaseItem {
        int id PK
        int purchase_id FK
        int product_id FK
        string batch_no
        date expiry_date
        int quantity
        decimal unit_cost
        decimal line_total
    }

    Sale ||--o{ SaleItem : contains
    Sale ||--o{ Payment : has
    Sale {
        int id PK
        string invoice_no UK
        int customer_id FK
        date invoice_date
        string pricing_mode
        decimal subtotal
        decimal discount_amount
        decimal tax_amount
        decimal total_amount
        decimal paid_amount
        string status
        string notes
        int user_id FK
        datetime created_at
    }

    SaleItem {
        int id PK
        int sale_id FK
        int product_id FK
        int batch_id FK
        int quantity
        decimal unit_price
        decimal line_total
    }

    Payment {
        int id PK
        string payment_no UK
        string linked_to_type
        int linked_to_id
        decimal amount
        string payment_method
        string reference_no
        date payment_date
        string notes
        int user_id FK
        datetime created_at
    }

    Account ||--o{ JournalEntryLine : affects
    Account {
        int id PK
        string code UK
        string name
        string name_ar
        string account_type
        int parent_id FK
        boolean is_active
        datetime created_at
    }

    JournalEntry ||--o{ JournalEntryLine : contains
    JournalEntry {
        int id PK
        string entry_no UK
        date entry_date
        string description
        string reference_type
        int reference_id
        decimal total_debit
        decimal total_credit
        int user_id FK
        datetime created_at
    }

    JournalEntryLine {
        int id PK
        int journal_entry_id FK
        int account_id FK
        decimal debit_amount
        decimal credit_amount
        string description
    }

    AuditLog {
        int id PK
        int user_id FK
        string table_name
        int record_id
        string action
        text old_values
        text new_values
        datetime timestamp
    }

    SystemSetting {
        int id PK
        string key UK
        string value
        string description
        datetime updated_at
    }
```

## Key Relationships Explained

### 1. Product Management
- **Product** → **Batch**: One product can have multiple batches (1:N)
- **Batch** → **StockTransaction**: Each batch can have multiple stock movements (1:N)
- Products can be configured to track batches or not (track_batches flag)

### 2. Transaction Flow
- **Purchase** → **PurchaseItem**: One purchase can have multiple line items (1:N)
- **Sale** → **SaleItem**: One sale can have multiple line items (1:N)
- **SaleItem** → **Batch**: Each sale item references a specific batch for FIFO tracking

### 3. Financial Management
- **Payment**: Polymorphic relationship - can link to Purchase or Sale
- **JournalEntry**: Auto-generated for all financial transactions
- **Account**: Hierarchical chart of accounts structure

### 4. Audit and Security
- **User**: Role-based access control
- **AuditLog**: Tracks all critical data changes
- **SystemSetting**: Configurable system parameters

## Database Indexes

### Primary Indexes
- All primary keys (id fields)
- Unique constraints on business keys (sku, invoice_no, etc.)

### Performance Indexes
- product_id on Batch, StockTransaction, PurchaseItem, SaleItem
- customer_id on Sale
- supplier_id on Purchase
- invoice_date on Sale and Purchase
- timestamp on StockTransaction and AuditLog
- batch_id on SaleItem for FIFO queries

## Data Integrity Constraints

### Foreign Key Constraints
- All FK relationships enforced at database level
- Cascade deletes where appropriate (e.g., PurchaseItem when Purchase deleted)
- Restrict deletes for referenced entities (e.g., cannot delete Product with existing stock)

### Business Logic Constraints
- Stock quantities cannot go negative (configurable)
- Expiry dates must be future dates for new batches
- Payment amounts cannot exceed outstanding balances
- Journal entries must balance (total_debit = total_credit)

### Data Validation
- Email format validation
- Phone number format validation
- Positive values for prices and quantities
- Valid date ranges for transactions
