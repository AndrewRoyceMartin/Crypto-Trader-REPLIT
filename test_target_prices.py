#!/usr/bin/env python3
"""
Test script to verify profitable target buy price calculations
"""

import requests
import json

def test_target_buy_prices():
    """Test target buy price calculations for different asset tiers"""
    
    print("🎯 Target Buy Price Calculation Test")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:5000/api/available-positions")
        data = response.json()
        
        if not data.get('available_positions'):
            print("❌ No available positions returned")
            return
            
        # Test different asset tiers
        test_symbols = ['BTC', 'ETH', 'SOL', 'GALA', 'PEPE', 'SAND', 'DOGE', 'ADA']
        
        print("Testing profitable target prices by asset tier:")
        print("=" * 60)
        
        for position in data['available_positions']:
            symbol = position['symbol']
            
            if symbol in test_symbols:
                current_price = position['current_price']
                target_price = position['target_buy_price']
                
                if current_price > 0 and target_price > 0:
                    discount_percent = ((current_price - target_price) / current_price) * 100
                    
                    # Determine expected tier
                    if symbol in ['BTC', 'ETH']:
                        tier = 'Large Cap'
                        expected_range = (3, 8)
                    elif symbol in ['SOL', 'ADA']:
                        tier = 'Mid Cap'
                        expected_range = (5, 12)
                    elif symbol in ['GALA', 'SAND']:
                        tier = 'Gaming/Meta'
                        expected_range = (8, 15)
                    elif symbol in ['PEPE', 'DOGE']:
                        tier = 'Meme'
                        expected_range = (10, 20)
                    else:
                        tier = 'Altcoin'
                        expected_range = (6, 12)
                    
                    print(f"\n🪙 {symbol} ({tier}):")
                    print(f"   Current Price: ${current_price:.8f}")
                    print(f"   Target Price:  ${target_price:.8f}")
                    print(f"   Discount:      {discount_percent:.1f}%")
                    print(f"   Expected Range: {expected_range[0]}-{expected_range[1]}%")
                    
                    if expected_range[0] <= discount_percent <= expected_range[1]:
                        print(f"   ✅ GOOD - Discount within profitable range")
                    else:
                        print(f"   ⚠️  WARNING - Discount outside expected range")
                        
        print(f"\n📊 Target Price Strategy:")
        print(f"   • Large Cap (BTC/ETH): 3-8% discount for stability")
        print(f"   • Mid Cap: 5-12% discount for moderate volatility")
        print(f"   • Gaming/Meta: 8-15% discount for higher volatility")
        print(f"   • Meme Coins: 10-20% discount for extreme volatility")
        print(f"   • General Altcoins: 6-12% standard discount")
        print(f"\n✅ All target prices should be BELOW current market price for profitable entries")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_target_buy_prices()