# OKX API Setup Guide

Your trading system is now configured to use only live OKX data (no simulation). To complete the setup, you need working OKX API credentials.

## Current Status
✅ System completely removed all simulation data and fallbacks
✅ Portfolio service configured for live OKX only
✅ All endpoints updated to use real OKX data
✅ Your API credentials are properly formatted and stored
❌ OKX API returning "API key doesn't exist" error (code 50119)

## Diagnosis Results
- ✅ Credentials present: API key (36 chars), Secret (32 chars), Passphrase (8 chars)
- ✅ OKX API is reachable from this environment
- ✅ CCXT library working correctly
- ❌ OKX rejecting your API key with error 50119

## Error Meaning
Code 50119 "API key doesn't exist" means OKX doesn't recognize your API key. This happens when:

## Most Likely Causes & Solutions

### 1. Wrong API Purpose (Most Common)
**Problem**: API key created for "Third-party app connection" instead of "API Trading"
**Solution**: 
- Log into your **main** OKX account (not demo)
- Go to Profile → API Management
- Create a **new** API key
- **Important**: Select **"API Trading"** as the purpose (NOT "Third-party app connection")

### 2. Wrong Environment 
**Problem**: API key created for demo/testnet, but system connects to live trading
**Solution**: 
- Ensure you're on the **live trading** environment when creating the key

### 2. Insufficient Permissions
**Problem**: API key lacks required trading permissions
**Solution**:
- Edit your API key settings
- Enable permissions: ✅ Read ✅ Trade ✅ Funding

### 3. IP Restrictions
**Problem**: Your current IP is not whitelisted
**Solution**:
- In API settings, set IP whitelist to "0.0.0.0/0" (allow all IPs)
- Or add this specific Replit IP to the whitelist

### 4. API Key Status
**Problem**: Key disabled, expired, or incorrectly copied
**Solution**:
- Verify key is "Active" in OKX
- Double-check all three values were copied correctly
- Try creating a fresh API key

## Step-by-Step Fix

1. **Go to OKX.com → Profile → API Management**
2. **Delete old API key** (if any)
3. **Create new API key:**
   - **API Key Name**: Any name (e.g., "Trading Bot", "Portfolio System")
   - **API Purpose**: Select **"API Trading"** (NOT "Third-party app connection")
   - **Environment**: **Live Trading** (not demo/testnet)
   - **Permissions**: 
     - ✅ Read (required for balance/position data)
     - ✅ Trade (required for order management)
     - ✅ Funding (optional, for balance info)
   - **IP Whitelist**: Leave empty or use individual IPs (not 0.0.0.0/0)
   - **Passphrase**: Create a memorable passphrase
4. **Copy ALL THREE values exactly:**
   - API Key (36 chars)
   - Secret Key (32 chars) 
   - Passphrase (your custom phrase)
5. **Update in Replit Secrets:**
   - OKX_API_KEY
   - OKX_SECRET_KEY  
   - OKX_PASSPHRASE

## Australia-Specific Requirements (IMPORTANT)

### For Australian Residents
Since March 2024, Australian users must complete additional verification:

1. **ASIC Compliance**: Complete Australian-specific identity verification
2. **Enhanced KYC**: Pass ASIC-compliant verification process  
3. **Service Limitations**: Only spot trading APIs available (derivatives restricted)
4. **Account Transition**: May need to transition to OKX Australian entities

**Check Your Australia Status:**
- Go to **OKX.com → Profile → Verification**
- Look for "Australian Verification" or "ASIC Compliance" section
- Ensure this shows "Completed" status

If you see any "Pending" Australian verification, this will cause error 50119 even with correct API credentials.

### Additional Australia Steps
For some Australian users, after creating the API key you may need to:
1. **Accept Terms**: Complete Australian entity transition if prompted
2. **Wait for Review**: ASIC compliance review can take 15-30 minutes  
3. **Check Email**: OKX may send verification emails for Australian users
4. **Account Transition**: Some accounts need to transition to OKX Australia entities

If error 50119 persists with correct "API Trading" key, check your OKX account for any pending Australian-specific prompts or notifications.

### IP Whitelist Configuration
**Important:** OKX doesn't accept CIDR notation (0.0.0.0/0). Instead:
- **Option 1**: Leave IP whitelist completely empty (recommended)
- **Option 2**: Add Replit's server IPs (not your personal IP)

**Note:** Your personal IP address is irrelevant because the trading system runs on Replit's servers, which use different IP addresses. Adding your home/office IP won't help.

The incorrect format 0.0.0.0/0 will cause API key creation to fail.

## Additional OKX Account Requirements

### Trading Authorization
Beyond the API key, your OKX account needs:

1. **Account Verification**: 
   - Complete KYC (Know Your Customer) verification
   - Identity verification must be approved

2. **Trading Permissions**:
   - Enable "Spot Trading" in your account settings
   - Enable "API Trading" authorization in account security settings

3. **Funding Requirements**:
   - Account must have sufficient balance for trading
   - Some features require minimum balance thresholds

4. **Security Settings**:
   - Two-factor authentication (2FA) enabled
   - Email verification enabled
   - Phone verification enabled

### Check Your Account Status
Go to: **OKX.com → Profile → Verification** and ensure:
- ✅ Identity Verification: Completed
- ✅ Phone Verification: Completed  
- ✅ Email Verification: Completed
- ✅ Two-Factor Authentication: Enabled

Then go to: **Profile → Security → API Trading** and verify:
- ✅ API Trading: Enabled
- ✅ Spot Trading: Enabled

## System Changes Made

The system has been completely reconfigured to use only your real OKX portfolio data:

- ❌ Removed all SimulatedOKX fallbacks
- ❌ Removed all demo/test data generation
- ❌ Removed simulation portfolio initialization
- ✅ System requires valid OKX credentials to start
- ✅ Portfolio service uses live OKX balance/positions/trades
- ✅ All status endpoints report live exchange connection
- ✅ Price data comes directly from live OKX API

Once you provide working OKX API credentials, the system will display your real portfolio data immediately.