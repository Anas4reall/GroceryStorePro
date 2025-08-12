# GroceryStorePro

A comprehensive desktop application for managing grocery warehouse operations, supporting both wholesale and retail business models with integrated accounting functionality.

## Features

- 📦 **Inventory Management**: Batch tracking, expiry dates, FIFO stock consumption
- 💰 **Dual Pricing**: Wholesale and retail pricing with customer-specific rates
- 📄 **Invoice Management**: Purchase and sales invoices with automatic accounting
- 👥 **Customer & Supplier Management**: Complete CRM functionality
- 📊 **Comprehensive Reporting**: Sales, inventory, financial reports with export options
- 🔐 **Multi-User Support**: Role-based access control (Admin, Manager, Cashier, Warehouse)
- 🏪 **Barcode Scanning**: Support for keyboard wedge barcode scanners
- 🌐 **Bilingual Interface**: Arabic (default) and English support
- 💾 **Automated Backup**: Daily backups with configurable retention
- 📱 **Offline Operation**: Complete local data storage, no internet required

## System Requirements

- **Operating System**: Windows 10/11, Linux, macOS
- **Python**: 3.11 or higher
- **RAM**: Minimum 4GB, Recommended 8GB
- **Storage**: 500MB for application, additional space for data
- **Display**: 1024x768 minimum resolution

## Installation

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/GroceryStorePro.git
   cd GroceryStorePro
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**:
   ```bash
   python -m database.init_db
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

### Production Installation

1. **Download the latest release** from the releases page
2. **Extract the ZIP file** to your desired location
3. **Run GroceryStorePro.exe** (Windows) or the appropriate executable
4. **Follow the setup wizard** to configure your store

## Default Login Credentials

- **Username**: admin
- **Password**: admin123
- **Role**: Administrator

⚠️ **Important**: Change the default password immediately after first login.

## Project Structure

```
GroceryStorePro/
├── database/           # Database models and migrations
│   ├── models/        # Peewee ORM models
│   ├── migrations/    # Database schema changes
│   └── init_db.py     # Database initialization
├── ui/                # User interface components
│   ├── windows/       # Main application windows
│   ├── dialogs/       # Dialog boxes and forms
│   ├── components/    # Reusable UI components
│   └── themes/        # UI themes and styling
├── logic/             # Business logic layer
│   ├── services/      # Business services
│   ├── validators/    # Data validation
│   └── utils/         # Utility functions
├── assets/            # Static assets
│   ├── icons/         # Application icons
│   ├── images/        # Images and logos
│   └── fonts/         # Custom fonts for Arabic support
├── reports/           # Report templates and generators
│   ├── templates/     # Report templates
│   └── generators/    # Report generation logic
├── tests/             # Unit and integration tests
├── config/            # Configuration files
├── docs/              # Documentation
├── main.py            # Application entry point
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Configuration

The application uses configuration files located in the `config/` directory:

- `app_config.ini`: General application settings
- `database_config.ini`: Database connection settings
- `ui_config.ini`: User interface preferences

## Usage

### First Time Setup

1. **Launch the application**
2. **Login with default credentials**
3. **Configure company information** in Settings
4. **Set up chart of accounts** (optional, defaults provided)
5. **Add your first products** and suppliers
6. **Create your first purchase** to add inventory
7. **Start selling!**

### Daily Operations

1. **Morning**: Check dashboard for alerts and low stock
2. **Receiving**: Process purchase invoices and receive stock
3. **Sales**: Create sales invoices using barcode scanner or manual entry
4. **Payments**: Record customer payments and supplier payments
5. **Evening**: Review daily sales report and backup data

## Backup and Restore

### Automatic Backup
- Daily backups are created automatically at midnight
- Backups are stored in `data/backups/` directory
- Retention policy: Keep last 14 backups (configurable)

### Manual Backup
1. Go to **Settings** → **Backup & Restore**
2. Click **Create Backup Now**
3. Choose backup location

### Restore
1. Go to **Settings** → **Backup & Restore**
2. Click **Restore from Backup**
3. Select backup file
4. Confirm restoration (this will overwrite current data)

## Troubleshooting

### Common Issues

**Application won't start**:
- Check Python version (3.11+ required)
- Verify all dependencies are installed
- Check database file permissions

**Database errors**:
- Ensure SQLite file is not corrupted
- Check disk space availability
- Verify database file permissions

**Barcode scanner not working**:
- Ensure scanner is configured as keyboard wedge
- Test scanner in a text editor first
- Check scanner settings for proper termination characters

**Reports not generating**:
- Check write permissions in reports directory
- Verify ReportLab installation
- Check available disk space

### Getting Help

1. **Check the documentation** in the `docs/` folder
2. **Search existing issues** on GitHub
3. **Create a new issue** with detailed description
4. **Contact support** at support@grocerystorepro.com

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

## Support

- 📧 Email: support@grocerystorepro.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/GroceryStorePro/issues)
- 📖 Documentation: [Wiki](https://github.com/yourusername/GroceryStorePro/wiki)

---

**GroceryStorePro** - Professional Grocery Store Management System
© 2024 - Made with ❤️ for grocery store owners
