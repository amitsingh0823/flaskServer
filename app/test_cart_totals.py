#!/usr/bin/env python3
"""
Test script to verify cart total calculations
"""

import json
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, '/Users/themagician/QualityClamps_Flask')

from app import *

def test_cart_totals():
    """Test cart total calculations"""
    print("🧪 Testing Cart Total Calculations")
    print("=" * 50)
    
    with app.app_context():
        # Clear any existing cart
        session.clear()
        
        # Load a sample product
        products = load_products('v_band')
        if not products:
            print("❌ No products found in v_band category")
            return False
        
        product = products[0]
        print(f"📦 Test Product: {product['name']}")
        print(f"💰 Base Price: ${product['price']}")
        print(f"⚖️  Weight: {product.get('weight', 1.0)} kg")
        
        # Add item to cart with shipping
        cart_key = add_to_cart('v_band', slugify(product['name']), 5, {}, {
            'country': 'United States',
            'method': 'air',
            'cost': 50.0
        })
        
        # Calculate different totals
        products_total = get_cart_products_total()
        shipping_total = get_cart_shipping_total()
        full_total = get_cart_total()
        
        print("\n📊 Cart Total Breakdown:")
        print(f"Products Total: ${products_total:.2f}")
        print(f"Shipping Total: ${shipping_total:.2f}")
        print(f"Full Total (products + shipping): ${full_total:.2f}")
        print(f"Manual Calculation: ${products_total + shipping_total:.2f}")
        
        # Verify the calculations
        expected_full_total = products_total + shipping_total
        
        if abs(full_total - expected_full_total) < 0.01:  # Allow for floating point precision
            print("\n✅ Cart totals are consistent!")
            return True
        else:
            print(f"\n❌ Cart totals are inconsistent!")
            print(f"Expected: ${expected_full_total:.2f}")
            print(f"Actual: ${full_total:.2f}")
            return False

if __name__ == "__main__":
    success = test_cart_totals()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)
