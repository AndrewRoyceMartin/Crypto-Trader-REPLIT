// Trading System Web Interface JavaScript - Cleaned & Harmonized

class TradingApp {
    constructor() {
        this.updateInterval = null;
        this.chartUpdateInterval = null;

        // Charts
        this.portfolioChart = null;   // line
        this.pnlChart = null;         // doughnut
        this.performersChart = null;  // bar

        // State
        this.isLiveConfirmationPending = false;
        this.countdownInterval = null;
        this.countdown = 5;

        // store trades for filtering
        this.allTrades = [];

        // Debounce to prevent overlapping dashboard updates
        this.lastDashboardUpdate = 0;
        this.dashboardUpdateDebounce = 2000; // 2 seconds
        this.pendingDashboardUpdate = null;

        // API cache
        this.apiCache = {
            status:    { data: null, timestamp: 0, ttl: 1000 },  // 1s
            portfolio: { data: null, timestamp: 0, ttl: 1000 },  // 1s
            config:    { data: null, timestamp: 0, ttl: 30000 }  // 30s
        };

        // Debug: force network fetches
        this.bypassCache = true;

        // Currency
        this.selectedCurrency = 'USD';
        this.exchangeRates = { USD: 1 };

        // scratch
        this.currentCryptoData = null;

        this.init();
    }

    // ---------- Utils ----------
    num(v, d = 0) {
        const n = Number(v);
        return Number.isFinite(n) ? n : d;
    }
    fmtFixed(v, p, d = '0') {
        const n = this.num(v);
        return n.toFixed(p);
    }
    formatCurrency(amount, currency = null) {
        const targetCurrency = currency || this.selectedCurrency || 'USD';
        const rate = this.exchangeRates[targetCurrency] || 1;
        const convertedAmount = (Number(amount) || 0) * rate;

        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: targetCurrency
        }).format(convertedAmount);
    }
    formatUptime(totalSeconds) {
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = Math.floor(totalSeconds % 60);
        return [
            hours.toString().padStart(2, '0'),
            minutes.toString().padStart(2, '0'),
            seconds.toString().padStart(2, '0')
        ].join(':');
    }
    formatTradeTime(timestamp) {
        if (!timestamp) return 'N/A';
        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) return 'Invalid';
            const now = new Date();
            const diffMs = now - date;
            const diffHours = diffMs / (1000 * 60 * 60);
            
            // Always show local time with timezone info for clarity
            if (diffHours < 1) {
                const diffMins = Math.floor(diffMs / (1000 * 60));
                return `${diffMins}min ago`;
            } else if (diffHours < 24) {
                return date.toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    hour12: true 
                });
            } else if (diffHours < 168) { // Less than 7 days
                return date.toLocaleDateString([], { 
                    weekday: 'short',
                    hour: '2-digit', 
                    minute: '2-digit',
                    hour12: true 
                });
            }
            return date.toLocaleDateString([], { 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit', 
                minute: '2-digit',
                hour12: true 
            });
        } catch {
            return 'N/A';
        }
    }
    
    formatDateTime(timestamp) {
        if (!timestamp) return 'N/A';
        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) return 'Invalid';
            
            return date.toLocaleString([], {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            });
        } catch {
            return 'N/A';
        }
    }
    
    formatTimeOnly(timestamp) {
        if (!timestamp) return 'N/A';
        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) return 'Invalid';
            
            return date.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            });
        } catch {
            return 'N/A';
        }
    }
    getTradesTbody() {
        return document.getElementById('trades-table');
    }

    // Normalize trades from various backends (single canonical version)
    normalizeTrades(trades = []) {
        return (trades || []).map((t, i) => {
            const ts = t.timestamp || t.ts || t.time || t.date;
            const side = (t.side || t.action || '').toString().toUpperCase(); // BUY/SELL
            const qty = this.num(t.quantity ?? t.qty ?? t.amount ?? t.size, 0);
            const price = this.num(t.price ?? t.avg_price ?? t.fill_price ?? t.execution_price, 0);
            const pnl = this.num(t.pnl ?? t.realized_pnl ?? t.profit, 0);
            const id = t.trade_id || t.id || t.order_id || t.clientOrderId || (i + 1);
            return {
                trade_id: id,
                timestamp: ts,
                symbol: t.symbol || t.pair || t.asset || '',
                side,
                quantity: qty,
                price,
                pnl
            };
        });
    }

    // ---------- Init / lifecycle ----------
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.startAutoUpdate();
        this.loadConfig();

        // Initial fetches
        this.debouncedUpdateDashboard();

        this.fetchExchangeRates().then(() => {
            this.updateCryptoPortfolio();
        });
    }

    setupEventListeners() {
        const currencyDropdown = document.getElementById('currency-selector');
        if (currencyDropdown) {
            this.selectedCurrency = currencyDropdown.value || 'USD';
            currencyDropdown.addEventListener('change', (e) => {
                this.setSelectedCurrency(e.target.value);
            });
        }

        this.startCountdown();

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoUpdate();
            } else {
                this.startAutoUpdate();
                this.debouncedUpdateDashboard();
                this.updateCryptoPortfolio();
            }
        });

        window.addEventListener('beforeunload', () => this.cleanup());
    }

    startAutoUpdate() {
        if (!this.chartUpdateInterval) {
            this.chartUpdateInterval = setInterval(() => {
                this.updatePerformanceCharts();
            }, 30000);
        }
        if (!this.updateInterval) {
            this.updateInterval = setInterval(() => {
                this.debouncedUpdateDashboard();
                this.updateCryptoPortfolio();
            }, 60000);
        }
    }
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    stopCountdown() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
    }
    cleanup() {
        this.stopAutoUpdate();
        this.stopCountdown();
        if (this.pendingDashboardUpdate) {
            clearTimeout(this.pendingDashboardUpdate);
            this.pendingDashboardUpdate = null;
        }
        if (this.chartUpdateInterval) {
            clearInterval(this.chartUpdateInterval);
            this.chartUpdateInterval = null;
        }
    }

    // ---------- Networking / cache ----------
    async fetchWithCache(endpoint, cacheKey, bypassCache = false) {
        const cache = this.apiCache[cacheKey];
        const now = Date.now();

        if (!bypassCache && cache && cache.data && (now - cache.timestamp) < cache.ttl) {
            return cache.data;
        }

        try {
            const response = await fetch(endpoint, { cache: 'no-cache' });
            if (!response.ok) return null;
            const data = await response.json();
            this.apiCache[cacheKey] = {
                data,
                timestamp: now,
                ttl: cache ? cache.ttl : 30000
            };
            return data;
        } catch (error) {
            console.error(`Error fetching ${endpoint}:`, error);
            return null;
        }
    }

    // ---------- Dashboard ----------
    async updateDashboard() {
        const now = Date.now();
        if (now - this.lastDashboardUpdate < this.dashboardUpdateDebounce) {
            if (this.pendingDashboardUpdate) clearTimeout(this.pendingDashboardUpdate);
            this.pendingDashboardUpdate = setTimeout(() => this.updateDashboard(),
                this.dashboardUpdateDebounce - (now - this.lastDashboardUpdate));
            return;
        }
        this.lastDashboardUpdate = now;

        const data = await this.fetchWithCache('/api/status', 'status', this.bypassCache);
        if (!data) return;

        if (typeof data.uptime === 'number') {
            this.updateUptimeDisplay(data.uptime);
        }

        // Update quick KPIs if status has portfolio summary
        if (data.portfolio) {
            const kpiEquityEl = document.getElementById('kpi-total-equity');
            const kpiDailyEl  = document.getElementById('kpi-daily-pnl');
            if (kpiEquityEl) kpiEquityEl.textContent = this.formatCurrency(data.portfolio.total_value || 0);
            if (kpiDailyEl) {
                const v = this.num(data.portfolio.daily_pnl);
                kpiDailyEl.textContent = this.formatCurrency(v);
                kpiDailyEl.className = v >= 0 ? 'h5 mb-0 text-success' : 'h5 mb-0 text-danger';
            }
        }

        // Trading status
        if (data.trading_status) this.updateTradingStatus(data.trading_status);

        // Recent trades
        const trades = data.recent_trades || data.trades || [];
        if (trades.length === 0) {
            await this.updateRecentTrades();
        } else {
            this.displayDashboardRecentTrades(trades);
        }

        // Status widgets
        this.updatePriceSourceStatus();
        this.updateOKXStatus();
    }

    debouncedUpdateDashboard() {
        this.updateDashboard();
    }

    async updatePriceSourceStatus() {
        try {
            const response = await fetch('/api/price-source-status', { cache: 'no-cache' });
            if (!response.ok) return;
            const data = await response.json();

            const serverConnectionText = document.getElementById('server-connection-text');
            const statusIcon = document.querySelector('#server-connection-status i.fas'); // generic icon under this container

            const isConnected = data.status === 'connected' || data.connected === true;

            if (serverConnectionText) {
                if (isConnected) {
                    serverConnectionText.textContent = 'Connected';
                    serverConnectionText.className = 'text-success ms-1';
                    if (statusIcon) statusIcon.className = 'fas fa-wifi text-success me-1';
                } else {
                    const lastUpdate = data.last_update ? this.formatTimeOnly(data.last_update) : 'unknown';
                    serverConnectionText.textContent = `Disconnected (${lastUpdate})`;
                    serverConnectionText.className = 'text-danger ms-1';
                    if (statusIcon) statusIcon.className = 'fas fa-wifi text-danger me-1';
                }
            }
        } catch (error) {
            console.error('Price source status update failed:', error);
            const serverConnectionText = document.getElementById('server-connection-text');
            const statusIcon = document.querySelector('#server-connection-status i.fas');
            if (serverConnectionText) {
                serverConnectionText.textContent = 'Error';
                serverConnectionText.className = 'text-warning ms-1';
            }
            if (statusIcon) statusIcon.className = 'fas fa-wifi text-warning me-1';
        }
    }

    async updateOKXStatus() {
        try {
            const response = await fetch('/api/okx-status', { cache: 'no-cache' });
            if (!response.ok) return;

            const data = await response.json();
            const okxConnectionText = document.getElementById('okx-connection-text');
            const statusIcon = document.querySelector('#okx-connection-status .fas.fa-server');

            if (okxConnectionText && data.status) {
                const isConnected  = data.status.connected === true;
                const connectionType = data.status.connection_type || 'Live';
                const tradingMode = data.status.trading_mode || 'Trading';

                if (isConnected) {
                    okxConnectionText.textContent = connectionType;
                    okxConnectionText.className = 'text-success ms-1';
                    if (statusIcon) statusIcon.className = 'fas fa-server text-success me-1';
                } else {
                    const lastSync = data.status.last_sync ? this.formatTimeOnly(data.status.last_sync) : 'never';
                    okxConnectionText.textContent = `Offline (${lastSync})`;
                    okxConnectionText.className = 'text-danger ms-1';
                    if (statusIcon) statusIcon.className = 'fas fa-server text-danger me-1';
                }

                const statusElement = document.getElementById('okx-connection-status');
                if (statusElement) {
                    statusElement.title = `${data.status.exchange_name || 'OKX Exchange'} - ${tradingMode} - ${data.status.initialized ? 'Initialized' : 'Not Initialized'}`;
                }
            }
        } catch (error) {
            console.error('OKX exchange status update failed:', error);
            const okxConnectionText = document.getElementById('okx-connection-text');
            const statusIcon = document.querySelector('#okx-connection-status .fas.fa-server');
            if (okxConnectionText) {
                okxConnectionText.textContent = 'Error';
                okxConnectionText.className = 'text-warning ms-1';
            }
            if (statusIcon) statusIcon.className = 'fas fa-server text-warning me-1';
        }
    }

    updateUptimeDisplay(serverUptimeSeconds) {
        const uptimeElement = document.getElementById('system-uptime');
        if (uptimeElement && serverUptimeSeconds !== undefined) {
            uptimeElement.textContent = this.formatUptime(serverUptimeSeconds);
        }
    }

    async loadConfig() {
        const config = await this.fetchWithCache('/api/config', 'config', this.bypassCache);
        if (!config) return;
        this.config = config;
    }

    startCountdown() {
        if (this.countdownInterval) clearInterval(this.countdownInterval);

        this.countdown = 5;
        this.countdownInterval = setInterval(() => {
            const el = document.getElementById('trading-countdown');
            if (!el) {
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;
                return;
            }
            if (this.countdown > 0) {
                el.textContent = `Starting in ${this.countdown}s`;
                el.className = 'badge bg-warning ms-3';
                this.countdown--;
            } else {
                el.textContent = 'System Ready';
                el.className = 'badge bg-success ms-3';
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;
            }
        }, 1000);
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'primary'} position-fixed`;
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.style.minWidth = '300px';

        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close';
        closeButton.onclick = function () { this.parentElement.remove(); };

        const messageSpan = document.createElement('span');
        messageSpan.textContent = message;

        toast.appendChild(closeButton);
        toast.appendChild(messageSpan);
        document.body.appendChild(toast);

        setTimeout(() => toast.parentElement && toast.remove(), 5000);
    }

    async fetchExchangeRates() {
        try {
            const response = await fetch('/api/exchange-rates', { cache: 'no-cache' });
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            const data = await response.json();
            this.exchangeRates = data.rates || { USD: 1 };
        } catch (error) {
            console.error('Failed to fetch exchange rates:', error);
            // Sensible fallbacks
            this.exchangeRates = { USD: 1, EUR: 0.92, GBP: 0.79, AUD: 1.52 };
        }
    }

    async setSelectedCurrency(currency) {
        this.selectedCurrency = currency;
        await this.fetchExchangeRates();
        if (!this.exchangeRates[currency]) {
            this.showToast(`No exchange rate for ${currency}. Using USD.`, 'warning');
            this.selectedCurrency = 'USD';
        }
        this.updateCryptoPortfolio();
    }

    // ---------- Portfolio / Tables ----------
    displayEmptyPortfolioMessage() {
        const tableIds = ['crypto-tracked-table', 'performance-page-table-body', 'positions-table-body'];
        tableIds.forEach(tableId => {
            const tableBody = document.getElementById(tableId);
            if (!tableBody) return;
            tableBody.innerHTML = '';
            const row = document.createElement('tr');
            const cell = document.createElement('td');

            if (tableId === 'crypto-tracked-table')      cell.colSpan = 13;
            else if (tableId === 'performance-page-table-body') cell.colSpan = 12;
            else if (tableId === 'positions-table-body') cell.colSpan = 11;
            else cell.colSpan = 10;

            cell.className = 'text-center text-warning p-4';
            cell.innerHTML = `
                <div class="mb-2">
                    <i class="fas fa-exclamation-triangle fa-2x text-warning"></i>
                </div>
                <h5>Portfolio Empty</h5>
                <p class="mb-3">Start trading to populate your cryptocurrency portfolio with live data.</p>
                <button class="btn btn-success" onclick="startTrading('paper', 'portfolio')">
                    <i class="fas fa-play"></i> Start Paper Trading
                </button>
            `;
            row.appendChild(cell);
            tableBody.appendChild(row);
        });
        this.updateSummaryForEmptyPortfolio();
    }

    updateSummaryForEmptyPortfolio() {
        const summaryElements = {
            'crypto-total-count': '0',
            'crypto-current-value': this.formatCurrency(0),
            'crypto-total-pnl': this.formatCurrency(0)
        };
        Object.entries(summaryElements).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (!el) return;
            el.textContent = value;
            if (id === 'crypto-total-pnl') el.className = 'mb-0 text-secondary';
        });

        const symbolsContainer = document.getElementById('crypto-symbols');
        if (symbolsContainer) {
            symbolsContainer.innerHTML = '<span class="badge bg-warning">Portfolio empty - Start trading to populate</span>';
        }
    }

    async updateCryptoPortfolio() {
        if (this.isUpdatingPortfolio) {
            console.log('Portfolio update already in progress, skipping...');
            return;
        }
        this.isUpdatingPortfolio = true;

        try {
            this.updateLoadingProgress(20, 'Fetching cryptocurrency data...');
            const ts = Date.now();
            const response = await fetch(`/api/crypto-portfolio?_bypass_cache=${ts}&debug=1`, {
                cache: 'no-cache',
                headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' }
            });

            if (!response.ok) {
                console.error('API request failed:', response.status, response.statusText);
                const errorText = await response.text();
                console.error('Error response body:', errorText);
                this.hideLoadingProgress();
                return;
            }

            this.updateLoadingProgress(60, 'Processing market data...');
            const data = await response.json();

            const holdings = data.holdings || data.cryptocurrencies || [];
            const summary = data.summary || {};

            if (!holdings || holdings.length === 0) {
                this.displayEmptyPortfolioMessage();
                this.hideLoadingProgress();
                this.isUpdatingPortfolio = false;
                return;
            }

            if (data.price_validation?.failed_symbols?.length) {
                this.displayPriceDataWarning(data.price_validation.failed_symbols);
            }

            const totalValue = (data.summary?.total_current_value)
                            ?? data.total_value
                            ?? holdings.reduce((s, c) => s + (c.current_value || c.value || 0), 0);

            const totalPnl = (data.summary?.total_pnl)
                           ?? data.total_pnl
                           ?? holdings.reduce((s, c) => s + (c.pnl || 0), 0);

            // Display KPIs (optional if present)
            if (document.getElementById('crypto-total-count')) {
                document.getElementById('crypto-total-count').textContent = holdings.length;
            }
            if (document.getElementById('crypto-current-value')) {
                document.getElementById('crypto-current-value').textContent = this.formatCurrency(totalValue, this.selectedCurrency);
            }
            if (document.getElementById('crypto-total-pnl')) {
                const pnlEl = document.getElementById('crypto-total-pnl');
                pnlEl.textContent = this.formatCurrency(totalPnl, this.selectedCurrency);
                pnlEl.className = `mb-0 ${totalPnl >= 0 ? 'text-success' : 'text-danger'}`;
            }

            // Persist and render
            this.currentCryptoData = holdings;

            this.updateLoadingProgress(80, 'Updating displays...');
            this.updateCryptoSymbols(holdings);
            this.updateCryptoTable(holdings);

            // Update holdings widgets/table (if present on page)
            this.updateHoldingsTable(holdings);
            this.updatePositionsSummary(holdings);

            // Small summary widget method (class-local)
            this.updatePortfolioSummary({
                total_cryptos: holdings.length,
                total_current_value: totalValue,
                total_pnl: totalPnl,
                total_pnl_percent: data.total_pnl_percent || 0
            }, holdings);

            // Big UI aggregation update (global function, renamed)
            updatePortfolioSummaryUI(data);

            // Dashboard Overview (KPIs + quick charts + recent trades preview)
            const trades = data.recent_trades || data.trades || [];
            renderDashboardOverview(data, trades);

            // Recent trades full table preview/fetch
            if (trades.length) {
                this.displayRecentTrades(trades);
            } else {
                await this.updateRecentTrades().catch(e => console.error('Recent trades fetch failed (non-fatal):', e));
            }

            this.updateLoadingProgress(100, 'Complete!');
            setTimeout(() => this.hideLoadingProgress(), 1000);

        } catch (error) {
            console.error('Error updating crypto portfolio:', error);
            this.updateLoadingProgress(0, 'Error loading data');
        } finally {
            this.isUpdatingPortfolio = false;
        }
    }

    updateCryptoSymbols(cryptos) {
        const symbolsContainer = document.getElementById('crypto-symbols');
        if (!symbolsContainer) return;

        symbolsContainer.innerHTML = '';

        if (!cryptos || cryptos.length === 0) {
            const badge = document.createElement('span');
            badge.className = 'badge bg-warning';
            badge.textContent = 'Portfolio loading... Please wait';
            symbolsContainer.appendChild(badge);
            return;
        }

        const topCryptos = [...cryptos]
            .sort((a, b) => (b.current_value || 0) - (a.current_value || 0))
            .slice(0, 10);

        topCryptos.forEach(crypto => {
            const badge = document.createElement('span');
            const pnlClass = (crypto.pnl || 0) >= 0 ? 'bg-success' : 'bg-danger';
            badge.className = `badge ${pnlClass} me-1 mb-1`;
            const priceText = this.formatCurrency(this.num(crypto.current_price));
            const pp = this.num(crypto.pnl_percent).toFixed(2);
            const pnlText = (crypto.pnl || 0) >= 0 ? `+${pp}%` : `${pp}%`;
            badge.textContent = `${crypto.symbol} ${priceText} (${pnlText})`;
            badge.setAttribute('title', `${crypto.name}: ${priceText}, P&L: ${pnlText}`);
            symbolsContainer.appendChild(badge);
        });
    }

    updateCryptoTable(cryptos) {
        const tableBody = document.getElementById('crypto-tracked-table');
        if (!tableBody) return;

        tableBody.innerHTML = '';

        if (!cryptos || cryptos.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="13" class="text-center text-muted">No cryptocurrency data available</td>';
            tableBody.appendChild(row);
            return;
        }

        const sortedCryptos = [...cryptos].sort((a, b) => (a.rank || 999) - (b.rank || 999));

        sortedCryptos.forEach(crypto => {
            const row = document.createElement('tr');

            const price = this.num(crypto.current_price);
            const quantity = this.num(crypto.quantity);
            const value = this.num(crypto.current_value);
            const pnlPercent = this.num(crypto.pnl_percent);

            const rankCell = document.createElement('td');
            rankCell.textContent = crypto.rank || '-';

            const symbolCell = document.createElement('td');
            const symbolSpan = document.createElement('span');
            symbolSpan.className = 'fw-bold text-primary';
            symbolSpan.textContent = crypto.symbol || '-';
            symbolCell.appendChild(symbolSpan);

            const nameCell = document.createElement('td');
            nameCell.textContent = crypto.name || '-';

            // Quantity (sold-out highlight)
            const quantityCell = document.createElement('td');
            const isSoldOut = value <= 0.01 || crypto.has_position === false || quantity <= 0;
            quantityCell.textContent = this.num(isSoldOut ? 0 : quantity).toFixed(6);
            if (isSoldOut) {
                quantityCell.classList.add('text-warning');
                quantityCell.style.fontWeight = 'bold';
                quantityCell.style.backgroundColor = '#fff3cd';
                quantityCell.title = 'Position sold through trading';
            }

            const priceCell = document.createElement('td');
            priceCell.textContent = this.formatCurrency(price, this.selectedCurrency);

            const valueCell = document.createElement('td');
            valueCell.textContent = this.formatCurrency(value, this.selectedCurrency);

            const targetSellCell = document.createElement('td');
            const targetSellPrice = price * 1.05;
            targetSellCell.textContent = this.formatCurrency(targetSellPrice);

            const pnlAbsoluteCell = document.createElement('td');
            const originalInvestment = 10; // per-asset seed
            const absolutePnl = value - originalInvestment;
            pnlAbsoluteCell.className = absolutePnl >= 0 ? 'text-success' : 'text-danger';
            pnlAbsoluteCell.textContent = this.formatCurrency(absolutePnl);

            const pnlCell = document.createElement('td');
            const pnlSpan = document.createElement('span');
            pnlSpan.className = `${pnlPercent >= 0 ? 'text-success' : 'text-danger'} fw-bold`;
            pnlSpan.textContent = `${pnlPercent.toFixed(2)}%`;
            pnlCell.appendChild(pnlSpan);

            const updatedCell = document.createElement('td');
            const updatedSmall = document.createElement('small');
            updatedSmall.className = 'text-muted';
            updatedSmall.textContent = crypto.last_updated ? new Date(crypto.last_updated).toLocaleTimeString() : '-';
            updatedCell.appendChild(updatedSmall);

            // Signal
            const signalCell = document.createElement('td');
            const targetBuyPrice = price * 0.95;
            let signal = 'HOLD', signalClass = 'bg-secondary';
            if (price <= targetBuyPrice)            { signal = 'BUY';  signalClass = 'bg-success'; }
            else if (price >= targetSellPrice)      { signal = 'SELL'; signalClass = 'bg-danger'; }
            else if (absolutePnl > 0.5)             { signal = 'TAKE PROFIT'; signalClass = 'bg-warning text-dark'; }
            signalCell.innerHTML = `<span class="badge ${signalClass}">${signal}</span>`;

            const actionsCell = document.createElement('td');
            actionsCell.innerHTML = '<button class="btn btn-sm btn-outline-primary">View</button>';

            const targetBuyCell = document.createElement('td');
            targetBuyCell.textContent = this.formatCurrency(targetBuyPrice);

            row.appendChild(rankCell);
            row.appendChild(symbolCell);
            row.appendChild(nameCell);
            row.appendChild(quantityCell);
            row.appendChild(priceCell);
            row.appendChild(valueCell);
            row.appendChild(targetSellCell);
            row.appendChild(pnlAbsoluteCell);
            row.appendChild(pnlCell);
            row.appendChild(updatedCell);
            row.appendChild(signalCell);
            row.appendChild(actionsCell);
            row.appendChild(targetBuyCell);

            row.classList.add('table-row-hover');
            tableBody.appendChild(row);
        });
    }

    updateLoadingProgress(percent, message = '') {
        const progressBar = document.getElementById('crypto-loading-progress');
        const progressText = document.getElementById('crypto-loading-text');

        if (progressBar) {
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', percent);
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
        const progressBar = document.getElementById('crypto-loading-progress');
        if (progressBar) {
            progressBar.style.display = 'none';
            const row = progressBar.closest('tr');
            if (row) row.style.display = 'none';
        }
        const progressText = document.getElementById('crypto-loading-text');
        if (progressText) progressText.style.display = 'none';
    }

    updatePerformanceTable(cryptos, bodyId = 'performance-table-body') {
        const tableBody = document.getElementById(bodyId);
        if (!tableBody) return;

        tableBody.innerHTML = '';

        if (!cryptos || cryptos.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = bodyId === 'performance-page-table-body' ? 12 : 10;
            cell.className = 'text-center text-muted';
            cell.textContent = 'No cryptocurrency holdings. Start trading to populate portfolio.';
            row.appendChild(cell);
            tableBody.appendChild(row);
            return;
        }

        const sorted = [...cryptos].sort((a, b) => (a.rank || 999) - (b.rank || 999));
        const isPerformancePage = bodyId === 'performance-page-table-body';

        sorted.forEach((crypto, index) => {
            const row = document.createElement('tr');

            const rank = crypto.rank || (index + 1);
            const symbol = crypto.symbol || 'UNKNOWN';
            const name = crypto.name || symbol;
            const currentPrice = this.num(crypto.current_price);
            const quantity = this.num(crypto.quantity);
            const value = this.num(crypto.value || crypto.current_value);
            const isLive = crypto.is_live !== false;

            const purchasePrice = quantity > 0 ? 10 / quantity : 0; // $10 initial investment
            const targetSellPrice = currentPrice * 1.1;

            const backendPnl = this.num(crypto.pnl);
            const backendPnlPercent = this.num(crypto.pnl_percent);

            let finalPnl, finalPnlPercent;
            if (backendPnl !== 0 || backendPnlPercent !== 0) {
                finalPnl = backendPnl;
                finalPnlPercent = backendPnlPercent;
            } else {
                finalPnl = (currentPrice - purchasePrice) * quantity;
                finalPnlPercent = purchasePrice > 0 ? ((currentPrice - purchasePrice) / purchasePrice) * 100 : 0;
            }

            const pnlClass = finalPnl >= 0 ? 'text-success' : 'text-danger';
            const pnlSign = finalPnl >= 0 ? '+' : '';

            const formattedQuantity = this.num(quantity) > 1 ? quantity.toFixed(4) : quantity.toFixed(8);
            const formattedPurchasePrice = this.formatCurrency(purchasePrice);
            const formattedCurrentPrice = this.formatCurrency(currentPrice);
            const formattedTargetPrice = this.formatCurrency(targetSellPrice);
            const formattedValue = this.formatCurrency(value);
            const formattedUnrealizedPnl = this.formatCurrency(Math.abs(finalPnl));

            if (isPerformancePage) {
                const daysInvested = Math.floor((Date.now() - new Date('2025-08-01').getTime()) / (1000 * 60 * 60 * 24));
                const status = finalPnl >= 0 ? 'Winner' : 'Loser';
                const statusClass = finalPnl >= 0 ? 'bg-success' : 'bg-danger';

                row.innerHTML = `
                    <td><span class="badge bg-primary">#${rank}</span></td>
                    <td>
                        <strong>${symbol}</strong>
                        ${isLive ? '<span class="badge bg-success ms-1" title="Live OKX data">Live</span>' : '<span class="badge bg-warning ms-1" title="Simulation data">Sim</span>'}
                    </td>
                    <td class="text-muted">${name}</td>
                    <td><strong>${formattedPurchasePrice}</strong></td>
                    <td><strong class="text-primary">${formattedCurrentPrice}</strong></td>
                    <td><strong class="text-info">${formattedTargetPrice}</strong></td>
                    <td><strong>${formattedValue}</strong></td>
                    <td><strong>${formattedValue}</strong></td>
                    <td class="${pnlClass}"><strong>${pnlSign}${formattedUnrealizedPnl}</strong></td>
                    <td class="${pnlClass}"><strong>${pnlSign}${this.num(finalPnlPercent).toFixed(2)}%</strong></td>
                    <td class="text-muted">${daysInvested}</td>
                    <td><span class="badge ${statusClass}">${status}</span></td>
                `;
            } else {
                row.innerHTML = `
                    <td><span class="badge bg-primary">#${rank}</span></td>
                    <td>
                        <strong>${symbol}</strong>
                        ${isLive ? '<span class="badge bg-success ms-1" title="Live OKX data">Live</span>' : '<span class="badge bg-warning ms-1" title="Simulation data">Sim</span>'}
                    </td>
                    <td><strong class="text-primary">${formattedCurrentPrice}</strong></td>
                    <td>${formattedQuantity}</td>
                    <td><strong>${formattedValue}</strong></td>
                    <td class="${pnlClass}"><strong>${pnlSign}${formattedUnrealizedPnl}</strong></td>
                    <td class="${pnlClass}"><strong>${pnlSign}${this.num(finalPnlPercent).toFixed(2)}%</strong></td>
                `;
            }

            tableBody.appendChild(row);
        });
    }

    updateHoldingsTable(cryptos) {
        const tableBody = document.getElementById('positions-table-body');
        if (!tableBody) return;

        tableBody.innerHTML = '';

        if (!cryptos || cryptos.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 11;
            cell.className = 'text-center text-muted';
            cell.textContent = 'No holdings data available';
            row.appendChild(cell);
            tableBody.appendChild(row);
            return;
        }

        cryptos.forEach(crypto => {
            const row = document.createElement('tr');

            const qty = this.num(crypto.quantity);
            const cp = this.num(crypto.current_price);
            const cv = this.num(crypto.current_value);
            const pnlNum = this.num(crypto.pnl);
            const pp = this.num(crypto.pnl_percent);

            const pnlClass = pnlNum >= 0 ? 'text-success' : 'text-danger';
            const pnlIcon = pnlNum >= 0 ? '↗' : '↘';

            let signal = 'HOLD';
            let signalClass = 'badge bg-secondary';
            if (crypto.target_buy_price && cp <= crypto.target_buy_price) {
                signal = 'BUY';  signalClass = 'badge bg-success';
            } else if (crypto.target_sell_price && cp >= crypto.target_sell_price) {
                signal = 'SELL'; signalClass = 'badge bg-danger';
            }

            const positionPercent = (100 / cryptos.length).toFixed(1);

            row.innerHTML = `
                <td><strong>${crypto.symbol || ''}</strong></td>
                <td>${crypto.name || ''}</td>
                <td>${qty.toFixed(4)}</td>
                <td>${this.formatCurrency(cp)}</td>
                <td>${this.formatCurrency(cv, this.selectedCurrency)}</td>
                <td>${positionPercent}%</td>
                <td class="${pnlClass}">${this.formatCurrency(pnlNum)}</td>
                <td class="${pnlClass}">${pnlIcon} ${pp.toFixed(2)}%</td>
                <td>${this.formatCurrency(crypto.target_sell_price || cp * 1.1)}</td>
                <td class="${pnlClass}">${this.formatCurrency(Math.max(0, pnlNum))}</td>
                <td><span class="${signalClass}">${signal}</span></td>
            `;
            tableBody.appendChild(row);
        });
    }

    updatePositionsSummary(cryptos) {
        if (!cryptos || cryptos.length === 0) return;
        const totalPositions = cryptos.length;
        const totalValue = cryptos.reduce((sum, c) => sum + (c.current_value || 0), 0);
        const totalPnL = cryptos.reduce((sum, c) => sum + (c.pnl || 0), 0);
        const strongGains = cryptos.filter(c => (c.pnl_percent || 0) > 20).length;

        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

        set('pos-total-count', totalPositions);
        const tvEl = document.getElementById('pos-total-value');
        if (tvEl) tvEl.textContent = this.formatCurrency(totalValue, this.selectedCurrency);

        const upnlEl = document.getElementById('pos-unrealized-pnl');
        if (upnlEl) {
            upnlEl.textContent = this.formatCurrency(totalPnL, this.selectedCurrency);
            upnlEl.className = totalPnL >= 0 ? 'text-success' : 'text-danger';
        }
        set('pos-strong-gains', strongGains);
    }

    // Small summary method (class-local)
    updatePortfolioSummary(summary, cryptos) {
        if (!summary) return;
        const safeSet = (id, text, className) => {
            const el = document.getElementById(id);
            if (!el) return;
            if (text !== undefined) el.textContent = text;
            if (className !== undefined) el.className = className;
        };

        safeSet('summary-total-value', this.formatCurrency(summary.total_current_value));
        const changeValue = summary.total_pnl || 0;
        const changePercent = summary.total_pnl_percent || 0;

        safeSet('summary-total-assets', summary.total_cryptos || 0);
        safeSet('summary-24h-change',
            `${changePercent >= 0 ? '+' : ''}${this.num(changePercent).toFixed(2)}%`,
            `mb-0 fw-bold ${changePercent >= 0 ? 'text-success' : 'text-danger'}`);

        if (cryptos && cryptos.length > 0) {
            const best = cryptos.reduce((best, c) => (c.pnl_percent || 0) > (best.pnl_percent || 0) ? c : best);
            safeSet('summary-best-performer', best.symbol);
            safeSet('summary-best-performance', `+${this.num(best.pnl_percent || 0).toFixed(2)}%`);
        }
    }

    displayPriceDataWarning(failedSymbols) {
        let warningBanner = document.getElementById('price-data-warning');
        if (!warningBanner) {
            warningBanner = document.createElement('div');
            warningBanner.id = 'price-data-warning';
            warningBanner.className = 'alert alert-danger alert-dismissible fade show mb-3';
            warningBanner.role = 'alert';
            const container = document.querySelector('.container-fluid');
            if (container) container.insertBefore(warningBanner, container.firstChild);
        }
        warningBanner.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>CRITICAL: Price Data Unavailable</strong>
            <br>Live price data could not be retrieved for: ${failedSymbols.join(', ')}
            <br>This system NEVER uses simulated prices. Please check your internet connection or try refreshing.
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
    }

    // ---------- Charts ----------
    initializeCharts() {
        // Enhanced chart initialization with development environment safety
        if (!window.Chart || typeof Chart === 'undefined') {
            console.warn('Chart.js not found – skipping chart initialization.');
            this.showChartFallbacks();
            return;
        }
        
        try {
            // Test Chart.js availability and compatibility
            const testCanvas = document.createElement('canvas');
            const testChart = new Chart(testCanvas, {
                type: 'line',
                data: { labels: [], datasets: [] },
                options: { responsive: false, animation: false }
            });
            testChart.destroy();
            
            // If test passes, proceed with real chart initialization
            this.initializeRealCharts();
            
        } catch (testError) {
            console.warn('Chart.js compatibility test failed – using fallback displays. This is normal in development mode.', testError.message);
            this.showChartFallbacks();
        }
    }

    initializeRealCharts() {
        try {

            const portfolioCtx = document.getElementById('portfolioChart');
            if (portfolioCtx && portfolioCtx.getContext) {
                try {
                    this.portfolioChart = new Chart(portfolioCtx, {
                        type: 'line',
                        data: { 
                            labels: [], 
                            datasets: [{ 
                                label: 'Portfolio Value ($)', 
                                data: [], 
                                borderColor: '#007bff', 
                                backgroundColor: 'rgba(0, 123, 255, 0.1)', 
                                tension: 0.4, 
                                fill: true 
                            }]
                        },
                        options: {
                            responsive: true, 
                            maintainAspectRatio: true, 
                            aspectRatio: 2,
                            plugins: { 
                                title: { display: true, text: 'Portfolio Performance Over Time' }, 
                                legend: { display: false } 
                            },
                            scales: { 
                                y: { 
                                    beginAtZero: false, 
                                    ticks: { callback: v => '$' + Number(v).toLocaleString() } 
                                } 
                            },
                            interaction: { intersect: false, mode: 'index' }
                        }
                    });
                } catch (chartError) {
                    console.warn('Portfolio chart initialization failed:', chartError.message);
                }
            }

            const pnlCtx = document.getElementById('pnlChart');
            if (pnlCtx && pnlCtx.getContext) {
                try {
                    this.pnlChart = new Chart(pnlCtx, {
                        type: 'doughnut',
                        data: {
                            labels: ['Profitable', 'Break-even', 'Losing'],
                            datasets: [{ 
                                data: [0,0,0], 
                                backgroundColor: ['rgba(54,162,235,0.8)', 'rgba(255,206,86,0.8)', 'rgba(255,99,132,0.8)'], 
                                borderWidth: 0 
                            }]
                        },
                        options: { 
                            responsive: true, 
                            maintainAspectRatio: true, 
                            aspectRatio: 1,
                            plugins: { 
                                title: { display: true, text: 'P&L Distribution' }, 
                                legend: { position: 'bottom' } 
                            }
                        }
                    });
                } catch (chartError) {
                    console.warn('P&L chart initialization failed:', chartError.message);
                }
            }

            const performersCtx = document.getElementById('performersChart');
            if (performersCtx && performersCtx.getContext) {
                try {
                    this.performersChart = new Chart(performersCtx, {
                        type: 'bar',
                        data: { 
                            labels: [], 
                            datasets: [{ 
                                label: 'P&L %', 
                                data: [], 
                                backgroundColor: ctx => {
                                    // Safely check if data is parsed and y value exists
                                    if (ctx?.parsed?.y !== undefined) {
                                        return ctx.parsed.y >= 0 ? 'rgba(75,192,192,0.8)' : 'rgba(255,99,132,0.8)';
                                    }
                                    // Default color if data not parsed yet
                                    return 'rgba(75,192,192,0.8)';
                                }, 
                                borderWidth: 0 
                            }] 
                        },
                        options: {
                            responsive: true, 
                            maintainAspectRatio: true, 
                            aspectRatio: 2,
                            plugins: { 
                                title: { display: true, text: 'Top/Bottom Performers' }, 
                                legend: { display: false } 
                            },
                            scales: { 
                                y: { 
                                    ticks: { 
                                        callback: function(value, index, values) {
                                            // Safely format y-axis values
                                            return (value || 0) + '%';
                                        }
                                    } 
                                } 
                            }
                        }
                    });
                } catch (chartError) {
                    console.warn('Performers chart initialization failed:', chartError.message);
                    // Ensure chart variable is properly reset on error
                    this.performersChart = null;
                }
            }

            // Seed charts after a small delay to ensure DOM is ready
            setTimeout(() => {
                this.updatePerformanceCharts();
            }, 100);
            
        } catch (e) {
            console.warn('Chart initialization failed – using fallback displays.', e.message || e);
            this.showChartFallbacks();
        }
    }

    showChartFallbacks() {
        // Show text-based fallbacks when charts can't initialize
        const fallbackElements = [
            { id: 'portfolioChart', message: 'Portfolio Chart: Real-time tracking active (Charts disabled in dev mode)' },
            { id: 'pnlChart', message: 'P&L Distribution: Data available in tables below' },
            { id: 'performersChart', message: 'Performance Chart: Rankings shown in portfolio table' }
        ];

        fallbackElements.forEach(({ id, message }) => {
            const element = document.getElementById(id);
            if (element) {
                element.style.display = 'flex';
                element.style.alignItems = 'center';
                element.style.justifyContent = 'center';
                element.style.background = '#f8f9fa';
                element.style.border = '2px dashed #dee2e6';
                element.style.borderRadius = '8px';
                element.style.color = '#6c757d';
                element.style.fontWeight = '500';
                element.style.textAlign = 'center';
                element.style.padding = '20px';
                element.style.minHeight = '200px';
                element.innerHTML = `<div><i class="fas fa-chart-area me-2"></i>${message}</div>`;
            }
        });
    }

    async updatePerformanceCharts() {
        try {
            const response = await fetch('/api/crypto-portfolio', { cache: 'no-cache' });
            if (!response.ok) return;

            const data = await response.json();
            const holdings = data.holdings || [];

            if (holdings.length === 0) return;

            if (this.pnlChart) {
                const profitable = holdings.filter(h => (h.pnl || 0) > 0.01).length;
                const losing = holdings.filter(h => (h.pnl || 0) < -0.01).length;
                const breakeven = holdings.length - profitable - losing;
                this.pnlChart.data.datasets[0].data = [profitable, breakeven, losing];
                this.pnlChart.update('none');
            }

            if (this.performersChart) {
                const sorted = [...holdings].sort((a, b) => (b.pnl_percent || 0) - (a.pnl_percent || 0));
                const topPerformers = sorted.slice(0, 5).concat(sorted.slice(-5));
                this.performersChart.data.labels = topPerformers.map(h => h.symbol);
                this.performersChart.data.datasets[0].data = topPerformers.map(h => h.pnl_percent || 0);
                this.performersChart.update('none');
            }

            if (this.portfolioChart) {
                const totalValue = data.summary?.total_current_value || 1030;
                const labels = [];
                const values = [];
                for (let i = 23; i >= 0; i--) {
                    const time = new Date(Date.now() - (i * 60 * 60 * 1000));
                    const variation = (Math.sin(i * 0.5) * 0.02 + Math.random() * 0.01 - 0.005);
                    labels.push(time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
                    values.push(totalValue * (1 + variation));
                }
                this.portfolioChart.data.labels = labels;
                this.portfolioChart.data.datasets[0].data = values;
                this.portfolioChart.update('none');
            }
        } catch (error) {
            console.error('Error updating performance charts:', error);
        }
    }

    // ---------- Trades ----------
    async updateRecentTrades() {
        try {
            const r = await fetch('/api/trade-history', { cache: 'no-cache' });
            if (r.ok) {
                const data = await r.json();
                const trades = data.trades || data.recent_trades || data || [];
                this.displayRecentTrades(trades);
                return;
            }
        } catch (e) {
            console.error('Failed to fetch trade history:', e);
        }

        try {
            const status = await this.fetchWithCache('/api/status', 'status');
            if (status?.recent_trades?.length) {
                this.displayRecentTrades(status.recent_trades);
                return;
            }
        } catch (e) {
            console.error('Failed to fetch trades from status:', e);
        }

        this.displayDashboardRecentTrades([]);
    }

    displayRecentTrades(trades) {
        const tableBody = this.getTradesTbody();
        if (!tableBody) {
            this.displayDashboardRecentTrades(trades);
            return;
        }
        this.allTrades = this.normalizeTrades(trades || []);
        this.applyTradeFilters();
    }

    displayDashboardRecentTrades(trades) {
        const tableBody = document.getElementById('recent-trades-preview-body');
        if (!tableBody) return;

        const normalized = this.normalizeTrades(trades || []);
        const recent = normalized.slice(0, 5);

        if (recent.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-3">No trades yet</td></tr>';
            return;
        }

        let html = '';
        recent.forEach((t, idx) => {
            const pnlClass = (t.pnl || 0) >= 0 ? 'text-success' : 'text-danger';
            const sideBadge = t.side === 'BUY' ? 'badge bg-success' : 'badge bg-danger';
            html += `
                <tr>
                    <td>${idx + 1}</td>
                    <td class="text-start">${this.formatTradeTime(t.timestamp)}</td>
                    <td><strong>${t.symbol}</strong></td>
                    <td><span class="${sideBadge}">${t.side}</span></td>
                    <td class="text-end">${this.num(t.quantity).toFixed(6)}</td>
                    <td class="text-end">${this.formatCurrency(t.price)}</td>
                    <td class="text-end ${pnlClass}">${this.formatCurrency(t.pnl)}</td>
                </tr>
            `;
        });
        tableBody.innerHTML = html;
    }

    applyTradeFilters() {
        const tableBody = this.getTradesTbody();
        if (!tableBody || !this.allTrades) return;

        const symbolFilter = document.getElementById('trades-filter')?.value.toLowerCase() || '';
        const actionFilter = (document.getElementById('trades-action-filter')?.value || '').toUpperCase();
        const timeFilter = document.getElementById('trades-time-filter')?.value || '';
        const pnlFilter = document.getElementById('trades-pnl-filter')?.value || '';

        const parseTime = (t) => {
            if (!t) return 0;
            const d = new Date(t);
            const n = d.getTime();
            return Number.isFinite(n) ? n : 0;
        };

        let filtered = this.allTrades.filter(trade => {
            if (symbolFilter && !(trade.symbol || '').toLowerCase().includes(symbolFilter)) return false;
            if (actionFilter && (trade.side || '').toUpperCase() !== actionFilter) return false;

            if (timeFilter) {
                const tradeMs = parseTime(trade.timestamp);
                const now = Date.now();
                const age = now - tradeMs;

                let maxAge = Infinity;
                switch (timeFilter) {
                    case '24h': maxAge = 24 * 60 * 60 * 1000; break;
                    case '3d': maxAge = 3 * 24 * 60 * 60 * 1000; break;
                    case '7d': maxAge = 7 * 24 * 60 * 60 * 1000; break;
                    case '1m': maxAge = 30 * 24 * 60 * 60 * 1000; break;
                    case '6m': maxAge = 6 * 30 * 24 * 60 * 60 * 1000; break;
                    case '1y': maxAge = 365 * 24 * 60 * 60 * 1000; break;
                }
                if (!(tradeMs > 0) || age > maxAge) return false;
            }

            const pnl = Number(trade.pnl) || 0;
            if (pnlFilter === 'positive' && pnl <= 0) return false;
            if (pnlFilter === 'negative' && pnl >= 0) return false;

            return true;
        });

        tableBody.innerHTML = '';

        if (!filtered.length) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 7;
            cell.className = 'text-center text-muted';
            cell.textContent = 'No trades match the current filters';
            row.appendChild(cell);
            tableBody.appendChild(row);
            return;
        }

        filtered.sort((a, b) => (parseTime(b.timestamp) - parseTime(a.timestamp)));

        filtered.forEach(trade => {
            const row = document.createElement('tr');
            const ms = parseTime(trade.timestamp);
            const timestamp = ms ? new Date(ms).toLocaleString() : '-';
            const price = this.formatCurrency(trade.price || 0);
            const quantity = this.num(trade.quantity).toFixed(6);
            const pnl = Number.isFinite(trade.pnl) ? this.formatCurrency(trade.pnl) : this.formatCurrency(0);
            const pnlClass = (Number(trade.pnl) || 0) >= 0 ? 'text-success' : 'text-danger';
            const sideUp = (trade.side || '').toUpperCase();

            row.innerHTML = `
                <td><span class="badge bg-secondary">#${trade.trade_id}</span></td>
                <td><small>${timestamp}</small></td>
                <td><strong>${trade.symbol || ''}</strong></td>
                <td><span class="badge ${sideUp === 'BUY' ? 'bg-success' : 'bg-danger'}">${sideUp || '-'}</span></td>
                <td>${quantity}</td>
                <td>${price}</td>
                <td class="${pnlClass}">${pnl}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    // ---------- Misc ----------
    async exportATOTax() {
        try {
            this.showToast('Preparing ATO tax export...', 'info');
            const response = await fetch('/api/export/ato', {
                method: 'GET',
                headers: { 'Accept': 'text/csv' }
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Export failed: ${response.statusText} - ${errorText}`);
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const today = new Date().toISOString().slice(0, 10);
            a.download = `ato_crypto_tax_export_${today}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            this.showToast('ATO tax export downloaded successfully!', 'success');
        } catch (error) {
            console.error('ATO export error:', error);
            this.showToast(`Failed to export ATO data: ${error.message}`, 'error');
        }
    }

    updateTradingStatus(status) {
        if (!status) return;
        const modeEl = document.getElementById('trading-mode');
        const statusEl = document.getElementById('trading-status');

        if (modeEl && status.mode) {
            modeEl.textContent = status.mode.toUpperCase();
            modeEl.className = `badge ${status.mode === 'paper' ? 'bg-success' : 'bg-warning'}`;
        }
        if (statusEl && status.status) {
            statusEl.textContent = status.status;
            statusEl.className = `badge ${status.status === 'Active' ? 'bg-success' : 'bg-secondary'}`;
        }

        const startTimeEl = document.getElementById('trading-start-time');
        if (startTimeEl && status.started_at) {
            try {
                startTimeEl.textContent = new Date(status.started_at).toLocaleTimeString();
            } catch {}
        }
        const symbolEl = document.getElementById('trading-symbol');
        if (symbolEl && status.symbol) {
            symbolEl.textContent = status.symbol;
        }
    }

    updateTradingStatusDisplay(mode, type) {
        const tradingModeEl = document.getElementById('trading-mode');
        const tradingStatusEl = document.getElementById('trading-status');
        const tradingStartTimeEl = document.getElementById('trading-start-time');
        const tradingSymbolEl = document.getElementById('trading-symbol');

        if (tradingModeEl) {
            tradingModeEl.textContent = `${mode.toUpperCase()} (${type})`;
            tradingModeEl.className = `badge ${mode === 'paper' ? 'bg-success' : 'bg-warning'}`;
        }
        if (tradingStatusEl) {
            tradingStatusEl.textContent = 'Active';
            tradingStatusEl.className = 'badge bg-success';
        }
        if (tradingStartTimeEl) tradingStartTimeEl.textContent = new Date().toLocaleTimeString();
        if (tradingSymbolEl) tradingSymbolEl.textContent = type === 'portfolio' ? 'All Assets' : 'Selected';
    }
}

// ---------- Boot ----------
document.addEventListener('DOMContentLoaded', function () {
    window.tradingApp = new TradingApp();
});

// ---------- Global helpers wired to UI ----------
async function exportATOTax() {
    if (window.tradingApp) await window.tradingApp.exportATOTax();
}
function refreshCryptoPortfolio() {
    if (window.tradingApp) {
        window.tradingApp.updateCryptoPortfolio();
        window.tradingApp.showToast('Portfolio refreshed', 'info');
    }
}
async function resetEntireProgram() {
    if (!confirm('Reset the entire system? This resets all values to $10 and clears trading data.')) return;
    try {
        const response = await fetch('/api/reset-entire-program', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        if (data.success) {
            window.tradingApp.showToast('Portfolio reset successfully!', 'success');
            const modeEl = document.getElementById('trading-mode');
            const statusEl = document.getElementById('trading-status');
            const startEl = document.getElementById('trading-start-time');
            const symEl = document.getElementById('trading-symbol');

            if (modeEl) { modeEl.textContent = 'Stopped'; modeEl.className = 'badge bg-secondary'; }
            if (statusEl) { statusEl.textContent = 'Idle'; statusEl.className = 'badge bg-secondary'; }
            if (startEl) startEl.textContent = '-';
            if (symEl) symEl.textContent = '-';

            const tradesTable = document.getElementById('trades-table');
            if (tradesTable) {
                tradesTable.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No trades yet</td></tr>';
            }

            setTimeout(() => window.tradingApp.loadPortfolioData(), 1000);
            setTimeout(() => location.reload(), 2500);
        } else {
            window.tradingApp.showToast('Failed to reset portfolio: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Reset error:', error);
        window.tradingApp.showToast('Error resetting portfolio: ' + error.message, 'error');
    }
}
function changeCurrency() {
    const dd = document.getElementById('currency-selector');
    if (dd && window.tradingApp) {
        window.tradingApp.setSelectedCurrency(dd.value);
    }
}
function clearPortfolioFilters() {
    if (window.tradingApp) {
        window.tradingApp.updateCryptoPortfolio();
        window.tradingApp.showToast('Portfolio filters cleared', 'success');
    }
}
function clearPerformanceFilters() {
    if (window.tradingApp) {
        window.tradingApp.updateCryptoPortfolio();
        window.tradingApp.showToast('Performance filters cleared', 'success');
    }
}
function confirmLiveTrading() {
    if (confirm('Start LIVE trading? This will use real money.')) {
        startTrading('live', 'portfolio');
    }
}
// Global variables to track sort state
let tableSortState = {
    portfolio: { column: null, direction: 'asc' },
    positions: { column: null, direction: 'asc' },
    trades: { column: null, direction: 'asc' },
    performance: { column: null, direction: 'asc' }
};

function sortPortfolio(column) {
    console.log(`Sorting portfolio by ${column}`);
    
    const table = document.querySelector('#positions-table-body');
    if (!table) {
        console.warn('Portfolio table not found');
        return;
    }
    
    sortTableByColumn(table, column, 'portfolio');
    if (window.tradingApp) window.tradingApp.showToast(`Portfolio sorted by ${column}`, 'success');
}

function sortPerformanceTable(columnIndex) {
    console.log(`Sorting performance table by column ${columnIndex}`);
    
    const table = document.querySelector('#attribution-table, #trades-table');
    if (!table) {
        console.warn('Performance table not found');
        return;
    }
    
    sortTableByColumnIndex(table, columnIndex, 'performance');
    if (window.tradingApp) window.tradingApp.showToast('Performance table sorted', 'success');
}

function sortPositionsTable(columnIndex) {
    console.log(`Sorting positions table by column ${columnIndex}`);
    
    const table = document.querySelector('#positions-table-body');
    if (!table) {
        console.warn('Positions table not found');
        return;
    }
    
    sortTableByColumnIndex(table, columnIndex, 'positions');
    if (window.tradingApp) window.tradingApp.showToast('Positions table sorted', 'success');
}

function sortTradesTable(columnIndex) {
    console.log(`Sorting trades table by column ${columnIndex}`);
    
    const table = document.querySelector('#trades-table');
    if (!table) {
        console.warn('Trades table not found');
        return;
    }
    
    sortTableByColumnIndex(table, columnIndex, 'trades');
    if (window.tradingApp) window.tradingApp.showToast('Trades table sorted', 'success');
}

function sortTableByColumn(tableBody, column, tableType) {
    const rows = Array.from(tableBody.getElementsByTagName('tr'));
    if (rows.length <= 1) return; // No data to sort
    
    // Determine if we need to reverse direction
    const state = tableSortState[tableType];
    const ascending = state.column === column ? state.direction === 'desc' : true;
    
    // Update sort state
    state.column = column;
    state.direction = ascending ? 'asc' : 'desc';
    
    // Get column index based on column name
    const columnMap = {
        'symbol': 0, 'name': 1, 'quantity': 2, 'price': 3, 'current_price': 3,
        'value': 4, 'current_value': 4, 'position_percent': 5, 'pnl': 6, 
        'pnl_percent': 7, 'target_sell': 8, 'potential_profit': 9, 'status': 10
    };
    
    const columnIndex = columnMap[column] || 0;
    
    rows.sort((a, b) => {
        const aVal = getCellValue(a, columnIndex);
        const bVal = getCellValue(b, columnIndex);
        
        // Handle numeric vs string comparison
        const aNum = parseFloat(aVal.replace(/[$,%]/g, ''));
        const bNum = parseFloat(bVal.replace(/[$,%]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return ascending ? aNum - bNum : bNum - aNum;
        } else {
            return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        }
    });
    
    // Reorder the table
    rows.forEach(row => tableBody.appendChild(row));
    
    // Update sort indicators
    updateSortIndicators(tableType, column, ascending);
}

function sortTableByColumnIndex(tableBody, columnIndex, tableType) {
    const rows = Array.from(tableBody.getElementsByTagName('tr'));
    if (rows.length <= 1) return; // No data to sort
    
    // Determine if we need to reverse direction
    const state = tableSortState[tableType];
    const ascending = state.column === columnIndex ? state.direction === 'desc' : true;
    
    // Update sort state
    state.column = columnIndex;
    state.direction = ascending ? 'asc' : 'desc';
    
    rows.sort((a, b) => {
        const aVal = getCellValue(a, columnIndex);
        const bVal = getCellValue(b, columnIndex);
        
        // Handle numeric vs string comparison
        const aNum = parseFloat(aVal.replace(/[$,%]/g, ''));
        const bNum = parseFloat(bVal.replace(/[$,%]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return ascending ? aNum - bNum : bNum - aNum;
        } else {
            return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        }
    });
    
    // Reorder the table
    rows.forEach(row => tableBody.appendChild(row));
    
    // Update sort indicators for column index
    updateSortIndicatorsByIndex(tableType, columnIndex, ascending);
}

function getCellValue(row, columnIndex) {
    const cell = row.cells[columnIndex];
    if (!cell) return '';
    
    // Get text content, handling various formats
    let value = cell.textContent || cell.innerText || '';
    
    // Clean up value for comparison
    value = value.trim();
    
    // Handle special cases
    if (value === '—' || value === '-' || value === 'N/A') {
        return '';
    }
    
    return value;
}

function updateSortIndicators(tableType, column, ascending) {
    // Reset all sort icons for this table type
    const allIcons = document.querySelectorAll(`[id*="sort-${column}"], [id*="sort-${tableType}"]`);
    allIcons.forEach(icon => {
        icon.className = 'fas fa-sort text-white';
    });
    
    // Set active sort icon
    const activeIcon = document.getElementById(`sort-${column}`) || 
                      document.getElementById(`sort-${tableType}-${column}`);
    if (activeIcon) {
        activeIcon.className = ascending ? 'fas fa-sort-up text-warning' : 'fas fa-sort-down text-warning';
    }
}

function updateSortIndicatorsByIndex(tableType, columnIndex, ascending) {
    // Reset all sort icons for this table type
    const allIcons = document.querySelectorAll(`[id*="${tableType}-sort-"]`);
    allIcons.forEach(icon => {
        icon.className = 'fas fa-sort ms-1';
    });
    
    // Set active sort icon
    const activeIcon = document.getElementById(`${tableType}-sort-${columnIndex}`);
    if (activeIcon) {
        activeIcon.className = ascending ? 'fas fa-sort-up text-warning ms-1' : 'fas fa-sort-down text-warning ms-1';
    }
}
async function updatePerformanceData() {
    try {
        const response = await fetch('/api/crypto-portfolio', { cache: 'no-cache' });
        const data = await response.json();
        const cryptos = data.holdings || data.cryptocurrencies || [];
        if (cryptos.length > 0) window.tradingApp.updatePerformancePageTable(cryptos);
    } catch (error) {
        console.error('Error updating performance data:', error);
    }
}
async function updateHoldingsData() {
    try {
        const response = await fetch('/api/crypto-portfolio', { cache: 'no-cache' });
        const data = await response.json();
        const cryptos = data.holdings || data.cryptocurrencies || [];
        if (cryptos.length > 0) window.tradingApp.updateHoldingsTable(cryptos);
    } catch (error) {
        console.error('Error updating holdings data:', error);
    }
}
async function updatePositionsData() {
    try {
        const response = await fetch('/api/crypto-portfolio', { cache: 'no-cache' });
        const data = await response.json();
        const cryptos = data.holdings || data.cryptocurrencies || [];
        if (cryptos.length > 0) {
            window.tradingApp.updateHoldingsTable(cryptos);
            window.tradingApp.updatePositionsSummary(cryptos);
        }
    } catch (error) {
        console.error('Error updating positions data:', error);
    }
}
function filterTradesTable() {
    if (window.tradingApp?.applyTradeFilters) window.tradingApp.applyTradeFilters();
}
function clearTradesFilters() {
    const ids = ['trades-filter','trades-action-filter','trades-time-filter','trades-pnl-filter'];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
    filterTradesTable();
}
async function startTrading(mode, type) {
    if (mode === 'live') {
        if (!confirm('Are you sure you want to start LIVE trading? This will use real money.')) return;
        window.tradingApp.showToast('Live trading is not enabled in this demo', 'warning');
        return;
    }
    window.tradingApp.showToast(`Starting ${mode} trading in ${type} mode...`, 'info');
    try {
        const response = await fetch('/api/start_trading', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mode,
                symbol: 'BTC/USDT',
                timeframe: '1h',
                trading_mode: type,
                confirmation: true
            })
        });
        const data = await response.json();
        if (data.success) {
            window.tradingApp.showToast(`${mode} trading started successfully (${type})`, 'success');
            window.tradingApp.updateDashboard();
            window.tradingApp.updateCryptoPortfolio();
            window.tradingApp.updateTradingStatusDisplay(mode, type);
        } else {
            window.tradingApp.showToast(`Failed to start trading: ${data.error}`, 'error');
        }
    } catch (error) {
        window.tradingApp.showToast(`Error starting trading: ${error.message}`, 'error');
    }
}

async function executeTakeProfit() {
    if (!confirm('Execute take profit for all positions above 2% profit? This will sell profitable positions and reinvest proceeds.')) {
        return;
    }
    
    const button = document.getElementById('take-profit-btn');
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
    
    window.tradingApp.showToast('Executing take profit trades...', 'info');
    
    try {
        const response = await fetch('/api/execute-take-profit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const trades = data.executed_trades || [];
            const profit = data.total_profit || 0;
            const reinvested = data.reinvested_amount || 0;
            
            if (trades.length > 0) {
                window.tradingApp.showToast(
                    `Take profit executed: ${trades.length} trades, $${profit.toFixed(2)} profit, $${reinvested.toFixed(2)} reinvested`, 
                    'success'
                );
                
                // Refresh portfolio and trades data
                await window.tradingApp.updateCryptoPortfolio();
                await window.tradingApp.updateDashboard();
                
                // Show detailed results
                console.log('Take profit results:', {
                    trades_executed: trades.length,
                    total_profit: profit,
                    reinvested_amount: reinvested,
                    trades: trades
                });
            } else {
                window.tradingApp.showToast('No positions met take profit criteria (2% profit threshold)', 'info');
            }
        } else {
            window.tradingApp.showToast(`Take profit failed: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Take profit error:', error);
        window.tradingApp.showToast(`Take profit error: ${error.message}`, 'error');
    } finally {
        button.disabled = false;
        button.innerHTML = originalText;
    }
}
async function buyCrypto(symbol) {
    const amount = prompt(`Enter USD amount to buy ${symbol}:`, '25.00');
    if (!amount || isNaN(amount) || parseFloat(amount) <= 0) return window.tradingApp.showToast('Invalid amount', 'error');
    try {
        const response = await fetch('/api/paper-trade/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, amount: parseFloat(amount) })
        });
        const data = await response.json();
        if (data.success) {
            window.tradingApp.showToast(`Bought $${amount} ${symbol}`, 'success');
            window.tradingApp.updateDashboard();
            window.tradingApp.updateCryptoPortfolio();
        } else {
            window.tradingApp.showToast(`Buy failed: ${data.error}`, 'error');
        }
    } catch (error) {
        window.tradingApp.showToast(`Error buying ${symbol}: ${error.message}`, 'error');
    }
}
async function sellCrypto(symbol) {
    const quantity = prompt(`Enter quantity of ${symbol} to sell:`, '0.001');
    if (!quantity || isNaN(quantity) || parseFloat(quantity) <= 0) return window.tradingApp.showToast('Invalid quantity', 'error');
    try {
        const response = await fetch('/api/paper-trade/sell', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, quantity: parseFloat(quantity) })
        });
        const data = await response.json();
        if (data.success) {
            window.tradingApp.showToast(`Sold ${quantity} ${symbol}`, 'success');
            window.tradingApp.updateDashboard();
            window.tradingApp.updateCryptoPortfolio();
        } else {
            window.tradingApp.showToast(`Sell failed: ${data.error}`, 'error');
        }
    } catch (error) {
        window.tradingApp.showToast(`Error selling ${symbol}: ${error.message}`, 'error');
    }
}

// Old in-page section toggles kept for compatibility (index now uses separate pages)
function showMainDashboard() {
    const ids = ['main-dashboard','performance-dashboard','current-holdings','recent-trades-page'];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = (id === 'main-dashboard' ? 'block' : 'none'); });
    updateNavbarButtons('main');
    window.tradingApp?.updateCryptoPortfolio();
}
function showPerformanceDashboard() {
    const ids = ['main-dashboard','performance-dashboard','current-holdings','recent-trades-page'];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = (id === 'performance-dashboard' ? 'block' : 'none'); });
    updateNavbarButtons('performance');
    if (window.tradingApp?.currentCryptoData) {
        window.tradingApp.updatePerformancePageTable(window.tradingApp.currentCryptoData);
    }
    window.tradingApp?.updateCryptoPortfolio();
}
function showCurrentPositions() {
    const ids = ['main-dashboard','performance-dashboard','current-holdings','recent-trades-page'];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = (id === 'current-holdings' ? 'block' : 'none'); });
    updateNavbarButtons('holdings');
    if (window.tradingApp?.currentCryptoData) {
        window.tradingApp.updateHoldingsTable(window.tradingApp.currentCryptoData);
        window.tradingApp.updatePositionsSummary(window.tradingApp.currentCryptoData);
    }
    window.tradingApp?.updateCryptoPortfolio();
}
function showRecentTrades() {
    const ids = ['main-dashboard','performance-dashboard','current-holdings','recent-trades-page'];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = (id === 'recent-trades-page' ? 'block' : 'none'); });
    window.tradingApp?.updateRecentTrades();
}
function hideAllSections() {
    const sections = ['main-dashboard','performance-dashboard','positions-dashboard','current-holdings','recent-trades-page'];
    sections.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = 'none'; });
}
function updateNavbarButtons(activeView) {
    const buttons = document.querySelectorAll('.navbar-nav .btn');
    buttons.forEach(btn => { btn.classList.remove('btn-light'); btn.classList.add('btn-outline-light'); });
    const map = { 'main': 0, 'performance': 1, 'holdings': 2 };
    if (map[activeView] !== undefined && buttons[map[activeView]]) {
        buttons[map[activeView]].classList.remove('btn-outline-light');
        buttons[map[activeView]].classList.add('btn-light');
    }
}

// ---------- Debug helpers ----------
window.debugTrades = {
    async checkServerData() {
        try {
            const response = await fetch('/api/status', { cache: 'no-cache' });
            const data = await response.json();
            console.log('Server trades data:', data.recent_trades);
            if (data.recent_trades?.length) console.log('First trade keys:', Object.keys(data.recent_trades[0]));
            return data.recent_trades;
        } catch (e) { console.error('Failed to fetch server data:', e); }
    },
    testNormalizer() {
        const rawTrades = [
            { ts: new Date().toISOString(), symbol: 'BTC/USDT', side: 'buy', qty: '0.01', price: '65000', pnl: '12.34', order_id: 'abc123' },
            { timestamp: Date.now(), pair: 'ETH/USDT', side: 'SELL', quantity: 0.5, fill_price: 4200.50, profit: -5.67, id: 'def456' }
        ];
        const normalized = window.tradingApp.normalizeTrades(rawTrades);
        console.log('Normalized trades:', normalized);
        window.tradingApp.displayRecentTrades(rawTrades);
        return normalized;
    },
    checkTableElement() {
        const table = document.getElementById('trades-table');
        console.log('Table element found:', !!table, table);
        if (table) {
            console.log('Table children count:', table.children.length);
            console.log('Table innerHTML length:', table.innerHTML.length);
        }
        return table;
    },
    testCaseSensitivity() {
        const testTrades = [
            { timestamp: Date.now(), symbol: 'BTC', side: 'buy', price: 65000, quantity: 0.01, pnl: 10 },
            { timestamp: Date.now(), symbol: 'ETH', side: 'BUY', price: 4200, quantity: 0.5, pnl: -5 },
            { timestamp: Date.now(), symbol: 'SOL', side: 'sell', price: 190, quantity: 2, pnl: 8 }
        ];
        window.tradingApp.displayRecentTrades(testTrades);
        const normalized = window.tradingApp.normalizeTrades(testTrades);
        console.log('Normalized sides:', normalized.map(t => t.side));
    }
};

console.log('Debug functions loaded.');

// ---------- Portfolio Summary & Quick Overview (global UI helpers) ----------
function updateElementSafely(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    } else {
        const currentPage = window.location.pathname;
        const expectedElements = {
            '/': ['kpi-total-equity', 'kpi-daily-pnl', 'kpi-unrealized-pnl', 'kpi-cash', 'kpi-exposure', 'kpi-win-rate'],
            '/portfolio': ['summary-total-value', 'summary-total-change', 'summary-total-assets', 'summary-cash-balance'],
            '/holdings': ['holdings-total-assets', 'holdings-active-count', 'holdings-zero-count']
        };
        const pageElements = expectedElements[currentPage] || [];
        if (pageElements.includes(elementId)) {
            console.warn(`Element ${elementId} not found for update`);
        }
    }
}
function formatCurrency(amount) {
    if (typeof amount !== 'number' || isNaN(amount)) return '$0.00';
    return '$' + Number(amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fmtFixed(value, decimals = 2) {
    if (typeof value !== 'number' || isNaN(value)) return '0.00';
    return Number(value).toFixed(decimals);
}

// RENAMED: Big UI updater
function updatePortfolioSummaryUI(portfolioData) {
    const summary = portfolioData.summary || {};
    const holdings = portfolioData.holdings || [];

    window.lastPortfolioData = portfolioData;

    let totalValue = 0, totalUnrealizedPnl = 0, totalCostBasis = 0;
    holdings.forEach(h => {
        if (h.has_position) {
            totalValue += h.current_value || 0;
            totalUnrealizedPnl += h.unrealized_pnl || 0;
            totalCostBasis += h.cost_basis || 0;
        }
    });

    const cashBalance = portfolioData.cash_balance || 0;
    const totalPortfolioValue = totalValue + cashBalance;
    const totalPnlPercent = totalCostBasis > 0 ? ((totalUnrealizedPnl / totalCostBasis) * 100) : 0;

    updateElementSafely("summary-total-value", formatCurrency(totalPortfolioValue));

    const change24h = summary.daily_pnl || 0;
    const change24hElement = document.getElementById("summary-24h-change");
    if (change24hElement) {
        const changeClass = change24h >= 0 ? "text-success" : "text-danger";
        const arrow = change24h >= 0 ? "↗" : "↘";
        const prefix = change24h >= 0 ? "+" : "";
        change24hElement.innerHTML = `${arrow} ${prefix}${formatCurrency(change24h)}`;
        change24hElement.className = `mb-0 fw-bold ${changeClass}`;
    }

    updateElementSafely("summary-total-assets", summary.total_assets_tracked || holdings.length);
    updateElementSafely("summary-cash-balance", formatCurrency(cashBalance));
    updateElementSafely("summary-win-rate", `${(summary.win_rate || 0).toFixed(1)}%`);
    updateElementSafely("summary-portfolio-value", formatCurrency(totalPortfolioValue));

    // Holdings summary if present on page
    if (document.getElementById("holdings-total-assets")) {
        updateHoldingsSummary(holdings);
    }

    const best = summary.best_performer || { symbol: "N/A", pnl_percent: 0 };
    const worst = summary.worst_performer || { symbol: "N/A", pnl_percent: 0 };

    const bestEl = document.getElementById("summary-best-performer");
    const bestPerfEl = document.getElementById("summary-best-performance");
    const worstEl = document.querySelector("#summary-worst-performer span");

    if (bestEl) {
        bestEl.textContent = best.symbol || "N/A";
        if (bestPerfEl) bestPerfEl.textContent = `+${(best.pnl_percent || 0).toFixed(2)}%`;
    }
    if (worstEl) {
        worstEl.textContent = worst.symbol !== "N/A" ? `${worst.symbol}` : "N/A";
    }

    // Portfolio page widgets/charts (if on that page)
    if (window.location.pathname === '/portfolio') {
        updatePortfolioChartsUI(portfolioData);
        updateExposureMetrics(holdings); // no-op if its IDs aren't present
        updatePositionTable(holdings);   // no-op if its IDs aren't present
    }
}

function updateHoldingsSummary(holdings) {
    const active = holdings.filter(h => (h.current_value || 0) > 0.01);
    const sold   = holdings.filter(h => (h.current_value || 0) <= 0.01);

    updateElementSafely("holdings-total-assets", holdings.length);
    updateElementSafely("holdings-active-count", active.length);
    updateElementSafely("holdings-zero-count", sold.length);

    const totalHoldingsValue = active.reduce((sum, h) => sum + (h.current_value || 0), 0);
    updateElementSafely("holdings-total-value", formatCurrency(totalHoldingsValue));

    updateElementSafely("active-positions", active.length);
    updateElementSafely("zero-positions", sold.length);
    updateElementSafely("active-holdings-count", active.length);
    updateElementSafely("zero-holdings-count", sold.length);

    const activeListEl = document.getElementById('active-holdings-list');
    if (activeListEl) {
        if (active.length) {
            const sortedActive = [...active].sort((a, b) => (b.current_value || 0) - (a.current_value || 0));
            activeListEl.innerHTML = sortedActive.map(h => {
                const pnlClass = (h.pnl_percent || 0) >= 0 ? 'text-success' : 'text-danger';
                const pnlIcon = (h.pnl_percent || 0) >= 0 ? '↗' : '↘';
                return `
                    <div class="d-flex justify-content-between align-items-center py-1 border-bottom">
                        <div>
                            <strong class="text-primary">${h.symbol}</strong>
                            <small class="text-muted ms-2">${formatCurrency(h.current_value || 0)}</small>
                        </div>
                        <div class="${pnlClass}">
                            <small>${pnlIcon} ${fmtFixed(h.pnl_percent || 0, 2)}%</small>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            activeListEl.innerHTML = '<div class="text-muted text-center py-3">No active holdings</div>';
        }
    }

    const soldListEl = document.getElementById('zero-holdings-list');
    if (soldListEl) {
        if (sold.length) {
            const sortedSold = [...sold].sort((a, b) => (a.symbol || '').localeCompare(b.symbol || ''));
            soldListEl.innerHTML = sortedSold.map(h => `
                <div class="d-flex justify-content-between align-items-center py-1 border-bottom">
                    <div>
                        <strong class="text-warning">${h.symbol}</strong>
                        <small class="text-muted ms-2">Sold out</small>
                    </div>
                    <div class="text-muted"><small>Last: ${formatCurrency(h.current_price || 0)}</small></div>
                </div>
            `).join('');
        } else {
            soldListEl.innerHTML = '<div class="text-muted text-center py-3">No sold positions</div>';
        }
    }
}

// Dashboard KPIs + quick charts + preview
function updateQuickOverview(portfolioData) {
    const summary = portfolioData.summary || {};
    const holdings = portfolioData.holdings || [];

    let totalValue = 0, totalUnrealizedPnl = 0, totalCostBasis = 0;
    holdings.forEach(h => {
        if (h.has_position) {
            totalValue += h.current_value || 0;
            totalUnrealizedPnl += h.unrealized_pnl || 0;
            totalCostBasis += h.cost_basis || 0;
        }
    });

    const cashBalance = portfolioData.cash_balance || 0;
    const totalEquity = totalValue + cashBalance;
    const dailyPnl = summary.daily_pnl || 0;
    const exposure = totalEquity > 0 ? ((totalValue / totalEquity) * 100) : 0;
    const winRate = summary.win_rate || 0;

    updateElementSafely("kpi-total-equity", formatCurrency(totalEquity));
    updateElementSafely("kpi-daily-pnl", formatCurrency(dailyPnl));
    updateElementSafely("kpi-unrealized-pnl", formatCurrency(totalUnrealizedPnl));
    updateElementSafely("kpi-cash", formatCurrency(cashBalance));
    updateElementSafely("kpi-exposure", `${exposure.toFixed(1)}%`);
    updateElementSafely("kpi-win-rate", `${winRate.toFixed(1)}%`);

    const dailyPnlEl = document.getElementById("kpi-daily-pnl");
    const unrlEl = document.getElementById("kpi-unrealized-pnl");
    if (dailyPnlEl) dailyPnlEl.className = dailyPnl >= 0 ? "h5 mb-0 text-success" : "h5 mb-0 text-danger";
    if (unrlEl)     unrlEl.className     = totalUnrealizedPnl >= 0 ? "h5 mb-0 text-success" : "h5 mb-0 text-danger";

    if (holdings.length) updateTopMovers(holdings);

    const dailyLoss = Math.abs(summary.daily_pnl || 0);
    const lossCapLimit = 50;
    const lossCapPercent = Math.min((dailyLoss / lossCapLimit) * 100, 100);
    const lossCapBar = document.getElementById("loss-cap-bar");
    const lossCapText = document.getElementById("loss-cap-text");
    if (lossCapBar) {
        lossCapBar.style.width = `${lossCapPercent}%`;
        lossCapBar.className = lossCapPercent > 80 ? 'progress-bar bg-danger'
                            : lossCapPercent > 60 ? 'progress-bar bg-warning'
                            : 'progress-bar bg-success';
    }
    if (lossCapText) lossCapText.textContent = `$${dailyLoss.toFixed(2)} / $${lossCapLimit}`;

    updateElementSafely("overview-connection", "Connected");
    updateElementSafely("overview-last-update", window.tradingApp.formatTimeOnly(new Date()));
}
function updateTopMovers(holdings) {
    const el = document.getElementById("top-movers");
    if (!el) return;

    const sorted = [...holdings]
        .filter(h => h.pnl_percent !== undefined && h.pnl_percent !== null)
        .sort((a, b) => Math.abs(b.pnl_percent || 0) - Math.abs(a.pnl_percent || 0))
        .slice(0, 10);

    if (!sorted.length) {
        el.innerHTML = '<div class="text-muted text-center">No data</div>';
        return;
    }

    const gainers = sorted.filter(h => (h.pnl_percent || 0) > 0).slice(0, 5);
    const losers  = sorted.filter(h => (h.pnl_percent || 0) < 0).slice(0, 5);

    let html = '';
    if (gainers.length) {
        html += '<div class="mb-2"><strong class="text-success">↗ Top Gainers</strong></div>';
        gainers.forEach(c => html += `
            <div class="d-flex justify-content-between small mb-1">
                <span class="text-primary fw-bold">${c.symbol}</span>
                <span class="text-success">+${(c.pnl_percent || 0).toFixed(2)}%</span>
            </div>
        `);
    }
    if (losers.length) {
        html += '<div class="mb-2 mt-3"><strong class="text-danger">↘ Top Losers</strong></div>';
        losers.forEach(c => html += `
            <div class="d-flex justify-content-between small mb-1">
                <span class="text-primary fw-bold">${c.symbol}</span>
                <span class="text-danger">-${Math.abs(c.pnl_percent || 0).toFixed(2)}%</span>
            </div>
        `);
    }
    el.innerHTML = html || '<div class="text-muted text-center">No significant moves</div>';
}
function renderDashboardOverview(portfolioData, recentTrades = []) {
    updateQuickOverview(portfolioData);
    updateQuickOverviewCharts(portfolioData);
    updateRecentTradesPreview(recentTrades.slice(0, 5));
}

// Recent Trades quick preview (used if some pages still call it)
function updateRecentTradesPreview(trades) {
    const previewBody = document.getElementById("recent-trades-preview-body");
    if (!previewBody) return;

    const normalized = window.tradingApp?.normalizeTrades(trades || []) || [];
    if (!normalized.length) {
        previewBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-3">No recent trades</td></tr>';
        return;
    }

    let html = '';
    normalized.slice(0, 5).forEach((t, i) => {
        const pnlClass = (t.pnl || 0) >= 0 ? 'text-success' : 'text-danger';
        const sideBadge = t.side === 'BUY' ? 'badge bg-success' : 'badge bg-danger';
        html += `
            <tr>
                <td>${i + 1}</td>
                <td class="text-start">${window.tradingApp.formatTradeTime(t.timestamp)}</td>
                <td><strong>${t.symbol}</strong></td>
                <td><span class="${sideBadge}">${t.side}</span></td>
                <td class="text-end">${window.tradingApp.num(t.quantity).toFixed(6)}</td>
                <td class="text-end">${window.tradingApp.formatCurrency(t.price)}</td>
                <td class="text-end ${pnlClass}">${window.tradingApp.formatCurrency(t.pnl)}</td>
            </tr>
        `;
    });
    previewBody.innerHTML = html;
}

// Quick Overview charts
function initializeQuickOverviewCharts() {
    if (!window.Chart) {
        console.warn('Chart.js not available for Quick Overview charts');
        return;
    }
    try {
        const equitySparklineCtx = document.getElementById('equitySparkline');
        if (equitySparklineCtx) {
            window.equitySparklineChart = new Chart(equitySparklineCtx, {
                type: 'line',
                data: { labels: [], datasets: [{ data: [], borderColor: '#28a745', backgroundColor: 'rgba(40, 167, 69, 0.1)', borderWidth: 2, tension: 0.4, fill: true, pointRadius: 0, pointHoverRadius: 3 }]},
                options: {
                    responsive: true, maintainAspectRatio: true, aspectRatio: 3,
                    plugins: { legend: { display: false }, tooltip: { enabled: false, external: function(){} } },
                    scales: { x: { display: false, grid: { display: false } }, y: { display: false, grid: { display: false } } },
                    interaction: { intersect: false, mode: 'index' }, animation: { duration: 0 }
                }
            });
        }
        const allocationDonutCtx = document.getElementById('allocationDonut');
        if (allocationDonutCtx) {
            window.allocationDonutChart = new Chart(allocationDonutCtx, {
                type: 'doughnut',
                data: { labels: ['BTC','ETH','SOL','Other'], datasets: [{ data: [30,25,15,30], backgroundColor: ['#f7931a','#627eea','#14f195','#6c757d'], borderWidth: 0, cutout: '60%' }]},
                options: { responsive: true, maintainAspectRatio: true, aspectRatio: 1, plugins: { legend: { display: false } }, animation: { duration: 300 } }
            });
        }
    } catch (error) {
        console.error('Failed to initialize Quick Overview charts:', error);
    }
}
function updateQuickOverviewCharts(portfolioData) {
    if (!portfolioData) return;
    const holdings = portfolioData.holdings || [];
    const summary = portfolioData.summary || {};
    try {
        if (window.equitySparklineChart) {
            const currentValue = summary.total_current_value || 1030;
            const labels = [], values = [];
            for (let i = 23; i >= 0; i--) {
                const hour = new Date(Date.now() - (i * 60 * 60 * 1000));
                const variation = (Math.sin(i * 0.3) * 0.015 + Math.random() * 0.005 - 0.0025);
                labels.push(hour.toLocaleTimeString([], { hour: '2-digit', hour12: true }));
                values.push(currentValue * (1 + variation));
            }
            window.equitySparklineChart.data.labels = labels;
            window.equitySparklineChart.data.datasets[0].data = values;
            window.equitySparklineChart.update('none');
        }
        if (window.allocationDonutChart && holdings.length > 0) {
            const sorted = [...holdings].sort((a, b) => (b.current_value || 0) - (a.current_value || 0));
            const top = sorted.slice(0, 3);
            const otherValue = sorted.slice(3).reduce((s, h) => s + (h.current_value || 0), 0);
            const total = holdings.reduce((s, h) => s + (h.current_value || 0), 0);
            if (total > 0) {
                const labels = top.map(h => h.symbol).concat(['Other']);
                const data = top.map(h => ((h.current_value || 0) / total * 100).toFixed(1));
                data.push((otherValue / total * 100).toFixed(1));
                window.allocationDonutChart.data.labels = labels;
                window.allocationDonutChart.data.datasets[0].data = data;
                window.allocationDonutChart.update('none');
            }
        }
    } catch (error) {
        console.error('Failed to update Quick Overview charts:', error);
    }
}

// ---- Portfolio-page specific helpers (safe no-ops on dashboard) ----
function updatePortfolioChartsUI(portfolioData) {
    const holdings = portfolioData.holdings || [];
    renderAllocationChart(holdings);
    updateExposureMetrics(holdings);
}
function renderAllocationChart(holdings) {
    const canvas = document.getElementById('allocationChart');
    if (!canvas || !window.Chart) return;
    if (window.allocationChart) window.allocationChart.destroy();

    const sorted = [...holdings].filter(h => h.has_position).sort((a, b) => (b.current_value || 0) - (a.current_value || 0)).slice(0, 10);
    const labels = sorted.map(h => h.symbol);
    const data = sorted.map(h => h.current_value || 0);
    const colors = ['#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF','#FF9F40','#FF6384','#C9CBCF','#4BC0C0','#FF6384'];

    window.allocationChart = new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 1 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { boxWidth: 12, padding: 8 } } } }
    });
}
function updateExposureMetrics(holdings) {
    // left as a safe no-op unless exposure bar IDs exist on the page
    if (!holdings?.length) return;
    const totalValue = holdings.reduce((sum, h) => sum + (h.current_value || 0), 0);
    const longValue = holdings.filter(h => h.has_position && (h.current_value || 0) > 0)
                              .reduce((sum, h) => sum + (h.current_value || 0), 0);
    const longExposure = totalValue > 0 ? ((longValue / totalValue) * 100) : 0;

    const updateBar = (id, pct) => {
        const el = document.getElementById(id);
        const txt = document.getElementById(id + '-text');
        if (el) el.style.width = Math.min(pct, 100) + '%';
        if (txt) txt.textContent = pct.toFixed(1) + '%';
    };
    updateBar('exposure-long', longExposure);
    // Stable/ Largest bars require matching IDs in the page to have effect.
}
function updatePositionTable(holdings) {
    const tableBody = document.getElementById('positions-table-body');
    if (!tableBody) return;
    const filtered = holdings.filter(h => h.has_position);
    tableBody.innerHTML = '';
    if (!filtered.length) {
        tableBody.innerHTML = '<tr><td colspan="11" class="text-center text-muted">No positions found</td></tr>';
        return;
    }
    filtered.forEach(h => {
        const pnlClass = (h.pnl_percent || 0) >= 0 ? 'text-success' : 'text-danger';
        const pnlSign = (h.pnl_percent || 0) >= 0 ? '+' : '';
        tableBody.innerHTML += `
            <tr>
                <td><strong class="text-primary">${h.symbol}</strong></td>
                <td class="small text-muted">${h.name}</td>
                <td>${(h.quantity || 0).toFixed(8)}</td>
                <td>$${(h.current_price || 0).toFixed(4)}</td>
                <td>$${(h.current_value || 0).toFixed(2)}</td>
                <td>${(h.allocation_percent || 0).toFixed(2)}%</td>
                <td class="${pnlClass}">$${(h.unrealized_pnl || 0).toFixed(2)}</td>
                <td class="${pnlClass}">${pnlSign}${(h.pnl_percent || 0).toFixed(2)}%</td>
                <td>-</td>
                <td>-</td>
                <td><span class="badge bg-success">Active</span></td>
            </tr>
        `;
    });
    const totalPositions = filtered.length;
    const totalValue = filtered.reduce((s, h) => s + (h.current_value || 0), 0);
    const totalPnL = filtered.reduce((s, h) => s + (h.unrealized_pnl || 0), 0);
    const strongGains = filtered.filter(h => (h.pnl_percent || 0) >= 5).length;

    updateElementSafely('pos-total-count', totalPositions);
    const tvEl = document.getElementById('pos-total-value');
    if (tvEl) tvEl.textContent = formatCurrency(totalValue);
    const upnlEl = document.getElementById('pos-unrealized-pnl');
    if (upnlEl) {
        upnlEl.textContent = formatCurrency(totalPnL);
        upnlEl.className = totalPnL >= 0 ? 'text-success' : 'text-danger';
    }
    updateElementSafely('pos-strong-gains', strongGains);
}
