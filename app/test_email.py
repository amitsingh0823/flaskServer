#!/usr/bin/env python3

"""
Test script for Quality Clamps email functionality
This script tests both order and contact form email notifications
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path so we can import from app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, send_order_notification, send_contact_notification
import time

def test_contact_email():
    """Test contact form email notification"""
    print("Testing contact form email notification...")
    
    # Sample contact data
    contact_data = {
        'name': 'Test Customer',
        'email': 'test@example.com',
        'phone': '+1-234-567-8900',
        'inquiry': 'Product Inquiry',
        'message': 'This is a test message from the contact form to verify email functionality.'
    }
    
    with app.app_context():
        success = send_contact_notification(contact_data)
        if success:
            print("✅ Contact form email sent successfully!")
        else:
            print("❌ Failed to send contact form email")
        return success

def test_order_email():
    """Test order notification email"""
    print("Testing order notification email...")
    
    # Sample order data (simplified version)
    order_data = {
        'order_id': 'TEST-ORD-12345',
        'customer_info': {
            'name': 'Test Customer',
            'company': 'Test Company Ltd.',
            'email': 'test@example.com',
            'phone': '+1-234-567-8900',
            'address': '123 Test Street',
            'city': 'Test City',
            'state': 'Test State',
            'country': 'United States',
            'postal_code': '12345',
            'shipping_method': 'air',
            'notes': 'This is a test order for email verification'
        },
        'order_items': [
            {
                'product': {
                    'name': 'Test V-Band Clamp 5.88 inch'
                },
                'quantity': 10,
                'final_unit_price': 7.20,
                'final_total': 72.00
            }
        ],
        'subtotal': 72.00,
        'shipping_cost': 25.50,
        'total': 97.50,
        'total_weight': 2.58,
        'payment_info': {
            'method': 'PayPal',
            'status': 'Paid',
            'amount': 97.50
        },
        'created_date': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with app.app_context():
        success = send_order_notification(order_data)
        if success:
            print("✅ Order notification email sent successfully!")
        else:
            print("❌ Failed to send order notification email")
        return success

def main():
    """Run email tests"""
    print("🧪 Quality Clamps Email Testing")
    print("=" * 40)
    
    # Check if email credentials are configured
    mail_username = os.getenv('MAIL_USERNAME')
    mail_password = os.getenv('MAIL_PASSWORD')
    
    if not mail_username:
        print("❌ MAIL_USERNAME not configured in .env file")
        return False
    
    if not mail_password or mail_password == 'your_email_password_here':
        print("❌ MAIL_PASSWORD not configured in .env file")
        print("📝 Please set MAIL_PASSWORD in your .env file with the actual email password")
        return False
    
    print(f"📧 Email configured: {mail_username}")
    print(f"📤 Will send notifications to: sales@qualclamps.com")
    print()
    
    # Test contact form email
    contact_success = test_contact_email()
    print()
    
    # Test order notification email  
    order_success = test_order_email()
    print()
    
    # Summary
    print("📊 Test Results:")
    print(f"   Contact Form Email: {'✅ PASS' if contact_success else '❌ FAIL'}")
    print(f"   Order Notification Email: {'✅ PASS' if order_success else '❌ FAIL'}")
    
    if contact_success and order_success:
        print("\n🎉 All email tests passed! Email notifications are working correctly.")
        return True
    else:
        print("\n⚠️  Some email tests failed. Check your email configuration.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
