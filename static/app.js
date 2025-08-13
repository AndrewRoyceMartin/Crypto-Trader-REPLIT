// Trading System Web Interface JavaScript

class TradingApp {
    constructor() {
        this.updateInterval = null;
        this.portfolioChart = null;
        this.returnsChart = null;
        this.tradesChart = null;
        this.isLiveConfirmationPending = false;
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
        // Auto-refresh every 5 seconds
        this.updateInterval = setInterval(() => {
            this.updateDashboard();
        }, 5000);
        
        // Handle page visibility change
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
            }, 5000);
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
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            this.updateTradingStatus(data.trading_status);
            this.updatePortfolio(data.portfolio);
            this.updateCharts(data.portfolio, data.recent_trades);
            this.updateRecentTrades(data.recent_trades);
            this.updatePositions(data.positions);
            this.updateCryptoPortfolio();
            
            this.updateConnectionStatus(true);
            
        } catch (error) {
            console.error('Error updating dashboard:', error);
            this.updateConnectionStatus(false);
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
            
        } catch (error) {
            console.error('Error updating crypto portfolio:', error);
        }
    }

    updateCryptoTable(cryptos) {
        const tbody = document.getElementById('crypto-portfolio-table');
        
        if (!cryptos || cryptos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">No cryptocurrency data available</td></tr>';
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
        
        tbody.innerHTML = window.cryptoPortfolioData.map(crypto => {
            const pnlClass = crypto.pnl >= 0 ? 'text-success' : 'text-danger';
            const priceDisplay = crypto.current_price < 1 ? crypto.current_price.toFixed(6) : crypto.current_price.toFixed(2);
            
            // Calculate proximity to target sell price
            const proximityClass = calculateTargetProximity(crypto.current_price, crypto.target_sell_price);
            
            return `
                <tr class="${proximityClass}">
                    <td class="fw-bold">${crypto.rank}</td>
                    <td class="fw-semibold">${crypto.symbol}</td>
                    <td class="text-muted">${crypto.name}</td>
                    <td>${crypto.quantity.toFixed(4)}</td>
                    <td>$${priceDisplay}</td>
                    <td>$${crypto.current_value.toFixed(2)}</td>
                    <td class="text-warning">$${crypto.target_sell_price ? crypto.target_sell_price.toFixed(crypto.target_sell_price < 1 ? 6 : 2) : 'N/A'}</td>
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
        
        if (!trades || trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No trades yet</td></tr>';
            return;
        }
        
        tbody.innerHTML = trades.slice(0, 10).map(trade => {
            const timestamp = new Date(trade.timestamp).toLocaleString();
            const actionClass = trade.action === 'buy' ? 'trade-buy' : 'trade-sell';
            const pnl = trade.pnl || 0;
            const pnlClass = pnl > 0 ? 'pnl-positive' : pnl < 0 ? 'pnl-negative' : 'pnl-neutral';
            
            return `
                <tr>
                    <td class="text-xs">${timestamp}</td>
                    <td>${trade.symbol}</td>
                    <td><span class="${actionClass}">${trade.action.toUpperCase()}</span></td>
                    <td>${parseFloat(trade.size).toFixed(6)}</td>
                    <td>$${parseFloat(trade.price).toFixed(2)}</td>
                    <td><span class="${pnlClass}">$${pnl.toFixed(2)}</span></td>
                </tr>
            `;
        }).join('');
    }
    
    updatePositions(positions) {
        const tbody = document.getElementById('positions-table');
        
        if (!positions || positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No open positions</td></tr>';
            return;
        }
        
        tbody.innerHTML = positions.map(position => {
            const entryTime = new Date(position.entry_time);
            const duration = this.formatDuration(Date.now() - entryTime.getTime());
            const pnl = position.unrealized_pnl || 0;
            const pnlClass = pnl > 0 ? 'pnl-positive' : pnl < 0 ? 'pnl-negative' : 'pnl-neutral';
            
            return `
                <tr>
                    <td>${position.symbol}</td>
                    <td>${parseFloat(position.size).toFixed(6)}</td>
                    <td>$${parseFloat(position.avg_price).toFixed(2)}</td>
                    <td><span class="${pnlClass}">$${pnl.toFixed(2)}</span></td>
                    <td>${duration}</td>
                </tr>
            `;
        }).join('');
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        
        if (connected) {
            statusElement.innerHTML = '<i class="fas fa-circle text-success me-1"></i>Connected';
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
        toast.innerHTML = `
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
            ${message}
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
}

// Global functions for button actions
async function startTrading(mode, tradingMode = 'single') {
    if (mode === 'live') {
        // Show confirmation modal for live trading
        const modal = new bootstrap.Modal(document.getElementById('liveConfirmModal'));
        modal.show();
        window.tradingApp.isLiveConfirmationPending = true;
        window.tradingApp.pendingTradingMode = tradingMode;
        return;
    }
    
    await executeStartTrading(mode, tradingMode);
}

async function confirmLiveTrading() {
    const checkbox = document.getElementById('live-confirm-checkbox');
    
    if (!checkbox.checked) {
        window.tradingApp.showToast('Please confirm you understand the risks', 'warning');
        return;
    }
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('liveConfirmModal'));
    modal.hide();
    
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
            window.tradingApp.showToast(result.message, 'success');
        } else {
            window.tradingApp.showToast(result.error, 'danger');
        }
        
    } catch (error) {
        window.tradingApp.showToast('Failed to start trading: ' + error.message, 'danger');
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
            window.tradingApp.showToast(result.message, 'success');
        } else {
            window.tradingApp.showToast(result.error, 'danger');
        }
        
    } catch (error) {
        window.tradingApp.showToast('Failed to stop trading: ' + error.message, 'danger');
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
            window.tradingApp.showToast(result.message, 'warning');
        } else {
            window.tradingApp.showToast(result.error, 'danger');
        }
        
    } catch (error) {
        window.tradingApp.showToast('Failed to execute emergency stop: ' + error.message, 'danger');
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

// Trade a specific cryptocurrency from the portfolio
// Toggle the color legend visibility
function toggleColorLegend() {
    const legend = document.getElementById('color-legend');
    if (legend.style.display === 'none') {
        legend.style.display = 'block';
    } else {
        legend.style.display = 'none';
    }
}

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
            const modal = new bootstrap.Modal(document.getElementById('cryptoChartModal'));
            modal.show();
            
            // Create chart after modal is shown
            modal._element.addEventListener('shown.bs.modal', () => {
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
function rebalancePortfolio() {
    if (confirm('Are you sure you want to rebalance the portfolio? This will reset all positions to equal $100 values.')) {
        fetch('/api/rebalance-portfolio', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.tradingApp.showToast('Portfolio rebalanced successfully', 'success');
                    refreshCryptoPortfolio();
                } else {
                    window.tradingApp.showToast('Failed to rebalance portfolio: ' + data.error, 'danger');
                }
            })
            .catch(error => {
                window.tradingApp.showToast('Error rebalancing portfolio: ' + error.message, 'danger');
            });
    }
}

function exportPortfolio() {
    window.open('/api/export-portfolio', '_blank');
}

function resetPortfolio() {
    if (confirm('Are you sure you want to reset all cryptocurrency positions to $100 each? This will lose all current price history.')) {
        fetch('/api/reset-portfolio', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.tradingApp.showToast('Portfolio reset successfully', 'success');
                    refreshCryptoPortfolio();
                } else {
                    window.tradingApp.showToast('Failed to reset portfolio: ' + data.error, 'danger');
                }
            })
            .catch(error => {
                window.tradingApp.showToast('Error resetting portfolio: ' + error.message, 'danger');
            });
    }
}

function showBacktestResults(results) {
    const resultsDiv = document.getElementById('backtest-results');
    
    resultsDiv.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>Performance Metrics</h6>
                <table class="table table-sm">
                    <tr><td>Total Return</td><td class="text-end">${(results.total_return * 100).toFixed(2)}%</td></tr>
                    <tr><td>Sharpe Ratio</td><td class="text-end">${results.sharpe_ratio.toFixed(3)}</td></tr>
                    <tr><td>Max Drawdown</td><td class="text-end">${(results.max_drawdown * 100).toFixed(2)}%</td></tr>
                    <tr><td>Calmar Ratio</td><td class="text-end">${results.calmar_ratio.toFixed(3)}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>Trading Statistics</h6>
                <table class="table table-sm">
                    <tr><td>Total Trades</td><td class="text-end">${results.total_trades}</td></tr>
                    <tr><td>Win Rate</td><td class="text-end">${(results.win_rate * 100).toFixed(1)}%</td></tr>
                    <tr><td>Profit Factor</td><td class="text-end">${results.profit_factor.toFixed(2)}</td></tr>
                    <tr><td>Avg Win</td><td class="text-end">$${results.avg_win.toFixed(2)}</td></tr>
                </table>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-12">
                <h6>Summary</h6>
                <div class="alert alert-info">
                    Initial Capital: $${results.initial_capital.toLocaleString()}<br>
                    Final Value: $${results.final_value.toLocaleString()}<br>
                    Profit/Loss: $${(results.final_value - results.initial_capital).toLocaleString()}
                </div>
            </div>
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('backtestModal'));
    modal.show();
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
        
        return `
            <tr>
                <td class="fw-bold">${crypto.rank}</td>
                <td class="fw-semibold">${crypto.symbol}</td>
                <td class="text-muted">${crypto.name}</td>
                <td>${crypto.quantity.toFixed(4)}</td>
                <td>$${priceDisplay}</td>
                <td>$${crypto.current_value.toFixed(2)}</td>
                <td class="${pnlClass}">$${crypto.pnl.toFixed(2)}</td>
                <td class="${pnlClass}">${crypto.pnl_percent.toFixed(2)}%</td>
                <td>
                    <button class="btn btn-outline-primary btn-sm" onclick="tradeCrypto('${crypto.symbol}')" title="Trade ${crypto.symbol}">
                        <i class="fas fa-chart-line"></i>
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
