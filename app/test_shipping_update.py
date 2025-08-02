#!/usr/bin/env python3
"""
Test script to verify the updated shipping calculations
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, '/Users/themagician/QualityClamps_Flask')

from app import calculate_shipping_cost

def test_shipping_calculations():
    """Test the updated shipping calculations"""
    print("🚢 Testing Updated Shipping Calculations")
    print("=" * 50)
    
    test_cases = [
        # (country, weight, quantity, method, description)
        ("United States", 10, 50, "air", "50 pieces to US - Air"),
        ("United States", 10, 100, "air", "100 pieces to US - Air"),
        ("United States", 10, 500, "air", "500 pieces to US - Air"),
        ("United States", 10, 1000, "air", "1000 pieces to US - Air"),
        ("United States", 10, 2000, "air", "2000 pieces to US - Air"),
        ("United States", 10, 5000, "air", "5000 pieces to US - Air"),
        ("United States", 10, 50, "sea", "50 pieces to US - Sea"),
        ("United States", 10, 500, "sea", "500 pieces to US - Sea"),
        ("United States", 10, 2000, "sea", "2000 pieces to US - Sea"),
        ("United States", 10, 5000, "sea", "5000 pieces to US - Sea"),
        ("India", 10, 100, "air", "100 pieces to India - Air"),
        ("Germany", 5, 1500, "air", "1500 pieces to Germany - Air"),
        ("Australia", 20, 3000, "sea", "3000 pieces to Australia - Sea"),
    ]
    
    for country, weight, quantity, method, description in test_cases:
        cost = calculate_shipping_cost(country, weight, quantity, method)
        
        if cost is not None:
            print(f"✅ {description}: ${cost:.2f}")
        else:
            print(f"❌ {description}: Shipping not allowed")
    
    print("\n📊 Discount Verification:")
    
    # Test discount progression for air shipping
    print("\nAir Shipping Discounts (10kg to United States):")
    quantities = [1, 50, 100, 200, 500, 1000, 1500, 2000, 3000, 5000]
    for qty in quantities:
        cost = calculate_shipping_cost("United States", 10, qty, "air")
        print(f"  {qty:>4} pcs: ${cost:.2f}")
    
    # Test sea shipping discounts
    print("\nSea Shipping Discounts (10kg to United States):")
    for qty in quantities:
        cost = calculate_shipping_cost("United States", 10, qty, "sea")
        print(f"  {qty:>4} pcs: ${cost:.2f}")
    
    print("\n🎯 Rate Verification:")
    # Test base rate calculation
    base_cost_no_discount = (12000 / 1000) * 10 * 14  # US distance, 10kg, $14 rate
    discounted_base = base_cost_no_discount * 0.5  # 50% discount
    print(f"Base calculation (no quantity discount): ${discounted_base:.2f}")
    
    actual_cost_1pc = calculate_shipping_cost("United States", 10, 1, "air")
    print(f"Actual cost for 1 piece: ${actual_cost_1pc:.2f}")
    
    if abs(discounted_base - actual_cost_1pc) < 0.01:
        print("✅ Base rate calculation is correct!")
    else:
        print("❌ Base rate calculation mismatch!")

if __name__ == "__main__":
    test_shipping_calculations()
