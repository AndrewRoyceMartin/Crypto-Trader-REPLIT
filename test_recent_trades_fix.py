#!/usr/bin/env python3
"""
Test script to verify recent trades display is working correctly
"""

import requests
import json

def test_recent_trades():
    """Test recent trades functionality"""
    
    print("🔄 Recent Trades Display Test")
    print("=" * 50)
    
    try:
        # Test the working trade-history endpoint
        print("✅ Testing /api/trade-history endpoint:")
        response = requests.get("http://localhost:5000/api/trade-history?timeframe=7d")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            trades = data.get('trades', [])
            print(f"   ✅ Success! Found {len(trades)} trades")
            
            if trades:
                print(f"   📊 Sample trade data:")
                sample_trade = trades[0]
                print(f"      Symbol: {sample_trade.get('symbol')}")
                print(f"      Side: {sample_trade.get('side')}")
                print(f"      Price: ${sample_trade.get('price', 0):.8f}")
                print(f"      Quantity: {sample_trade.get('quantity', 0)}")
                print(f"      Value: ${sample_trade.get('total_value', 0):.2f}")
                print(f"      Timestamp: {sample_trade.get('timestamp')}")
                print(f"      Source: {sample_trade.get('source')}")
            else:
                print("   ⚠️  No trades returned")
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        
        # Test the problematic recent-trades endpoint
        print(f"\n❌ Testing /api/recent-trades endpoint (should redirect):")
        response = requests.get("http://localhost:5000/api/recent-trades?timeframe=7d", allow_redirects=True)
        print(f"   Status: {response.status_code}")
        print(f"   Final URL: {response.url}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                trades = data.get('trades', [])
                print(f"   ✅ Redirect worked! Found {len(trades)} trades")
            except:
                print(f"   ❌ Response not JSON: {response.text[:100]}")
        else:
            print(f"   ❌ Failed with status {response.status_code}")
        
        print(f"\n📝 Recommendation:")
        print(f"   Frontend should use: /api/trade-history?timeframe=7d")
        print(f"   This endpoint returns authentic OKX and database trade data")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_recent_trades()