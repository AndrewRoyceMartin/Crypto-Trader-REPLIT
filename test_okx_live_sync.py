import os
import unittest
import hmac
import hashlib
import base64
import requests
from datetime import datetime

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
        print(f"\n🔍 Testing live OKX synchronization...")
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

        print(f"📡 Fetching live OKX balance data...")
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
        print(f"🖥️  Fetching backend portfolio data...")
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
        print(f"\n🔍 Comparing OKX vs Backend data...")
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
        print(f"\n📊 SYNCHRONIZATION RESULTS:")
        print(f"   Perfect Matches: {len(perfect_matches)}")
        print(f"   Mismatches: {len(mismatches)}")
        
        if perfect_matches:
            print(f"\n✅ PERFECT MATCHES:")
            for match in perfect_matches:
                print(f"   {match}")

        if mismatches:
            print(f"\n❌ ISSUES FOUND:")
            for mismatch in mismatches:
                print(f"   {mismatch}")
            self.fail("Live OKX data and backend holdings are not fully synchronized.")
        else:
            print(f"\n🎉 SUCCESS: All OKX holdings perfectly synchronized with backend!")

    def test_price_data_freshness(self):
        """Verify that prices are fresh and from live sources"""
        print(f"\n🕐 Testing price data freshness...")
        
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
        
        print(f"✅ All price data is fresh and live!")

if __name__ == "__main__":
    print("🚀 OKX Live Sync Test Suite")
    print("=" * 50)
    unittest.main(verbosity=2)
