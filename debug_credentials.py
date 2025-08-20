#!/usr/bin/env python3
import os

print("=== OKX CREDENTIAL DEBUG ===")
print()

# Check all OKX environment variables
okx_vars = [
    'OKX_API_KEY', 'OKX_SECRET_KEY', 'OKX_API_SECRET', 
    'OKX_PASSPHRASE', 'OKX_API_PASSPHRASE',
    'OKX_DEMO', 'OKX_USE_DEMO'
]

for var in okx_vars:
    value = os.getenv(var)
    if value:
        if 'KEY' in var or 'SECRET' in var:
            print(f"{var}: {value[:4]}...{value[-4:]} ({len(value)} chars)")
        elif 'PASSPHRASE' in var:
            print(f"{var}: {'*' * len(value)} ({len(value)} chars)")
        else:
            print(f"{var}: {value}")
    else:
        print(f"{var}: NOT SET")

print()
print("=== CREDENTIAL PRIORITY TEST ===")

def env_first(*keys):
    for k in keys:
        v = os.getenv(k)
        if v and str(v).strip():
            return str(v).strip()
    return None

api_key = env_first("OKX_API_KEY")
secret = env_first("OKX_API_SECRET", "OKX_SECRET_KEY")  
passwd = env_first("OKX_API_PASSPHRASE", "OKX_PASSPHRASE")

print(f"Final API Key: {api_key[:8] if api_key else 'NONE'}...{api_key[-4:] if api_key else ''}")
print(f"Final Secret: {secret[:4] if secret else 'NONE'}...{secret[-4:] if secret else ''}")
print(f"Final Passphrase: {'*' * len(passwd) if passwd else 'NONE'}")

if not (api_key and secret and passwd):
    print("\n❌ MISSING CREDENTIALS")
else:
    print("\n✅ ALL CREDENTIALS PRESENT")