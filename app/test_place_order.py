#!/usr/bin/env python3
"""
Debug script to test place_order function
"""

import requests
import json

def test_place_order():
    """Test the place_order endpoint with debug info"""
    
    # Test data for placing an order
    test_data = {
        'name': 'Test Customer',
        'email': 'test@example.com',
        'phone': '+1234567890',
        'company': 'Test Company',
        'address': '123 Test Street',
        'city': 'Test City',
        'state': 'Test State',
        'country': 'United States',
        'postal_code': '12345',
        'shipping_method': 'air',
        'payment_method': 'paypal',
        'notes': 'Test order'
    }
    
    try:
        # First, let's check if the checkout page loads
        print("🔍 Testing checkout page...")
        checkout_response = requests.get('http://127.0.0.1:5000/checkout')
        print(f"Checkout page status: {checkout_response.status_code}")
        
        if checkout_response.status_code == 302:
            print("🛒 Cart is empty - checkout redirected")
            return
        
        # Test the place_order endpoint
        print("\n📦 Testing place_order endpoint...")
        response = requests.post('http://127.0.0.1:5000/place-order', data=test_data)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 302:
            print(f"🔄 Redirect to: {response.headers.get('Location', 'Unknown')}")
        else:
            print(f"Response content preview: {response.text[:500]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure Flask app is running")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_place_order()
