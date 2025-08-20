# OKX Error 50119 Troubleshooting Guide

## The Error
```
okx {"msg":"API key doesn't exist","code":"50119"}
```

## What This Really Means
Despite the message "API key doesn't exist", this error has multiple causes. Here's the systematic approach:

## Step 1: Verify Clean Test
Run our clean smoke test first:
```bash
python smoke_test_live_okx.py
```

If this fails, the issue is with API credentials. If this works but the main app fails, it's an app configuration issue.

## Step 2: API Key Creation Checklist

### ✅ Correct Purpose
- **Must Select**: "API Trading" 
- **NOT**: "Third-party app connection"

### ✅ Correct Environment  
- **Must Select**: "Live Trading"
- **NOT**: "Demo/Testnet"

### ✅ Correct Account
- Create on **main account**
- **NOT**: subaccount

### ✅ Correct Permissions
- ✅ **Read** (required)
- ✅ **Trade** (required) 
- ✅ **Funding** (optional but recommended)

### ✅ IP Whitelist (Critical for Replit)
**Option 1 (Recommended)**: Leave completely empty
**Option 2**: Add `35.229.97.108`

**Note**: Replit's IP can change, so empty whitelist is safest.

## Step 3: Credential Verification

### Format Check
- **API Key**: 36 characters (UUID format)
- **Secret**: 32 characters (hex format)  
- **Passphrase**: Your custom string (case-sensitive)

### Copy Verification
- No leading/trailing spaces
- No extra characters
- Passphrase matches EXACTLY (case-sensitive)

## Step 4: Australian Compliance (If Applicable)
For Australian users, ensure:
- ASIC-compliant verification completed
- Account fully verified for live trading
- All KYC requirements met

## Step 5: System Configuration Check

Run this to verify your system is properly configured:
```bash
python debug_credentials.py
```

Should show:
- All credentials present
- Correct lengths
- Environment variables set properly

## If Still Failing

### 1. Try Key Rotation
- Delete old API key completely
- Create brand new key with fresh passphrase
- Wait 5 minutes after creation
- Update all credentials in Replit Secrets

### 2. Contact OKX Support
If following all steps exactly still results in 50119:
- Screenshot your API key settings page
- Include the error message
- Mention you're using "API Trading" purpose on live environment
- Request verification of key status

## Success Indicators

When working correctly, you'll see:
```
Sandbox mode: False
Headers: {}
✅ LIVE SUCCESS - Balance fetched
```

The 50119 error will disappear completely once credentials are properly configured.