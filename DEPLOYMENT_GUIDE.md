# 🚀 GroceryStorePro - Deployment Guide

## 📋 **Prerequisites**

### **System Requirements**
- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.8 or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 500MB free space
- **Display**: 1024x768 minimum resolution

### **Python Dependencies**
```bash
pip install peewee bcrypt python-dateutil
```

## 🛠️ **Installation Steps**

### **1. Download and Extract**
```bash
# Extract the GroceryStorePro files to your desired directory
cd /path/to/grocerystorepro
```

### **2. Install Dependencies**
```bash
# Install required Python packages
pip install -r requirements.txt
```

### **3. Initialize Database**
```bash
# Create and populate the database with default data
python -m database.init_db
```

### **4. Test Installation**
```bash
# Run the core functionality test
python test_core_functionality.py
```

### **5. Run Application**
```bash
# Start the application
python main.py
```

## 🔐 **Default Login Credentials**

- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Important**: Change the default password immediately after first login!

## 📁 **Directory Structure**

```
GroceryStorePro/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── config/                # Configuration files
│   └── app_config.py      # Application settings
├── database/              # Database layer
│   ├── models/            # Database models
│   └── init_db.py         # Database initialization
├── logic/                 # Business logic
│   ├── services/          # Business services
│   ├── validators/        # Data validation
│   └── utils/             # Utility functions
├── ui/                    # User interface
│   ├── windows/           # Main windows
│   ├── dialogs/           # Dialog boxes
│   └── components/        # UI components
├── data/                  # Data storage
│   └── grocerystore.db    # SQLite database
├── logs/                  # Application logs
├── reports/               # Generated reports
└── tests/                 # Test files
```

## ⚙️ **Configuration**

### **Application Settings**
Edit `config/settings.ini` to customize:

```ini
[APPLICATION]
language = ar
theme = modern
auto_backup = true

[DATABASE]
backup_retention_days = 14

[BUSINESS]
company_name = متجر البقالة المحترف
default_currency = SAR
default_tax_rate = 15.0
```

### **System Settings**
Access via: **Tools → Settings** in the application menu

## 🔒 **Security Configuration**

### **User Management**
1. **Change Default Password**
   - Login as admin
   - Go to **Tools → Settings → Users**
   - Change admin password

2. **Create User Accounts**
   - Add users with appropriate roles:
     - **Admin**: Full system access
     - **Manager**: Business operations
     - **Cashier**: Sales only
     - **Warehouse**: Inventory management

### **Backup Configuration**
1. **Automatic Backups**
   - Enabled by default
   - Daily backups to `data/backups/`
   - Retention: 14 days

2. **Manual Backup**
   - **Tools → Backup → Create Backup**
   - Export to external storage

## 📊 **Initial Setup**

### **1. Company Information**
- **Tools → Settings → General**
- Set company name (Arabic/English)
- Configure currency and tax rates

### **2. Product Categories**
- **Edit → Products → Categories**
- Add your product categories
- Set up units of measurement

### **3. Chart of Accounts**
- Pre-configured for grocery stores
- Customize via **Tools → Settings → Accounting**

### **4. Customers and Suppliers**
- **Edit → Customers** - Add regular customers
- **Edit → Suppliers** - Add your suppliers

## 🎯 **First Steps After Installation**

### **Day 1: Setup**
1. ✅ Change admin password
2. ✅ Configure company information
3. ✅ Set up product categories
4. ✅ Add initial products
5. ✅ Create user accounts

### **Day 2: Data Entry**
1. ✅ Add customers and suppliers
2. ✅ Enter opening stock
3. ✅ Configure pricing
4. ✅ Test sales process

### **Day 3: Training**
1. ✅ Train staff on system usage
2. ✅ Test all workflows
3. ✅ Generate sample reports
4. ✅ Verify backup system

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Database Connection Error**
```bash
# Reinitialize database
python -m database.init_db
```

#### **Permission Errors**
```bash
# Check file permissions
chmod +x main.py
```

#### **Missing Dependencies**
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

#### **UI Not Displaying**
- Ensure GUI environment is available
- Check display settings
- Verify tkinter installation

### **Log Files**
Check `logs/grocerystorepro.log` for detailed error information.

## 📱 **Multi-Language Support**

### **Arabic Interface**
- Default language is Arabic
- RTL (Right-to-Left) text support
- Arabic number formatting

### **English Interface**
- Switch via login screen
- Or **Tools → Settings → Language**

## 🔄 **Backup and Recovery**

### **Automatic Backup**
- Daily backups at midnight
- Stored in `data/backups/`
- Compressed SQLite files

### **Manual Backup**
```bash
# Create backup
python -c "from logic.utils.backup import create_backup; create_backup()"
```

### **Restore from Backup**
```bash
# Restore database
python -c "from logic.utils.backup import restore_backup; restore_backup('backup_file.db')"
```

## 📈 **Performance Optimization**

### **Database Optimization**
- Regular VACUUM operations
- Index maintenance
- Log file rotation

### **System Requirements**
- **Small Store**: 2GB RAM, 100MB storage
- **Medium Store**: 4GB RAM, 500MB storage
- **Large Store**: 8GB RAM, 1GB+ storage

## 🆘 **Support and Maintenance**

### **Regular Maintenance**
- **Weekly**: Check backup files
- **Monthly**: Review user accounts
- **Quarterly**: Update system settings

### **Support Resources**
- User Manual: `docs/user_manual.pdf`
- Video Tutorials: Available on request
- Technical Support: Contact system administrator

## 🎉 **Go Live Checklist**

- [ ] Database initialized successfully
- [ ] Admin password changed
- [ ] Company information configured
- [ ] Product categories set up
- [ ] Initial products added
- [ ] User accounts created
- [ ] Customers and suppliers added
- [ ] Opening stock entered
- [ ] Pricing configured
- [ ] Staff trained
- [ ] Backup system tested
- [ ] Reports verified
- [ ] System performance tested

## 📞 **Getting Help**

If you encounter any issues:

1. **Check the logs**: `logs/grocerystorepro.log`
2. **Run diagnostics**: `python test_core_functionality.py`
3. **Review documentation**: `README.md`
4. **Contact support**: Include log files and error messages

---

**GroceryStorePro** is now ready for production use! 🎉
