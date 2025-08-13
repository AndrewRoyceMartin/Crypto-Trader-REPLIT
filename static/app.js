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
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No cryptocurrency data available</td></tr>';
            return;
        }
        
        tbody.innerHTML = cryptos.map(crypto => {
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
async function startTrading(mode) {
    if (mode === 'live') {
        // Show confirmation modal for live trading
        const modal = new bootstrap.Modal(document.getElementById('liveConfirmModal'));
        modal.show();
        window.tradingApp.isLiveConfirmationPending = true;
        return;
    }
    
    await executeStartTrading(mode);
}

async function confirmLiveTrading() {
    const checkbox = document.getElementById('live-confirm-checkbox');
    
    if (!checkbox.checked) {
        window.tradingApp.showToast('Please confirm you understand the risks', 'warning');
        return;
    }
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('liveConfirmModal'));
    modal.hide();
    
    await executeStartTrading('live');
}

async function executeStartTrading(mode) {
    const symbol = document.getElementById('symbol-select').value;
    const timeframe = document.getElementById('timeframe-select').value;
    
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    document.getElementById('loading-message').textContent = `Starting ${mode} trading...`;
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

async function runBacktest() {
    const symbol = document.getElementById('symbol-select').value;
    const timeframe = document.getElementById('timeframe-select').value;
    const days = parseInt(document.getElementById('backtest-days').value);
    
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    document.getElementById('loading-message').textContent = 'Running backtest...';
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
                days: days
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showBacktestResults(result.results);
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

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.tradingApp = new TradingApp();
});
