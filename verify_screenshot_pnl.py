#!/usr/bin/env python3
"""
Verify P&L calculations match the OKX screenshot data showing losses
"""

import requests
import json

def verify_screenshot_pnl():
    """Verify P&L calculations match screenshot losses"""
    
    print("📸 Screenshot P&L Verification")
    print("=" * 50)
    
    # Expected P&L from screenshot
    expected_pnl = {
        'SOL': {'pnl_percent': -1.13, 'pnl_amount': -0.36},
        'GALA': {'pnl_percent': -1.62, 'pnl_amount': -0.52},
        'TRX': {'pnl_percent': -1.63, 'pnl_amount': -0.52},
        'PEPE': {'pnl_percent': -0.30, 'pnl_amount': -0.01}
    }
    
    try:
        # Fetch current holdings data
        response = requests.get("http://localhost:5000/api/current-holdings")
        data = response.json()
        
        if not data.get('success'):
            print("❌ Failed to fetch holdings data")
            return
            
        holdings = data.get('holdings', [])
        
        print("Comparing calculated vs expected P&L:")
        
        for holding in holdings:
            symbol = holding['symbol']
            calculated_pnl_percent = holding['pnl_percent']
            calculated_pnl_amount = holding['pnl']
            
            if symbol in expected_pnl:
                expected = expected_pnl[symbol]
                
                print(f"\n🔍 {symbol}:")
                print(f"   Expected P&L: {expected['pnl_percent']:.2f}% (${expected['pnl_amount']:.2f})")
                print(f"   Calculated P&L: {calculated_pnl_percent:.2f}% (${calculated_pnl_amount:.2f})")
                
                # Check if calculations are close to expected
                pnl_percent_diff = abs(calculated_pnl_percent - expected['pnl_percent'])
                pnl_amount_diff = abs(calculated_pnl_amount - expected['pnl_amount'])
                
                if pnl_percent_diff < 0.5 and pnl_amount_diff < 0.1:
                    print(f"   ✅ MATCH - P&L calculations are correct!")
                else:
                    print(f"   ❌ MISMATCH - Calculations don't match screenshot")
                    print(f"      Percent difference: {pnl_percent_diff:.2f}%")
                    print(f"      Amount difference: ${pnl_amount_diff:.2f}")
        
        print(f"\n📊 Summary:")
        print(f"   Screenshot shows realistic small losses (-0.30% to -1.63%)")
        print(f"   System should match these values, not show artificial 17.65% gains")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    verify_screenshot_pnl()