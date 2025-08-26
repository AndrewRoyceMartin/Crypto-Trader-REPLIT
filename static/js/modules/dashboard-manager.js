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
            bestPerformer: this.extractBestPerformer(data),
            worstPerformer: this.extractWorstPerformer(data)
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

        // Update Best and Worst Performers
        this.updatePerformerCard('best', overview.bestPerformer);
        this.updatePerformerCard('worst', overview.worstPerformer);
    }

    updatePerformerCard(type, performer) {
        // Use the actual HTML element IDs from the patched template
        const titleEl = document.getElementById(`${type}-performer-card-title`);
        const symbolEl = document.getElementById(`${type}-performer-symbol`);
        const nameEl = document.getElementById(`${type}-performer-name`);
        const priceEl = document.getElementById(`${type}-performer-price`);
        const pnlEl = document.getElementById(`${type}-performer-pnl`);
        const allocationEl = document.getElementById(`${type}-performer-allocation`);
        const valueEl = document.getElementById(`${type}-performer-value`);
        const volumeEl = document.getElementById(`${type}-performer-volume`);
        const h24El = document.getElementById(`${type}-performer-24h`);
        const d7El = document.getElementById(`${type}-performer-7d`);
        
        if (!titleEl) {
            // Skip update if element not found
            return;
        }

        if (performer && typeof performer === 'object') {
            // Update title with performer type
            titleEl.textContent = `${type === 'best' ? 'Best' : 'Worst'} Performer: ${performer.symbol || 'N/A'}`;
            
            // Update all data fields
            if (symbolEl) symbolEl.textContent = performer.symbol || '—';
            if (nameEl) nameEl.textContent = performer.name || '—';
            if (priceEl) priceEl.textContent = AppUtils.formatCurrency(performer.price || 0);
            if (allocationEl) allocationEl.textContent = `${(performer.allocation || 0).toFixed(2)}%`;
            if (valueEl) valueEl.textContent = AppUtils.formatCurrency(performer.value || 0);
            if (volumeEl) volumeEl.textContent = AppUtils.formatCurrency(performer.volume || 0);
            if (h24El) h24El.textContent = `${(performer.change24h || 0).toFixed(2)}%`;
            if (d7El) d7El.textContent = `${(performer.change7d || 0).toFixed(2)}%`;
            
            // Update P&L with proper styling
            if (pnlEl) {
                const pnlClass = (performer.pnl || 0) >= 0 ? 'text-success' : 'text-danger';
                const pnlSign = (performer.pnl || 0) >= 0 ? '+' : '';
                pnlEl.className = pnlClass;
                pnlEl.textContent = `${pnlSign}${AppUtils.formatCurrency(performer.pnl || 0)} (${((performer.pnl_percent || 0) * 100).toFixed(2)}%)`;
            }
        } else {
            // Set defaults when no performer data
            titleEl.textContent = `${type === 'best' ? 'Best' : 'Worst'} Performer`;
            if (symbolEl) symbolEl.textContent = '—';
            if (nameEl) nameEl.textContent = '—';
            if (priceEl) priceEl.textContent = '—';
            if (allocationEl) allocationEl.textContent = '—';
            if (valueEl) valueEl.textContent = '—';
            if (volumeEl) volumeEl.textContent = '—';
            if (h24El) h24El.textContent = '—';
            if (d7El) d7El.textContent = '—';
            if (pnlEl) {
                pnlEl.className = 'text-muted';
                pnlEl.textContent = '—';
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

    extractWorstPerformer(data) {
        if (data.holdings && Array.isArray(data.holdings)) {
            const negative = data.holdings.filter(h => AppUtils.safeNum(h.pnl_percent) < 0);
            if (negative.length > 0) {
                return negative.reduce((worst, current) => 
                    AppUtils.safeNum(current.pnl_percent) < AppUtils.safeNum(worst.pnl_percent) ? current : worst
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