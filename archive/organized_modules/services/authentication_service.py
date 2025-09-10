"""
Authentication Service
Handles authentication, authorization, and security logic
"""
from typing import Dict, Any, Optional, Callable
import logging
import os
import time
import threading
from collections import defaultdict
from functools import wraps

logger = logging.getLogger(__name__)

class AuthenticationService:
    """Business logic for authentication and security operations."""
    
    def __init__(self):
        self.logger = logger
        self.admin_token = os.getenv("ADMIN_TOKEN", "")
        self._rate_lock = threading.RLock()
        self._rate_hits: Dict[tuple, list] = defaultdict(list)
    
    def verify_admin_token(self, provided_token: Optional[str]) -> bool:
        """Verify admin authentication token."""
        if not self.admin_token:
            return True  # No token configured, allow access
        
        if not provided_token:
            return False
        
        return provided_token == self.admin_token
    
    def require_admin_decorator(self) -> Callable:
        """Decorator factory for admin authentication requirement."""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapper(*args, **kwargs):
                from flask import request, jsonify
                
                token = request.headers.get("X-Admin-Token")
                if not self.verify_admin_token(token):
                    return jsonify({"error": "unauthorized"}), 401
                
                return f(*args, **kwargs)
            return wrapper
        return decorator
    
    def check_rate_limit(self, identifier: str, path: str, max_hits: int, 
                        per_seconds: int) -> tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limits."""
        key = (identifier, path)
        now = time.time()
        
        with self._rate_lock:
            # Get and clean old hits
            hits = self._rate_hits[key]
            hits = [t for t in hits if now - t < per_seconds]
            self._rate_hits[key] = hits
            
            # Check if over limit
            if len(hits) >= max_hits:
                return False, {
                    "error": "rate_limited",
                    "retry_after": per_seconds,
                    "max_requests": max_hits,
                    "window_seconds": per_seconds
                }
            
            # Add current request
            hits.append(now)
            
            return True, {
                "requests_remaining": max_hits - len(hits),
                "window_seconds": per_seconds,
                "reset_time": int(now + per_seconds)
            }
    
    def rate_limit_decorator(self, max_hits: int, per_seconds: int) -> Callable:
        """Decorator factory for rate limiting endpoints."""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapper(*args, **kwargs):
                from flask import request, jsonify
                
                identifier = request.remote_addr or "unknown"
                path = request.path
                
                allowed, rate_info = self.check_rate_limit(
                    identifier, path, max_hits, per_seconds
                )
                
                if not allowed:
                    response = jsonify(rate_info)
                    response.status_code = 429
                    response.headers["Retry-After"] = str(rate_info["retry_after"])
                    return response
                
                # Add rate limit headers to successful responses
                result = f(*args, **kwargs)
                if hasattr(result, 'headers'):
                    result.headers["X-RateLimit-Limit"] = str(max_hits)
                    result.headers["X-RateLimit-Remaining"] = str(rate_info["requests_remaining"])
                    result.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])
                
                return result
            return wrapper
        return decorator
    
    def validate_api_credentials(self) -> Dict[str, Any]:
        """Validate OKX API credentials configuration."""
        okx_api_key = os.getenv("OKX_API_KEY", "")
        okx_secret = os.getenv("OKX_SECRET_KEY", "")
        okx_pass = os.getenv("OKX_PASSPHRASE", "")
        
        credentials_configured = bool(okx_api_key and okx_secret and okx_pass)
        
        return {
            "credentials_configured": credentials_configured,
            "api_key_length": len(okx_api_key) if okx_api_key else 0,
            "secret_key_length": len(okx_secret) if okx_secret else 0,
            "passphrase_length": len(okx_pass) if okx_pass else 0,
            "has_admin_token": bool(self.admin_token)
        }
    
    def generate_api_signature(self, secret_key: str, timestamp: str, method: str, 
                             path: str, body: str = "") -> str:
        """Generate OKX API signature for authentication."""
        import hmac
        import hashlib
        import base64
        
        # OKX signature format: timestamp + method + path + body
        message = f"{timestamp}{method.upper()}{path}{body}"
        
        # Create HMAC-SHA256 signature
        signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Base64 encode the signature
        return base64.b64encode(signature).decode('utf-8')
    
    def sanitize_log_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for safe logging (remove sensitive information)."""
        sensitive_keys = {
            'password', 'secret', 'token', 'key', 'auth', 'credential',
            'private', 'passphrase', 'signature', 'authorization'
        }
        
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if key contains sensitive information
            is_sensitive = any(sensitive in key_lower for sensitive in sensitive_keys)
            
            if is_sensitive:
                # Replace with masked value
                if isinstance(value, str) and len(value) > 4:
                    sanitized[key] = f"{value[:2]}***{value[-2:]}"
                else:
                    sanitized[key] = "***"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def validate_request_data(self, data: Dict[str, Any], 
                            required_fields: list, 
                            optional_fields: list = None) -> tuple[bool, Dict[str, Any]]:
        """Validate request data for required fields and types."""
        optional_fields = optional_fields or []
        errors = {}
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                errors[field] = "Required field missing"
            elif data[field] is None:
                errors[field] = "Field cannot be null"
            elif isinstance(data[field], str) and not data[field].strip():
                errors[field] = "Field cannot be empty"
        
        # Validate allowed fields
        allowed_fields = set(required_fields + optional_fields)
        for field in data.keys():
            if field not in allowed_fields:
                errors[field] = "Unknown field"
        
        is_valid = len(errors) == 0
        
        return is_valid, {
            "valid": is_valid,
            "errors": errors,
            "field_count": len(data),
            "required_count": len(required_fields)
        }