"""
Client-side smoke test for Portfolio Analytics page.

Tests:
- Portfolio page returns 200
- Critical HTML elements are present
- Chart.js is included (portfolio page requirement)
- Base layout contains showToast function
- TradingDebug system is available
- Page script defines window.refreshPageData
"""

import pytest
from bs4 import BeautifulSoup


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


class TestPortfolioPageSmoke:
    """Smoke tests for the Portfolio Analytics page."""
    
    def test_portfolio_page_loads(self, client):
        """Test that /portfolio returns 200."""
        response = client.get('/portfolio')
        assert response.status_code == 200
        assert response.headers['Content-Type'].startswith('text/html')
    
    def test_portfolio_page_critical_elements(self, client):
        """Test that portfolio page contains critical DOM elements."""
        response = client.get('/portfolio')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Critical elements from portfolio_advanced.html
        critical_elements = [
            '#totalPortfolioValue',
            '#allocationChart', 
            '#portfolioPositionsTable',
            '#positionsCount'
        ]
        
        missing_elements = []
        for selector in critical_elements:
            element = soup.select_one(selector)
            if element is None:
                missing_elements.append(selector)
        
        assert len(missing_elements) == 0, f"Missing critical elements: {missing_elements}"
    
    def test_portfolio_page_canvas_element(self, client):
        """Test that allocation chart canvas element is present."""
        response = client.get('/portfolio')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Check for canvas element specifically
        canvas = soup.find('canvas', {'id': 'allocationChart'})
        assert canvas is not None, "allocationChart canvas element not found"
    
    def test_portfolio_page_includes_chartjs(self, client):
        """Test that portfolio page includes Chart.js script."""
        response = client.get('/portfolio')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Portfolio page should include Chart.js since base layout removed it globally
        # Look for Chart.js CDN or local script inclusion
        chartjs_patterns = [
            'chart.js',
            'Chart.js',
            'chartjs',
            'new Chart('
        ]
        
        found_chartjs = False
        for pattern in chartjs_patterns:
            if pattern.lower() in html_content.lower():
                found_chartjs = True
                break
        
        assert found_chartjs, "Chart.js not found in portfolio page - required for allocation chart"
    
    def test_base_layout_contains_showtoast(self, client):
        """Test that base layout contains showToast function definition."""
        # Test any page that uses base_layout.html
        response = client.get('/portfolio')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check for showToast function definition
        showtoast_patterns = [
            'function showToast',
            'showToast =',
            'window.showToast'
        ]
        
        found_showtoast = False
        for pattern in showtoast_patterns:
            if pattern in html_content:
                found_showtoast = True
                break
        
        assert found_showtoast, "showToast function not found in base layout"
    
    def test_base_layout_contains_trading_debug(self, client):
        """Test that base layout contains TradingDebug system."""
        response = client.get('/portfolio')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check for TradingDebug system
        debug_patterns = [
            'TradingDebug',
            'tradingDebug',
            'window.TradingDebug'
        ]
        
        found_debug = False
        for pattern in debug_patterns:
            if pattern in html_content:
                found_debug = True
                break
        
        assert found_debug, "TradingDebug system not found in base layout"
    
    def test_page_script_defines_refresh_function(self, client):
        """Test that portfolio page script defines window.refreshPageData."""
        response = client.get('/portfolio')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check for refreshPageData function definition
        refresh_patterns = [
            'window.refreshPageData',
            'refreshPageData =',
            'function refreshPageData'
        ]
        
        found_refresh = False
        for pattern in refresh_patterns:
            if pattern in html_content:
                found_refresh = True
                break
        
        assert found_refresh, "window.refreshPageData function not found in portfolio page script"
    
    def test_portfolio_page_has_valid_structure(self, client):
        """Test that portfolio page has valid HTML structure."""
        response = client.get('/portfolio')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Basic HTML structure checks
        assert soup.find('html') is not None, "No <html> element found"
        assert soup.find('head') is not None, "No <head> element found"
        assert soup.find('body') is not None, "No <body> element found"
        assert soup.find('title') is not None, "No <title> element found"
        
        # Check that title is appropriate
        title = soup.find('title')
        title_text = title.get_text() if title else ""
        assert 'portfolio' in title_text.lower() or 'analytics' in title_text.lower(), f"Title '{title_text}' doesn't indicate portfolio page"
    
    def test_portfolio_page_responsive_elements(self, client):
        """Test that portfolio page contains responsive design elements."""
        response = client.get('/portfolio')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Check for Bootstrap responsive classes (common in the template)
        responsive_classes = soup.find_all(class_=lambda x: x and any(cls in x for cls in ['col-', 'row', 'container']))
        
        assert len(responsive_classes) > 0, "No responsive design classes found - page may not be mobile-friendly"
    
    def test_portfolio_page_data_loading_elements(self, client):
        """Test that portfolio page has data loading/skeleton elements."""
        response = client.get('/portfolio')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check for loading indicators or skeleton elements
        loading_patterns = [
            'loading',
            'skeleton',
            'spinner',
            'Loading...'
        ]
        
        found_loading = False
        for pattern in loading_patterns:
            if pattern in html_content:
                found_loading = True
                break
        
        assert found_loading, "No loading indicators found - page may not show proper loading states"


class TestOtherPagesSmoke:
    """Basic smoke tests for other pages to ensure they work."""
    
    def test_dashboard_page_loads(self, client):
        """Test that dashboard page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_trades_page_loads(self, client):
        """Test that trades page loads successfully."""
        response = client.get('/trades')
        assert response.status_code == 200
    
    def test_signals_page_loads(self, client):
        """Test that signals page loads successfully."""
        response = client.get('/signals')
        assert response.status_code == 200
    
    def test_health_endpoint(self, client):
        """Test health endpoint works."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert data['status'] == 'healthy'