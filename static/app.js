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
        
        // Load data immediately on startup
        this.updateDashboard();
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
            // Show loading progress
            this.updateLoadingProgress(20, 'Fetching cryptocurrency data...');
            
            const response = await fetch('/api/crypto-portfolio');
            if (!response.ok) return;
            
            this.updateLoadingProgress(60, 'Processing market data...');
            const data = await response.json();
            
            // CRITICAL: Check for failed price retrieval and display warnings
            if (data.price_validation && data.price_validation.failed_symbols && data.price_validation.failed_symbols.length > 0) {
                this.displayPriceDataWarning(data.price_validation.failed_symbols);
            }
            
            // Update summary statistics
            if (data.summary) {
                document.getElementById('crypto-total-count').textContent = data.summary.total_cryptos;
                document.getElementById('crypto-current-value').textContent = this.formatCurrency(data.summary.total_current_value);
                document.getElementById('crypto-total-pnl').textContent = this.formatCurrency(data.summary.total_pnl);
                
                const pnlElement = document.getElementById('crypto-total-pnl');
                const pnlClass = data.summary.total_pnl >= 0 ? 'text-success' : 'text-danger';
                pnlElement.className = `mb-0 ${pnlClass}`;
            }
            
            // Update crypto symbols display and table
            if (data.cryptocurrencies) {
                this.updateLoadingProgress(80, 'Updating displays...');
                this.updateCryptoSymbols(data.cryptocurrencies);
                this.updateCryptoTable(data.cryptocurrencies);
                this.updatePortfolioSummary(data.summary, data.cryptocurrencies);
                this.updateLoadingProgress(100, 'Complete!');
                
                // Hide progress bar after completion
                setTimeout(() => {
                    this.hideLoadingProgress();
                }, 1000);
            }
            
        } catch (error) {
            console.error('Error updating crypto portfolio:', error);
            this.updateLoadingProgress(0, 'Error loading data');
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
    
    updateCryptoTable(cryptos) {
        const tableBody = document.getElementById('crypto-table');
        if (!tableBody) return;
        
        // Clear existing content
        tableBody.innerHTML = '';
        
        if (!cryptos || cryptos.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="13" class="text-center text-muted">No cryptocurrency data available</td>';
            tableBody.appendChild(row);
            return;
        }
        
        // Populate table with cryptocurrency data
        cryptos.forEach(crypto => {
            const row = document.createElement('tr');
            
            // Format values
            const price = crypto.current_price < 1 ? 
                crypto.current_price.toFixed(6) : 
                crypto.current_price.toFixed(2);
            const quantity = crypto.quantity.toFixed(4);
            const currentValue = this.formatCurrency(crypto.current_value);
            const pnl = this.formatCurrency(crypto.pnl);
            const pnlPercent = crypto.pnl_percent.toFixed(2);
            const targetBuy = crypto.target_buy_price ? this.formatCurrency(crypto.target_buy_price) : '-';
            const targetSell = crypto.target_sell_price ? this.formatCurrency(crypto.target_sell_price) : '-';
            
            // Determine PnL colors
            const pnlClass = crypto.pnl >= 0 ? 'text-success' : 'text-danger';
            const pnlIcon = crypto.pnl >= 0 ? '↗' : '↘';
            
            // Signal based on current price vs target prices
            let signal = 'HOLD';
            let signalClass = 'badge bg-secondary';
            if (crypto.target_buy_price && crypto.current_price <= crypto.target_buy_price) {
                signal = 'BUY';
                signalClass = 'badge bg-success';
            } else if (crypto.target_sell_price && crypto.current_price >= crypto.target_sell_price) {
                signal = 'SELL';
                signalClass = 'badge bg-danger';
            }
            
            row.innerHTML = `
                <td><strong>${crypto.symbol}</strong></td>
                <td>${crypto.name}</td>
                <td>#${crypto.rank}</td>
                <td>$${price}</td>
                <td>${quantity}</td>
                <td>${currentValue}</td>
                <td>${targetSell}</td>
                <td class="${pnlClass}">${pnl}</td>
                <td class="${pnlClass}">${pnlIcon} ${pnlPercent}%</td>
                <td class="text-muted small">Just now</td>
                <td><span class="${signalClass}">${signal}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-success me-1" onclick="buyCrypto('${crypto.symbol}')" title="Buy ${crypto.symbol}">
                        <i class="fas fa-plus"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="sellCrypto('${crypto.symbol}')" title="Sell ${crypto.symbol}">
                        <i class="fas fa-minus"></i>
                    </button>
                </td>
                <td class="text-muted">
                    ${crypto.target_buy_price ? 
                        (crypto.current_price <= crypto.target_buy_price ? '🎯 At buy target' : `${((crypto.current_price - crypto.target_buy_price) / crypto.target_buy_price * 100).toFixed(1)}% above`) :
                        '-'
                    }
                </td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    updateLoadingProgress(percent, message = '') {
        const progressBar = document.getElementById('crypto-loading-progress');
        const progressText = document.getElementById('crypto-loading-text');
        
        if (progressBar) {
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', percent);
            
            // Add visual feedback
            if (percent === 100) {
                progressBar.className = 'progress-bar bg-success';
                setTimeout(() => {
                    if (progressBar) {
                        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
                    }
                }, 500);
            }
        }
        
        if (progressText) {
            progressText.textContent = message || `${percent}%`;
        }
        
        console.log(`Loading progress: ${percent}% - ${message}`);
    }
    
    hideLoadingProgress() {
        const loadingRow = document.querySelector('#crypto-table tr');
        if (loadingRow && loadingRow.querySelector('.progress')) {
            // Progress is hidden when table gets populated with actual data
        }
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
    
    displayPriceDataWarning(failedSymbols) {
        // Create or update warning banner for failed price data
        let warningBanner = document.getElementById('price-data-warning');
        if (!warningBanner) {
            warningBanner = document.createElement('div');
            warningBanner.id = 'price-data-warning';
            warningBanner.className = 'alert alert-danger alert-dismissible fade show mb-3';
            warningBanner.role = 'alert';
            
            // Insert at top of main container
            const container = document.querySelector('.container-fluid');
            if (container) {
                container.insertBefore(warningBanner, container.firstChild);
            }
        }
        
        warningBanner.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>CRITICAL: Price Data Unavailable</strong>
            <br>Live price data could not be retrieved from CoinGecko API for: ${failedSymbols.join(', ')}
            <br>This system NEVER uses simulated prices. Please check your internet connection or try refreshing.
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
    }

    updatePortfolioSummary(summary, cryptos) {
        if (!summary) return;
        
        // Update main summary card
        document.getElementById('summary-total-value').textContent = this.formatCurrency(summary.total_current_value);
        
        const changeElement = document.getElementById('summary-total-change');
        const changeValue = summary.total_pnl || 0;
        const changePercent = summary.total_pnl_percent || 0;
        
        changeElement.textContent = `${changeValue >= 0 ? '+' : ''}${this.formatCurrency(changeValue)} (${changePercent.toFixed(2)}%)`;
        changeElement.className = `badge ${changeValue >= 0 ? 'bg-success' : 'bg-danger'}`;
        
        // Update summary stats
        document.getElementById('summary-total-assets').textContent = summary.total_cryptos || 0;
        document.getElementById('summary-portfolio-value').textContent = this.formatCurrency(summary.total_current_value);
        
        const dailyChangeElement = document.getElementById('summary-24h-change');
        dailyChangeElement.textContent = `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%`;
        dailyChangeElement.className = `mb-0 fw-bold ${changePercent >= 0 ? 'text-success' : 'text-danger'}`;
        
        // Find best performer
        if (cryptos && cryptos.length > 0) {
            const bestPerformer = cryptos.reduce((best, crypto) => {
                const currentPnlPercent = crypto.pnl_percent || 0;
                const bestPnlPercent = best.pnl_percent || 0;
                return currentPnlPercent > bestPnlPercent ? crypto : best;
            });
            
            document.getElementById('summary-best-performer').textContent = bestPerformer.symbol;
            document.getElementById('summary-best-performance').textContent = `+${(bestPerformer.pnl_percent || 0).toFixed(2)}%`;
        }
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