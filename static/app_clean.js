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
            if (data.uptime_seconds !== undefined) {
                this.updateUptimeDisplay(data.uptime_seconds);
            } else if (data.uptime_human !== undefined) {
                // If we have human-readable uptime, display it directly
                const uptimeElement = document.getElementById('system-uptime');
                if (uptimeElement) {
                    uptimeElement.textContent = data.uptime_human;
                }
            }
            
            // Update portfolio values from status endpoint
            if (data.portfolio) {
                document.getElementById('portfolio-value').textContent = this.formatCurrency(data.portfolio.total_value || 0);
                document.getElementById('portfolio-pnl').textContent = this.formatCurrency(data.portfolio.daily_pnl || 0);
                
                const pnlElement = document.getElementById('portfolio-pnl');
                pnlElement.className = (data.portfolio.daily_pnl || 0) >= 0 ? 'text-success' : 'text-danger';
            }
            
            // Update trading status and bot state
            if (data.trading_status) {
                this.updateTradingStatus(data.trading_status);
            }
            
            // Update bot status from main status response
            if (data.bot !== undefined) {
                this.updateBotStatus(data.bot);
            }
            
            // Update overall active status
            if (data.active !== undefined) {
                this.updateActiveStatus(data.active);
            }
            
        } catch (error) {
            console.error('Status update failed:', error);
        }
        
        // Update crypto portfolio data
        this.updateCryptoPortfolio();
        
        // Update price source status
        this.updatePriceSourceStatus();
        
        // Poll bot status separately to ensure button state is current
        this.pollBotStatus();
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
    
    updateBotStatus(botData) {
        const botButton = document.getElementById('bot-status-top');
        if (botButton && botData) {
            const isRunning = botData.running === true;
            botButton.textContent = isRunning ? 'STOP BOT' : 'START BOT';
        }
    }
    
    updateActiveStatus(isActive) {
        const statusElement = document.getElementById('trading-status');
        if (statusElement) {
            statusElement.innerHTML = `<span class="icon icon-circle me-1" aria-hidden="true"></span>${isActive ? 'Active' : 'Inactive'}`;
            statusElement.className = `badge ${isActive ? 'bg-success' : 'bg-secondary'} ms-2`;
        }
    }
    
    updateTradingStatus(tradingStatus) {
        if (tradingStatus && tradingStatus.status) {
            this.updateActiveStatus(tradingStatus.status === 'Active');
        }
    }
    
    async pollBotStatus() {
        try {
            const response = await fetch('/api/bot/status');
            if (response.ok) {
                const botData = await response.json();
                this.updateBotStatus(botData);
                this.updateActiveStatus(botData.active === true);
            }
        } catch (error) {
            console.debug('Bot status polling failed:', error);
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
    
    // Rest of the existing methods remain the same...
    // (Charts, crypto portfolio, trading functions, etc.)
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.tradingApp = new TradingApp();
});

// Trading functions
async function startPaperTrading() {
    try {
        const response = await fetch('/api/start-paper-trading', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast('Paper trading started successfully!', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast('Failed to start paper trading: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showToast('Error starting paper trading: ' + error.message, 'error');
    }
}

async function stopTrading() {
    try {
        const response = await fetch('/api/stop-trading', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast('Trading stopped successfully!', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast('Failed to stop trading: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showToast('Error stopping trading: ' + error.message, 'error');
    }
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed`;
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}