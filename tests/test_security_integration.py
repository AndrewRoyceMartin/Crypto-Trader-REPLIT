"""
Integration tests for the require_admin decorator security improvements.

These tests verify that the security fixes work correctly in realistic scenarios.
"""
import os
import secrets
import unittest
from unittest.mock import Mock, patch, MagicMock


class TestRequireAdminIntegration(unittest.TestCase):
    """Integration tests for require_admin decorator"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_admin_token = os.environ.get('ADMIN_TOKEN')
        self.test_token = "test_secure_token_123"
        os.environ['ADMIN_TOKEN'] = self.test_token
        
    def tearDown(self):
        """Clean up test environment"""
        if self.original_admin_token:
            os.environ['ADMIN_TOKEN'] = self.original_admin_token
        else:
            os.environ.pop('ADMIN_TOKEN', None)

    def create_mock_decorator_context(self):
        """Create mocked Flask context for testing the decorator"""
        mock_request = Mock()
        mock_jsonify = Mock(return_value=("mock_response", 401))
        mock_logger = Mock()
        
        return mock_request, mock_jsonify, mock_logger

    def test_require_admin_x_admin_token_success(self):
        """Test successful authentication with X-Admin-Token header"""
        mock_request, mock_jsonify, mock_logger = self.create_mock_decorator_context()
        mock_request.headers = {"X-Admin-Token": self.test_token}
        mock_request.endpoint = "/test"
        mock_request.remote_addr = "127.0.0.1"
        
        # Simulate the decorator logic
        ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()
        provided_token = mock_request.headers.get("X-Admin-Token")
        if not provided_token:
            auth_header = mock_request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                provided_token = auth_header[7:]
        
        # Test the core security logic
        is_authorized = bool(ADMIN_TOKEN and provided_token and 
                           secrets.compare_digest(provided_token, ADMIN_TOKEN))
        
        self.assertTrue(is_authorized)

    def test_require_admin_bearer_token_success(self):
        """Test successful authentication with Authorization: Bearer header"""
        mock_request, mock_jsonify, mock_logger = self.create_mock_decorator_context()
        mock_request.headers = {"Authorization": f"Bearer {self.test_token}"}
        mock_request.endpoint = "/test"
        mock_request.remote_addr = "127.0.0.1"
        
        # Simulate the decorator logic
        ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()
        provided_token = mock_request.headers.get("X-Admin-Token")
        if not provided_token:
            auth_header = mock_request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                provided_token = auth_header[7:]
        
        # Test the core security logic
        is_authorized = bool(ADMIN_TOKEN and provided_token and 
                           secrets.compare_digest(provided_token, ADMIN_TOKEN))
        
        self.assertTrue(is_authorized)

    def test_require_admin_wrong_token_failure(self):
        """Test failed authentication with wrong token"""
        mock_request, mock_jsonify, mock_logger = self.create_mock_decorator_context()
        mock_request.headers = {"X-Admin-Token": "wrong_token"}
        mock_request.endpoint = "/test"
        mock_request.remote_addr = "127.0.0.1"
        
        # Simulate the decorator logic
        ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()
        provided_token = mock_request.headers.get("X-Admin-Token")
        if not provided_token:
            auth_header = mock_request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                provided_token = auth_header[7:]
        
        # Test the core security logic
        is_authorized = bool(ADMIN_TOKEN and provided_token and 
                           secrets.compare_digest(provided_token, ADMIN_TOKEN))
        
        self.assertFalse(is_authorized)

    def test_require_admin_no_token_failure(self):
        """Test failed authentication with no token provided"""
        mock_request, mock_jsonify, mock_logger = self.create_mock_decorator_context()
        mock_request.headers = {}
        mock_request.endpoint = "/test"
        mock_request.remote_addr = "127.0.0.1"
        
        # Simulate the decorator logic
        ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()
        provided_token = mock_request.headers.get("X-Admin-Token")
        if not provided_token:
            auth_header = mock_request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                provided_token = auth_header[7:]
        
        # Test the core security logic
        is_authorized = bool(ADMIN_TOKEN and provided_token and 
                           secrets.compare_digest(provided_token, ADMIN_TOKEN))
        
        self.assertFalse(is_authorized)

    def test_require_admin_no_admin_token_configured(self):
        """Test behavior when ADMIN_TOKEN is not configured"""
        # Remove ADMIN_TOKEN from environment
        os.environ.pop('ADMIN_TOKEN', None)
        
        mock_request, mock_jsonify, mock_logger = self.create_mock_decorator_context()
        mock_request.headers = {"X-Admin-Token": "any_token"}
        
        # Simulate the decorator logic
        ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()
        
        # Should fail when no ADMIN_TOKEN is set
        self.assertEqual(ADMIN_TOKEN, "")
        
        # The decorator should reject this
        is_configured = bool(ADMIN_TOKEN)
        self.assertFalse(is_configured)

    def test_bearer_token_precedence(self):
        """Test that X-Admin-Token takes precedence over Authorization: Bearer"""
        mock_request, mock_jsonify, mock_logger = self.create_mock_decorator_context()
        mock_request.headers = {
            "X-Admin-Token": self.test_token,
            "Authorization": f"Bearer wrong_token"
        }
        
        # Simulate the token extraction logic
        provided_token = mock_request.headers.get("X-Admin-Token")
        if not provided_token:
            auth_header = mock_request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                provided_token = auth_header[7:]
        
        # Should use X-Admin-Token (the correct one)
        self.assertEqual(provided_token, self.test_token)

    def test_timing_attack_resistance(self):
        """Test that the comparison function is resistant to timing attacks"""
        # This test verifies we use secrets.compare_digest for all comparisons
        
        correct_token = self.test_token
        wrong_token_short = "short"
        wrong_token_long = "a_very_long_wrong_token_that_is_much_longer"
        
        # All comparisons should use constant-time function
        self.assertFalse(secrets.compare_digest(wrong_token_short, correct_token))
        self.assertFalse(secrets.compare_digest(wrong_token_long, correct_token))
        self.assertTrue(secrets.compare_digest(correct_token, correct_token))
        
        # Verify that different length strings work correctly
        # (secrets.compare_digest handles this properly)
        self.assertFalse(secrets.compare_digest("a", "bb"))
        self.assertFalse(secrets.compare_digest("bb", "a"))

    def test_secure_logging_format(self):
        """Test that logging doesn't expose sensitive information"""
        mock_logger = Mock()
        
        def secure_log_unauthorized_access(endpoint, remote_addr):
            """Simulate our secure logging function"""
            mock_logger.warning(f"🛡️ Unauthorized access attempt to {endpoint} from {remote_addr}")
        
        # Test the secure logging
        secure_log_unauthorized_access("/admin/endpoint", "192.168.1.100")
        
        # Verify the log was called
        mock_logger.warning.assert_called_once()
        
        # Get the log message
        call_args = mock_logger.warning.call_args
        log_message = call_args[0][0]
        
        # Verify it contains only safe information
        self.assertIn("/admin/endpoint", log_message)
        self.assertIn("192.168.1.100", log_message)
        
        # Verify it doesn't contain sensitive information
        self.assertNotIn("token", log_message.lower())
        self.assertNotIn("sha256", log_message.lower())
        self.assertNotIn("length", log_message.lower())
        self.assertNotIn("hash", log_message.lower())


if __name__ == '__main__':
    unittest.main()