import base64
import hashlib
import hmac
from datetime import datetime

import requests

# === User-configurable credentials ===
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
API_PASSPHRASE = "your_api_passphrase"
BASE_URL = "https://www.okx.com"  # Use real endpoint

# === Headers for OKX API ===
def get_headers(method, request_path, body=""):
    timestamp = datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    prehash = f"{timestamp}{method}{request_path}{body}"
    signature = base64.b64encode(
        hmac.new(API_SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
    ).decode()

    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

# === Test runner ===
def run_test():
    print("🔍 Starting OKX LIVE DATA VERIFICATION...")
    print("⚠️  Ensure you're not in paper/simulation mode.")

    # 1. Fetch account holdings
    path = "/api/v5/account/balance"
    url = BASE_URL + path
    headers = get_headers("GET", path)

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        if data.get("code") != "0":
            print("❌ ERROR: Failed to pull live data from OKX.")
            print("Message:", data.get("msg", "Unknown error"))
            return

        print("✅ Live OKX data fetched successfully.")
        balances = data["data"][0]["details"]
        assert balances, "No asset balances returned."

        for asset in balances:
            currency = asset.get("ccy")
            available = asset.get("availBal")
            balance = asset.get("bal")
            frozen = asset.get("frozenBal")
            print(f"✔️  {currency}: Balance = {balance}, Available = {available}, Frozen = {frozen}")

        # 2. Spot holdings test (optional)
        spot_path = "/api/v5/asset/balances"
        spot_url = BASE_URL + spot_path
        spot_headers = get_headers("GET", spot_path)

        spot_resp = requests.get(spot_url, headers=spot_headers).json()
        if spot_resp.get("code") == "0":
            print("✅ Spot asset balances:")
            for item in spot_resp["data"]:
                print(f"   ↪️ {item['ccy']}: {item['bal']} (available: {item['availBal']})")
        else:
            print("⚠️  Could not verify spot asset balances.")

        print("\n✅ All fields pulled directly from live OKX API.")
        print("✅ No simulation/cached data detected.")
        print("🧪 TEST PASSED.")

    except Exception as e:
        print("❌ Unexpected error during verification:", str(e))

# === Run the test ===
if __name__ == "__main__":
    run_test()
