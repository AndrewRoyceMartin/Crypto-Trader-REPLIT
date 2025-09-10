#!/usr/bin/env python3
"""
Test script to verify Target Value and Target P&L calculations
"""

import requests
import json

def test_target_calculations():
    """Test and verify target value calculations"""
    
    print("🎯 Target Value & P&L Calculation Test")
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
            cost_basis = holding['cost_basis']
            current_value = holding['current_value']
            current_pnl_percent = holding['pnl_percent']
            
            print(f"\n📊 {symbol} Target Analysis:")
            print(f"   Cost Basis: ${cost_basis:.8f}")
            print(f"   Current Value: ${current_value:.8f}")
            print(f"   Current P&L: {current_pnl_percent:.2f}%")
            
            # Calculate different target scenarios
            targets = {
                'Conservative (15%)': 1.15,
                'Standard (20%)': 1.20,
                'Aggressive (25%)': 1.25,
                'Meme Coin (30%)': 1.30
            }
            
            for target_name, multiplier in targets.items():
                target_value = cost_basis * multiplier
                target_pnl = target_value - cost_basis
                target_pnl_percent = ((target_pnl / cost_basis) * 100) if cost_basis > 0 else 0
                progress = (current_value / target_value * 100) if target_value > 0 else 0
                
                print(f"   {target_name}: ${target_value:.8f} (${target_pnl:.8f}, {target_pnl_percent:.1f}%) - Progress: {progress:.1f}%")
                
            # Recommended target based on asset type
            if symbol in ['BTC', 'ETH']:
                recommended = 'Conservative (15%)'
            elif symbol == 'PEPE':
                recommended = 'Meme Coin (30%)'
            elif symbol in ['SOL', 'GALA', 'TRX']:
                recommended = 'Aggressive (25%)'
            else:
                recommended = 'Standard (20%)'
                
            print(f"   ✅ Recommended Target: {recommended}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_target_calculations()