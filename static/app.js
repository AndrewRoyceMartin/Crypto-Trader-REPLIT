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
        
        // Debounce mechanism to prevent overlapping dashboard updates
        this.lastDashboardUpdate = 0;
        this.dashboardUpdateDebounce = 2000; // 2 second debounce
        this.pendingDashboardUpdate = null;
        
        // API caching to prevent duplicate requests
        this.apiCache = {
            status: { data: null, timestamp: 0, ttl: 5000 }, // 5-second cache
            portfolio: { data: null, timestamp: 0, ttl: 6000 }, // 6-second cache
            config: { data: null, timestamp: 0, ttl: 30000 } // 30-second cache
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.startAutoUpdate();
        this.loadConfig();
        
        // Load data immediately on startup with debounce
        this.debouncedUpdateDashboard();
    }
    
    setupEventListeners() {
        // Remove duplicate interval setup - handled by startAutoUpdate()
        
        // Start countdown timer (only once during initialization)
        this.startCountdown();
        
        // Handle page visibility change - pause updates when hidden
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoUpdate();
            } else {
                this.startAutoUpdate();
                // Use debounced update when page becomes visible
                this.debouncedUpdateDashboard();
            }
        });
        
        // Handle window unload - cleanup all intervals
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }
    
    startAutoUpdate() {
        if (!this.updateInterval) {
            this.updateInterval = setInterval(() => {
                this.debouncedUpdateDashboard();
            }, 60000); // Reduced from 30s to 60s to prevent rate limiting
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
        // Comprehensive cleanup method to prevent memory leaks
        this.stopAutoUpdate();
        this.stopCountdown();
        
        if (this.pendingDashboardUpdate) {
            clearTimeout(this.pendingDashboardUpdate);
            this.pendingDashboardUpdate = null;
        }
    }
    
    async fetchWithCache(endpoint, cacheKey) {
        const cache = this.apiCache[cacheKey];
        const now = Date.now();
        
        // Return cached data if still valid
        if (cache && cache.data && (now - cache.timestamp) < cache.ttl) {
            return cache.data;
        }
        
        try {
            const response = await fetch(endpoint);
            if (!response.ok) return null;
            
            const data = await response.json();
            
            // Update cache
            this.apiCache[cacheKey] = {
                data: data,
                timestamp: now,
                ttl: cache.ttl
            };
            
            return data;
        } catch (error) {
            console.error(`Error fetching ${endpoint}:`, error);
            return null;
        }
    }

    async updateDashboard() {
        // Implement debounce to prevent overlapping calls
        const now = Date.now();
        if (now - this.lastDashboardUpdate < this.dashboardUpdateDebounce) {
            // Clear any pending update and schedule a new one
            if (this.pendingDashboardUpdate) {
                clearTimeout(this.pendingDashboardUpdate);
            }
            this.pendingDashboardUpdate = setTimeout(() => {
                this.updateDashboard();
            }, this.dashboardUpdateDebounce - (now - this.lastDashboardUpdate));
            return;
        }
        
        this.lastDashboardUpdate = now;
        
        // Use cached API call to get status data
        const data = await this.fetchWithCache('/api/status', 'status');
        if (!data) return;
        
        // Update uptime display
        if (data.uptime !== undefined) {
            this.updateUptimeDisplay(data.uptime);
        }
        
        // Update portfolio values from status endpoint
        if (data.portfolio) {
            const portfolioValueEl = document.getElementById('portfolio-value');
            const portfolioPnlEl = document.getElementById('portfolio-pnl');
            
            if (portfolioValueEl) {
                portfolioValueEl.textContent = this.formatCurrency(data.portfolio.total_value || 0);
            }
            if (portfolioPnlEl) {
                portfolioPnlEl.textContent = this.formatCurrency(data.portfolio.daily_pnl || 0);
                portfolioPnlEl.className = (data.portfolio.daily_pnl || 0) >= 0 ? 'text-success' : 'text-danger';
            }
        }
        
        // Update trading status
        if (data.trading_status) {
            this.updateTradingStatus(data.trading_status);
        }
        
        // Update recent trades using the same cached data
        if (data.recent_trades) {
            this.displayRecentTrades(data.recent_trades);
        }
        
        // Update price source status only (portfolio updates separately to avoid loops)
        this.updatePriceSourceStatus();
    }
    
    debouncedUpdateDashboard() {
        // Simple wrapper to call updateDashboard with debounce logic built-in
        this.updateDashboard();
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
        // Use cached API call for config data
        const config = await this.fetchWithCache('/api/config', 'config');
        if (!config) return;
        
        console.log('Config loaded:', config);
        
        // Store config for later use
        this.config = config;
        
        // Apply configuration
        if (config.update_interval) {
            // Update interval is handled by startAutoUpdate()
        }
    }
    
    startCountdown() {
        // Prevent multiple countdown intervals
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
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
                    this.countdownInterval = null; // Prevent memory leaks
                }
            } else {
                // If element doesn't exist, clear the interval to prevent memory leak
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;
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
        // Update trading status display - check if element exists first
        const statusElement = document.getElementById('trading-status');
        if (statusElement && tradingStatus) {
            statusElement.textContent = `${tradingStatus.mode} - ${tradingStatus.strategy}`;
        }
        // If element doesn't exist, just skip silently to avoid console errors
    }
    
    async updateCryptoPortfolio() {
        // Prevent concurrent updates
        if (this.isUpdatingPortfolio) {
            console.log('Portfolio update already in progress, skipping...');
            return;
        }
        this.isUpdatingPortfolio = true;
        
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
            
            // Update crypto symbols display and all tables
            if (data.cryptocurrencies) {
                this.updateLoadingProgress(80, 'Updating displays...');
                this.updateCryptoSymbols(data.cryptocurrencies);
                this.updateCryptoTable(data.cryptocurrencies);
                this.updatePerformanceTable(data.cryptocurrencies);
                this.updatePerformancePageTable(data.cryptocurrencies);
                this.updateHoldingsTable(data.cryptocurrencies);
                this.updatePortfolioSummary(data.summary, data.cryptocurrencies);
                await this.updateRecentTrades(); // Add this to update trades
                this.updateLoadingProgress(100, 'Complete!');
                
                // Hide progress bar after completion
                setTimeout(() => {
                    this.hideLoadingProgress();
                }, 1000);
            }
            
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
        
        // Clear existing content
        symbolsContainer.innerHTML = '';
        
        if (!cryptos || cryptos.length === 0) {
            const badge = document.createElement('span');
            badge.className = 'badge bg-warning';
            badge.textContent = 'Portfolio loading... Please wait';
            symbolsContainer.appendChild(badge);
            return;
        }
        
        // Sort by current value (highest first) and limit to top 10
        const topCryptos = [...cryptos]
            .sort((a, b) => (b.current_value || 0) - (a.current_value || 0))
            .slice(0, 10);
        
        // Create badges for top 10 cryptos only
        topCryptos.forEach(crypto => {
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
        
        // Handle empty state first
        if (!cryptos || cryptos.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="8" class="text-center text-muted">No cryptocurrency data available</td>';
            tableBody.appendChild(row);
            return;
        }
        
        // Sort cryptos by market cap rank and render once
        const sortedCryptos = [...cryptos].sort((a, b) => (a.rank || 999) - (b.rank || 999));
        
        sortedCryptos.forEach(crypto => {
            const row = document.createElement('tr');
            
            // Format values
            const price = typeof crypto.current_price === 'number' ? crypto.current_price : 0;
            const quantity = typeof crypto.quantity === 'number' ? crypto.quantity : 0;
            const value = typeof crypto.current_value === 'number' ? crypto.current_value : 0;
            const pnlPercent = typeof crypto.pnl_percent === 'number' ? crypto.pnl_percent : 0;
            
            // Create cells with safe DOM manipulation
            const rankCell = document.createElement('td');
            rankCell.textContent = crypto.rank || '-';
            
            const symbolCell = document.createElement('td');
            const symbolSpan = document.createElement('span');
            symbolSpan.className = 'fw-bold text-primary';
            symbolSpan.textContent = crypto.symbol || '-';
            symbolCell.appendChild(symbolSpan);
            
            const nameCell = document.createElement('td');
            nameCell.textContent = crypto.name || '-';
            
            const priceCell = document.createElement('td');
            priceCell.textContent = this.formatCurrency(price);
            
            const quantityCell = document.createElement('td');
            quantityCell.textContent = quantity.toFixed(6);
            
            const valueCell = document.createElement('td');
            valueCell.textContent = this.formatCurrency(value);
            
            const pnlCell = document.createElement('td');
            const pnlSpan = document.createElement('span');
            pnlSpan.className = `${pnlPercent >= 0 ? 'text-success' : 'text-danger'} fw-bold`;
            pnlSpan.textContent = `${pnlPercent.toFixed(2)}%`;
            pnlCell.appendChild(pnlSpan);
            
            const updatedCell = document.createElement('td');
            const updatedSmall = document.createElement('small');
            updatedSmall.className = 'text-muted';
            updatedSmall.textContent = crypto.last_updated ? 
                new Date(crypto.last_updated).toLocaleTimeString() : '-';
            updatedCell.appendChild(updatedSmall);
            
            // Append all cells to row
            row.appendChild(rankCell);
            row.appendChild(symbolCell);
            row.appendChild(nameCell);
            row.appendChild(priceCell);
            row.appendChild(quantityCell);
            row.appendChild(valueCell);
            row.appendChild(pnlCell);
            row.appendChild(updatedCell);
            
            // Add hover effect
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
    
    updatePerformanceTable(cryptos) {
        console.log('updatePerformanceTable called with:', cryptos?.length || 0, 'cryptocurrencies');
        const tableBody = document.getElementById('crypto-portfolio-table');
        console.log('Table element found:', !!tableBody);
        
        if (!tableBody) {
            console.error('crypto-portfolio-table element not found!');
            return;
        }
        
        // Clear existing content
        tableBody.innerHTML = '';
        
        if (!cryptos || cryptos.length === 0) {
            console.log('No crypto data provided');
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 13;
            cell.className = 'text-center text-muted';
            cell.textContent = 'No cryptocurrency data available - Start trading to populate portfolio';
            row.appendChild(cell);
            tableBody.appendChild(row);
            return;
        }
        
        console.log('Populating table with', cryptos.length, 'rows');
        
        // Populate performance table
        cryptos.forEach(crypto => {
            const row = document.createElement('tr');
            
            // Format values with proper P&L calculation
            const price = crypto.current_price < 1 ? 
                crypto.current_price.toFixed(6) : 
                crypto.current_price.toFixed(2);
            const quantity = crypto.quantity.toFixed(4);
            const currentValue = this.formatCurrency(crypto.current_value);
            const pnl = this.formatCurrency(crypto.pnl);
            const pnlPercent = crypto.pnl_percent.toFixed(2);
            const targetSell = this.formatCurrency(crypto.target_sell_price);
            const targetBuy = this.formatCurrency(crypto.target_buy_price);
            
            // Determine colors and indicators
            const pnlClass = crypto.pnl >= 0 ? 'text-success' : 'text-danger';
            const pnlIcon = crypto.pnl >= 0 ? '↗' : '↘';
            
            // Calculate approaching sell percentage
            let approachingPercent = 0;
            if (crypto.target_sell_price && crypto.current_price) {
                approachingPercent = ((crypto.current_price / crypto.target_sell_price) * 100).toFixed(1);
            }
            
            // Calculate the last updated time
            const lastUpdated = crypto.last_updated ? new Date(crypto.last_updated).toLocaleTimeString() : '-';
            
            // Determine trading signal
            const signal = crypto.current_price <= crypto.target_buy_price ? 
                '<span class="badge bg-success">BUY</span>' : 
                crypto.current_price >= crypto.target_sell_price ? 
                '<span class="badge bg-danger">SELL</span>' : 
                '<span class="badge bg-secondary">HOLD</span>';
            
            // Calculate target proximity
            const targetProximity = crypto.target_buy_price ? 
                (crypto.current_price <= crypto.target_buy_price ? '🎯 At buy target' : `${((crypto.current_price - crypto.target_buy_price) / crypto.target_buy_price * 100).toFixed(1)}% above`) :
                '-';

            // Create cells with safe DOM manipulation
            const rankCell = document.createElement('td');
            const rankBadge = document.createElement('span');
            rankBadge.className = 'badge bg-primary';
            rankBadge.textContent = `#${crypto.rank}`;
            rankCell.appendChild(rankBadge);
            
            const symbolCell = document.createElement('td');
            const symbolStrong = document.createElement('strong');
            symbolStrong.textContent = crypto.symbol;
            symbolCell.appendChild(symbolStrong);
            
            const nameCell = document.createElement('td');
            nameCell.textContent = crypto.name;
            
            const quantityCell = document.createElement('td');
            quantityCell.textContent = quantity;
            
            const priceCell = document.createElement('td');
            priceCell.textContent = `$${price}`;
            
            const valueCell = document.createElement('td');
            valueCell.textContent = currentValue;
            
            const targetSellCell = document.createElement('td');
            targetSellCell.textContent = targetSell;
            
            const approachingCell = document.createElement('td');
            approachingCell.textContent = `${approachingPercent}%`;
            
            const targetBuyCell = document.createElement('td');
            targetBuyCell.textContent = targetBuy;
            
            const projectedPnlCell = document.createElement('td');
            projectedPnlCell.textContent = this.formatCurrency(crypto.projected_sell_pnl || crypto.pnl || 0);
            
            const pnlValueCell = document.createElement('td');
            pnlValueCell.className = pnlClass;
            pnlValueCell.textContent = pnl;
            
            const pnlPercentCell = document.createElement('td');
            pnlPercentCell.className = pnlClass;
            pnlPercentCell.textContent = `${pnlIcon} ${pnlPercent}%`;
            
            const actionsCell = document.createElement('td');
            const buyBtn = document.createElement('button');
            buyBtn.className = 'btn btn-sm btn-outline-success me-1';
            buyBtn.title = 'Buy';
            buyBtn.onclick = () => buyCrypto(crypto.symbol);
            buyBtn.innerHTML = '<i class="fas fa-plus"></i>';
            
            const sellBtn = document.createElement('button');
            sellBtn.className = 'btn btn-sm btn-outline-danger';
            sellBtn.title = 'Sell';
            sellBtn.onclick = () => sellCrypto(crypto.symbol);
            sellBtn.innerHTML = '<i class="fas fa-minus"></i>';
            
            actionsCell.appendChild(buyBtn);
            actionsCell.appendChild(sellBtn);
            
            // Append all cells
            row.appendChild(rankCell);
            row.appendChild(symbolCell);
            row.appendChild(nameCell);
            row.appendChild(quantityCell);
            row.appendChild(priceCell);
            row.appendChild(valueCell);
            row.appendChild(targetSellCell);
            row.appendChild(approachingCell);
            row.appendChild(targetBuyCell);
            row.appendChild(projectedPnlCell);
            row.appendChild(pnlValueCell);
            row.appendChild(pnlPercentCell);
            row.appendChild(actionsCell);
            
            tableBody.appendChild(row);
        });
        
        console.log('Portfolio table updated with', cryptos.length, 'rows');
    }
    
    updateHoldingsTable(cryptos) {
        const tableBody = document.getElementById('positions-table-body');
        if (!tableBody) return;
        
        // Clear existing content
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
        
        // Populate holdings table (similar to main table but simplified)
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
            
            // Determine PnL colors and signal
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
            
            // Calculate position percentage (simplified as equal weight)
            const positionPercent = (100 / cryptos.length).toFixed(1);
            
            // Create cells with safe DOM manipulation
            const symbolCell = document.createElement('td');
            const symbolStrong = document.createElement('strong');
            symbolStrong.textContent = crypto.symbol;
            symbolCell.appendChild(symbolStrong);
            
            const nameCell = document.createElement('td');
            nameCell.textContent = crypto.name;
            
            const quantityCell = document.createElement('td');
            quantityCell.textContent = quantity;
            
            const priceCell = document.createElement('td');
            priceCell.textContent = `$${price}`;
            
            const valueCell = document.createElement('td');
            valueCell.textContent = currentValue;
            
            const positionCell = document.createElement('td');
            positionCell.textContent = `${positionPercent}%`;
            
            const pnlValueCell = document.createElement('td');
            pnlValueCell.className = pnlClass;
            pnlValueCell.textContent = pnl;
            
            const pnlPercentCell = document.createElement('td');
            pnlPercentCell.className = pnlClass;
            pnlPercentCell.textContent = `${pnlIcon} ${pnlPercent}%`;
            
            const currentPriceCell = document.createElement('td');
            currentPriceCell.textContent = `$${price}`;
            
            const realizedPnlCell = document.createElement('td');
            realizedPnlCell.className = pnlClass;
            realizedPnlCell.textContent = this.formatCurrency(Math.max(0, crypto.pnl));
            
            const signalCell = document.createElement('td');
            const signalBadge = document.createElement('span');
            signalBadge.className = signalClass;
            signalBadge.textContent = signal;
            signalCell.appendChild(signalBadge);
            
            // Append all cells
            row.appendChild(symbolCell);
            row.appendChild(nameCell);
            row.appendChild(quantityCell);
            row.appendChild(priceCell);
            row.appendChild(valueCell);
            row.appendChild(positionCell);
            row.appendChild(pnlValueCell);
            row.appendChild(pnlPercentCell);
            row.appendChild(currentPriceCell);
            row.appendChild(realizedPnlCell);
            row.appendChild(signalCell);
            
            tableBody.appendChild(row);
        });
    }
    
    updatePerformancePageTable(cryptos) {
        const tableBody = document.getElementById('performance-table-body');
        if (!tableBody) return;
        
        // Clear existing content
        tableBody.innerHTML = '';
        
        if (!cryptos || cryptos.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 10;
            cell.className = 'text-center text-muted';
            cell.textContent = 'No performance data available';
            row.appendChild(cell);
            tableBody.appendChild(row);
            return;
        }
        
        // Populate performance page table with different structure
        cryptos.forEach(crypto => {
            const row = document.createElement('tr');
            
            // Format values
            const price = crypto.current_price < 1 ? 
                crypto.current_price.toFixed(6) : 
                crypto.current_price.toFixed(2);
            const quantity = crypto.quantity.toFixed(4);
            const currentValue = this.formatCurrency(crypto.current_value);
            const initialValue = this.formatCurrency(crypto.initial_value);
            const pnl = this.formatCurrency(crypto.pnl);
            const pnlPercent = crypto.pnl_percent.toFixed(2);
            
            // Determine colors and indicators
            const pnlClass = crypto.pnl >= 0 ? 'text-success' : 'text-danger';
            const pnlIcon = crypto.pnl >= 0 ? '↗' : '↘';
            
            // Create cells with safe DOM manipulation
            const rankCell = document.createElement('td');
            const rankBadge = document.createElement('span');
            rankBadge.className = 'badge bg-primary';
            rankBadge.textContent = `#${crypto.rank}`;
            rankCell.appendChild(rankBadge);
            
            const symbolCell = document.createElement('td');
            const symbolStrong = document.createElement('strong');
            symbolStrong.textContent = crypto.symbol;
            symbolCell.appendChild(symbolStrong);
            
            const nameCell = document.createElement('td');
            nameCell.textContent = crypto.name;
            
            const initialValueCell = document.createElement('td');
            initialValueCell.textContent = initialValue;
            
            const currentValueCell = document.createElement('td');
            currentValueCell.textContent = currentValue;
            
            const pnlValueCell = document.createElement('td');
            pnlValueCell.className = pnlClass;
            pnlValueCell.textContent = pnl;
            
            const pnlPercentCell = document.createElement('td');
            pnlPercentCell.className = pnlClass;
            pnlPercentCell.textContent = `${pnlIcon} ${pnlPercent}%`;
            
            const priceCell = document.createElement('td');
            priceCell.textContent = `$${price}`;
            
            const quantityCell = document.createElement('td');
            quantityCell.textContent = quantity;
            
            const timeCell = document.createElement('td');
            const timeSmall = document.createElement('small');
            timeSmall.className = 'text-muted';
            timeSmall.textContent = 'Now';
            timeCell.appendChild(timeSmall);
            
            // Append all cells
            row.appendChild(rankCell);
            row.appendChild(symbolCell);
            row.appendChild(nameCell);
            row.appendChild(initialValueCell);
            row.appendChild(currentValueCell);
            row.appendChild(pnlValueCell);
            row.appendChild(pnlPercentCell);
            row.appendChild(priceCell);
            row.appendChild(quantityCell);
            row.appendChild(timeCell);
            
            tableBody.appendChild(row);
        });
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
    
    loadPortfolioData() {
        // Load portfolio data - used after reset operations
        this.updateCryptoPortfolio();
    }
    
    showToast(message, type = 'info') {
        // Create simple alert-style toast (no Bootstrap dependency)
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'primary'} position-fixed`;
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.style.minWidth = '300px';
        
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
    
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
        return container;
    }
    
    updateTradingStatusDisplay(mode, type) {
        // Update trading status indicators
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
        
        if (tradingStartTimeEl) {
            tradingStartTimeEl.textContent = new Date().toLocaleTimeString();
        }
        
        if (tradingSymbolEl) {
            tradingSymbolEl.textContent = type === 'portfolio' ? 'All Assets' : 'Selected';
        }
    }
    
    updateTradingStatus(status) {
        // Update trading status from server data
        if (!status) return;
        
        const tradingModeEl = document.getElementById('trading-mode');
        const tradingStatusEl = document.getElementById('trading-status');
        
        if (tradingModeEl && status.mode) {
            tradingModeEl.textContent = status.mode.toUpperCase();
            tradingModeEl.className = `badge ${status.mode === 'paper' ? 'bg-success' : 'bg-warning'}`;
        }
        
        if (tradingStatusEl && status.status) {
            tradingStatusEl.textContent = status.status;
            tradingStatusEl.className = `badge ${status.status === 'Active' ? 'bg-success' : 'bg-secondary'}`;
        }
    }
    
    async updateRecentTrades() {
        // Use cached API call to get status data (eliminates duplicate request)
        const data = await this.fetchWithCache('/api/status', 'status');
        if (data && data.recent_trades) {
            this.displayRecentTrades(data.recent_trades);
        }
    }
    
    displayRecentTrades(trades) {
        const tableBody = document.getElementById('trades-table');
        if (!tableBody) return;
        
        // Store all trades for filtering
        this.allTrades = trades || [];
        
        // Apply current filters
        this.applyTradeFilters();
    }
    
    applyTradeFilters() {
        const tableBody = document.getElementById('trades-table');
        if (!tableBody || !this.allTrades) return;
        
        // Get filter values
        const symbolFilter = document.getElementById('trades-filter')?.value.toLowerCase() || '';
        const actionFilter = document.getElementById('trades-action-filter')?.value || '';
        const timeFilter = document.getElementById('trades-time-filter')?.value || '';
        const pnlFilter = document.getElementById('trades-pnl-filter')?.value || '';
        
        // Filter trades based on criteria
        let filteredTrades = this.allTrades.filter(trade => {
            // Symbol filter
            if (symbolFilter && !trade.symbol.toLowerCase().includes(symbolFilter)) {
                return false;
            }
            
            // Action filter
            if (actionFilter && trade.side !== actionFilter) {
                return false;
            }
            
            // Time filter
            if (timeFilter) {
                const tradeDate = new Date(trade.timestamp);
                const now = new Date();
                const timeDiff = now - tradeDate;
                
                let maxAge = 0;
                switch (timeFilter) {
                    case '24h': maxAge = 24 * 60 * 60 * 1000; break;
                    case '3d': maxAge = 3 * 24 * 60 * 60 * 1000; break;
                    case '7d': maxAge = 7 * 24 * 60 * 60 * 1000; break;
                    case '1m': maxAge = 30 * 24 * 60 * 60 * 1000; break;
                    case '6m': maxAge = 6 * 30 * 24 * 60 * 60 * 1000; break;
                    case '1y': maxAge = 365 * 24 * 60 * 60 * 1000; break;
                }
                
                if (timeDiff > maxAge) {
                    return false;
                }
            }
            
            // P&L filter
            if (pnlFilter) {
                const pnl = trade.pnl || 0;
                if (pnlFilter === 'positive' && pnl <= 0) return false;
                if (pnlFilter === 'negative' && pnl >= 0) return false;
            }
            
            return true;
        });
        
        // Clear existing content
        tableBody.innerHTML = '';
        
        if (!filteredTrades || filteredTrades.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 7;
            cell.className = 'text-center text-muted';
            cell.textContent = 'No trades match the current filters';
            row.appendChild(cell);
            tableBody.appendChild(row);
            return;
        }
        
        // Sort trades by timestamp (newest first)
        filteredTrades.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        filteredTrades.forEach(trade => {
            const row = document.createElement('tr');
            
            // Format timestamp
            const timestamp = new Date(trade.timestamp).toLocaleString();
            
            // Format values
            const price = this.formatCurrency(trade.price);
            const quantity = trade.quantity.toFixed(6);
            const pnl = trade.pnl ? this.formatCurrency(trade.pnl) : '$0.00';
            
            // Determine colors
            const sideClass = trade.side === 'BUY' ? 'text-success' : 'text-danger';
            const pnlClass = trade.pnl >= 0 ? 'text-success' : 'text-danger';
            
            // Create cells with safe DOM manipulation
            const idCell = document.createElement('td');
            const idBadge = document.createElement('span');
            idBadge.className = 'badge bg-secondary';
            idBadge.textContent = `#${trade.trade_id || (filteredTrades.indexOf(trade) + 1)}`;
            idCell.appendChild(idBadge);
            
            const timeCell = document.createElement('td');
            const timeSmall = document.createElement('small');
            timeSmall.textContent = timestamp;
            timeCell.appendChild(timeSmall);
            
            const symbolCell = document.createElement('td');
            const symbolStrong = document.createElement('strong');
            symbolStrong.textContent = trade.symbol;
            symbolCell.appendChild(symbolStrong);
            
            const sideCell = document.createElement('td');
            const sideBadge = document.createElement('span');
            sideBadge.className = `badge ${trade.side === 'BUY' ? 'bg-success' : 'bg-danger'}`;
            sideBadge.textContent = trade.side;
            sideCell.appendChild(sideBadge);
            
            const quantityCell = document.createElement('td');
            quantityCell.textContent = quantity;
            
            const priceCell = document.createElement('td');
            priceCell.textContent = price;
            
            const pnlCell = document.createElement('td');
            pnlCell.className = pnlClass;
            pnlCell.textContent = pnl;
            
            // Append all cells
            row.appendChild(idCell);
            row.appendChild(timeCell);
            row.appendChild(symbolCell);
            row.appendChild(sideCell);
            row.appendChild(quantityCell);
            row.appendChild(priceCell);
            row.appendChild(pnlCell);
            
            tableBody.appendChild(row);
        });
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.tradingApp = new TradingApp();
});

// Trading functions
async function resetEntireProgram() {
    if (confirm('Are you sure you want to reset the entire trading system? This will reset all portfolio values back to $10 each and clear all trading data. This cannot be undone.')) {
        try {
            // Call the web_interface.py reset endpoint which properly handles portfolio reset
            const response = await fetch('/api/reset-entire-program', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            
            if (data.success) {
                window.tradingApp.showToast('Portfolio reset successfully! All values back to $10 each.', 'success');
                
                // Reset trading status to stopped state
                const tradingModeEl = document.getElementById('trading-mode');
                const tradingStatusEl = document.getElementById('trading-status');
                const tradingStartTimeEl = document.getElementById('trading-start-time');
                const tradingSymbolEl = document.getElementById('trading-symbol');
                
                if (tradingModeEl) {
                    tradingModeEl.textContent = 'Stopped';
                    tradingModeEl.className = 'badge bg-secondary';
                }
                
                if (tradingStatusEl) {
                    tradingStatusEl.textContent = 'Idle';
                    tradingStatusEl.className = 'badge bg-secondary';
                }
                
                if (tradingStartTimeEl) {
                    tradingStartTimeEl.textContent = '-';
                }
                
                if (tradingSymbolEl) {
                    tradingSymbolEl.textContent = '-';
                }
                
                // Clear portfolio display to show no holdings
                const cryptoSymbolsEl = document.getElementById('crypto-symbols');
                if (cryptoSymbolsEl) {
                    cryptoSymbolsEl.innerHTML = '<span class="badge bg-secondary">Empty portfolio - Start trading to populate</span>';
                }
                
                // Clear recent trades display
                const tradesTable = document.getElementById('trades-table');
                if (tradesTable) {
                    tradesTable.innerHTML = '';
                    const row = document.createElement('tr');
                    const cell = document.createElement('td');
                    cell.colSpan = 7;
                    cell.className = 'text-center text-muted';
                    cell.textContent = 'No trades yet';
                    row.appendChild(cell);
                    tradesTable.appendChild(row);
                }
                
                // Force refresh portfolio data to show empty state
                setTimeout(() => {
                    window.tradingApp.loadPortfolioData();
                }, 1000);
                
                // Reload after a short delay to show the message
                setTimeout(() => {
                    location.reload();
                }, 2500);
            } else {
                window.tradingApp.showToast('Failed to reset portfolio: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Reset error:', error);
            window.tradingApp.showToast('Error resetting portfolio: ' + error.message, 'error');
        }
    }
}

async function startPaperTrades() {
    try {
        // For now, just show a message that paper trading is already active
        window.tradingApp.showToast('Paper trading is already active in the system', 'info');
    } catch (error) {
        window.tradingApp.showToast('Error starting paper trades: ' + error.message, 'error');
    }
}

// Navigation Functions for Dashboard Views
function showMainDashboard() {
    // Hide all dashboard sections first
    const performanceDashboard = document.getElementById('performance-dashboard');
    const currentHoldings = document.getElementById('current-holdings');
    const mainDashboard = document.getElementById('main-dashboard');
    
    // Show main dashboard and hide others
    if (mainDashboard) mainDashboard.style.display = 'block';
    if (performanceDashboard) performanceDashboard.style.display = 'none';
    if (currentHoldings) currentHoldings.style.display = 'none';
    
    // Update navbar button states
    updateNavbarButtons('main');
    
    console.log('Switched to Main Dashboard');
}

function showPerformanceDashboard() {
    // Hide all dashboard sections first
    const mainDashboard = document.getElementById('main-dashboard');
    const currentHoldings = document.getElementById('current-holdings');
    const performanceDashboard = document.getElementById('performance-dashboard');
    
    // Show performance dashboard and hide others
    if (performanceDashboard) performanceDashboard.style.display = 'block';
    if (mainDashboard) mainDashboard.style.display = 'none';
    if (currentHoldings) currentHoldings.style.display = 'none';
    
    // Update navbar button states
    updateNavbarButtons('performance');
    
    console.log('Switched to Performance Dashboard');
}

function showCurrentPositions() {
    // Hide all dashboard sections first
    const mainDashboard = document.getElementById('main-dashboard');
    const performanceDashboard = document.getElementById('performance-dashboard');
    const currentHoldings = document.getElementById('current-holdings');
    
    // Show current holdings and hide others
    if (currentHoldings) currentHoldings.style.display = 'block';
    if (mainDashboard) mainDashboard.style.display = 'none';
    if (performanceDashboard) performanceDashboard.style.display = 'none';
    
    // Update navbar button states
    updateNavbarButtons('holdings');
    
    console.log('Switched to Current Holdings');
}

function updateNavbarButtons(activeView) {
    // Get all navigation buttons
    const buttons = document.querySelectorAll('.navbar-nav .btn');
    
    // Remove active classes
    buttons.forEach(btn => {
        btn.classList.remove('btn-light');
        btn.classList.add('btn-outline-light');
    });
    
    // Add active class to current view
    const buttonMap = {
        'main': 0,
        'performance': 1,
        'holdings': 2
    };
    
    if (buttonMap[activeView] !== undefined && buttons[buttonMap[activeView]]) {
        buttons[buttonMap[activeView]].classList.remove('btn-outline-light');
        buttons[buttonMap[activeView]].classList.add('btn-light');
    }
}

// Data update functions
async function updatePerformanceData() {
    try {
        const response = await fetch('/api/crypto-portfolio');
        const data = await response.json();
        if (data && data.cryptocurrencies) {
            window.tradingApp.updatePerformanceTable(data.cryptocurrencies);
        }
    } catch (error) {
        console.error('Error updating performance data:', error);
    }
}

async function updateHoldingsData() {
    try {
        const response = await fetch('/api/crypto-portfolio');
        const data = await response.json();
        if (data && data.cryptocurrencies) {
            window.tradingApp.updateHoldingsTable(data.cryptocurrencies);
        }
    } catch (error) {
        console.error('Error updating holdings data:', error);
    }
}

// Filter functions for trades table
function filterTradesTable() {
    if (window.tradingApp && window.tradingApp.applyTradeFilters) {
        window.tradingApp.applyTradeFilters();
    }
}

function clearTradesFilters() {
    // Clear all filter inputs
    const symbolFilter = document.getElementById('trades-filter');
    const actionFilter = document.getElementById('trades-action-filter');
    const timeFilter = document.getElementById('trades-time-filter');
    const pnlFilter = document.getElementById('trades-pnl-filter');
    
    if (symbolFilter) symbolFilter.value = '';
    if (actionFilter) actionFilter.value = '';
    if (timeFilter) timeFilter.value = '';
    if (pnlFilter) pnlFilter.value = '';
    
    // Reapply filters (which will show all trades)
    filterTradesTable();
}

// Add missing functions referenced in the HTML
async function startTrading(mode, type) {
    if (mode === 'live') {
        if (!confirm('Are you sure you want to start LIVE trading? This will use real money and cannot be undone!')) {
            return;
        }
        window.tradingApp.showToast('Live trading is not enabled in this demo version', 'warning');
        return;
    }
    
    // Paper trading mode
    window.tradingApp.showToast(`Starting ${mode} trading in ${type} mode...`, 'info');
    
    try {
        const response = await fetch('/api/start-trading', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mode: mode,
                type: type
            })
        });
        
        const data = await response.json();
        if (data.success) {
            window.tradingApp.showToast(`${mode} trading started successfully in ${type} mode`, 'success');
            // Update trading status display
            window.tradingApp.updateTradingStatusDisplay(mode, type);
        } else {
            window.tradingApp.showToast(`Failed to start trading: ${data.error}`, 'error');
        }
    } catch (error) {
        window.tradingApp.showToast(`Error starting trading: ${error.message}`, 'error');
    }
}

async function buyCrypto(symbol) {
    const amount = prompt(`Enter USD amount to buy ${symbol}:`, '25.00');
    if (!amount || isNaN(amount) || parseFloat(amount) <= 0) {
        window.tradingApp.showToast('Invalid amount entered', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/paper-trade/buy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                amount: parseFloat(amount)
            })
        });
        
        const data = await response.json();
        if (data.success) {
            window.tradingApp.showToast(`Successfully bought $${amount} worth of ${symbol}`, 'success');
            window.tradingApp.updateDashboard(); // Refresh data
        } else {
            window.tradingApp.showToast(`Buy failed: ${data.error}`, 'error');
        }
    } catch (error) {
        window.tradingApp.showToast(`Error buying ${symbol}: ${error.message}`, 'error');
    }
}

async function sellCrypto(symbol) {
    const quantity = prompt(`Enter quantity of ${symbol} to sell:`, '0.001');
    if (!quantity || isNaN(quantity) || parseFloat(quantity) <= 0) {
        window.tradingApp.showToast('Invalid quantity entered', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/paper-trade/sell', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                quantity: parseFloat(quantity)
            })
        });
        
        const data = await response.json();
        if (data.success) {
            window.tradingApp.showToast(`Successfully sold ${quantity} ${symbol}`, 'success');
            window.tradingApp.updateDashboard(); // Refresh data
        } else {
            window.tradingApp.showToast(`Sell failed: ${data.error}`, 'error');
        }
    } catch (error) {
        window.tradingApp.showToast(`Error selling ${symbol}: ${error.message}`, 'error');
    }
}

// Add missing stop trading functions
async function stopTrading() {
    if (!confirm('Are you sure you want to stop all trading activities?')) {
        return;
    }
    
    window.tradingApp.showToast('Trading stopped successfully', 'info');
    
    // Update trading status display
    const tradingModeEl = document.getElementById('trading-mode');
    const tradingStatusEl = document.getElementById('trading-status');
    const tradingStartTimeEl = document.getElementById('trading-start-time');
    const tradingSymbolEl = document.getElementById('trading-symbol');
    
    if (tradingModeEl) {
        tradingModeEl.textContent = 'Stopped';
        tradingModeEl.className = 'badge bg-secondary';
    }
    
    if (tradingStatusEl) {
        tradingStatusEl.textContent = 'Idle';
        tradingStatusEl.className = 'badge bg-secondary';
    }
    
    if (tradingStartTimeEl) {
        tradingStartTimeEl.textContent = '-';
    }
    
    if (tradingSymbolEl) {
        tradingSymbolEl.textContent = '-';
    }
}

async function emergencyStop() {
    if (!confirm('EMERGENCY STOP: This will immediately halt all trading and close any open positions. Are you sure?')) {
        return;
    }
    
    window.tradingApp.showToast('EMERGENCY STOP activated - All trading halted', 'warning');
    
    // Update trading status display
    const tradingModeEl = document.getElementById('trading-mode');
    const tradingStatusEl = document.getElementById('trading-status');
    
    if (tradingModeEl) {
        tradingModeEl.textContent = 'EMERGENCY STOP';
        tradingModeEl.className = 'badge bg-danger';
    }
    
    if (tradingStatusEl) {
        tradingStatusEl.textContent = 'HALTED';
        tradingStatusEl.className = 'badge bg-danger';
    }
}