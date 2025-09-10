# scripts/verify_runtime.py
import sys, json, os, requests

BASE = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")

def fail(msg):
    print(f"❌ {msg}")
    sys.exit(1)

try:
    r = requests.get(f"{BASE}/api/self-check", timeout=20)
    if r.status_code != 200:
        fail(f"/api/self-check HTTP {r.status_code}")
    data = r.json()
    ok = data.get("healthy", False)
    status = data.get("status", {})
    print(json.dumps(status, indent=2))
    if not ok:
        fail("Self-check not healthy")
    print("✅ Self-check healthy")
except Exception as e:
    fail(f"error: {e}")