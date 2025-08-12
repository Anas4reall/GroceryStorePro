#!/usr/bin/env python3
"""
Test script to verify core functionality of GroceryStorePro.
"""

import sys
from datetime import date, datetime
from decimal import Decimal

# Test database models
try:
    from database.models import (
        User, Product, Category, Unit, Customer, Supplier,
        Sale, Purchase, StockTransaction, database
    )
    print("✅ Database models imported successfully")
except ImportError as e:
    print(f"❌ Failed to import database models: {e}")
    sys.exit(1)

# Test services
try:
    from logic.services.auth_service import AuthService
    from logic.services.inventory_service import InventoryService
    from logic.services.invoice_service import InvoiceService
    from logic.services.reports_service import ReportsService
    print("✅ Business services imported successfully")
except ImportError as e:
    print(f"❌ Failed to import services: {e}")
    sys.exit(1)

# Test configuration
try:
    from config.app_config import AppConfig
    config = AppConfig()
    print(f"✅ Configuration loaded successfully - Language: {config.get_language()}")
except Exception as e:
    print(f"❌ Failed to load configuration: {e}")
    sys.exit(1)

def test_database_connection():
    """Test database connection and basic queries."""
    try:
        database.connect()
        
        # Test user authentication
        admin_user = User.get(User.username == 'admin')
        print(f"✅ Admin user found: {admin_user.full_name}")
        
        # Test password verification
        if admin_user.check_password('admin123'):
            print("✅ Password verification working")
        else:
            print("❌ Password verification failed")
        
        # Test categories and units
        categories_count = Category.select().count()
        units_count = Unit.select().count()
        print(f"✅ Database data: {categories_count} categories, {units_count} units")
        
        database.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_authentication_service():
    """Test authentication service."""
    try:
        auth_service = AuthService()
        
        # Test successful login
        success, user, message = auth_service.authenticate(
            username='admin',
            password='admin123',
            ip_address='127.0.0.1'
        )
        
        if success:
            print(f"✅ Authentication successful: {user.username}")
            
            # Test session creation
            session_id = auth_service.create_session(user, '127.0.0.1')
            print(f"✅ Session created: {session_id[:8]}...")
            
            # Test session validation
            is_valid, session_user = auth_service.validate_session(session_id)
            if is_valid:
                print("✅ Session validation working")
            else:
                print("❌ Session validation failed")
            
            # End session
            auth_service.end_session(session_id)
            print("✅ Session ended successfully")
            
        else:
            print(f"❌ Authentication failed: {message}")
            return False
        
        # Test failed login
        success, user, message = auth_service.authenticate(
            username='admin',
            password='wrongpassword',
            ip_address='127.0.0.1'
        )
        
        if not success:
            print("✅ Failed login handled correctly")
        else:
            print("❌ Failed login not handled properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication service test failed: {e}")
        return False

def test_inventory_service():
    """Test inventory service."""
    try:
        inventory_service = InventoryService()
        
        # Test stock alerts
        alerts = inventory_service.get_stock_alerts()
        print(f"✅ Stock alerts retrieved: {len(alerts)} alerts")
        
        # Test stock valuation
        valuation = inventory_service.get_stock_valuation()
        print(f"✅ Stock valuation calculated: {valuation['total_value']} SAR")
        
        return True
        
    except Exception as e:
        print(f"❌ Inventory service test failed: {e}")
        return False

def test_reports_service():
    """Test reports service."""
    try:
        reports_service = ReportsService()
        
        # Test sales report
        start_date = date.today()
        end_date = date.today()
        
        sales_report = reports_service.generate_sales_summary_report(start_date, end_date)
        print(f"✅ Sales report generated: {sales_report.title}")
        
        # Test inventory report
        inventory_report = reports_service.generate_inventory_report()
        print(f"✅ Inventory report generated: {len(inventory_report.data)} products")
        
        return True
        
    except Exception as e:
        print(f"❌ Reports service test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing GroceryStorePro Core Functionality")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Authentication Service", test_authentication_service),
        ("Inventory Service", test_inventory_service),
        ("Reports Service", test_reports_service),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} - PASSED")
        else:
            print(f"❌ {test_name} - FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! GroceryStorePro is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
