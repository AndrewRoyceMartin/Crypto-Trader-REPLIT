#!/usr/bin/env python3
"""
Test script to verify stable target price functionality - ensuring targets don't move exponentially
"""

import time

import requests


def test_stable_target_prices():
    """Test that target prices remain stable across multiple API calls"""

    print("🔒 Stable Target Price Test")
    print("=" * 60)

    test_symbols = ['BTC', 'ETH', 'SOL', 'GALA', 'PEPE']

    print("Testing target price stability across multiple calls...")
    print("=" * 60)

    # First API call - establish initial targets
    print("\n📞 Call #1: Establishing initial target prices")
    response1 = requests.get("http://localhost:5000/api/available-positions")
    data1 = response1.json()

    targets_call1 = {}
    for position in data1.get('available_positions', []):
        symbol = position['symbol']
        if symbol in test_symbols:
            targets_call1[symbol] = {
                'current_price': position['current_price'],
                'target_price': position['target_buy_price'],
                'discount': position.get('price_diff_percent', 0)
            }

    # Wait 2 seconds
    print("\n⏱️  Waiting 2 seconds...")
    time.sleep(2)

    # Second API call - verify targets remain stable
    print("\n📞 Call #2: Checking target price stability")
    response2 = requests.get("http://localhost:5000/api/available-positions")
    data2 = response2.json()

    targets_call2 = {}
    for position in data2.get('available_positions', []):
        symbol = position['symbol']
        if symbol in test_symbols:
            targets_call2[symbol] = {
                'current_price': position['current_price'],
                'target_price': position['target_buy_price'],
                'discount': position.get('price_diff_percent', 0)
            }

    # Third API call - further verification
    print("\n📞 Call #3: Final stability check")
    response3 = requests.get("http://localhost:5000/api/available-positions")
    data3 = response3.json()

    targets_call3 = {}
    for position in data3.get('available_positions', []):
        symbol = position['symbol']
        if symbol in test_symbols:
            targets_call3[symbol] = {
                'current_price': position['current_price'],
                'target_price': position['target_buy_price'],
                'discount': position.get('price_diff_percent', 0)
            }

    # Compare results
    print("\n🔍 Stability Analysis:")
    print("=" * 60)

    all_stable = True

    for symbol in test_symbols:
        if symbol in targets_call1 and symbol in targets_call2 and symbol in targets_call3:
            target1 = targets_call1[symbol]['target_price']
            target2 = targets_call2[symbol]['target_price']
            target3 = targets_call3[symbol]['target_price']

            current1 = targets_call1[symbol]['current_price']
            current3 = targets_call3[symbol]['current_price']

            # Check if targets remained stable
            if target1 == target2 == target3:
                status = "✅ STABLE"
            else:
                status = "❌ UNSTABLE"
                all_stable = False

            print(f"\n🪙 {symbol}:")
            print(f"   Current Price: ${current1:.8f} → ${current3:.8f}")
            print(f"   Target Price:  ${target1:.8f} → ${target2:.8f} → ${target3:.8f}")
            print(f"   Status: {status}")

            if target1 != target2 or target2 != target3:
                print("   ⚠️  Target changed! This means orders may never execute!")

    # Check target price manager status
    try:
        status_response = requests.get("http://localhost:5000/api/target-price-status")
        status_data = status_response.json()

        print("\n📊 Target Price Manager Status:")
        print(f"   Total Locked Targets: {status_data.get('total_locked', 0)}")

        for symbol, info in status_data.get('locked_targets', {}).items():
            if symbol in test_symbols:
                print(f"   {symbol}: Locked until {info['locked_until'][:16]} ({info['tier']} tier, {info['discount_percent']:.1f}% discount)")

    except Exception as e:
        print(f"   ⚠️  Could not get target manager status: {e}")

    print("\n🎯 Overall Result:")
    if all_stable:
        print("✅ SUCCESS: All target prices remained stable across multiple calls")
        print("✅ Orders can be placed with confidence that targets won't move")
    else:
        print("❌ FAILURE: Target prices are still moving - orders may never execute!")
        print("❌ This needs to be fixed to prevent exponential recalculation")

    print("\n📈 Expected Behavior:")
    print("   • Target prices should lock for 24 hours once calculated")
    print("   • Only recalculate if market drops >5% from original price")
    print("   • This prevents moving targets that are impossible to reach")

if __name__ == "__main__":
    test_stable_target_prices()
