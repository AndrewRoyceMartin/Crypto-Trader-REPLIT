// Trading System Web Interface JavaScript

class TradingApp {
    constructor() {
        this.updateInterval = null;
        this.portfolioChart = null;
        this.returnsChart = null;
        this.tradesChart = null;
        this.isLiveConfirmationPending = false;
        this.countdownInterval = null;
        this.countdown = 5;
        this.reconnectCountdown = null;
        this.reconnectInterval = null;
        this.nextRetryTime = null;
        this.startTime = null;
        this.uptimeInterval = null;
        this.uptimeStarted = false;
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
        
        // Initialize news ticker after DOM is ready
        setTimeout(() => {
            if (typeof window.initializeNewsTicker === 'function') {
                window.initializeNewsTicker();
            }
        }, 3000);
    }
    
    setupEventListeners() {
        // Auto-refresh every 6 seconds (10 times per minute to respect CoinGecko limits)
        this.updateInterval = setInterval(() => {
            this.updateDashboard();
        }, 6000);
        
        // Start countdown timer
        this.startCountdown();
        
        // Uptime counter will start when connection is confirmed
        
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
        
        // Initialize news ticker
        // News ticker initialized separately
    }
    
    startAutoUpdate() {
        if (!this.updateInterval) {
            this.updateInterval = setInterval(() => {
                this.updateDashboard();
            }, 6000);
        }
    }
    
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
        if (this.uptimeInterval) {
            clearInterval(this.uptimeInterval);
            this.uptimeInterval = null;
        }
    }
    
    startCountdown() {
        this.countdown = 5;
        this.updateCountdownDisplay();
        
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        
        this.countdownInterval = setInterval(() => {
            this.countdown--;
            if (this.countdown <= 0) {
                this.countdown = 5; // Reset for next cycle
            }
            this.updateCountdownDisplay();
        }, 1000);
    }
    
    updateCountdownDisplay() {
        const countdownElement = document.getElementById('trading-countdown');
        if (countdownElement) {
            if (this.countdown === 5) {
                countdownElement.textContent = 'Checking trades...';
                countdownElement.className = 'badge bg-primary ms-2';
            } else {
                countdownElement.textContent = `Next check: ${this.countdown}s`;
                countdownElement.className = 'badge bg-secondary ms-2';
            }
        }
    }
    
    async updateDashboard() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            this.updateTradingStatus(data.trading_status);
            this.updatePortfolio(data.portfolio);
            this.updateCharts(data.portfolio, data.recent_trades);
            this.updateRecentTrades(data.recent_trades);
            this.updateCryptoPortfolio();
            
            // Connection status managed by updateConnectionStatusDisplay()
            
        } catch (error) {
            console.error('Error updating dashboard:', error.message || error);
            console.error('Full error:', error);
            // Connection status managed by updateConnectionStatusDisplay()
        }
    }

    initializeCharts() {
        // Portfolio Value Chart
        const portfolioCtx = document.getElementById('portfolioChart').getContext('2d');
        this.portfolioChart = new Chart(portfolioCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `Portfolio: $${context.parsed.y.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Value ($)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

        // Returns Chart
        const returnsCtx = document.getElementById('returnsChart').getContext('2d');
        this.returnsChart = new Chart(returnsCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Total Return (%)',
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `Return: ${context.parsed.y.toFixed(2)}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Return (%)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });

        // Trade P&L Chart
        const tradesCtx = document.getElementById('tradesChart').getContext('2d');
        this.tradesChart = new Chart(tradesCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Trade P&L',
                    data: [],
                    backgroundColor: [],
                    borderColor: [],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const pnl = context.parsed.y;
                                return `P&L: $${pnl.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Trade #'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'P&L ($)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    }
                }
            }
        });
    }

    updateCharts(portfolioData, tradesData) {
        this.updatePortfolioChart(portfolioData);
        this.updateReturnsChart(portfolioData);
        this.updateTradesChart(tradesData);
    }

    updatePortfolioChart(portfolioData) {
        if (!this.portfolioChart || !portfolioData.chart_data) return;

        const chartData = portfolioData.chart_data;
        const labels = chartData.map(point => new Date(point.timestamp).toLocaleTimeString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }));
        const values = chartData.map(point => point.value);

        this.portfolioChart.data.labels = labels;
        this.portfolioChart.data.datasets[0].data = values;
        this.portfolioChart.update('none');
    }

    updateReturnsChart(portfolioData) {
        if (!this.returnsChart || !portfolioData.chart_data) return;

        const chartData = portfolioData.chart_data;
        if (chartData.length === 0) return;

        const initialValue = chartData[0]?.value || 10000;
        const labels = chartData.map(point => new Date(point.timestamp).toLocaleTimeString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }));
        const returns = chartData.map(point => ((point.value - initialValue) / initialValue) * 100);

        this.returnsChart.data.labels = labels;
        this.returnsChart.data.datasets[0].data = returns;
        this.returnsChart.update('none');
    }

    updateTradesChart(tradesData) {
        if (!this.tradesChart || !tradesData) return;

        // Filter trades with P&L data
        const tradesWithPnL = tradesData.filter(trade => trade.realized_pnl !== undefined && trade.realized_pnl !== null);
        
        if (tradesWithPnL.length === 0) return;

        const labels = tradesWithPnL.map((_, index) => `Trade ${index + 1}`);
        const pnlValues = tradesWithPnL.map(trade => trade.realized_pnl || 0);
        
        // Color bars based on profit/loss
        const colors = pnlValues.map(pnl => pnl >= 0 ? 'rgba(40, 167, 69, 0.8)' : 'rgba(220, 53, 69, 0.8)');
        const borderColors = pnlValues.map(pnl => pnl >= 0 ? '#28a745' : '#dc3545');

        this.tradesChart.data.labels = labels;
        this.tradesChart.data.datasets[0].data = pnlValues;
        this.tradesChart.data.datasets[0].backgroundColor = colors;
        this.tradesChart.data.datasets[0].borderColor = borderColors;
        this.tradesChart.update('none');
    }

    async updateCryptoPortfolio() {
        try {
            const response = await fetch('/api/crypto-portfolio');
            if (!response.ok) return;
            
            const data = await response.json();
            
            // Update summary statistics
            document.getElementById('crypto-total-count').textContent = data.summary.total_cryptos;
            document.getElementById('crypto-initial-value').textContent = this.formatCurrency(data.summary.total_initial_value);
            document.getElementById('crypto-current-value').textContent = this.formatCurrency(data.summary.total_current_value);
            document.getElementById('crypto-total-pnl').textContent = this.formatCurrency(data.summary.total_pnl);
            document.getElementById('crypto-pnl-percent').textContent = data.summary.total_pnl_percent.toFixed(2) + '%';
            
            // Update P&L color
            const pnlElement = document.getElementById('crypto-total-pnl');
            const pnlPercentElement = document.getElementById('crypto-pnl-percent');
            const pnlClass = data.summary.total_pnl >= 0 ? 'text-success' : 'text-danger';
            pnlElement.className = `mb-0 ${pnlClass}`;
            pnlPercentElement.className = `mb-0 ${pnlClass}`;
            
            // Update crypto table
            this.updateCryptoTable(data.cryptocurrencies);
            
            // Restore table state after update
            restoreTableState();
            
        } catch (error) {
            console.error('Error updating crypto portfolio:', error);
        }
    }

    updateCryptoTable(cryptos) {
        const tbody = document.getElementById('crypto-portfolio-table');
        
        if (!cryptos || cryptos.length === 0) {
            // Clear existing rows safely
            tbody.textContent = '';
            
            // Create empty state row using safe DOM methods
            const emptyRow = document.createElement('tr');
            const emptyCell = document.createElement('td');
            emptyCell.setAttribute('colspan', '13');
            emptyCell.className = 'text-center text-muted';
            emptyCell.textContent = 'No cryptocurrency data available';
            emptyRow.appendChild(emptyCell);
            tbody.appendChild(emptyRow);
            return;
        }
        
        // Store cryptos globally for sorting
        window.cryptoPortfolioData = cryptos;
        window.sortColumn = window.sortColumn || null;
        window.sortDirection = window.sortDirection || 'asc';
        
        // Apply existing sort if one is active
        if (window.sortColumn) {
            applySortToCryptoData();
            updateSortIcons(window.sortColumn);
        }
        
        // Clear existing rows safely
        tbody.textContent = '';
        
        // Create rows using safe DOM methods
        window.cryptoPortfolioData.forEach(crypto => {
            const pnlClass = crypto.pnl >= 0 ? 'text-success' : 'text-danger';
            const priceDisplay = crypto.current_price < 1 ? crypto.current_price.toFixed(6) : crypto.current_price.toFixed(2);
            
            // Calculate proximity to target sell price  
            const proximityClass = calculateTargetProximity(crypto.current_price, crypto.target_sell_price);
            
            // Debug logging removed to prevent console spam
            
            const projectedPnl = crypto.projected_sell_pnl || 0;
            const projectedPnlClass = projectedPnl >= 0 ? 'text-success' : 'text-danger';
            const targetBuyDisplay = crypto.target_buy_price ? crypto.target_buy_price.toFixed(crypto.target_buy_price < 1 ? 6 : 2) : '0.00';
            
            // Calculate approaching sell percentage
            const approachingSellPercentage = crypto.target_sell_price ? 
                Math.min(100, Math.max(0, (crypto.current_price / crypto.target_sell_price) * 100)) : 0;
            const approachingClass = approachingSellPercentage >= 95 ? 'text-white fw-bold bg-danger bg-opacity-75' : 
                                   approachingSellPercentage >= 90 ? 'text-dark fw-semibold bg-warning bg-opacity-50' : 
                                   approachingSellPercentage >= 80 ? 'text-white fw-normal bg-info bg-opacity-75' : 'text-dark';
            
            // Create row element safely
            const row = document.createElement('tr');
            row.className = proximityClass;
            
            // Create cells with safe methods
            const cells = [
                { content: crypto.rank.toString(), className: 'fw-bold' },
                { content: crypto.symbol, className: 'fw-semibold' },
                { content: crypto.name, className: 'text-muted' },
                { content: crypto.quantity.toFixed(4) },
                { content: `$${priceDisplay}` },
                { content: `$${crypto.current_value.toFixed(2)}` },
                { content: `$${crypto.target_sell_price ? crypto.target_sell_price.toFixed(crypto.target_sell_price < 1 ? 6 : 2) : 'N/A'}`, className: 'bg-light text-dark fw-semibold' },
                { content: `${approachingSellPercentage.toFixed(1)}%`, className: approachingClass, style: 'padding: 8px; border-radius: 4px;' },
                { content: `$${targetBuyDisplay}`, className: 'bg-light text-success' },
                { content: `$${projectedPnl >= 0 ? '+' : ''}${projectedPnl.toFixed(2)}`, className: `bg-light ${projectedPnlClass}` },
                { content: `$${crypto.pnl.toFixed(2)}`, className: pnlClass },
                { content: `${crypto.pnl_percent.toFixed(2)}%`, className: pnlClass }
            ];
            
            // Add data cells safely
            cells.forEach(cellData => {
                const cell = document.createElement('td');
                if (cellData.className) cell.className = cellData.className;
                if (cellData.style) cell.setAttribute('style', cellData.style);
                cell.textContent = cellData.content;
                row.appendChild(cell);
            });
            
            // Create action buttons cell safely
            const actionCell = document.createElement('td');
            
            // Chart button
            const chartBtn = document.createElement('button');
            chartBtn.className = 'btn btn-outline-primary btn-sm me-1';
            chartBtn.setAttribute('onclick', `showCryptoChart('${crypto.symbol}')`);
            chartBtn.setAttribute('title', `View ${crypto.symbol} Chart`);
            
            const chartIcon = document.createElement('i');
            chartIcon.className = 'fas fa-chart-line';
            chartBtn.appendChild(chartIcon);
            
            // Trade button
            const tradeBtn = document.createElement('button');
            tradeBtn.className = 'btn btn-outline-success btn-sm';
            tradeBtn.setAttribute('onclick', `tradeCrypto('${crypto.symbol}')`);
            tradeBtn.setAttribute('title', `Trade ${crypto.symbol}`);
            
            const tradeIcon = document.createElement('i');
            tradeIcon.className = 'fas fa-exchange-alt';
            tradeBtn.appendChild(tradeIcon);
            
            actionCell.appendChild(chartBtn);
            actionCell.appendChild(tradeBtn);
            row.appendChild(actionCell);
            
            tbody.appendChild(row);
        });
    }

    updateTradingStatus(status) {
        const modeElement = document.getElementById('trading-mode');
        const symbolElement = document.getElementById('trading-symbol');
        const startTimeElement = document.getElementById('trading-start-time');
        const statusElement = document.getElementById('trading-status');
        
        modeElement.textContent = status.mode || 'Stopped';
        symbolElement.textContent = status.symbol || '-';
        
        if (status.start_time) {
            const startTime = new Date(status.start_time);
            startTimeElement.textContent = startTime.toLocaleString();
        } else {
            startTimeElement.textContent = '-';
        }
        
        // Update status badge
        if (status.is_running) {
            statusElement.textContent = 'Running';
            statusElement.className = 'badge bg-success';
            modeElement.className = 'badge bg-success';
        } else {
            statusElement.textContent = 'Idle';
            statusElement.className = 'badge bg-secondary';
            modeElement.className = 'badge bg-secondary';
        }
    }
    
    updatePortfolio(portfolio) {
        document.getElementById('portfolio-value').textContent = this.formatCurrency(portfolio.total_value);
        document.getElementById('portfolio-cash').textContent = this.formatCurrency(portfolio.cash);
        document.getElementById('portfolio-positions').textContent = this.formatCurrency(portfolio.positions_value);
        
        const pnlElement = document.getElementById('portfolio-pnl');
        const pnl = portfolio.daily_pnl || 0;
        pnlElement.textContent = this.formatCurrency(pnl);
        
        // Update PnL color
        if (pnl > 0) {
            pnlElement.className = 'pnl-positive';
        } else if (pnl < 0) {
            pnlElement.className = 'pnl-negative';
        } else {
            pnlElement.className = 'pnl-neutral';
        }
        
        // Chart updates are handled by updateCharts() method
    }
    
    updateRecentTrades(trades) {
        const tbody = document.getElementById('trades-table');
        
        // Clear existing content
        tbody.innerHTML = '';
        
        if (!trades || trades.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.setAttribute('colspan', '6');
            cell.className = 'text-center text-muted';
            cell.textContent = 'No trades yet';
            row.appendChild(cell);
            tbody.appendChild(row);
            return;
        }
        
        trades.slice(-50).reverse().forEach(trade => {
            const row = document.createElement('tr');
            
            // Timestamp cell
            const timestampCell = document.createElement('td');
            timestampCell.className = 'text-xs';
            timestampCell.textContent = new Date(trade.timestamp).toLocaleString();
            row.appendChild(timestampCell);
            
            // Symbol cell
            const symbolCell = document.createElement('td');
            symbolCell.textContent = trade.symbol;
            row.appendChild(symbolCell);
            
            // Action cell
            const actionCell = document.createElement('td');
            const actionSpan = document.createElement('span');
            const actionClass = trade.action === 'buy' ? 'trade-buy' : 'trade-sell';
            actionSpan.className = actionClass;
            actionSpan.textContent = String(trade.action).toUpperCase();
            actionCell.appendChild(actionSpan);
            row.appendChild(actionCell);
            
            // Size cell
            const sizeCell = document.createElement('td');
            sizeCell.textContent = parseFloat(trade.size).toFixed(6);
            row.appendChild(sizeCell);
            
            // Price cell
            const priceCell = document.createElement('td');
            priceCell.textContent = '$' + parseFloat(trade.price).toFixed(2);
            row.appendChild(priceCell);
            
            // PnL cell
            const pnlCell = document.createElement('td');
            const pnlSpan = document.createElement('span');
            const pnl = trade.pnl || 0;
            const pnlClass = pnl > 0 ? 'pnl-positive' : pnl < 0 ? 'pnl-negative' : 'pnl-neutral';
            pnlSpan.className = pnlClass;
            pnlSpan.textContent = '$' + pnl.toFixed(2);
            pnlCell.appendChild(pnlSpan);
            row.appendChild(pnlCell);
            
            tbody.appendChild(row);
        });
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        
        if (connected) {
            // Don't override the connection status display - it's handled by updateConnectionStatusDisplay()
        } else {
            statusElement.innerHTML = '<i class="fas fa-circle text-danger me-1"></i>Disconnected';
        }
    }
    
    initializeChart() {
        const ctx = document.getElementById('portfolioChart').getContext('2d');
        
        this.portfolioChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
    
    updateChart(chartData) {
        if (!this.portfolioChart || !chartData.length) return;
        
        const labels = chartData.map(point => new Date(point.timestamp).toLocaleDateString());
        const values = chartData.map(point => point.value);
        
        this.portfolioChart.data.labels = labels;
        this.portfolioChart.data.datasets[0].data = values;
        this.portfolioChart.update('none');
    }
    
    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            
            // Update form defaults
            if (config.trading) {
                const symbolSelect = document.getElementById('symbol-select');
                const timeframeSelect = document.getElementById('timeframe-select');
                
                if (symbolSelect && config.trading.default_symbol) {
                    symbolSelect.value = config.trading.default_symbol;
                }
                
                if (timeframeSelect && config.trading.default_timeframe) {
                    timeframeSelect.value = config.trading.default_timeframe;
                }
            }
            
        } catch (error) {
            console.error('Error loading config:', error);
        }
    }
    
    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(value || 0);
    }
    
    formatDuration(milliseconds) {
        const seconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (days > 0) return `${days}d ${hours % 24}h`;
        if (hours > 0) return `${hours}h ${minutes % 60}m`;
        if (minutes > 0) return `${minutes}m`;
        return `${seconds}s`;
    }
    
    showToast(message, type = 'info') {
        // Create a simple toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
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
    
    startReconnectionCountdown(retrySeconds = 30) {
        // Clear any existing countdown
        this.stopReconnectionCountdown();
        
        this.nextRetryTime = Date.now() + (retrySeconds * 1000);
        this.reconnectCountdown = retrySeconds;
        
        // Update the status display immediately
        this.updateReconnectionDisplay();
        
        // Start the countdown interval
        this.reconnectInterval = setInterval(() => {
            const timeLeft = Math.max(0, Math.ceil((this.nextRetryTime - Date.now()) / 1000));
            this.reconnectCountdown = timeLeft;
            
            if (timeLeft <= 0) {
                this.stopReconnectionCountdown();
                // Reset status to show checking...
                this.updateConnectionStatusForReconnect();
            } else {
                this.updateReconnectionDisplay();
            }
        }, 1000);
    }
    
    stopReconnectionCountdown() {
        if (this.reconnectInterval) {
            clearInterval(this.reconnectInterval);
            this.reconnectInterval = null;
        }
        this.reconnectCountdown = null;
        this.nextRetryTime = null;
    }
    
    updateReconnectionDisplay() {
        const connectionIcon = document.getElementById("connection-icon");
        const connectionText = document.getElementById("connection-text");
        const cryptoStatus = document.getElementById("crypto-status");
        const connectionStatus = document.getElementById("connection-status");
        
        const countdownText = this.reconnectCountdown > 0 
            ? `Reconnecting in ${this.reconnectCountdown}s` 
            : "Reconnecting...";
        
        // Update new top-right corner connection status
        if (connectionIcon && connectionText) {
            connectionIcon.className = "fas fa-clock text-warning me-1";
            connectionText.textContent = countdownText;
        }
        
        // Update old top-right corner connection status
        if (connectionStatus && (!connectionIcon || !connectionText)) {
            connectionStatus.innerHTML = `<i class="fas fa-clock text-warning me-1"></i>${countdownText}`;
        }
        
        // Update crypto portfolio status badge
        if (cryptoStatus) {
            cryptoStatus.className = "badge bg-warning";
            cryptoStatus.textContent = countdownText;
        }
    }
    
    updateConnectionStatusForReconnect() {
        const connectionIcon = document.getElementById("connection-icon");
        const connectionText = document.getElementById("connection-text");
        const cryptoStatus = document.getElementById("crypto-status");
        const connectionStatus = document.getElementById("connection-status");
        
        // Update new top-right corner connection status
        if (connectionIcon && connectionText) {
            connectionIcon.className = "fas fa-sync fa-spin text-info me-1";
            connectionText.textContent = "Checking connection...";
        }
        
        // Update old top-right corner connection status
        if (connectionStatus && (!connectionIcon || !connectionText)) {
            connectionStatus.innerHTML = `<i class="fas fa-sync fa-spin text-info me-1"></i>Checking connection...`;
        }
        
        // Update crypto portfolio status badge
        if (cryptoStatus) {
            cryptoStatus.className = "badge bg-info";
            cryptoStatus.textContent = "Checking connection...";
        }
    }
    
    startUptimeCounter() {
        if (this.uptimeStarted) return; // Already started
        
        this.startTime = Date.now();
        this.uptimeStarted = true;
        
        // Update uptime every second
        this.uptimeInterval = setInterval(() => {
            this.updateUptimeDisplay();
        }, 1000);
        
        // Update immediately
        this.updateUptimeDisplay();
    }
    
    updateUptimeDisplay() {
        const uptimeElement = document.getElementById('system-uptime');
        if (uptimeElement) {
            if (!this.startTime) {
                uptimeElement.textContent = 'Waiting...';
                return;
            }
            const uptimeSeconds = Math.floor((Date.now() - this.startTime) / 1000);
            const uptimeText = this.formatUptime(uptimeSeconds);
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
}

// Global functions for button actions
async function startTrading(mode, tradingMode = 'single') {
    if (mode === 'live') {
        // Show confirmation modal for live trading
        const confirmModal = new bootstrap.Modal(document.getElementById('liveConfirmModal'));
        confirmModal.show();
        window.tradingApp.isLiveConfirmationPending = true;
        window.tradingApp.pendingTradingMode = tradingMode;
        return;
    }
    
    await executeStartTrading(mode, tradingMode);
}

async function confirmLiveTrading() {
    const checkbox = document.getElementById('live-confirm-checkbox');
    
    if (!checkbox.checked) {
        if (window.tradingApp && window.tradingApp.showToast) {
            window.tradingApp.showToast('Please confirm you understand the risks', 'warning');
        } else {
            alert('Please confirm you understand the risks');
        }
        return;
    }
    
    const liveConfirmModal = bootstrap.Modal.getInstance(document.getElementById('liveConfirmModal'));
    liveConfirmModal.hide();
    
    await executeStartTrading('live', window.tradingApp.pendingTradingMode || 'single');
}

async function executeStartTrading(mode, tradingMode = 'single') {
    const symbol = document.getElementById('symbol-select').value;
    const timeframe = document.getElementById('timeframe-select').value;
    
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    const tradingModeText = tradingMode === 'portfolio' ? 'portfolio' : 'single asset';
    document.getElementById('loading-message').textContent = `Starting ${mode} ${tradingModeText} trading...`;
    loadingModal.show();
    
    try {
        const response = await fetch('/api/start_trading', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mode: mode,
                symbol: symbol,
                timeframe: timeframe,
                trading_mode: tradingMode,
                confirmation: mode === 'live'
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            if (window.tradingApp && window.tradingApp.showToast) {
                window.tradingApp.showToast(result.message, 'success');
            } else {
                console.log('Trading started:', result.message);
            }
        } else {
            if (window.tradingApp && window.tradingApp.showToast) {
                window.tradingApp.showToast(result.error, 'danger');
            } else {
                console.error('Trading error:', result.error);
            }
        }
        
    } catch (error) {
        if (window.tradingApp && window.tradingApp.showToast) {
            window.tradingApp.showToast('Failed to start trading: ' + error.message, 'danger');
        } else {
            console.error('Failed to start trading:', error.message);
        }
    } finally {
        loadingModal.hide();
    }
}

async function stopTrading() {
    try {
        const response = await fetch('/api/stop_trading', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            if (window.tradingApp && window.tradingApp.showToast) {
                window.tradingApp.showToast(result.message, 'success');
            } else {
                console.log('Trading stopped:', result.message);
            }
        } else {
            if (window.tradingApp && window.tradingApp.showToast) {
                window.tradingApp.showToast(result.error, 'danger');
            } else {
                console.error('Stop trading error:', result.error);
            }
        }
        
    } catch (error) {
        if (window.tradingApp && window.tradingApp.showToast) {
            window.tradingApp.showToast('Failed to stop trading: ' + error.message, 'danger');
        } else {
            console.error('Failed to stop trading:', error.message);
        }
    }
}

async function emergencyStop() {
    if (!confirm('Are you sure you want to trigger an emergency stop? This will halt all trading immediately.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/emergency_stop', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            if (window.tradingApp && window.tradingApp.showToast) {
                window.tradingApp.showToast(result.message, 'warning');
            } else {
                console.log('Emergency stop:', result.message);
            }
        } else {
            if (window.tradingApp && window.tradingApp.showToast) {
                window.tradingApp.showToast(result.error, 'danger');
            } else {
                console.error('Emergency stop error:', result.error);
            }
        }
        
    } catch (error) {
        if (window.tradingApp && window.tradingApp.showToast) {
            window.tradingApp.showToast('Failed to execute emergency stop: ' + error.message, 'danger');
        } else {
            console.error('Failed to execute emergency stop:', error.message);
        }
    }
}

async function runSingleBacktest() {
    await runBacktest('single');
}

async function runPortfolioBacktest() {
    await runBacktest('portfolio');
}

async function runBacktest(mode = 'single') {
    const symbol = document.getElementById('symbol-select').value;
    const timeframe = document.getElementById('timeframe-select').value;
    const days = parseInt(document.getElementById('backtest-days').value);
    
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    const modeText = mode === 'portfolio' ? 'portfolio backtest (100 cryptos)' : `single asset backtest (${symbol})`;
    document.getElementById('loading-message').textContent = `Running ${modeText}...`;
    loadingModal.show();
    
    try {
        const response = await fetch('/api/backtest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                timeframe: timeframe,
                days: days,
                mode: mode
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showBacktestResults(result.results);
            
            // Show different toast messages for portfolio vs single asset
            if (mode === 'portfolio') {
                const portfolioSummary = result.results.portfolio_summary;
                const totalReturn = (portfolioSummary.total_portfolio_return * 100).toFixed(2);
                const totalTrades = portfolioSummary.total_trades;
                const profitableAssets = portfolioSummary.profitable_assets;
                const totalAssets = portfolioSummary.total_assets_tested;
                
                window.tradingApp.showToast(
                    `Portfolio backtest completed: ${totalReturn}% return, ${totalTrades} trades across ${totalAssets} assets, ${profitableAssets} profitable`, 
                    'success'
                );
            } else {
                const totalReturn = (result.results.total_return * 100).toFixed(2);
                window.tradingApp.showToast(`Backtest completed: ${totalReturn}% return`, 'success');
            }
        } else {
            window.tradingApp.showToast(result.error, 'danger');
        }
        
    } catch (error) {
        window.tradingApp.showToast('Failed to run backtest: ' + error.message, 'danger');
    } finally {
        loadingModal.hide();
    }
}

// Global crypto portfolio refresh function
function refreshCryptoPortfolio() {
    if (window.tradingDashboard) {
        window.tradingDashboard.updateCryptoPortfolio();
    }
}

// News ticker functionality
function initializeNewsTicker() {
    updateNewsTicker();
    // Update news every 10 minutes
    setInterval(() => {
        updateNewsTicker();
    }, 10 * 60 * 1000);
}

// Make sure functions are available globally immediately
window.initializeNewsTicker = initializeNewsTicker;
window.updateNewsTicker = updateNewsTicker;
window.refreshNews = refreshNews;
window.displayNews = displayNews;
window.getTimeAgo = getTimeAgo;

async function updateNewsTicker() {
    try {
        const response = await fetch('/api/crypto-news');
        if (!response.ok) return;
        
        const data = await response.json();
        displayNews(data.articles || []);
    } catch (error) {
        console.error('Error fetching news:', error);
    }
}

function displayNews(articles) {
    const ticker = document.getElementById('news-ticker');
    if (!ticker || !articles.length) return;
    
    // Create news items
    const newsItems = articles.slice(0, 5).map(article => {
        const timeAgo = getTimeAgo(new Date(article.publishedAt));
        return `<span class="news-item text-light">${article.title} (${timeAgo})</span>`;
    }).join('');
    
    ticker.innerHTML = newsItems;
}

function getTimeAgo(date) {
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 60) {
        return `${diffInMinutes}m ago`;
    } else if (diffInMinutes < 1440) {
        return `${Math.floor(diffInMinutes / 60)}h ago`;
    } else {
        return `${Math.floor(diffInMinutes / 1440)}d ago`;
    }
}

function refreshNews() {
    if (typeof window.updateNewsTicker === 'function') {
        window.updateNewsTicker();
    }
}

// State management for table sorting and filtering
const tableState = {
    portfolio: {
        sortColumn: null,
        sortDirection: 'asc',
        filters: {}
    },
    trades: {
        sortColumn: null,
        sortDirection: 'asc',
        filters: {}
    },
    performance: {
        sortColumn: null,
        sortDirection: 'asc',
        filters: {}
    }
};

// Save current filter states
function saveTableFilters() {
    tableState.portfolio.filters = {
        text: document.getElementById('portfolio-filter')?.value || '',
        pnl: document.getElementById('portfolio-pnl-filter')?.value || '',
        value: document.getElementById('portfolio-value-filter')?.value || ''
    };
    
    tableState.trades.filters = {
        text: document.getElementById('trades-filter')?.value || '',
        action: document.getElementById('trades-action-filter')?.value || '',
        pnl: document.getElementById('trades-pnl-filter')?.value || ''
    };
    
    tableState.performance.filters = {
        text: document.getElementById('performance-filter')?.value || '',
        pnl: document.getElementById('performance-pnl-filter')?.value || '',
        return: document.getElementById('performance-return-filter')?.value || '',
        status: document.getElementById('performance-status-filter')?.value || ''
    };
}

// Restore filter states
function restoreTableFilters() {
    // Portfolio filters
    if (document.getElementById('portfolio-filter')) {
        document.getElementById('portfolio-filter').value = tableState.portfolio.filters.text || '';
        document.getElementById('portfolio-pnl-filter').value = tableState.portfolio.filters.pnl || '';
        document.getElementById('portfolio-value-filter').value = tableState.portfolio.filters.value || '';
    }
    
    // Trades filters
    if (document.getElementById('trades-filter')) {
        document.getElementById('trades-filter').value = tableState.trades.filters.text || '';
        document.getElementById('trades-action-filter').value = tableState.trades.filters.action || '';
        document.getElementById('trades-pnl-filter').value = tableState.trades.filters.pnl || '';
    }
    
    // Performance filters
    if (document.getElementById('performance-filter')) {
        document.getElementById('performance-filter').value = tableState.performance.filters.text || '';
        document.getElementById('performance-pnl-filter').value = tableState.performance.filters.pnl || '';
        document.getElementById('performance-return-filter').value = tableState.performance.filters.return || '';
        document.getElementById('performance-status-filter').value = tableState.performance.filters.status || '';
    }
}

// Apply saved sorting to table
function applySavedSorting(tableType) {
    const state = tableState[tableType];
    if (state.sortColumn !== null) {
        if (tableType === 'portfolio') {
            sortPortfolio(state.sortColumn, false);
        } else if (tableType === 'trades') {
            sortTradesTable(state.sortColumn, false);
        } else if (tableType === 'performance') {
            sortPerformanceTable(state.sortColumn, false);
        }
    }
}

// Filter Functions for Tables
function filterPortfolioTable() {
    saveTableFilters(); // Save current state
    const textFilter = document.getElementById('portfolio-filter').value.toLowerCase();
    const pnlFilter = document.getElementById('portfolio-pnl-filter').value;
    const valueFilter = document.getElementById('portfolio-value-filter').value;
    const table = document.getElementById('crypto-portfolio-table');
    const rows = table.getElementsByTagName('tr');

    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        if (cells.length === 0) continue; // Skip header rows

        let showRow = true;
        
        // Text filter (symbol and name)
        if (textFilter) {
            const symbol = cells[1]?.textContent.toLowerCase() || '';
            const name = cells[2]?.textContent.toLowerCase() || '';
            if (!symbol.includes(textFilter) && !name.includes(textFilter)) {
                showRow = false;
            }
        }
        
        // P&L filter
        if (pnlFilter && cells[10]) {
            const pnlText = cells[10].textContent;
            const isPositive = pnlText.includes('+') || (!pnlText.includes('-') && !pnlText.includes('$0.00'));
            if ((pnlFilter === 'positive' && !isPositive) || (pnlFilter === 'negative' && isPositive)) {
                showRow = false;
            }
        }
        
        // Value filter
        if (valueFilter && cells[5]) {
            const valueText = cells[5].textContent.replace('$', '').replace(',', '');
            const value = parseFloat(valueText);
            if (!isNaN(value)) {
                if ((valueFilter === 'high' && value <= 15) ||
                    (valueFilter === 'medium' && (value < 5 || value > 15)) ||
                    (valueFilter === 'low' && value >= 5)) {
                    showRow = false;
                }
            }
        }
        
        row.style.display = showRow ? '' : 'none';
    }
}

function clearPortfolioFilters() {
    document.getElementById('portfolio-filter').value = '';
    document.getElementById('portfolio-pnl-filter').value = '';
    document.getElementById('portfolio-value-filter').value = '';
    // Clear state
    tableState.portfolio.filters = {};
    filterPortfolioTable();
}

function filterTradesTable() {
    saveTableFilters(); // Save current state
    const textFilter = document.getElementById('trades-filter').value.toLowerCase();
    const actionFilter = document.getElementById('trades-action-filter').value;
    const pnlFilter = document.getElementById('trades-pnl-filter').value;
    const table = document.getElementById('trades-table');
    const rows = table.getElementsByTagName('tr');

    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        if (cells.length === 0) continue; // Skip header rows

        let showRow = true;
        
        // Text filter (symbol)
        if (textFilter && cells[1]) {
            const symbol = cells[1].textContent.toLowerCase();
            if (!symbol.includes(textFilter)) {
                showRow = false;
            }
        }
        
        // Action filter
        if (actionFilter && cells[2]) {
            const action = cells[2].textContent.trim();
            if (action !== actionFilter) {
                showRow = false;
            }
        }
        
        // P&L filter
        if (pnlFilter && cells[5]) {
            const pnlText = cells[5].textContent;
            const isPositive = pnlText.includes('+') || (!pnlText.includes('-') && !pnlText.includes('$0.00'));
            if ((pnlFilter === 'positive' && !isPositive) || (pnlFilter === 'negative' && isPositive)) {
                showRow = false;
            }
        }
        
        row.style.display = showRow ? '' : 'none';
    }
}

function clearTradesFilters() {
    document.getElementById('trades-filter').value = '';
    document.getElementById('trades-action-filter').value = '';
    document.getElementById('trades-pnl-filter').value = '';
    // Clear state
    tableState.trades.filters = {};
    filterTradesTable();
}

function filterPerformanceTable() {
    saveTableFilters(); // Save current state
    const textFilter = document.getElementById('performance-filter').value.toLowerCase();
    const pnlFilter = document.getElementById('performance-pnl-filter').value;
    const returnFilter = document.getElementById('performance-return-filter').value;
    const statusFilter = document.getElementById('performance-status-filter').value;
    const table = document.getElementById('performance-table-body');
    const rows = table.getElementsByTagName('tr');

    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        if (cells.length === 0) continue; // Skip header rows

        let showRow = true;
        
        // Text filter (symbol and name)
        if (textFilter && cells[1] && cells[2]) {
            const symbol = cells[1].textContent.toLowerCase();
            const name = cells[2].textContent.toLowerCase();
            if (!symbol.includes(textFilter) && !name.includes(textFilter)) {
                showRow = false;
            }
        }
        
        // P&L filter
        if (pnlFilter && cells[6]) {
            const pnlText = cells[6].textContent;
            const isPositive = pnlText.includes('+') || (!pnlText.includes('-') && !pnlText.includes('$0.00'));
            if ((pnlFilter === 'positive' && !isPositive) || (pnlFilter === 'negative' && isPositive)) {
                showRow = false;
            }
        }
        
        // Return % filter
        if (returnFilter && cells[7]) {
            const returnText = cells[7].textContent.replace('%', '');
            const returnValue = parseFloat(returnText);
            if (!isNaN(returnValue)) {
                if ((returnFilter === 'high' && returnValue <= 50) ||
                    (returnFilter === 'medium' && (returnValue < 0 || returnValue > 50)) ||
                    (returnFilter === 'low' && returnValue >= 0)) {
                    showRow = false;
                }
            }
        }
        
        // Status filter
        if (statusFilter && cells[9]) {
            const status = cells[9].textContent.trim();
            if (status !== statusFilter) {
                showRow = false;
            }
        }
        
        row.style.display = showRow ? '' : 'none';
    }
}

function clearPerformanceFilters() {
    document.getElementById('performance-filter').value = '';
    document.getElementById('performance-pnl-filter').value = '';
    document.getElementById('performance-return-filter').value = '';
    document.getElementById('performance-status-filter').value = '';
    // Clear state
    tableState.performance.filters = {};
    filterPerformanceTable();
}

// Hook into data update functions to restore state
function restoreTableState() {
    // Wait a bit for tables to be populated
    setTimeout(() => {
        restoreTableFilters();
        
        // Apply saved sorting
        applySavedSorting('portfolio');
        applySavedSorting('trades');
        applySavedSorting('performance');
        
        // Re-apply filters
        if (document.getElementById('portfolio-filter')) {
            filterPortfolioTable();
        }
        if (document.getElementById('trades-filter')) {
            filterTradesTable();
        }
        if (document.getElementById('performance-filter')) {
            filterPerformanceTable();
        }
    }, 100);
}

// Trade a specific cryptocurrency from the portfolio


function tradeCrypto(symbol) {
    try {
        // Set the trading symbol to the selected crypto
        const symbolSelect = document.getElementById('symbol-select');
        const tradingPair = symbol + '/USDT';
        
        // Check if this trading pair exists in our options
        let optionExists = false;
        for (let option of symbolSelect.options) {
            if (option.value === tradingPair) {
                symbolSelect.value = tradingPair;
                optionExists = true;
                break;
            }
        }
        
        // If the pair doesn't exist, add it dynamically
        if (!optionExists) {
            const newOption = new Option(tradingPair, tradingPair);
            // Add to the "Popular Alts" group or create a new group
            const altGroup = symbolSelect.querySelector('optgroup[label="Popular Alts"]');
            if (altGroup) {
                altGroup.appendChild(newOption);
            } else {
                symbolSelect.appendChild(newOption);
            }
            symbolSelect.value = tradingPair;
        }
        
        // Scroll to trading controls
        document.querySelector('#trading-form').scrollIntoView({ 
            behavior: 'smooth',
            block: 'center'
        });
        
        // Show notification
        if (window.tradingApp && window.tradingApp.showToast) {
            window.tradingApp.showToast(`Trading pair set to ${tradingPair}`, 'info');
        } else {
            console.log(`Trading pair set to ${tradingPair}`);
        }
    } catch (error) {
        console.error('Error in tradeCrypto function:', error);
        if (window.tradingApp && window.tradingApp.showToast) {
            window.tradingApp.showToast('Error setting trading pair', 'error');
        }
    }
}

// Global variable to store current chart instance
let currentCryptoChart = null;

// New function to show individual crypto chart
function showCryptoChart(symbol, duration = '1d') {
    // Fetch individual crypto chart data with duration
    fetch(`/api/crypto-chart/${symbol}?duration=${duration}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                if (window.tradingApp) {
                    window.tradingApp.showToast(`Error: ${data.error}`, 'error');
                }
                return;
            }
            
            // Create modal for individual crypto chart
            const modalHtml = `
                <div class="modal fade" id="cryptoChartModal" tabindex="-1" aria-labelledby="cryptoChartModalLabel" aria-hidden="true">
                    <div class="modal-dialog modal-xl modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="cryptoChartModalLabel">
                                    ${data.name} (${data.symbol}) - $${data.current_price.toFixed(data.current_price < 1 ? 6 : 2)}
                                </h5>
                                <div class="btn-group me-3" role="group" aria-label="Duration Selection">
                                    <button type="button" class="btn btn-outline-primary btn-sm duration-btn" data-duration="1h" onclick="updateChartDuration('${data.symbol}', '1h')">1H</button>
                                    <button type="button" class="btn btn-outline-primary btn-sm duration-btn" data-duration="4h" onclick="updateChartDuration('${data.symbol}', '4h')">4H</button>
                                    <button type="button" class="btn btn-outline-primary btn-sm duration-btn active" data-duration="1d" onclick="updateChartDuration('${data.symbol}', '1d')">1D</button>
                                    <button type="button" class="btn btn-outline-primary btn-sm duration-btn" data-duration="7d" onclick="updateChartDuration('${data.symbol}', '7d')">7D</button>
                                    <button type="button" class="btn btn-outline-primary btn-sm duration-btn" data-duration="30d" onclick="updateChartDuration('${data.symbol}', '30d')">30D</button>
                                </div>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <h6>Current Price</h6>
                                        <span class="h4">$${data.current_price.toFixed(data.current_price < 1 ? 6 : 2)}</span>
                                    </div>
                                    <div class="col-md-6">
                                        <h6>Performance</h6>
                                        <span class="h4 ${data.pnl_percent >= 0 ? 'text-success' : 'text-danger'}">
                                            ${data.pnl_percent >= 0 ? '+' : ''}${data.pnl_percent.toFixed(2)}%
                                        </span>
                                    </div>
                                </div>
                                <div class="chart-container-responsive">
                                    <canvas id="individualCryptoChart"></canvas>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-outline-secondary" onclick="showMainDashboard(); bootstrap.Modal.getInstance(document.getElementById('cryptoChartModal')).hide();">
                                    <i class="fas fa-home me-1"></i>Dashboard
                                </button>
                                <button type="button" class="btn btn-primary" onclick="tradeCrypto('${data.symbol}'); bootstrap.Modal.getInstance(document.getElementById('cryptoChartModal')).hide();">
                                    <i class="fas fa-exchange-alt me-1"></i>Trade ${data.symbol}
                                </button>
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if any
            const existingModal = document.getElementById('cryptoChartModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // Add modal to page
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // Show modal
            const cryptoChartModal = new bootstrap.Modal(document.getElementById('cryptoChartModal'));
            cryptoChartModal.show();
            
            // Create chart after modal is shown
            cryptoChartModal._element.addEventListener('shown.bs.modal', () => {
                const ctx = document.getElementById('individualCryptoChart').getContext('2d');
                
                // Destroy existing chart if it exists
                if (currentCryptoChart) {
                    currentCryptoChart.destroy();
                }
                
                currentCryptoChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: `${data.symbol} Price`,
                            data: data.price_history,
                            borderColor: data.pnl_percent >= 0 ? '#28a745' : '#dc3545',
                            backgroundColor: data.pnl_percent >= 0 ? 'rgba(40, 167, 69, 0.1)' : 'rgba(220, 53, 69, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: false,
                                ticks: {
                                    callback: function(value) {
                                        return '$' + value.toFixed(value < 1 ? 6 : 2);
                                    }
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return `${data.symbol}: $${context.parsed.y.toFixed(context.parsed.y < 1 ? 6 : 2)}`;
                                    }
                                }
                            }
                        }
                    }
                });
            });
        })
        .catch(error => {
            console.error('Error fetching crypto chart:', error);
            if (window.tradingApp) {
                window.tradingApp.showToast('Error loading chart data', 'error');
            }
        });
}

// Function to update chart duration
function updateChartDuration(symbol, duration) {
    // Update active button
    document.querySelectorAll('.duration-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.duration === duration) {
            btn.classList.add('active');
        }
    });
    
    // Fetch new data and update chart
    fetch(`/api/crypto-chart/${symbol}?duration=${duration}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                if (window.tradingApp) {
                    window.tradingApp.showToast(`Error: ${data.error}`, 'error');
                }
                return;
            }
            
            // Update chart data
            if (currentCryptoChart) {
                // Debug logging
                console.log(`Updating chart for ${symbol} with duration ${duration}`);
                console.log(`Data points: ${data.price_history.length}, Labels: ${data.labels.length}`);
                console.log(`Price range: ${Math.min(...data.price_history).toFixed(4)} - ${Math.max(...data.price_history).toFixed(4)}`);
                
                currentCryptoChart.data.labels = data.labels;
                currentCryptoChart.data.datasets[0].data = data.price_history;
                currentCryptoChart.data.datasets[0].borderColor = data.pnl_percent >= 0 ? '#28a745' : '#dc3545';
                currentCryptoChart.data.datasets[0].backgroundColor = data.pnl_percent >= 0 ? 'rgba(40, 167, 69, 0.1)' : 'rgba(220, 53, 69, 0.1)';
                
                // Force a complete refresh
                currentCryptoChart.update('none');
                currentCryptoChart.resize();
            }
            
            // Update modal title with current price
            const modalTitle = document.getElementById('cryptoChartModalLabel');
            if (modalTitle) {
                modalTitle.textContent = `${data.name} (${data.symbol}) - $${data.current_price.toFixed(data.current_price < 1 ? 6 : 2)}`;
            }
            
            // Update performance display
            const performanceSpan = document.querySelector('.modal-body .h4.text-success, .modal-body .h4.text-danger');
            if (performanceSpan) {
                performanceSpan.className = `h4 ${data.pnl_percent >= 0 ? 'text-success' : 'text-danger'}`;
                performanceSpan.textContent = `${data.pnl_percent >= 0 ? '+' : ''}${data.pnl_percent.toFixed(2)}%`;
            }
        })
        .catch(error => {
            console.error('Error updating chart duration:', error);
            if (window.tradingApp) {
                window.tradingApp.showToast('Error updating chart duration', 'error');
            }
        });
}

// Portfolio management functions
function exportPortfolio() {
    window.open('/api/export-portfolio', '_blank');
}

function exportATOTax() {
    window.open('/api/export-ato-tax', '_blank');
}

function resetEntireProgram() {
    if (confirm('PROGRAM RESET: This will completely reset the entire trading system to its initial state. All data will be cleared and the portfolio will be reset to $10 per cryptocurrency. This cannot be undone. Continue?')) {
        fetch('/api/reset-entire-program', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.tradingApp.showToast('PROGRAM RESET COMPLETE: ' + data.message, 'success');
                    // Force refresh the page after a short delay to show all changes
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    window.tradingApp.showToast('Program reset failed: ' + data.error, 'danger');
                }
            })
            .catch(error => {
                window.tradingApp.showToast('Error during program reset: ' + error.message, 'danger');
            });
    }
}

function showBacktestResults(results) {
    const resultsDiv = document.getElementById('backtest-results');
    
    // Clear existing content
    resultsDiv.textContent = '';
    
    // Create the structure using safe DOM methods
    const rowDiv = document.createElement('div');
    rowDiv.className = 'row';
    
    // Performance Metrics Column
    const col1 = document.createElement('div');
    col1.className = 'col-md-6';
    const h6_1 = document.createElement('h6');
    h6_1.textContent = 'Performance Metrics';
    col1.appendChild(h6_1);
    
    const table1 = document.createElement('table');
    table1.className = 'table table-sm';
    
    // Add performance metrics rows
    const metricsData = [
        ['Total Return', (results.total_return * 100).toFixed(2) + '%'],
        ['Sharpe Ratio', results.sharpe_ratio.toFixed(3)],
        ['Max Drawdown', (results.max_drawdown * 100).toFixed(2) + '%'],
        ['Calmar Ratio', results.calmar_ratio.toFixed(3)]
    ];
    
    metricsData.forEach(([label, value]) => {
        const row = document.createElement('tr');
        const td1 = document.createElement('td');
        td1.textContent = label;
        const td2 = document.createElement('td');
        td2.className = 'text-end';
        td2.textContent = value;
        row.appendChild(td1);
        row.appendChild(td2);
        table1.appendChild(row);
    });
    
    col1.appendChild(table1);
    rowDiv.appendChild(col1);
    
    // Trading Statistics Column
    const col2 = document.createElement('div');
    col2.className = 'col-md-6';
    const h6_2 = document.createElement('h6');
    h6_2.textContent = 'Trading Statistics';
    col2.appendChild(h6_2);
    
    const table2 = document.createElement('table');
    table2.className = 'table table-sm';
    
    // Add trading statistics rows
    const statsData = [
        ['Total Trades', results.total_trades.toString()],
        ['Win Rate', (results.win_rate * 100).toFixed(1) + '%'],
        ['Profit Factor', results.profit_factor.toFixed(2)],
        ['Avg Win', '$' + results.avg_win.toFixed(2)]
    ];
    
    statsData.forEach(([label, value]) => {
        const row = document.createElement('tr');
        const td1 = document.createElement('td');
        td1.textContent = label;
        const td2 = document.createElement('td');
        td2.className = 'text-end';
        td2.textContent = value;
        row.appendChild(td1);
        row.appendChild(td2);
        table2.appendChild(row);
    });
    
    col2.appendChild(table2);
    rowDiv.appendChild(col2);
    
    resultsDiv.appendChild(rowDiv);
    
    // Summary section
    const summaryRow = document.createElement('div');
    summaryRow.className = 'row mt-3';
    const summaryCol = document.createElement('div');
    summaryCol.className = 'col-12';
    
    const summaryH6 = document.createElement('h6');
    summaryH6.textContent = 'Summary';
    summaryCol.appendChild(summaryH6);
    
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-info';
    
    // Create text nodes for summary
    const initialCapitalText = document.createTextNode('Initial Capital: $' + results.initial_capital.toLocaleString());
    const finalValueText = document.createTextNode('Final Value: $' + results.final_value.toLocaleString());
    const profitLossText = document.createTextNode('Profit/Loss: $' + (results.final_value - results.initial_capital).toLocaleString());
    
    alertDiv.appendChild(initialCapitalText);
    alertDiv.appendChild(document.createElement('br'));
    alertDiv.appendChild(finalValueText);
    alertDiv.appendChild(document.createElement('br'));
    alertDiv.appendChild(profitLossText);
    
    summaryCol.appendChild(alertDiv);
    summaryRow.appendChild(summaryCol);
    resultsDiv.appendChild(summaryRow);
    
    // Show modal with unique variable name
    const backtestModal = new bootstrap.Modal(document.getElementById('backtestModal'));
    backtestModal.show();
}

// Portfolio sorting functionality
function sortPortfolio(column) {
    if (!window.cryptoPortfolioData) return;
    
    // Toggle sort direction if same column
    if (window.sortColumn === column) {
        window.sortDirection = window.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        window.sortColumn = column;
        window.sortDirection = 'asc';
    }
    
    // Apply the sort
    applySortToCryptoData();
    
    // Update sort icons
    updateSortIcons(column);
    
    // Re-render table
    renderCryptoTable();
}

function applySortToCryptoData() {
    if (!window.cryptoPortfolioData || !window.sortColumn) return;
    
    // Sort the data
    window.cryptoPortfolioData.sort((a, b) => {
        let valueA, valueB;
        
        switch(window.sortColumn) {
            case 'rank':
                valueA = parseInt(a.rank);
                valueB = parseInt(b.rank);
                break;
            case 'symbol':
            case 'name':
                valueA = a[window.sortColumn].toLowerCase();
                valueB = b[window.sortColumn].toLowerCase();
                break;
            case 'quantity':
            case 'current_price':
            case 'current_value':
            case 'pnl':
            case 'pnl_percent':
                valueA = parseFloat(a[window.sortColumn] || 0);
                valueB = parseFloat(b[window.sortColumn] || 0);
                break;
            case 'price':
                valueA = parseFloat(a.current_price || 0);
                valueB = parseFloat(b.current_price || 0);
                break;
            case 'value':
                valueA = parseFloat(a.current_value || 0);
                valueB = parseFloat(b.current_value || 0);
                break;
            case 'target_sell':
                valueA = parseFloat(a.target_sell_price || 0);
                valueB = parseFloat(b.target_sell_price || 0);
                break;
            case 'approaching_sell':
                valueA = a.target_sell_price ? Math.min(100, Math.max(0, (a.current_price / a.target_sell_price) * 100)) : 0;
                valueB = b.target_sell_price ? Math.min(100, Math.max(0, (b.current_price / b.target_sell_price) * 100)) : 0;
                break;
            case 'target_buy':
                valueA = parseFloat(a.target_buy_price || 0);
                valueB = parseFloat(b.target_buy_price || 0);
                break;
            case 'projected_pnl':
                valueA = parseFloat(a.projected_sell_pnl || 0);
                valueB = parseFloat(b.projected_sell_pnl || 0);
                break;
            default:
                return 0;
        }
        
        if (valueA < valueB) return window.sortDirection === 'asc' ? -1 : 1;
        if (valueA > valueB) return window.sortDirection === 'asc' ? 1 : -1;
        return 0;
    });
}

function updateSortIcons(activeColumn) {
    // Reset all sort icons
    const columns = ['rank', 'symbol', 'name', 'quantity', 'price', 'value', 'pnl', 'pnl_percent'];
    columns.forEach(col => {
        const icon = document.getElementById(`sort-${col}`);
        if (icon) {
            icon.className = 'fas fa-sort text-muted';
        }
    });
    
    // Set active column icon
    const activeIcon = document.getElementById(`sort-${activeColumn}`);
    if (activeIcon) {
        if (window.sortDirection === 'asc') {
            activeIcon.className = 'fas fa-sort-up text-primary';
        } else {
            activeIcon.className = 'fas fa-sort-down text-primary';
        }
    }
}

function renderCryptoTable() {
    if (!window.cryptoPortfolioData) return;
    
    const tbody = document.getElementById('crypto-portfolio-table');
    tbody.innerHTML = window.cryptoPortfolioData.map(crypto => {
        const pnlClass = crypto.pnl >= 0 ? 'text-success' : 'text-danger';
        const priceDisplay = crypto.current_price < 1 ? crypto.current_price.toFixed(6) : crypto.current_price.toFixed(2);
        
        // Calculate proximity to target sell price  
        const proximityClass = calculateTargetProximity(crypto.current_price, crypto.target_sell_price);
        
        const projectedPnl = crypto.projected_sell_pnl || 0;
        const projectedPnlClass = projectedPnl >= 0 ? 'text-success' : 'text-danger';
        const targetBuyDisplay = crypto.target_buy_price ? crypto.target_buy_price.toFixed(crypto.target_buy_price < 1 ? 6 : 2) : '0.00';
        
        return `
            <tr class="${proximityClass}">
                <td class="fw-bold">${crypto.rank}</td>
                <td class="fw-semibold">${crypto.symbol}</td>
                <td class="text-muted">${crypto.name}</td>
                <td>${crypto.quantity.toFixed(4)}</td>
                <td>$${priceDisplay}</td>
                <td>$${crypto.current_value.toFixed(2)}</td>
                <td class="bg-light text-warning">$${crypto.target_sell_price ? crypto.target_sell_price.toFixed(crypto.target_sell_price < 1 ? 6 : 2) : 'N/A'}</td>
                <td class="bg-light text-success">$${targetBuyDisplay}</td>
                <td class="bg-light ${projectedPnlClass}">$${projectedPnl >= 0 ? '+' : ''}${projectedPnl.toFixed(2)}</td>
                <td class="${pnlClass}">$${crypto.pnl.toFixed(2)}</td>
                <td class="${pnlClass}">${crypto.pnl_percent.toFixed(2)}%</td>
                <td>
                    <button class="btn btn-outline-primary btn-sm me-1" onclick="showCryptoChart('${crypto.symbol}')" title="View ${crypto.symbol} Chart">
                        <i class="fas fa-chart-line"></i>
                    </button>
                    <button class="btn btn-outline-success btn-sm" onclick="tradeCrypto('${crypto.symbol}')" title="Trade ${crypto.symbol}">
                        <i class="fas fa-exchange-alt"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// Home/Dashboard navigation function
function showMainDashboard() {
    // Close any open modals
    const modals = document.querySelectorAll('.modal.show');
    modals.forEach(modal => {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    });
    
    // Reset to main dashboard view
    // Activate portfolio tab if tabs exist
    const portfolioTab = document.getElementById('portfolio-tab');
    if (portfolioTab) {
        portfolioTab.click();
    }
    
    // Scroll to top smoothly
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Refresh dashboard data
    if (window.tradingApp) {
        window.tradingApp.updateDashboard();
    }
    
    console.log('Returned to main dashboard');
}

// Calculate proximity to target sell price for color coding
function calculateTargetProximity(currentPrice, targetPrice) {
    if (!targetPrice || !currentPrice || targetPrice <= currentPrice) {
        // Target already reached or invalid data
        if (targetPrice && currentPrice >= targetPrice) {
            return 'target-proximity-achieved';
        }
        return 'target-proximity-cold';
    }
    
    // Calculate how close current price is to target (as percentage)
    const proximityPercent = (currentPrice / targetPrice) * 100;
    
    if (proximityPercent >= 95) {
        return 'target-proximity-very-hot'; // 95%+ to target - red
    } else if (proximityPercent >= 90) {
        return 'target-proximity-hot'; // 90-95% to target - orange
    } else if (proximityPercent >= 80) {
        return 'target-proximity-warm'; // 80-90% to target - yellow
    } else if (proximityPercent >= 60) {
        return 'target-proximity-cool'; // 60-80% to target - blue
    } else {
        return 'target-proximity-cold'; // <60% to target - gray
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.tradingApp = new TradingApp();
});


// API Status Display Functions
function updateConnectionStatusDisplay(apiStatus) {
    const connectionIcon = document.getElementById("connection-icon");
    const connectionText = document.getElementById("connection-text");
    const cryptoStatus = document.getElementById("crypto-status");
    const connectionStatus = document.getElementById("connection-status");
    
    console.log('Updating connection status display with:', apiStatus);
    
    if (apiStatus.status === "connected") {
        // Stop any reconnection countdown since we're connected
        if (window.tradingApp) {
            window.tradingApp.stopReconnectionCountdown();
            // Restart trading countdown when connection is restored
            window.tradingApp.startCountdown();
            // Start uptime counter when connection is first confirmed
            window.tradingApp.startUptimeCounter();
        }
        
        // Update new top-right corner connection status (if elements exist)
        if (connectionIcon && connectionText) {
            connectionIcon.className = "fas fa-circle text-success me-1";
            connectionText.textContent = `Connected to ${apiStatus.api_provider}`;
        }
        
        // Update old top-right corner connection status (fallback)
        if (connectionStatus && (!connectionIcon || !connectionText)) {
            connectionStatus.innerHTML = `<i class="fas fa-circle text-success me-1"></i>Connected to ${apiStatus.api_provider}`;
        }
        
        // Update crypto portfolio status badge
        if (cryptoStatus) {
            cryptoStatus.className = "badge bg-success";
            cryptoStatus.textContent = `Connected to ${apiStatus.api_provider}`;
        }
        
        // Clear any previous disconnection warning
        window.connectionLost = false;
        
        console.log('Status updated: Connected to', apiStatus.api_provider);
    } else {
        // Stop trading countdown when connection is lost
        if (window.tradingApp) {
            if (window.tradingApp.countdownInterval) {
                clearInterval(window.tradingApp.countdownInterval);
                window.tradingApp.countdownInterval = null;
            }
            // Update countdown display to show connection issue
            const countdownElement = document.getElementById('trading-countdown');
            if (countdownElement) {
                countdownElement.textContent = 'Connection Lost';
                countdownElement.className = 'badge bg-danger ms-2';
            }
        }
        
        // Update new top-right corner connection status (if elements exist)
        if (connectionIcon && connectionText) {
            connectionIcon.className = "fas fa-circle text-danger me-1";
            connectionText.textContent = "Connection Lost";
        }
        
        // Update old top-right corner connection status (fallback)
        if (connectionStatus && (!connectionIcon || !connectionText)) {
            connectionStatus.innerHTML = `<i class="fas fa-circle text-danger me-1"></i>Connection Lost`;
        }
        
        // Update crypto portfolio status badge
        if (cryptoStatus) {
            cryptoStatus.className = "badge bg-danger";
            cryptoStatus.textContent = "Connection Lost";
        }
        
        // Show warning popup if connection was lost and start reconnection countdown
        if (!window.connectionLost) {
            window.connectionLost = true;
            showConnectionWarning(apiStatus.error || "Connection failed");
            
            // Start reconnection countdown - CoinGecko API retries every 30 seconds
            if (window.tradingApp) {
                window.tradingApp.startReconnectionCountdown(30);
            }
        }
        
        console.log('Status updated: Connection Lost');
    }
}

// Show connection warning popup
function showConnectionWarning(errorMessage) {
    // Remove existing modal if present
    const existingModal = document.getElementById('connectionWarningModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal elements safely
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'connectionWarningModal';
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-hidden', 'true');
    
    const modalDialog = document.createElement('div');
    modalDialog.className = 'modal-dialog modal-dialog-centered';
    
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content border-warning';
    
    // Header
    const modalHeader = document.createElement('div');
    modalHeader.className = 'modal-header bg-warning text-dark';
    
    const modalTitle = document.createElement('h5');
    modalTitle.className = 'modal-title';
    modalTitle.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Connection Warning';
    
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'btn-close';
    closeButton.setAttribute('data-bs-dismiss', 'modal');
    
    modalHeader.appendChild(modalTitle);
    modalHeader.appendChild(closeButton);
    
    // Body
    const modalBody = document.createElement('div');
    modalBody.className = 'modal-body';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning mb-3';
    alertDiv.innerHTML = '<strong>API Connection Lost!</strong>';
    
    const p1 = document.createElement('p');
    p1.textContent = 'The connection to the cryptocurrency price API has been interrupted.';
    
    const p2 = document.createElement('p');
    p2.innerHTML = '<strong>Error:</strong> ';
    const errorSpan = document.createElement('span');
    errorSpan.textContent = errorMessage; // Safe text content
    p2.appendChild(errorSpan);
    
    const p3 = document.createElement('p');
    p3.className = 'mb-0';
    p3.textContent = 'The system will continue using simulated prices and automatically retry the connection.';
    
    modalBody.appendChild(alertDiv);
    modalBody.appendChild(p1);
    modalBody.appendChild(p2);
    modalBody.appendChild(p3);
    
    // Footer
    const modalFooter = document.createElement('div');
    modalFooter.className = 'modal-footer';
    
    const understoodButton = document.createElement('button');
    understoodButton.type = 'button';
    understoodButton.className = 'btn btn-warning';
    understoodButton.setAttribute('data-bs-dismiss', 'modal');
    understoodButton.innerHTML = '<i class="fas fa-check me-1"></i>Understood';
    
    modalFooter.appendChild(understoodButton);
    
    // Assemble modal
    modalContent.appendChild(modalHeader);
    modalContent.appendChild(modalBody);
    modalContent.appendChild(modalFooter);
    modalDialog.appendChild(modalContent);
    modal.appendChild(modalDialog);
    
    // Add modal to page
    document.body.appendChild(modal);
    
    // Show the modal
    const connectionWarningModal = new bootstrap.Modal(document.getElementById('connectionWarningModal'));
    connectionWarningModal.show();
    
    console.log('Connection warning popup displayed');
}

// Check API status and update display
function checkApiStatusAndDisplay() {
    fetch("/api/price-source-status")
        .then(response => response.json())
        .then(data => {
            updateConnectionStatusDisplay(data.status);
        })
        .catch(error => {
            console.error("Error checking API status:", error);
            updateConnectionStatusDisplay({
                status: "error",
                error: "Connection failed",
                api_provider: "Unknown"
            });
        });
}

// Initialize API status display on page load and update periodically
document.addEventListener("DOMContentLoaded", function() {
    // Initialize connection status tracking
    window.connectionLost = false;
    
    const connectionText = document.getElementById('connection-text');
    const cryptoStatus = document.getElementById('crypto-status');
    
    if (connectionText) {
        connectionText.textContent = 'Connecting...';
    }
    if (cryptoStatus) {
        cryptoStatus.textContent = 'Connecting...';
    }
    
    console.log('Connection status display initialized');
    
    setTimeout(checkApiStatusAndDisplay, 2000); // Wait for page to load
    setInterval(checkApiStatusAndDisplay, 30000); // Check every 30 seconds
});

// Dashboard Navigation Functions
function showMainDashboard() {
    document.querySelectorAll('[id$="-dashboard"]').forEach(el => el.classList.add('d-none'));
    const mainDashboard = document.querySelector('.container-fluid[id]:not([id*="dashboard"]), .container-fluid:not([id])');
    if (mainDashboard) {
        mainDashboard.style.display = 'block';
    }
    
    // Show all main dashboard sections
    document.querySelectorAll('.row').forEach(row => {
        if (!row.closest('#performance-dashboard') && !row.closest('#positions-dashboard')) {
            row.style.display = '';
        }
    });
    
    // Update navbar buttons
    document.querySelectorAll('.navbar .btn').forEach(btn => btn.classList.remove('active'));
    const mainBtn = document.querySelector('[onclick="showMainDashboard()"]');
    if (mainBtn) mainBtn.classList.add('active');
    
    // Update dashboard data
    if (window.tradingApp) {
        window.tradingApp.updateDashboard();
    }
}

function showPerformanceDashboard() {
    document.querySelectorAll('.row').forEach(row => {
        if (!row.closest('#performance-dashboard') && !row.closest('#positions-dashboard')) {
            row.style.display = 'none';
        }
    });
    
    document.getElementById('performance-dashboard').classList.remove('d-none');
    document.getElementById('positions-dashboard').classList.add('d-none');
    
    // Update navbar buttons
    document.querySelectorAll('.navbar .btn').forEach(btn => btn.classList.remove('active'));
    const perfBtn = document.querySelector('[onclick="showPerformanceDashboard()"]');
    if (perfBtn) perfBtn.classList.add('active');
    
    // Load performance data
    updatePerformanceData();
}

function showCurrentPositions() {
    document.querySelectorAll('.row').forEach(row => {
        if (!row.closest('#performance-dashboard') && !row.closest('#positions-dashboard')) {
            row.style.display = 'none';
        }
    });
    
    document.getElementById('performance-dashboard').classList.add('d-none');
    document.getElementById('positions-dashboard').classList.remove('d-none');
    
    // Update navbar buttons
    document.querySelectorAll('.navbar .btn').forEach(btn => btn.classList.remove('active'));
    const posBtn = document.querySelector('[onclick="showCurrentPositions()"]');
    if (posBtn) posBtn.classList.add('active');
    
    // Load positions data
    updatePositionsData();
}

// Performance Dashboard Functions
async function updatePerformanceData() {
    try {
        const response = await fetch('/api/portfolio-performance');
        const data = await response.json();
        
        if (response.ok) {
            displayPerformanceData(data);
        } else {
            console.error('Error loading performance data:', data.error);
            if (window.tradingApp) {
                window.tradingApp.showToast('Failed to load performance data', 'danger');
            }
        }
    } catch (error) {
        console.error('Error fetching performance data:', error);
        if (window.tradingApp) {
            window.tradingApp.showToast('Failed to fetch performance data', 'danger');
        }
    }
}

function displayPerformanceData(data) {
    // Update summary metrics
    document.getElementById('perf-total-invested').textContent = '$' + data.summary.total_invested.toLocaleString();
    document.getElementById('perf-current-value').textContent = '$' + data.summary.total_current_value.toLocaleString();
    document.getElementById('perf-total-pnl').textContent = '$' + data.summary.total_accumulated_pnl.toLocaleString();
    document.getElementById('perf-overall-return').textContent = data.summary.overall_return_percent.toFixed(2) + '%';
    document.getElementById('perf-winners').textContent = data.summary.winners_count;
    document.getElementById('perf-win-rate').textContent = data.summary.win_rate.toFixed(1) + '%';
    
    // Update P&L color
    const pnlElement = document.getElementById('perf-total-pnl');
    const returnElement = document.getElementById('perf-overall-return');
    if (data.summary.total_accumulated_pnl > 0) {
        pnlElement.className = 'text-success';
        returnElement.className = 'text-success';
    } else if (data.summary.total_accumulated_pnl < 0) {
        pnlElement.className = 'text-danger';
        returnElement.className = 'text-danger';
    }
    
    // Update table
    const tbody = document.getElementById('performance-table-body');
    tbody.innerHTML = '';
    
    data.performance.forEach((crypto) => {
        const row = document.createElement('tr');
        const statusClass = crypto.status === 'winning' ? 'text-success' : 'text-danger';
        const pnlClass = crypto.accumulated_pnl_percent > 0 ? 'text-success' : 'text-danger';
        
        row.innerHTML = `
            <td>${crypto.rank}</td>
            <td><strong>${crypto.symbol}</strong></td>
            <td>${crypto.name}</td>
            <td>${crypto.days_invested}</td>
            <td>$${crypto.total_invested.toLocaleString()}</td>
            <td>$${crypto.current_value.toLocaleString()}</td>
            <td class="${pnlClass}">$${crypto.total_accumulated_pnl.toLocaleString()}</td>
            <td class="${pnlClass}">${crypto.accumulated_pnl_percent.toFixed(2)}%</td>
            <td>${crypto.daily_return_percent.toFixed(3)}%</td>
            <td><span class="badge ${crypto.best_performer ? 'bg-success' : crypto.status === 'winning' ? 'bg-info' : 'bg-secondary'}">${crypto.status === 'winning' ? 'WINNING' : 'LOSING'}</span></td>
        `;
        tbody.appendChild(row);
    });
}

// Current Positions Functions
async function updatePositionsData() {
    try {
        const response = await fetch('/api/current-positions');
        const data = await response.json();
        
        if (response.ok) {
            displayPositionsData(data);
        } else {
            console.error('Error loading positions data:', data.error);
            if (window.tradingApp) {
                window.tradingApp.showToast('Failed to load positions data', 'danger');
            }
        }
    } catch (error) {
        console.error('Error fetching positions data:', error);
        if (window.tradingApp) {
            window.tradingApp.showToast('Failed to fetch positions data', 'danger');
        }
    }
}

function displayPositionsData(data) {
    // Update summary metrics
    document.getElementById('pos-total-count').textContent = data.summary.total_positions;
    document.getElementById('pos-total-value').textContent = '$' + data.summary.total_position_value.toLocaleString();
    document.getElementById('pos-unrealized-pnl').textContent = '$' + data.summary.total_unrealized_pnl.toLocaleString();
    
    // Count strong gains
    const strongGains = data.positions.filter(p => p.status === 'strong_gain').length;
    document.getElementById('pos-strong-gains').textContent = strongGains;
    
    // Update P&L color
    const pnlElement = document.getElementById('pos-unrealized-pnl');
    if (data.summary.total_unrealized_pnl > 0) {
        pnlElement.className = 'text-success';
    } else if (data.summary.total_unrealized_pnl < 0) {
        pnlElement.className = 'text-danger';
    }
    
    // Update table
    const tbody = document.getElementById('positions-table-body');
    tbody.innerHTML = '';
    
    data.positions.forEach((position) => {
        const row = document.createElement('tr');
        const pnlClass = position.unrealized_pnl > 0 ? 'text-success' : 'text-danger';
        
        let statusBadge = '';
        switch (position.status) {
            case 'strong_gain':
                statusBadge = '<span class="badge bg-success">Strong Gain</span>';
                break;
            case 'moderate_gain':
                statusBadge = '<span class="badge bg-info">Moderate Gain</span>';
                break;
            case 'stable':
                statusBadge = '<span class="badge bg-secondary">Stable</span>';
                break;
            case 'moderate_loss':
                statusBadge = '<span class="badge bg-warning">Moderate Loss</span>';
                break;
            case 'significant_loss':
                statusBadge = '<span class="badge bg-danger">Significant Loss</span>';
                break;
        }
        
        row.innerHTML = `
            <td><strong>${position.symbol}</strong></td>
            <td>${position.name}</td>
            <td>${position.quantity.toFixed(6)}</td>
            <td>$${position.current_price.toFixed(4)}</td>
            <td>$${position.current_value.toLocaleString()}</td>
            <td>${position.position_percent.toFixed(1)}%</td>
            <td class="${pnlClass}">$${position.unrealized_pnl.toLocaleString()}</td>
            <td class="${pnlClass}">${position.pnl_percent.toFixed(2)}%</td>
            <td>$${position.avg_buy_price.toFixed(4)}</td>
            <td class="text-info">$${position.potential_profit.toLocaleString()}</td>
            <td>${statusBadge}</td>
        `;
        tbody.appendChild(row);
    });
}

// Enhanced Table Sorting Functions with Visual Feedback
window.perfSortState = { column: -1, direction: 'desc' };

function sortPerformanceTable(columnIndex, toggleDirection = true) {
    const table = document.getElementById('performance-table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Save state to tableState
    if (toggleDirection) {
        if (tableState.performance.sortColumn === columnIndex) {
            tableState.performance.sortDirection = tableState.performance.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            tableState.performance.sortColumn = columnIndex;
            tableState.performance.sortDirection = 'desc';
        }
    }
    
    // Update legacy sort state for compatibility
    window.perfSortState = window.perfSortState || {};
    window.perfSortState.column = tableState.performance.sortColumn;
    window.perfSortState.direction = tableState.performance.sortDirection;
    
    // Clear all sort indicators and set active one
    table.querySelectorAll('th i.fas').forEach(icon => {
        icon.className = 'fas fa-sort text-muted ms-1';
    });
    const currentHeader = table.querySelector(`th:nth-child(${columnIndex + 1}) i.fas`);
    if (currentHeader) {
        currentHeader.className = `fas fa-sort-${tableState.performance.sortDirection === 'asc' ? 'up' : 'down'} text-white ms-1`;
    }
    
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent.trim();
        const bVal = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as number
        const aNum = parseFloat(aVal.replace(/[$,%+\-]/g, ''));
        const bNum = parseFloat(bVal.replace(/[$,%+\-]/g, ''));
        
        let result = 0;
        if (!isNaN(aNum) && !isNaN(bNum)) {
            result = aNum - bNum;
        } else {
            result = aVal.localeCompare(bVal);
        }
        
        return tableState.performance.sortDirection === 'asc' ? result : -result;
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

window.posSortState = { column: -1, direction: 'desc' };

function sortPositionsTable(columnIndex) {
    const table = document.getElementById('positions-table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Determine sort direction
    if (window.posSortState.column === columnIndex) {
        window.posSortState.direction = window.posSortState.direction === 'asc' ? 'desc' : 'asc';
    } else {
        window.posSortState.column = columnIndex;
        window.posSortState.direction = 'desc';
    }
    
    // Clear all sort indicators and set active one
    table.querySelectorAll('th i.fas').forEach(icon => {
        icon.className = 'fas fa-sort text-muted ms-1';
    });
    const currentHeader = table.querySelector(`th:nth-child(${columnIndex + 1}) i.fas`);
    if (currentHeader) {
        currentHeader.className = `fas fa-sort-${window.posSortState.direction === 'asc' ? 'up' : 'down'} text-primary ms-1`;
    }
    
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent.trim();
        const bVal = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as number
        const aNum = parseFloat(aVal.replace(/[$,%+\-]/g, ''));
        const bNum = parseFloat(bVal.replace(/[$,%+\-]/g, ''));
        
        let result = 0;
        if (!isNaN(aNum) && !isNaN(bNum)) {
            result = aNum - bNum;
        } else {
            result = aVal.localeCompare(bVal);
        }
        
        return window.posSortState.direction === 'asc' ? result : -result;
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

window.tradesSortState = { column: -1, direction: 'desc' };

function sortTradesTable(columnIndex, toggleDirection = true) {
    const table = document.querySelector('#trades-table').closest('table');
    const tbody = document.getElementById('trades-table');
    const rows = Array.from(tbody.querySelectorAll('tr')).filter(row => row.cells.length > 1);
    
    // Return early if no data to sort
    if (rows.length === 0) return;
    
    // Save state to tableState
    if (toggleDirection) {
        if (tableState.trades.sortColumn === columnIndex) {
            tableState.trades.sortDirection = tableState.trades.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            tableState.trades.sortColumn = columnIndex;
            tableState.trades.sortDirection = 'desc';
        }
    }
    
    // Update legacy sort state for compatibility
    window.tradesSortState = window.tradesSortState || {};
    window.tradesSortState.column = tableState.trades.sortColumn;
    window.tradesSortState.direction = tableState.trades.sortDirection;
    
    // Clear all sort indicators and set active one
    table.querySelectorAll('th i.fas').forEach(icon => {
        icon.className = 'fas fa-sort text-muted';
    });
    const currentHeader = document.getElementById(`trades-sort-${columnIndex}`);
    if (currentHeader) {
        currentHeader.className = `fas fa-sort-${tableState.trades.sortDirection === 'asc' ? 'up' : 'down'} text-white`;
    }
    
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent.trim();
        const bVal = b.cells[columnIndex].textContent.trim();
        
        let result = 0;
        
        // Handle different column types
        if (columnIndex === 0) { // Time column - sort by date
            const aDate = new Date(aVal);
            const bDate = new Date(bVal);
            result = aDate - bDate;
        } else if (columnIndex === 3 || columnIndex === 4 || columnIndex === 5) { // Size, Price, P&L columns - numeric
            const aNum = parseFloat(aVal.replace(/[$,]/g, ''));
            const bNum = parseFloat(bVal.replace(/[$,]/g, ''));
            result = !isNaN(aNum) && !isNaN(bNum) ? aNum - bNum : aVal.localeCompare(bVal);
        } else { // Symbol, Action columns - text
            result = aVal.localeCompare(bVal);
        }
        
        return tableState.trades.sortDirection === 'asc' ? result : -result;
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

/* Cache refresh - Wed Aug 14 03:09:38 AM UTC 2025 */


// Enhanced sorting for main crypto portfolio table
window.portfolioSortState = { column: '', direction: 'desc' };

function sortPortfolio(columnType, toggleDirection = true) {
    const table = document.querySelector('#crypto-portfolio-table').closest('table');
    const tbody = document.getElementById('crypto-portfolio-table');
    const rows = Array.from(tbody.querySelectorAll('tr')).filter(row => row.cells.length > 1);
    
    // Save state to tableState
    if (toggleDirection) {
        if (tableState.portfolio.sortColumn === columnType) {
            tableState.portfolio.sortDirection = tableState.portfolio.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            tableState.portfolio.sortColumn = columnType;
            tableState.portfolio.sortDirection = 'desc';
        }
    }
    
    // Update legacy sort state for compatibility
    window.portfolioSortState = window.portfolioSortState || {};
    window.portfolioSortState.column = tableState.portfolio.sortColumn;
    window.portfolioSortState.direction = tableState.portfolio.sortDirection;
    
    // Clear all sort indicators
    table.querySelectorAll('th i.fas').forEach(icon => {
        icon.className = 'fas fa-sort text-muted';
    });
    
    // Set active sort indicator
    const currentIcon = document.getElementById(`sort-${columnType}`);
    if (currentIcon) {
        currentIcon.className = `fas fa-sort-${tableState.portfolio.sortDirection === 'asc' ? 'up' : 'down'} text-white`;
    }
    
    // Sort rows based on column type
    rows.sort((a, b) => {
        let aVal, bVal;
        
        switch(columnType) {
            case 'rank':
                aVal = parseInt(a.cells[0].textContent) || 0;
                bVal = parseInt(b.cells[0].textContent) || 0;
                break;
            case 'symbol':
                aVal = a.cells[1].textContent.trim();
                bVal = b.cells[1].textContent.trim();
                break;
            case 'name':
                aVal = a.cells[2].textContent.trim();
                bVal = b.cells[2].textContent.trim();
                break;
            case 'quantity':
                aVal = parseFloat(a.cells[3].textContent.replace(/[,]/g, '')) || 0;
                bVal = parseFloat(b.cells[3].textContent.replace(/[,]/g, '')) || 0;
                break;
            case 'price':
                aVal = parseFloat(a.cells[4].textContent.replace(/[$,]/g, '')) || 0;
                bVal = parseFloat(b.cells[4].textContent.replace(/[$,]/g, '')) || 0;
                break;
            case 'value':
                aVal = parseFloat(a.cells[5].textContent.replace(/[$,]/g, '')) || 0;
                bVal = parseFloat(b.cells[5].textContent.replace(/[$,]/g, '')) || 0;
                break;
            case 'target_sell':
                aVal = parseFloat(a.cells[6].textContent.replace(/[$,]/g, '')) || 0;
                bVal = parseFloat(b.cells[6].textContent.replace(/[$,]/g, '')) || 0;
                break;
            case 'approaching_sell':
                aVal = parseFloat(a.cells[7].textContent.replace(/[%]/g, '')) || 0;
                bVal = parseFloat(b.cells[7].textContent.replace(/[%]/g, '')) || 0;
                break;
            case 'target_buy':
                aVal = parseFloat(a.cells[8].textContent.replace(/[$,]/g, '')) || 0;
                bVal = parseFloat(b.cells[8].textContent.replace(/[$,]/g, '')) || 0;
                break;
            case 'projected_pnl':
                aVal = parseFloat(a.cells[9].textContent.replace(/[$,+\-]/g, '')) || 0;
                bVal = parseFloat(b.cells[9].textContent.replace(/[$,+\-]/g, '')) || 0;
                break;
            case 'pnl':
                aVal = parseFloat(a.cells[10].textContent.replace(/[$,+\-]/g, '')) || 0;
                bVal = parseFloat(b.cells[10].textContent.replace(/[$,+\-]/g, '')) || 0;
                break;
            case 'pnl_percent':
                aVal = parseFloat(a.cells[11].textContent.replace(/[%+\-]/g, '')) || 0;
                bVal = parseFloat(b.cells[11].textContent.replace(/[%+\-]/g, '')) || 0;
                break;
            default:
                return 0;
        }
        
        let result = 0;
        if (typeof aVal === 'number' && typeof bVal === 'number') {
            result = aVal - bVal;
        } else {
            result = String(aVal).localeCompare(String(bVal));
        }
        
        return tableState.portfolio.sortDirection === 'asc' ? result : -result;
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}
