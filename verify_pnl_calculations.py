#!/usr/bin/env python3
"""
Independent P&L calculation verification script.
Verifies the mathematical accuracy of portfolio P&L calculations.
"""

import requests
import json

def verify_pnl_calculations():
    """Verify P&L calculations with independent mathematical methods."""
    
    print("🔍 P&L Calculation Verification")
    print("=" * 50)
    
    try:
        # Fetch current holdings data
        response = requests.get("http://localhost:5000/api/current-holdings")
        data = response.json()
        
        if not data.get('success'):
            print("❌ Failed to fetch holdings data")
            return
            
        holdings = data.get('holdings', [])
        
        for holding in holdings:
            symbol = holding['symbol']
            quantity = holding['quantity']
            cost_basis = holding['cost_basis']
            current_value = holding['current_value']
            reported_pnl = holding['pnl']
            reported_pnl_percent = holding['pnl_percent']
            
            print(f"\n📊 {symbol} Analysis:")
            print(f"   Quantity: {quantity:,.8f}")
            print(f"   Cost Basis: ${cost_basis:.8f}")
            print(f"   Current Value: ${current_value:.8f}")
            
            # Method 1: Direct calculation
            calculated_pnl = current_value - cost_basis
            calculated_pnl_percent = (calculated_pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            print(f"   Reported P&L: ${reported_pnl:.8f} ({reported_pnl_percent:.2f}%)")
            print(f"   Calculated P&L: ${calculated_pnl:.8f} ({calculated_pnl_percent:.2f}%)")
            
            # Method 2: Per-unit calculation
            if quantity > 0:
                purchase_price = cost_basis / quantity
                current_price = current_value / quantity
                profit_per_unit = current_price - purchase_price
                total_profit_alt = profit_per_unit * quantity
                profit_percent_alt = (profit_per_unit / purchase_price * 100) if purchase_price > 0 else 0
                
                print(f"   Purchase Price: ${purchase_price:.8f}")
                print(f"   Current Price: ${current_price:.8f}")
                print(f"   Profit per unit: ${profit_per_unit:.8f}")
                print(f"   Alternative P&L: ${total_profit_alt:.8f} ({profit_percent_alt:.2f}%)")
                
                # Verification
                pnl_match = abs(calculated_pnl - reported_pnl) < 0.01
                pnl_percent_match = abs(calculated_pnl_percent - reported_pnl_percent) < 0.1
                
                if pnl_match and pnl_percent_match:
                    print(f"   ✅ P&L calculations are CORRECT")
                else:
                    print(f"   ❌ P&L calculations have ERRORS")
                    print(f"      P&L Difference: ${abs(calculated_pnl - reported_pnl):.8f}")
                    print(f"      P&L % Difference: {abs(calculated_pnl_percent - reported_pnl_percent):.2f}%")
                    
                # Special verification for specific symbols
                if symbol == 'PEPE':
                    print(f"   🔎 PEPE Special Check:")
                    if cost_basis > 0:
                        print(f"      Cost basis is properly set (not zero)")
                        expected_pepe_price = 0.00000800
                        actual_purchase_price = cost_basis / quantity
                        if abs(actual_purchase_price - expected_pepe_price) < 0.00000001:
                            print(f"      ✅ Purchase price matches expected ${expected_pepe_price:.8f}")
                        else:
                            print(f"      ❌ Purchase price ${actual_purchase_price:.8f} doesn't match expected ${expected_pepe_price:.8f}")
                    else:
                        print(f"      ❌ Cost basis is zero - this is incorrect")
                        
        print(f"\n📈 Portfolio Summary:")
        total_pnl = data.get('total_pnl', 0)
        total_pnl_percent = data.get('total_pnl_percent', 0)
        total_value = data.get('total_current_value', 0)
        print(f"   Total Current Value: ${total_value:.2f}")
        print(f"   Total P&L: ${total_pnl:.2f} ({total_pnl_percent:.2f}%)")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    verify_pnl_calculations()