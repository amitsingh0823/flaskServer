#!/usr/bin/env python3
"""
Test script to add items to cart and then test checkout
"""

import requests
import json

def test_full_checkout_flow():
    """Test the complete checkout flow including adding items to cart"""
    
    session = requests.Session()
    
    try:
        # Step 1: Load the main page to get session started
        print("🏠 Loading main page...")
        response = session.get('http://127.0.0.1:5000/')
        print(f"Main page status: {response.status_code}")
        
        # Step 2: Add an item to cart
        print("\n🛒 Adding item to cart...")
        cart_data = {
            'category_folder': 'v_band',
            'product_slug': 'test-product',
            'quantity': 2,
            'specifications': {},
            'shipping': {
                'country': 'United States',
                'method': 'air',
                'cost': 50.0
            }
        }
        
        add_response = session.post(
            'http://127.0.0.1:5000/add-to-cart',
            json=cart_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Add to cart status: {add_response.status_code}")
        if add_response.status_code == 200:
            result = add_response.json()
            print(f"Cart result: {result}")
        
        # Step 3: Check checkout page
        print("\n🧾 Loading checkout page...")
        checkout_response = session.get('http://127.0.0.1:5000/checkout')
        print(f"Checkout page status: {checkout_response.status_code}")
        
        if checkout_response.status_code == 302:
            print("🔄 Checkout redirected (likely empty cart)")
            return
        
        # Step 4: Test place order
        print("\n📦 Testing place order...")
        order_data = {
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
        
        order_response = session.post('http://127.0.0.1:5000/place-order', data=order_data)
        print(f"Place order status: {order_response.status_code}")
        print(f"Response headers: {dict(order_response.headers)}")
        
        if order_response.status_code == 302:
            redirect_url = order_response.headers.get('Location', 'Unknown')
            print(f"🔄 Redirected to: {redirect_url}")
            if 'paypal.com' in redirect_url:
                print("✅ Successfully redirected to PayPal!")
            else:
                print("❌ Redirected somewhere else, not PayPal")
        else:
            print("❌ No redirect - something went wrong")
            print(f"Response content preview: {order_response.text[:300]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_full_checkout_flow()
