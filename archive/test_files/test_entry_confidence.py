#!/usr/bin/env python3
"""
Test script to verify Predictive Entry Point Confidence Indicator functionality
"""


import requests


def test_entry_confidence():
    """Test entry confidence calculation for individual symbols and batch analysis."""

    print("🎯 Predictive Entry Point Confidence Indicator Test")
    print("=" * 70)

    # Test individual symbol confidence
    print("\n🔍 Testing Individual Symbol Analysis:")
    print("-" * 50)

    test_symbols = ['BTC', 'ETH', 'SOL', 'GALA', 'PEPE']

    for symbol in test_symbols:
        try:
            response = requests.get(f"http://localhost:5000/api/entry-confidence/{symbol}")

            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    info = data['data']
                    print(f"\n💰 {symbol}:")
                    print(f"   Confidence Score: {info['confidence_score']}/100 ({info['confidence_level']})")
                    print(f"   Timing Signal: {info['timing_signal']}")
                    print(f"   Risk Level: {info['risk_level']}")
                    print(f"   Recommendation: {info['entry_recommendation']}")

                    breakdown = info['breakdown']
                    print(f"   Technical Analysis: {breakdown['technical_analysis']}/100")
                    print(f"   Volatility Assessment: {breakdown['volatility_assessment']}/100")
                    print(f"   Momentum Indicators: {breakdown['momentum_indicators']}/100")
                    print(f"   Volume Analysis: {breakdown['volume_analysis']}/100")
                    print(f"   Support/Resistance: {breakdown['support_resistance']}/100")
                else:
                    print(f"   ❌ Error: {data.get('message', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")

    # Test batch analysis
    print("\n\n📊 Testing Batch Analysis:")
    print("-" * 50)

    try:
        response = requests.get("http://localhost:5000/api/entry-confidence-batch")

        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                results = data['data']
                summary = data['summary']

                print(f"Analyzed {data['analyzed_symbols']} symbols")
                print("")
                print("📈 Summary:")
                print(f"   Excellent Entries (90-100): {summary['excellent_entries']}")
                print(f"   Good Entries (75-89): {summary['good_entries']}")
                print(f"   Fair Entries (60-74): {summary['fair_entries']}")
                print(f"   Weak Entries (<60): {summary['weak_entries']}")

                print("\n🏆 Top 5 Entry Opportunities:")
                for i, result in enumerate(results[:5], 1):
                    print(f"   {i}. {result['symbol']}: {result['confidence_score']}/100 ({result['timing_signal']})")

                print("\n⚠️  Symbols to Avoid:")
                weak_entries = [r for r in results if r['confidence_score'] < 50]
                for result in weak_entries[-3:]:  # Show worst 3
                    print(f"   • {result['symbol']}: {result['confidence_score']}/100 ({result['timing_signal']})")
            else:
                print(f"❌ Error: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")

    except Exception as e:
        print(f"❌ Exception: {e}")

    # Test Available Positions integration
    print("\n\n🎪 Testing Available Positions Integration:")
    print("-" * 50)

    try:
        response = requests.get("http://localhost:5000/api/available-positions")

        if response.status_code == 200:
            data = response.json()
            positions = data.get('available_positions', [])

            # Check if confidence data is included
            confidence_enabled_positions = [p for p in positions if 'entry_confidence' in p]

            print(f"Total positions: {len(positions)}")
            print(f"Positions with confidence data: {len(confidence_enabled_positions)}")

            if confidence_enabled_positions:
                print("\n📋 Sample Positions with Confidence:")
                for i, pos in enumerate(confidence_enabled_positions[:5], 1):
                    conf = pos['entry_confidence']
                    print(f"   {i}. {pos['symbol']}: ${pos['current_price']:.6f} | Confidence: {conf['score']}/100 ({conf['level']}) | Signal: {conf['timing_signal']}")
            else:
                print("⚠️  No positions found with confidence data")
        else:
            print(f"❌ HTTP Error: {response.status_code}")

    except Exception as e:
        print(f"❌ Exception: {e}")

    print("\n\n🎯 Feature Summary:")
    print("=" * 70)
    print("✅ Individual Symbol Analysis - Detailed confidence breakdown")
    print("✅ Batch Analysis - Compare multiple assets simultaneously")
    print("✅ Available Positions Integration - Confidence data in trading interface")
    print("✅ Multi-factor Analysis - Technical, volatility, momentum, volume, S/R")
    print("✅ Risk Assessment - Categorized risk levels for position sizing")
    print("✅ Timing Signals - Clear buy/wait/avoid recommendations")
    print("\n📊 Confidence Scale:")
    print("   90-100: EXCELLENT (Strong technical setup)")
    print("   75-89:  GOOD (Solid signals)")
    print("   60-74:  FAIR (Mixed signals, use caution)")
    print("   40-59:  WEAK (Unfavorable conditions)")
    print("   0-39:   POOR (Avoid entry)")

if __name__ == "__main__":
    test_entry_confidence()
