// Dashboard management module
import { AppUtils } from './utils.js';

export class DashboardManager {
    constructor() {
        this.updateInterval = null;
        this.lastDashboardUpdate = 0;
        this.dashboardUpdateDebounce = 2000; // 2 seconds
        this.pendingDashboardUpdate = null;
        this.portfolioAbortController = null;
        this.selectedCurrency = 'USD';
        
        // API cache configuration
        this.apiCache = {
            status: { data: null, timestamp: 0, ttl: 15000 },
            portfolio: { data: null, timestamp: 0, ttl: 10000 },
            config: { data: null, timestamp: 0, ttl: 60000 },
            analytics: { data: null, timestamp: 0, ttl: 30000 },
            portfolioHistory: { data: null, timestamp: 0, ttl: 120000 },
            assetAllocation: { data: null, timestamp: 0, ttl: 15000 },
            bestPerformer: { data: null, timestamp: 0, ttl: 10000 },
            worstPerformer: { data: null, timestamp: 0, ttl: 10000 },
            equityCurve: { data: null, timestamp: 0, ttl: 30000 },
            drawdownAnalysis: { data: null, timestamp: 0, ttl: 30000 },
            currentHoldings: { data: null, timestamp: 0, ttl: 15000 },
            recentTrades: { data: null, timestamp: 0, ttl: 20000 },
            performanceAnalytics: { data: null, timestamp: 0, ttl: 30000 }
        };
        
        this.bypassCache = true; // Debug: force network fetches
        this.isUpdatingTables = false;
        this.lastTableUpdate = 0;
    }

    async cachedFetch(key, url, options = {}) {
        const now = Date.now();
        const cached = this.apiCache[key];
        
        if (!this.bypassCache && cached.data && (now - cached.timestamp) < cached.ttl) {
            return cached.data;
        }
        
        const data = await AppUtils.fetchJSON(url, options);
        if (data) {
            this.apiCache[key] = { data, timestamp: now, ttl: cached.ttl };
        }
        
        return data;
    }

    async updatePortfolioOverview() {
        try {
            console.debug('Loading progress: 20% - Fetching cryptocurrency data...');
            const data = await this.cachedFetch('portfolio', `/api/crypto-portfolio?_bypass_cache=${Date.now()}&debug=1&currency=${this.selectedCurrency}`);
            
            if (!data) {
                console.debug('Portfolio data not available');
                return;
            }

            console.debug('Loading progress: 60% - Processing market data...');
            this.updatePortfolioCards(data);
            
            console.debug('Loading progress: 80% - Updating displays...');
            this.updateConnectionStatus();
            
            console.debug('Loading progress: 100% - Complete!');
            
        } catch (error) {
            console.error('Portfolio overview update failed:', error);
            AppUtils.showToast('Failed to update portfolio data', 'error');
        }
    }

    updatePortfolioCards(data) {
        if (!data) return;
        
        const overview = {
            totalValue: this.extractTotalValue(data),
            totalPnl: this.extractTotalPnL(data),
            totalPnlPercent: this.extractTotalPnLPercent(data),
            dailyPnl: 0, // Would need daily data
            dailyPnlPercent: 0,
            activePositions: this.extractActivePositions(data),
            bestPerformer: this.extractBestPerformer(data)
        };

        console.debug('Updating OKX Portfolio Overview cards with data:', overview);
        this.updateKPICards(overview);
    }

    updateKPICards(overview) {
        // Update Total Value
        const totalValueEl = document.getElementById('total-value');
        if (totalValueEl) {
            totalValueEl.textContent = AppUtils.formatCurrency(overview.totalValue);
        }

        // Update Total P&L
        const totalPnlEl = document.getElementById('total-pnl');
        if (totalPnlEl) {
            const pnlClass = overview.totalPnl >= 0 ? 'text-success' : 'text-danger';
            const pnlSign = overview.totalPnl >= 0 ? '+' : '';
            totalPnlEl.className = `h5 mb-0 ${pnlClass}`;
            totalPnlEl.textContent = `${pnlSign}${AppUtils.formatCurrency(overview.totalPnl)} (${overview.totalPnlPercent.toFixed(2)}%)`;
        }

        // Update Active Positions
        const activePositionsEl = document.getElementById('active-positions');
        if (activePositionsEl) {
            activePositionsEl.textContent = overview.activePositions.toString();
        }

        // Update Best Performer
        this.updatePerformerCard('best', overview.bestPerformer);
    }

    updatePerformerCard(type, performer) {
        const titleEl = document.querySelector(`#summary-${type}-performer .card-title`);
        const valueEl = document.querySelector(`#summary-${type}-performer span`);
        
        if (!titleEl) {
            console.debug(`${type.charAt(0).toUpperCase() + type.slice(1)} performer card title element not found - skipping update`);
            return;
        }

        if (performer && typeof performer === 'object') {
            titleEl.textContent = performer.symbol || 'N/A';
            if (valueEl) {
                const pnlClass = (performer.pnl || 0) >= 0 ? 'text-success' : 'text-danger';
                const pnlSign = (performer.pnl || 0) >= 0 ? '+' : '';
                valueEl.className = pnlClass;
                valueEl.textContent = `${pnlSign}${((performer.pnl_percent || 0) * 100).toFixed(2)}%`;
            }
        } else {
            titleEl.textContent = 'N/A';
            if (valueEl) {
                valueEl.className = 'text-muted';
                valueEl.textContent = '0.00%';
            }
        }
    }

    async updateConnectionStatus() {
        try {
            await Promise.all([
                this.updateServerStatus(),
                this.updateOKXStatus()
            ]);
        } catch (error) {
            console.debug('Connection status update failed:', error);
        }
    }

    async updateServerStatus() {
        try {
            const response = await fetch('/api/price-source-status', { cache: 'no-cache' });
            if (!response.ok) return;
            const data = await response.json();

            const serverConnectionText = document.getElementById('server-connection-text');
            const serverStatusContainer = document.getElementById('server-connection-status');
            const statusIcon = serverStatusContainer ? serverStatusContainer.querySelector('i.fas') : null;
            
            const isConnected = data.status === 'connected' || data.connected === true;
            
            if (serverConnectionText) {
                serverConnectionText.textContent = isConnected ? 'Connected' : 'Disconnected';
                serverConnectionText.className = isConnected ? 'text-success ms-1' : 'text-danger ms-1';
            }
            
            if (statusIcon) {
                statusIcon.className = isConnected ? 'fa-solid fa-wifi text-success me-1' : 'fa-solid fa-wifi text-danger me-1';
            }
        } catch (error) {
            console.debug('Server status update failed:', error);
        }
    }

    async updateOKXStatus() {
        try {
            const response = await fetch('/api/okx-status', { cache: 'no-cache' });
            if (!response.ok) return;

            const data = await response.json();
            const okxConnectionText = document.getElementById('okx-connection-text');
            const okxStatusContainer = document.getElementById('okx-connection-status');
            const statusIcon = okxStatusContainer ? okxStatusContainer.querySelector('.fas.fa-server') : null;
            
            if (okxConnectionText && data.status) {
                const isConnected = data.status.connected === true;
                okxConnectionText.textContent = isConnected ? 'Connected' : 'Disconnected';
                okxConnectionText.className = isConnected ? 'text-success ms-1' : 'text-danger ms-1';
                
                if (statusIcon) {
                    statusIcon.className = isConnected ? 'fa-solid fa-server text-success me-1' : 'fa-solid fa-server text-danger me-1';
                }
            }
        } catch (error) {
            console.debug('OKX status update failed:', error);
        }
    }

    // Data extraction helpers
    extractTotalValue(data) {
        return AppUtils.safeNum(data.total_current_value || data.totalValue || 0);
    }

    extractTotalPnL(data) {
        return AppUtils.safeNum(data.total_pnl || data.totalPnl || 0);
    }

    extractTotalPnLPercent(data) {
        return AppUtils.safeNum(data.total_pnl_percent || data.totalPnlPercent || 0);
    }

    extractActivePositions(data) {
        if (data.holdings && Array.isArray(data.holdings)) {
            return data.holdings.filter(h => AppUtils.safeNum(h.quantity) > 0).length;
        }
        return 0;
    }

    extractBestPerformer(data) {
        if (data.holdings && Array.isArray(data.holdings)) {
            const positive = data.holdings.filter(h => AppUtils.safeNum(h.pnl_percent) > 0);
            if (positive.length > 0) {
                return positive.reduce((best, current) => 
                    AppUtils.safeNum(current.pnl_percent) > AppUtils.safeNum(best.pnl_percent) ? current : best
                );
            }
        }
        return null;
    }

    startAutoUpdate() {
        // Update every 30 seconds
        this.updateInterval = setInterval(() => {
            this.updatePortfolioOverview();
        }, 30000);
        
        // Initial update
        this.updatePortfolioOverview();
    }

    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
}