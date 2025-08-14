// Trading System Web Interface JavaScript - Clean Version

class TradingApp {
    constructor() {
        this.updateInterval = null;
        this.portfolioChart = null;
        this.returnsChart = null;
        this.tradesChart = null;
        this.isLiveConfirmationPending = false;
        this.countdownInterval = null;
        this.countdown = 5;
        this.chartData = {
            portfolio: [],
            returns: [],
            trades: []
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.startAutoUpdate();
        this.loadConfig();
    }
    
    setupEventListeners() {
        // Auto-refresh every 60 seconds (once per minute to reduce CoinGecko API usage)
        this.updateInterval = setInterval(() => {
            this.updateDashboard();
        }, 60000);
        
        // Start countdown timer
        this.startCountdown();
        
        // Handle page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoUpdate();
            } else {
                this.startAutoUpdate();
                this.updateDashboard();
            }
        });
        
        // Add page auto-refresh every 5 minutes
        setInterval(() => {
            console.log('Auto-refreshing page...');
            window.location.reload();
        }, 5 * 60 * 1000); // 5 minutes
        
        // Handle window unload
        window.addEventListener('beforeunload', () => {
            this.stopAutoUpdate();
        });
    }
    
    startAutoUpdate() {
        if (!this.updateInterval) {
            this.updateInterval = setInterval(() => {
                this.updateDashboard();
            }, 60000);
        }
    }
    
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    async updateDashboard() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) return;
            
            const data = await response.json();
            
            // Update uptime display
            if (data.uptime !== undefined) {
                this.updateUptimeDisplay(data.uptime);
            }
            
            // Update portfolio values from status endpoint
            if (data.portfolio) {
                document.getElementById('portfolio-value').textContent = this.formatCurrency(data.portfolio.total_value || 0);
                document.getElementById('portfolio-pnl').textContent = this.formatCurrency(data.portfolio.daily_pnl || 0);
                
                const pnlElement = document.getElementById('portfolio-pnl');
                pnlElement.className = (data.portfolio.daily_pnl || 0) >= 0 ? 'text-success' : 'text-danger';
            }
            
            // Update trading status
            if (data.trading_status) {
                this.updateTradingStatus(data.trading_status);
            }
            
        } catch (error) {
            console.error('Status update failed:', error);
        }
        
        // Update crypto portfolio data
        this.updateCryptoPortfolio();
        
        // Update price source status
        this.updatePriceSourceStatus();
    }
    
    async updatePriceSourceStatus() {
        try {
            const response = await fetch('/api/price-source-status');
            if (!response.ok) return;
            
            const data = await response.json();
            
            const serverConnectionText = document.getElementById('server-connection-text');
            if (serverConnectionText) {
                if (data.connected) {
                    serverConnectionText.textContent = 'Connected';
                    serverConnectionText.className = 'text-success ms-1';
                } else {
                    serverConnectionText.textContent = `Disconnected (${data.last_update || 'unknown'})`;
                    serverConnectionText.className = 'text-danger ms-1';
                }
            }
            
        } catch (error) {
            console.error('Price source status update failed:', error);
        }
    }
    
    updateUptimeDisplay(serverUptimeSeconds) {
        const uptimeElement = document.getElementById('system-uptime');
        
        if (uptimeElement && serverUptimeSeconds !== undefined) {
            const uptimeText = this.formatUptime(serverUptimeSeconds);
            uptimeElement.textContent = uptimeText;
        }
    }
    
    formatUptime(totalSeconds) {
        const days = Math.floor(totalSeconds / 86400);
        const hours = Math.floor((totalSeconds % 86400) / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        
        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m ${seconds}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds}s`;
        } else {
            return `${seconds}s`;
        }
    }
    
    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                const config = await response.json();
                console.log('Config loaded:', config);
            }
        } catch (error) {
            console.error('Failed to load config:', error);
        }
    }
    
    startCountdown() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        
        this.countdown = 5;
        this.countdownInterval = setInterval(() => {
            const countdownElement = document.getElementById('trading-countdown');
            if (countdownElement) {
                if (this.countdown > 0) {
                    countdownElement.textContent = `Starting in ${this.countdown}s`;
                    countdownElement.className = 'badge bg-warning ms-3';
                    this.countdown--;
                } else {
                    countdownElement.textContent = 'System Ready';
                    countdownElement.className = 'badge bg-success ms-3';
                    clearInterval(this.countdownInterval);
                }
            }
        }, 1000);
    }
    
    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }
    
    updateTradingStatus(tradingStatus) {
        // Update trading status display
        const statusElement = document.getElementById('trading-status');
        if (statusElement && tradingStatus) {
            statusElement.textContent = `${tradingStatus.mode} - ${tradingStatus.strategy}`;
        }
    }
    
    async updateCryptoPortfolio() {
        try {
            const response = await fetch('/api/crypto-portfolio');
            if (!response.ok) return;
            
            const data = await response.json();
            
            // Update summary statistics
            if (data.summary) {
                document.getElementById('crypto-total-count').textContent = data.summary.total_cryptos;
                document.getElementById('crypto-current-value').textContent = this.formatCurrency(data.summary.total_current_value);
                document.getElementById('crypto-total-pnl').textContent = this.formatCurrency(data.summary.total_pnl);
                
                const pnlElement = document.getElementById('crypto-total-pnl');
                const pnlClass = data.summary.total_pnl >= 0 ? 'text-success' : 'text-danger';
                pnlElement.className = `mb-0 ${pnlClass}`;
            }
            
            // Update crypto symbols display
            if (data.cryptocurrencies) {
                this.updateCryptoSymbols(data.cryptocurrencies);
            }
            
        } catch (error) {
            console.error('Error updating crypto portfolio:', error);
        }
    }
    
    updateCryptoSymbols(cryptos) {
        const symbolsContainer = document.getElementById('crypto-symbols');
        if (!symbolsContainer) return;
        
        // Clear existing content
        symbolsContainer.innerHTML = '';
        
        if (!cryptos || cryptos.length === 0) {
            const badge = document.createElement('span');
            badge.className = 'badge bg-secondary';
            badge.textContent = 'No cryptocurrencies loaded';
            symbolsContainer.appendChild(badge);
            return;
        }
        
        // Create badges for each crypto with price and PnL info
        cryptos.forEach(crypto => {
            const badge = document.createElement('span');
            const pnlClass = crypto.pnl >= 0 ? 'bg-success' : 'bg-danger';
            badge.className = `badge ${pnlClass} me-1 mb-1`;
            
            const price = crypto.current_price < 1 ? 
                crypto.current_price.toFixed(6) : 
                crypto.current_price.toFixed(2);
            const pnl = crypto.pnl >= 0 ? `+${crypto.pnl.toFixed(2)}` : crypto.pnl.toFixed(2);
            
            badge.textContent = `${crypto.symbol} $${price} (${pnl})`;
            badge.setAttribute('title', `${crypto.name}: $${price}, P&L: ${pnl}`);
            symbolsContainer.appendChild(badge);
        });
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed`;
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        
        // Create close button safely
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close';
        closeButton.onclick = function() { this.parentElement.remove(); };
        
        // Add message as text content (prevents XSS)
        const messageSpan = document.createElement('span');
        messageSpan.textContent = message;
        
        // Append elements safely
        toast.appendChild(closeButton);
        toast.appendChild(messageSpan);
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    initializeCharts() {
        // Basic chart initialization - placeholder for actual chart setup
        console.log('Charts initialized');
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.tradingApp = new TradingApp();
});

// Trading functions
async function resetEntireProgram() {
    if (confirm('Are you sure you want to reset the entire trading system? This will clear all data and cannot be undone.')) {
        try {
            const response = await fetch('/api/reset-entire-program', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                window.tradingApp.showToast('System reset successfully!', 'success');
                setTimeout(() => location.reload(), 2000);
            } else {
                window.tradingApp.showToast('Failed to reset system: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            window.tradingApp.showToast('Error resetting system: ' + error.message, 'error');
        }
    }
}