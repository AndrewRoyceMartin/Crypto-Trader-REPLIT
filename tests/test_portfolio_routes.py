"""
Portfolio Analytics API routes test suite.

Tests all Portfolio Analytics page routes with authentic data only approach:
- Positive tests use monkeypatch to provide fake services with authentic-shaped data
- Negative tests verify 4xx/5xx responses when services unavailable
- No hardcoded demo data in production routes
"""

import json
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock
import pytest


class FakePortfolioService:
    """Fake portfolio service that provides authentic-shaped data for testing."""
    
    def __init__(self, available=True, has_data=True):
        self.available = available
        self.has_data = has_data
    
    def get_portfolio_data(self, currency='USD', force_refresh=False):
        if not self.available:
            raise RuntimeError("Portfolio service unavailable")
            
        if not self.has_data:
            return None
            
        return {
            'total_current_value': 12450.75,
            'total_pnl': 1250.25,
            'total_pnl_percent': 11.15,
            'cash_balance': 500.0,
            'holdings': [
                {
                    'symbol': 'BTC',
                    'name': 'Bitcoin',
                    'amount': 0.25,
                    'current_price': 45000.0,
                    'current_value': 11250.0,
                    'pnl_amount': 1250.0,
                    'pnl_percentage': 12.5,
                    'cost_basis': 10000.0
                },
                {
                    'symbol': 'ETH', 
                    'name': 'Ethereum',
                    'amount': 0.5,
                    'current_price': 2400.0,
                    'current_value': 1200.0,
                    'pnl_amount': 0.25,
                    'pnl_percentage': 0.02,
                    'cost_basis': 1199.75
                }
            ],
            'last_update': datetime.now().isoformat()
        }
    
    def get_portfolio_data_OKX_NATIVE_ONLY(self, currency='USD', force_refresh=False):
        return self.get_portfolio_data(currency, force_refresh)


@pytest.fixture
def app():
    """Create test Flask app."""
    import app as app_module
    app_module.app.config['TESTING'] = True
    return app_module.app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestPortfolioRoutesPositive:
    """Test portfolio routes with fake services (positive path)."""
    
    def test_crypto_portfolio_with_fake_service(self, client, monkeypatch):
        """Test /api/crypto-portfolio with fake portfolio service."""
        fake_service = FakePortfolioService()
        
        # Mock both the import and the function call
        monkeypatch.setattr('app.get_portfolio_service', lambda: fake_service)
        monkeypatch.setattr('src.services.portfolio_service.get_portfolio_service', lambda: fake_service)
        
        response = client.get('/api/crypto-portfolio')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Validate authentic-shaped response
        assert 'holdings' in data
        assert 'overview' in data
        assert isinstance(data['holdings'], list)
        assert len(data['holdings']) == 2
        
        # Validate holding structure
        holding = data['holdings'][0]
        required_fields = ['symbol', 'name', 'amount', 'current_price', 'current_value', 'pnl_amount', 'pnl_percentage']
        for field in required_fields:
            assert field in holding
            
        # Validate overview structure  
        overview = data['overview']
        assert 'total_value' in overview
        assert 'total_pnl' in overview
        assert 'total_pnl_percent' in overview
        assert overview['total_value'] == 12450.75
    
    def test_portfolio_analytics_with_fake_service(self, client, monkeypatch):
        """Test /api/portfolio-analytics with fake portfolio service."""
        fake_service = FakePortfolioService()
        monkeypatch.setattr('app.get_portfolio_service', lambda: fake_service)
        
        response = client.get('/api/portfolio-analytics')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert 'analytics' in data
        assert 'timestamp' in data
        
        analytics = data['analytics']
        assert 'total_value' in analytics
        assert 'total_pnl' in analytics
        assert 'holdings_count' in analytics
        assert analytics['total_value'] == 12450.75
    
    def test_best_performer_with_fake_service(self, client, monkeypatch):
        """Test /api/best-performer with fake portfolio service."""
        fake_service = FakePortfolioService()
        monkeypatch.setattr('app.get_portfolio_service', lambda: fake_service)
        
        response = client.get('/api/best-performer')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert 'best_performer' in data
        assert 'timestamp' in data
        
        best = data['best_performer']
        assert 'symbol' in best
        assert 'pnl_percent' in best
        assert best['symbol'] == 'BTC'  # BTC has higher pnl_percent in fake data
    
    def test_available_positions_with_fake_service(self, client, monkeypatch):
        """Test /api/available-positions with fake portfolio service.""" 
        fake_service = FakePortfolioService()
        monkeypatch.setattr('app.get_portfolio_service', lambda: fake_service)
        
        response = client.get('/api/available-positions')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert 'positions' in data
        assert 'count' in data
        assert isinstance(data['positions'], list)
        assert data['count'] == 2
    
    def test_hybrid_signal_basic(self, client):
        """Test /api/hybrid-signal basic response structure."""
        response = client.get('/api/hybrid-signal?symbol=BTC&price=45000')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert 'symbol' in data
        assert 'signal' in data
        assert 'confidence' in data
        assert 'timestamp' in data
        assert data['symbol'] == 'BTC'
    
    def test_current_holdings_with_fake_service(self, client, monkeypatch):
        """Test /api/current-holdings with fake portfolio service."""
        fake_service = FakePortfolioService()
        
        # Mock both the import and the function call
        monkeypatch.setattr('app.get_portfolio_service', lambda: fake_service)
        monkeypatch.setattr('src.services.portfolio_service.get_portfolio_service', lambda: fake_service)
        
        response = client.get('/api/current-holdings')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'holdings' in data
        assert isinstance(data['holdings'], list)
        assert len(data['holdings']) == 2
        
        # Validate holding format for frontend
        holding = data['holdings'][0]
        required_fields = ['symbol', 'quantity', 'price', 'marketValue', 'pnlPercent']
        for field in required_fields:
            assert field in holding
    
    def test_signals_log_csv_structure_validation(self, client, monkeypatch):
        """Test /signals_log.csv structure validation - skip file content mocking."""
        # This test validates that the CSV endpoint works and returns proper headers
        # The real file test already covers the actual CSV content
        
        # Mock os.path.exists to control file availability
        original_exists = os.path.exists
        
        def mock_exists(path):
            if 'signals_log.csv' in path:
                return True  # Simulate file exists
            return original_exists(path)
        
        monkeypatch.setattr('os.path.exists', mock_exists)
        
        response = client.get('/signals_log.csv')
        
        # Should return 200 with proper CSV headers
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        assert 'no-cache' in response.headers.get('Cache-Control', '')
        
        # Validate that we get some CSV-like content (basic structure check)
        text = response.get_data(as_text=True)
        assert 'timestamp' in text.lower()  # Should have timestamp column
        assert len(text.strip()) > 0  # Should not be empty
    
    def test_signals_log_csv_real_file(self, client):
        """Test /signals_log.csv with the real existing file (if present)."""
        response = client.get('/signals_log.csv')
        
        # Real file exists, should return 200
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        
        # Validate that we get CSV content (basic check)
        text = response.get_data(as_text=True)
        lines = text.strip().split('\n')
        assert len(lines) >= 1  # At least header
        
        # Check header contains expected timestamp field
        header = lines[0].lower()
        assert 'timestamp' in header
    
    def test_export_portfolio_with_fake_service(self, client, monkeypatch):
        """Test /api/export-portfolio with fake portfolio service."""
        fake_service = FakePortfolioService()
        monkeypatch.setattr('app.get_portfolio_service', lambda: fake_service)
        
        response = client.get('/api/export-portfolio')
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        assert 'attachment' in response.headers.get('Content-Disposition', '')
        
        # Validate CSV structure
        text = response.get_data(as_text=True)
        lines = text.strip().split('\n')
        assert len(lines) == 3  # header + 2 holdings
        
        header = lines[0]
        expected_fields = ['symbol', 'name', 'amount', 'current_price', 'current_value', 'cost_basis', 'pnl_amount', 'pnl_percentage']
        for field in expected_fields:
            assert field in header
            
        # Validate data line
        data_line = lines[1]
        assert 'BTC,Bitcoin' in data_line


class TestPortfolioRoutesNegative:
    """Test portfolio routes without fake services (negative path)."""
    
    def test_crypto_portfolio_without_service(self, client, monkeypatch):
        """Test /api/crypto-portfolio fails gracefully when service unavailable."""
        monkeypatch.setattr('app.get_portfolio_service', lambda: None)
        
        response = client.get('/api/crypto-portfolio')
        
        # Should return 500 error, not demo data
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error'] is not None
    
    def test_portfolio_analytics_without_service(self, client, monkeypatch):
        """Test /api/portfolio-analytics fails when service unavailable."""
        monkeypatch.setattr('app.get_portfolio_service', lambda: None)
        
        response = client.get('/api/portfolio-analytics')
        
        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_best_performer_without_holdings(self, client, monkeypatch):
        """Test /api/best-performer with no holdings returns 404."""
        fake_service = FakePortfolioService(has_data=True)  # Service available but returns empty holdings
        fake_service.get_portfolio_data = lambda *args, **kwargs: {'holdings': []}  # Empty holdings
        
        monkeypatch.setattr('app.get_portfolio_service', lambda: fake_service)
        monkeypatch.setattr('src.services.portfolio_service.get_portfolio_service', lambda: fake_service)
        
        response = client.get('/api/best-performer')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_available_positions_service_error(self, client, monkeypatch):
        """Test /api/available-positions with service error."""
        fake_service = FakePortfolioService(available=False)
        monkeypatch.setattr('app.get_portfolio_service', lambda: fake_service)
        
        response = client.get('/api/available-positions')
        
        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_hybrid_signal_missing_symbol(self, client):
        """Test /api/hybrid-signal with missing symbol parameter."""
        response = client.get('/api/hybrid-signal')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Symbol parameter required' in data['error']
    
    def test_signals_log_csv_missing_file(self, client, monkeypatch):
        """Test /signals_log.csv when file doesn't exist."""
        # Move to a directory without the signals file
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            monkeypatch.chdir(temp_dir)
            
            try:
                response = client.get('/signals_log.csv')
                
                # Should return 404, not generate demo data
                assert response.status_code == 404
                data = response.get_json()
                assert 'error' in data
                assert 'not found' in data['error'].lower()
            finally:
                monkeypatch.chdir(original_cwd)
    
    def test_export_portfolio_without_service(self, client, monkeypatch):
        """Test /api/export-portfolio without portfolio service."""
        monkeypatch.setattr('app.get_portfolio_service', lambda: None)
        
        response = client.get('/api/export-portfolio')
        
        assert response.status_code == 503
        data = response.get_json()
        assert data['success'] is False
        assert 'not available' in data['error']
    
    def test_export_portfolio_no_holdings(self, client, monkeypatch):
        """Test /api/export-portfolio with no holdings available."""
        fake_service = FakePortfolioService(has_data=False)
        monkeypatch.setattr('app.get_portfolio_service', lambda: fake_service)
        
        response = client.get('/api/export-portfolio')
        
        assert response.status_code == 503
        data = response.get_json()
        assert data['success'] is False
        assert 'not available' in data['error']
    
    def test_rebalance_portfolio_without_service(self, client, monkeypatch):
        """Test /api/rebalance-portfolio without portfolio service."""
        monkeypatch.setattr('app.get_portfolio_service', lambda: None)
        
        response = client.post('/api/rebalance-portfolio')
        
        assert response.status_code == 503
        data = response.get_json()
        assert data['success'] is False
        assert 'not available' in data['error']
    
    def test_rebalance_portfolio_insufficient_holdings(self, client, monkeypatch):
        """Test /api/rebalance-portfolio with insufficient holdings."""
        fake_service = Mock()
        fake_service.get_portfolio_data.return_value = {'holdings': [{'symbol': 'BTC'}]}  # Only 1 holding
        monkeypatch.setattr('app.get_portfolio_service', lambda: fake_service)
        
        response = client.post('/api/rebalance-portfolio')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Insufficient holdings' in data['error']
    
    def test_equity_curve_without_service(self, client, monkeypatch):
        """Test /api/equity-curve without portfolio service."""
        monkeypatch.setattr('app.get_portfolio_service', lambda: None)
        
        response = client.get('/api/equity-curve')
        
        assert response.status_code == 503
        data = response.get_json() 
        assert data['success'] is False
        assert 'not available' in data['error']


class TestAdminProtectedRoutes:
    """Test admin-protected endpoints require ADMIN_TOKEN."""
    
    def test_performance_charts_without_admin_token(self, client, monkeypatch):
        """Test /api/performance-charts requires admin token."""
        # Ensure ADMIN_TOKEN is set in environment
        monkeypatch.setenv('ADMIN_TOKEN', 'test-admin-token')
        
        # Need to reload the ADMIN_TOKEN variable in app module
        import app
        monkeypatch.setattr('app.ADMIN_TOKEN', 'test-admin-token')
        
        response = client.get('/api/performance-charts')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'unauthorized'
    
    def test_performance_charts_with_admin_token(self, client, monkeypatch):
        """Test /api/performance-charts with valid admin token."""
        admin_token = 'test-admin-token'
        monkeypatch.setenv('ADMIN_TOKEN', admin_token)
        
        # Need to reload the ADMIN_TOKEN variable in app module
        import app
        monkeypatch.setattr('app.ADMIN_TOKEN', admin_token)
        
        # Mock portfolio service for this test
        fake_service = FakePortfolioService()
        monkeypatch.setattr('app.get_portfolio_service', lambda: fake_service)
        
        response = client.get('/api/performance-charts', headers={'X-Admin-Token': admin_token})
        
        # Should not be 401 unauthorized (may be other errors due to missing services)
        assert response.status_code != 401
    
    def test_admin_token_not_configured(self, client, monkeypatch):
        """Test admin endpoints when ADMIN_TOKEN not configured."""
        # Clear ADMIN_TOKEN from environment
        monkeypatch.delenv('ADMIN_TOKEN', raising=False)
        
        # Need to reload the ADMIN_TOKEN variable in app module
        import app
        monkeypatch.setattr('app.ADMIN_TOKEN', '')
        
        response = client.get('/api/performance-charts')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'server misconfigured'