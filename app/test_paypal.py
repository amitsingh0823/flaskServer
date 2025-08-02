#!/usr/bin/env python3
"""
PayPal Integration Test Script for Quality Clamps Flask App
This script tests the PayPal payment creation functionality
"""

import os
import sys
from dotenv import load_dotenv
import paypalrestsdk

# Load environment variables
load_dotenv()

def test_paypal_configuration():
    """Test PayPal SDK configuration"""
    print("Testing PayPal Configuration...")
    
    # Configure PayPal SDK
    paypalrestsdk.configure({
        "mode": os.getenv('PAYPAL_MODE', 'sandbox'),
        "client_id": os.getenv('PAYPAL_CLIENT_ID'),
        "client_secret": os.getenv('PAYPAL_CLIENT_SECRET')
    })
    
    # Check if credentials are loaded
    client_id = os.getenv('PAYPAL_CLIENT_ID')
    client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
    mode = os.getenv('PAYPAL_MODE', 'sandbox')
    
    print(f"PayPal Mode: {mode}")
    print(f"Client ID: {'✓ Loaded' if client_id else '✗ Missing'}")
    print(f"Client Secret: {'✓ Loaded' if client_secret else '✗ Missing'}")
    
    if not client_id or not client_secret:
        print("\n❌ PayPal credentials not found!")
        print("Please add your PayPal credentials to the .env file:")
        print("PAYPAL_CLIENT_ID=your_client_id_here")
        print("PAYPAL_CLIENT_SECRET=your_client_secret_here")
        print("PAYPAL_MODE=sandbox")
        return False
    
    return True

def test_payment_creation():
    """Test creating a PayPal payment"""
    print("\nTesting Payment Creation...")
    
    try:
        # Create a test payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": "http://localhost:5000/paypal/success",
                "cancel_url": "http://localhost:5000/paypal/cancel"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "Test Clamp",
                        "sku": "TEST-001",
                        "price": "100.00",
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": "100.00",
                    "currency": "USD"
                },
                "description": "Test order for Quality Clamps"
            }]
        })
        
        if payment.create():
            print("✅ Payment created successfully!")
            print(f"Payment ID: {payment.id}")
            
            # Get approval URL
            for link in payment.links:
                if link.rel == "approval_url":
                    print(f"Approval URL: {link.href}")
                    
            return True
        else:
            print("❌ Payment creation failed!")
            print(f"Error: {payment.error}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 Quality Clamps PayPal Integration Test")
    print("=" * 50)
    
    # Test configuration
    if not test_paypal_configuration():
        sys.exit(1)
    
    # Test payment creation
    if test_payment_creation():
        print("\n✅ All tests passed! PayPal integration is working.")
    else:
        print("\n❌ Tests failed! Please check your configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
