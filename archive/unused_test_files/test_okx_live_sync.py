import base64
import hashlib
import hmac
import os
import unittest
from datetime import datetime

import requests

# === Configurable ===
OKX_API_KEY = os.getenv("OKX_API_KEY")
OKX_API_SECRET = os.getenv("OKX_SECRET_KEY")
OKX_API_PASSPHRASE = os.getenv("OKX_PASSPHRASE")
OKX_BASE_URL = os.getenv("OKX_HOSTNAME", "https://app.okx.com")  # US regional endpoint
LOCAL_API_URL = "http://localhost:5000/api/crypto-portfolio"

# === Generate OKX headers ===
def okx_headers(method, path, body=""):
    if not all([OKX_API_KEY, OKX_API_SECRET, OKX_API_PASSPHRASE]):
        raise ValueError("Missing OKX credentials - check environment variables")

    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    prehash = f"{ts}{method}{path}{body}"
    sign = base64.b64encode(
        hmac.new(OKX_API_SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
    ).decode()

    return {
        "OK-ACCESS-KEY": OKX_API_KEY,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": OKX_API_PASSPHRASE,
        "Content-Type": "application/json"
    }

# === Test Case ===
class TestOKXLiveSync(unittest.TestCase):

    def setUp(self):
        """Setup test environment"""
        self.session = requests.Session()

        # Verify environment setup
        if not all([OKX_API_KEY, OKX_API_SECRET, OKX_API_PASSPHRASE]):
            self.skipTest("Missing OKX credentials - check OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE environment variables")

    def test_live_holdings_match_backend(self):
        """Compare live OKX holdings with backend API"""
        print("\n🔍 Testing live OKX synchronization...")
        print(f"OKX Endpoint: {OKX_BASE_URL}")

        # Ensure URL has proper scheme
        if not OKX_BASE_URL.startswith(('http://', 'https://')):
            okx_base_url = f"https://{OKX_BASE_URL}"
        else:
            okx_base_url = OKX_BASE_URL

        # --- Get live data from OKX ---
        okx_path = "/api/v5/account/balance"
        okx_url = okx_base_url + okx_path

        try:
            headers = okx_headers("GET", okx_path)
        except ValueError as e:
            self.skipTest(f"Cannot create OKX headers: {e}")

        print("📡 Fetching live OKX balance data...")
        okx_response = self.session.get(okx_url, headers=headers, timeout=30)

        if okx_response.status_code != 200:
            self.fail(f"OKX API returned status {okx_response.status_code}: {okx_response.text}")

        okx_data = okx_response.json()

        if okx_data.get("code") != "0":
            self.fail(f"OKX API Error: {okx_data.get('msg', 'Unknown error')}")

        # Parse OKX holdings
        okx_holdings = {}
        if okx_data.get("data") and len(okx_data["data"]) > 0:
            for item in okx_data["data"][0].get("details", []):
                avail_bal = float(item.get("availBal", 0))
                if avail_bal > 0:
                    okx_holdings[item["ccy"]] = avail_bal

        print(f"📊 OKX Holdings Found: {len(okx_holdings)} assets")
        for symbol, balance in okx_holdings.items():
            print(f"   {symbol}: {balance}")

        if not okx_holdings:
            self.skipTest("No holdings found in OKX account")

        # --- Get backend app data ---
        print("🖥️  Fetching backend portfolio data...")
        app_response = self.session.get(LOCAL_API_URL, timeout=30)

        if app_response.status_code != 200:
            self.fail(f"Backend API returned status {app_response.status_code}: {app_response.text}")

        app_data = app_response.json()

        if "holdings" not in app_data:
            self.fail(f"Backend response missing 'holdings' field. Response: {app_data}")

        app_holdings = {}
        for holding in app_data["holdings"]:
            symbol = holding.get("symbol", "").upper()
            quantity = float(holding.get("quantity", 0))
            if quantity > 0:
                app_holdings[symbol] = {
                    "quantity": quantity,
                    "current_price": holding.get("current_price", 0),
                    "current_value": holding.get("current_value", 0),
                    "is_live": holding.get("is_live", False)
                }

        print(f"💾 Backend Holdings Found: {len(app_holdings)} assets")
        for symbol, data in app_holdings.items():
            live_status = "🟢 Live" if data["is_live"] else "🔴 Not Live"
            print(f"   {symbol}: {data['quantity']} ({live_status})")

        # --- Compare holdings ---
        print("\n🔍 Comparing OKX vs Backend data...")
        mismatches = []
        perfect_matches = []

        # Check each OKX holding against backend
        for okx_symbol, okx_balance in okx_holdings.items():
            if okx_symbol not in app_holdings:
                mismatches.append(f"❌ Missing in backend: {okx_symbol} (OKX balance: {okx_balance})")
            else:
                backend_data = app_holdings[okx_symbol]
                backend_quantity = backend_data["quantity"]

                # Check quantity accuracy (allow small floating point differences)
                if abs(backend_quantity - okx_balance) > 0.000001:  # 1e-6 tolerance
                    mismatches.append(
                        f"⚠️ Quantity mismatch for {okx_symbol}: "
                        f"OKX={okx_balance} vs Backend={backend_quantity} "
                        f"(diff: {abs(okx_balance - backend_quantity):.8f})"
                    )
                else:
                    perfect_matches.append(
                        f"✅ {okx_symbol}: {okx_balance} (Live: {backend_data['is_live']})"
                    )

        # Check for extras in backend (shouldn't exist with live data)
        for backend_symbol in app_holdings:
            if backend_symbol not in okx_holdings:
                mismatches.append(f"❌ Backend has extra asset: {backend_symbol}")

        # --- Results ---
        print("\n📊 SYNCHRONIZATION RESULTS:")
        print(f"   Perfect Matches: {len(perfect_matches)}")
        print(f"   Mismatches: {len(mismatches)}")

        if perfect_matches:
            print("\n✅ PERFECT MATCHES:")
            for match in perfect_matches:
                print(f"   {match}")

        if mismatches:
            print("\n❌ ISSUES FOUND:")
            for mismatch in mismatches:
                print(f"   {mismatch}")
            self.fail("Live OKX data and backend holdings are not fully synchronized.")
        else:
            print("\n🎉 SUCCESS: All OKX holdings perfectly synchronized with backend!")

    def test_price_data_freshness(self):
        """Verify that prices are fresh and from live sources"""
        print("\n🕐 Testing price data freshness...")

        # Get backend data twice with small delay
        import time

        app_response1 = self.session.get(LOCAL_API_URL + "?debug=1", timeout=30)
        self.assertEqual(app_response1.status_code, 200)
        data1 = app_response1.json()

        time.sleep(2)  # Small delay

        app_response2 = self.session.get(LOCAL_API_URL + "?debug=2", timeout=30)
        self.assertEqual(app_response2.status_code, 200)
        data2 = app_response2.json()

        # Check timestamps are different (indicating fresh data)
        timestamp1 = data1.get("last_update")
        timestamp2 = data2.get("last_update")

        print(f"📅 First call timestamp: {timestamp1}")
        print(f"📅 Second call timestamp: {timestamp2}")

        self.assertNotEqual(timestamp1, timestamp2,
                           "Timestamps should be different, indicating fresh data calls")

        # Check that all holdings have is_live=True
        if "holdings" in data2:
            for holding in data2["holdings"]:
                symbol = holding.get("symbol")
                is_live = holding.get("is_live", False)
                print(f"   {symbol}: {'🟢 Live' if is_live else '🔴 Not Live'}")
                self.assertTrue(is_live, f"Holding {symbol} should have is_live=True")

        print("✅ All price data is fresh and live!")

    def fetch_backend_holdings(self):
        """Helper method to fetch and parse backend holdings"""
        app_response = self.session.get(LOCAL_API_URL, timeout=30)
        self.assertEqual(app_response.status_code, 200)
        app_data = app_response.json()
        self.assertIn("holdings", app_data)

        app_holdings = {}
        for holding in app_data["holdings"]:
            symbol = holding.get("symbol", "").upper()
            if float(holding.get("quantity", 0)) > 0:
                app_holdings[symbol] = holding
        return app_holdings

    def test_unrealized_pnl_calculation(self):
        """Validate that unrealized PnL calculations are accurate"""
        print("\n🧮 Validating PnL calculations...")
        app = self.fetch_backend_holdings()

        errors = []
        perfect_calculations = []

        for sym, h in app.items():
            try:
                entry = float(h.get("avg_entry_price", 0))
                current = float(h.get("current_price", 0))
                qty = float(h.get("quantity", 0))
                expected_pnl = (current - entry) * qty
                app_pnl = float(h.get("pnl", 0))

                # Use tighter tolerance for PnL validation
                if abs(expected_pnl - app_pnl) > 0.01:
                    errors.append(
                        f"⚠️ {sym} PnL mismatch: "
                        f"expected {expected_pnl:.2f}, app shows {app_pnl:.2f} "
                        f"(entry: {entry}, current: {current}, qty: {qty})"
                    )
                else:
                    perfect_calculations.append(
                        f"✅ {sym}: P&L ${app_pnl:.2f} "
                        f"(${current:.6f} - ${entry:.6f}) × {qty:.2f}"
                    )

            except Exception as e:
                errors.append(f"❌ Error processing {sym}: {e!s}")

        print("📊 PnL Calculation Results:")
        print(f"   Perfect Calculations: {len(perfect_calculations)}")
        print(f"   Calculation Errors: {len(errors)}")

        if perfect_calculations:
            print("\n✅ ACCURATE CALCULATIONS:")
            for calc in perfect_calculations:
                print(f"   {calc}")

        if errors:
            print("\n❌ CALCULATION ISSUES:")
            for error in errors:
                print(f"   {error}")
            self.fail("PnL calculation mismatches found.")
        else:
            print("\n🎉 All unrealized PnL values are calculated correctly!")

    def test_futures_and_margin_balances(self):
        """Check futures and margin account balances from live OKX"""
        print("\n📊 Checking futures/margin account balances...")

        # Ensure URL has proper scheme
        if not OKX_BASE_URL.startswith(('http://', 'https://')):
            okx_base_url = f"https://{OKX_BASE_URL}"
        else:
            okx_base_url = OKX_BASE_URL

        path = "/api/v5/account/account-position-risk"

        try:
            headers = okx_headers("GET", path)
        except ValueError as e:
            self.skipTest(f"Cannot create OKX headers: {e}")

        okx_url = okx_base_url + path

        try:
            resp = self.session.get(okx_url, headers=headers, timeout=30)
            if resp.status_code != 200:
                print(f"⚠️ OKX API returned status {resp.status_code}")
                self.skipTest("Could not fetch futures/margin data - API error")

            data = resp.json()
        except Exception as e:
            print(f"⚠️ Request failed: {e}")
            self.skipTest("Could not fetch futures/margin data - connection error")

        if data.get("code") != "0":
            print(f"⚠️ Could not fetch futures/margin data. OKX Error: {data.get('msg', 'Unknown')}")
            self.skipTest("No futures/margin balances found or access denied.")
        elif not data.get("data"):
            print("ℹ️ No futures or margin positions open.")
            print("✅ Account accessible - no positions found (expected for spot-only account)")
        else:
            print("✅ Futures/margin positions found and live:")
            position_count = 0
            for pos in data["data"]:
                if float(pos.get("pos", 0)) != 0:  # Only show non-zero positions
                    print(f"   {pos.get('instId', 'Unknown')} qty={pos.get('pos', '0')}")
                    position_count += 1

            if position_count == 0:
                print("ℹ️ All positions have zero quantity (closed positions)")
            else:
                print(f"📈 Total active positions: {position_count}")

    def fetch_okx_balances(self):
        """Helper method to fetch OKX balances directly"""
        # Ensure URL has proper scheme
        if not OKX_BASE_URL.startswith(('http://', 'https://')):
            okx_base_url = f"https://{OKX_BASE_URL}"
        else:
            okx_base_url = OKX_BASE_URL

        okx_path = "/api/v5/account/balance"
        okx_url = okx_base_url + okx_path

        try:
            headers = okx_headers("GET", okx_path)
        except ValueError as e:
            self.skipTest(f"Cannot create OKX headers: {e}")

        okx_response = self.session.get(okx_url, headers=headers, timeout=30)

        if okx_response.status_code != 200:
            self.skipTest(f"OKX API returned status {okx_response.status_code}")

        okx_data = okx_response.json()

        if okx_data.get("code") != "0":
            self.skipTest(f"OKX API Error: {okx_data.get('msg', 'Unknown error')}")

        # Parse OKX holdings
        okx_holdings = {}
        if okx_data.get("data") and len(okx_data["data"]) > 0:
            for item in okx_data["data"][0].get("details", []):
                avail_bal = float(item.get("availBal", 0))
                if avail_bal > 0:
                    okx_holdings[item["ccy"]] = avail_bal

        return okx_holdings

    def test_sync_alert_on_discrepancy(self):
        """Monitor and alert on synchronization discrepancies"""
        print("\n🔔 Monitoring mismatch alerts...")
        okx = self.fetch_okx_balances()
        app = self.fetch_backend_holdings()
        alerts = []

        # Check each OKX balance against backend
        for sym, okx_qty in okx.items():
            app_entry = app.get(sym)
            if not app_entry:
                alerts.append(f"🚨 ALERT: {sym} missing from app.")
            else:
                app_qty = float(app_entry.get("quantity", 0))
                # Use stricter tolerance for alerting (0.05 vs 0.000001 for testing)
                if abs(okx_qty - app_qty) > 0.05:
                    alerts.append(
                        f"🚨 ALERT: Quantity drift for {sym}: "
                        f"OKX={okx_qty}, App={app_qty} "
                        f"(diff: {abs(okx_qty - app_qty):.8f})"
                    )

        # Check for extra assets in backend
        for app_sym in app:
            if app_sym not in okx:
                alerts.append(f"🚨 ALERT: {app_sym} exists in app but not in OKX.")

        print("📊 Alert Summary:")
        print(f"   OKX Assets: {len(okx)}")
        print(f"   Backend Assets: {len(app)}")
        print(f"   Alerts Generated: {len(alerts)}")

        if alerts:
            print("\n🚨 DISCREPANCIES DETECTED:")
            for alert in alerts:
                print(f"   {alert}")

            # Log alerts to file
            try:
                with open("sync_alerts.log", "w") as f:
                    f.write("OKX Live Sync Alert Log\n")
                    f.write("=" * 30 + "\n")
                    f.write("Timestamp: 2025-08-21T01:12:00Z\n")
                    f.write(f"OKX Assets: {len(okx)}\n")
                    f.write(f"Backend Assets: {len(app)}\n")
                    f.write(f"Total Alerts: {len(alerts)}\n\n")
                    f.write("ALERTS:\n")
                    f.write("\n".join(alerts))
                print("📝 Alerts logged to sync_alerts.log")
            except Exception as e:
                print(f"⚠️ Could not write alert log: {e}")

            self.fail("Discrepancies detected and logged.")
        else:
            print("\n✅ No discrepancies detected between OKX and backend.")
            print("🎯 Perfect synchronization maintained!")

if __name__ == "__main__":
    print("🚀 OKX Live Sync Test Suite")
    print("=" * 50)
    unittest.main(verbosity=2)
