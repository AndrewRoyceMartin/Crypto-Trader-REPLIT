#!/usr/bin/env python3
"""
Test script to verify /api/trades datetime handling and JSON serialization.
"""

import requests
import json
from datetime import datetime


def test_trades_endpoint():
    """Test that /api/trades endpoint handles datetimes correctly."""
    print("🧪 Testing /api/trades datetime handling...")
    
    try:
        # Test the endpoint
        response = requests.get("http://127.0.0.1:5000/api/trades", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(response.text[:500])
            return False
            
        # Parse JSON response
        data = response.json()
        
        print(f"✅ JSON parsing successful")
        print(f"Success: {data.get('success', False)}")
        print(f"Total trades: {len(data.get('trades', []))}")
        
        # Check timestamp format in trades
        trades = data.get('trades', [])
        if trades:
            first_trade = trades[0]
            timestamp = first_trade.get('timestamp')
            print(f"First trade timestamp: {timestamp}")
            print(f"Timestamp type: {type(timestamp)}")
            
            # Verify timestamp is string and properly formatted
            if isinstance(timestamp, str) and timestamp.endswith('Z'):
                print("✅ Timestamp format is correct (ISO Z)")
            else:
                print(f"❌ Timestamp format issue: {timestamp}")
                return False
                
        # Test sorting (timestamps should be descending)
        timestamps = [t.get('timestamp') for t in trades[:5]]
        print(f"First 5 timestamps: {timestamps}")
        
        # Verify chronological order
        for i in range(len(timestamps) - 1):
            if timestamps[i] < timestamps[i + 1]:
                print(f"❌ Sorting issue: {timestamps[i]} should be >= {timestamps[i + 1]}")
                return False
                
        print("✅ Timestamp sorting is correct")
        print("✅ All datetime tests passed!")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_trades_endpoint()
    exit(0 if success else 1)