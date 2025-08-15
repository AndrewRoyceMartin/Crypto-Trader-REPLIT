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
        // Auto-refresh every 30 seconds (prevent CoinGecko 429 rate limit errors)
        this.updateInterval = setInterval(() => {
            this.updateDashboard();
        }, 30000);
        
        // Start countdown timer
        this.startCountdown();
        
        // Handle page visibility change - pause updates when hidden
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoUpdate();
            } else {
                this.startAutoUpdate();
                this.updateDashboard();
            }
        });
        
        // Handle window unload
        window.addEventListener('beforeunload', () => {
            this.stopAutoUpdate();
        });
    }
    
    startAutoUpdate() {
        if (!this.updateInterval) {
            this.updateInterval = setInterval(() => {
                this.updateDashboard();
            }, 30000);
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
            
        } catch (error) {
            console.error('Status update failed:', {});
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
        // Update trading status display - check if element exists first
        const statusElement = document.getElementById('trading-status');
        if (statusElement && tradingStatus) {
            statusElement.textContent = `${tradingStatus.mode} - ${tradingStatus.strategy}`;
        }
        // If element doesn't exist, just skip silently to avoid console errors
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
            
            // Update crypto symbols display and all tables
            if (data.cryptocurrencies) {
                this.updateLoadingProgress(80, 'Updating displays...');
                this.updateCryptoSymbols(data.cryptocurrencies);
                this.updateCryptoTable(data.cryptocurrencies);
                this.updatePerformanceTable(data.cryptocurrencies);
                this.updatePerformancePageTable(data.cryptocurrencies);
                this.updateHoldingsTable(data.cryptocurrencies);
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
        
        // Sort cryptos by market cap rank
        const sortedCryptos = [...cryptos].sort((a, b) => (a.rank || 999) - (b.rank || 999));
        
        sortedCryptos.forEach(crypto => {
            const row = tableBody.insertRow();
            
            // Format values
            const price = typeof crypto.current_price === 'number' ? crypto.current_price : 0;
            const quantity = typeof crypto.quantity === 'number' ? crypto.quantity : 0;
            const value = typeof crypto.current_value === 'number' ? crypto.current_value : 0;
            const pnlPercent = typeof crypto.pnl_percent === 'number' ? crypto.pnl_percent : 0;
            
            // Create cells
            const rankCell = row.insertCell(0);
            const symbolCell = row.insertCell(1);
            const nameCell = row.insertCell(2);
            const priceCell = row.insertCell(3);
            const quantityCell = row.insertCell(4);
            const valueCell = row.insertCell(5);
            const pnlPercentCell = row.insertCell(6);
            const updatedCell = row.insertCell(7);
            
            // Fill cells with data
            rankCell.textContent = crypto.rank || '-';
            symbolCell.innerHTML = `<span class="fw-bold text-primary">${crypto.symbol || '-'}</span>`;
            nameCell.textContent = crypto.name || '-';
            priceCell.textContent = this.formatCurrency(price);
            quantityCell.textContent = quantity.toFixed(6);
            valueCell.textContent = this.formatCurrency(value);
            
            // Color-code P&L percentage
            const pnlClass = pnlPercent >= 0 ? 'text-success' : 'text-danger';
            pnlPercentCell.innerHTML = `<span class="${pnlClass} fw-bold">${pnlPercent.toFixed(2)}%</span>`;
            
            // Format last updated
            if (crypto.last_updated) {
                const updateTime = new Date(crypto.last_updated);
                updatedCell.innerHTML = `<small class="text-muted">${updateTime.toLocaleTimeString()}</small>`;
            } else {
                updatedCell.innerHTML = '<small class="text-muted">-</small>';
            }
            
            // Add hover effect
            row.classList.add('table-row-hover');
        });
        
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
    
    updatePerformanceTable(cryptos) {
        const tableBody = document.getElementById('crypto-portfolio-table');
        if (!tableBody) return;
        
        // Clear existing content
        tableBody.innerHTML = '';
        
        if (!cryptos || cryptos.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="13" class="text-center text-muted">No performance data available</td>';
            tableBody.appendChild(row);
            return;
        }
        
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

            row.innerHTML = `
                <td><span class="badge bg-primary">#${crypto.rank}</span></td>
                <td><strong>${crypto.symbol}</strong></td>
                <td>${crypto.name}</td>
                <td>${quantity}</td>
                <td>$${price}</td>
                <td>${currentValue}</td>
                <td>${targetSell}</td>
                <td class="${pnlClass}">${pnl}</td>
                <td class="${pnlClass}">${pnlIcon} ${pnlPercent}%</td>
                <td><small class="text-muted">${lastUpdated}</small></td>
                <td>${signal}</td>
                <td>
                    <button class="btn btn-sm btn-outline-success me-1" onclick="buyCrypto('${crypto.symbol}')" title="Buy">
                        <i class="fas fa-plus"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="sellCrypto('${crypto.symbol}')" title="Sell">
                        <i class="fas fa-minus"></i>
                    </button>
                </td>
                <td><small class="text-info">${targetProximity}</small></td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    updateHoldingsTable(cryptos) {
        const tableBody = document.getElementById('positions-table-body');
        if (!tableBody) return;
        
        // Clear existing content
        tableBody.innerHTML = '';
        
        if (!cryptos || cryptos.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="11" class="text-center text-muted">No holdings data available</td>';
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
            
            row.innerHTML = `
                <td><strong>${crypto.symbol}</strong></td>
                <td>${crypto.name}</td>
                <td>${quantity}</td>
                <td>$${price}</td>
                <td>${currentValue}</td>
                <td>${positionPercent}%</td>
                <td class="${pnlClass}">${pnl}</td>
                <td class="${pnlClass}">${pnlIcon} ${pnlPercent}%</td>
                <td>$${price}</td>
                <td class="${pnlClass}">${this.formatCurrency(Math.max(0, crypto.pnl))}</td>
                <td><span class="${signalClass}">${signal}</span></td>
            `;
            
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
            row.innerHTML = '<td colspan="10" class="text-center text-muted">No performance data available</td>';
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
            
            row.innerHTML = `
                <td><span class="badge bg-primary">#${crypto.rank}</span></td>
                <td><strong>${crypto.symbol}</strong></td>
                <td>${crypto.name}</td>
                <td>${initialValue}</td>
                <td>${currentValue}</td>
                <td class="${pnlClass}">${pnl}</td>
                <td class="${pnlClass}">${pnlIcon} ${pnlPercent}%</td>
                <td>$${price}</td>
                <td>${quantity}</td>
                <td><small class="text-muted">Now</small></td>
            `;
            
            tableBody.appendChild(row);
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

// Add missing functions referenced in the HTML
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