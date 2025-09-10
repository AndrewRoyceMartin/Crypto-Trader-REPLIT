# scripts/verify_runtime.py
import json
import os
import sys

import requests

BASE = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")

def die(msg):
    print(f"❌ {msg}")
    sys.exit(1)

try:
    r = requests.get(f"{BASE}/api/self-check", timeout=25)
    if r.status_code != 200:
        die(f"/api/self-check HTTP {r.status_code}")
    data = r.json()
    print(json.dumps(data.get("status", {}), indent=2))
    if not data.get("healthy", False):
        die("Self-check unhealthy — blocking deploy.")
    print("✅ Self-check healthy")
except Exception as e:
    die(f"error: {e}")
