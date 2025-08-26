// Trading System Web Interface - Modular ES6 Architecture
import { AppUtils } from './js/modules/utils.js';
import { DashboardManager } from './js/modules/dashboard-manager.js';
import { ChartUpdater } from './js/modules/chart-updater.js';
import { TradeManager } from './js/modules/trade-manager.js';

// Global error handlers to prevent console errors
window.addEventListener('unhandledrejection', (event) => {
    // Silently prevent unhandled promise rejections from appearing in console
    event.preventDefault();
});

window.addEventListener('error', (event) => {
    // Silently handle script errors to prevent generic "Script error" messages
    event.preventDefault();
});

// Main Application Class - Lightweight coordinator with singleton pattern
class ModularTradingApp {
    static instance = null;
    constructor() {
        // Prevent duplicate initialization
        if (ModularTradingApp.instance) {
            return ModularTradingApp.instance;
        }
        
        // Initialize modular components
        this.utils = AppUtils;
        this.dashboard = new DashboardManager();
        this.charts = new ChartUpdater();
        this.trades = new TradeManager();
        
        // Store singleton reference
        ModularTradingApp.instance = this;
        
        this.init();
    }

    init() {
        console.log('Loading progress: 20% - Fetching cryptocurrency data...');
        
        // Wait for all deferred libraries to be ready
        this.waitForLibraries().then(() => {
            // Initialize charts if Chart.js is available
            if (window.Chart) {
                this.charts.initializeCharts();
                this.charts.startAutoUpdate();
            }
            
            // Start dashboard updates
            this.dashboard.startAutoUpdate();
            
            console.log('Loading progress: 100% - Complete!');
        });
        
        // Setup event listeners (can run immediately)
        this.setupEventListeners();
        
        // Initialize legacy table functions (maintain backward compatibility)
        this.initLegacyTableFunctions();
        
        // Expose for debugging
        window.dashboardManager = this.dashboard;
        window.chartUpdater = this.charts;
        window.tradeManager = this.trades;
    }

    async waitForLibraries() {
        // Wait for Bootstrap and Chart.js to load (both are deferred)
        const maxWait = 5000; // 5 seconds max wait
        const checkInterval = 50; // Check every 50ms
        let elapsed = 0;
        
        return new Promise((resolve) => {
            const checkLibraries = () => {
                if ((window.bootstrap && window.Chart) || elapsed >= maxWait) {
                    resolve();
                } else {
                    elapsed += checkInterval;
                    setTimeout(checkLibraries, checkInterval);
                }
            };
            checkLibraries();
        });
    }

    setupEventListeners() {
        // Currency selector change
        const currencySelector = document.getElementById('currency-selector');
        if (currencySelector) {
            currencySelector.addEventListener('change', (e) => {
                this.dashboard.selectedCurrency = e.target.value;
                this.dashboard.updatePortfolioOverview();
            });
        }

        // Portfolio update event listener
        window.addEventListener('portfolioUpdated', (event) => {
            console.log('Portfolio updated:', event.detail);
            this.dashboard.updatePortfolioOverview();
        });

        // Trade update event listener
        window.addEventListener('tradesUpdated', (event) => {
            console.log('Trades updated:', event.detail);
            this.updateTradesTable(event.detail.trades);
        });

        // Auto-load positions data
        setTimeout(() => {
            this.loadInitialData();
        }, 500);
    }

    async loadInitialData() {
        try {
            // Load holdings data
            await this.refreshHoldingsData();
            
            // Load available positions
            await this.loadAvailablePositions();
            
        } catch (error) {
            console.debug('Initial data load error:', error);
        }
    }

    async refreshHoldingsData() {
        try {
            const data = await AppUtils.fetchJSON('/api/current-holdings', {
                cache: 'no-store',
                timeout: 45000  // Extended timeout for complex OKX calculations
            });
            
            if (data && data.holdings) {
                console.log('Holdings data received:', data.holdings);
                this.updateHoldingsTable(data.holdings);
            }
        } catch (error) {
            console.debug('Holdings refresh failed:', error);
        }
    }

    async loadAvailablePositions() {
        try {
            const data = await AppUtils.fetchJSON('/api/available-positions');
            
            // Handle both direct array response and wrapped object response
            let positions = null;
            if (Array.isArray(data)) {
                positions = data;
            } else if (data && data.available_positions) {
                positions = data.available_positions;
            } else if (data && Array.isArray(data.positions)) {
                positions = data.positions;
            }
            
            if (positions && positions.length > 0) {
                console.log('Available positions loaded:', positions.length, 'positions');
                this.renderAvailableTable(positions);
            } else {
                console.debug('No available positions data found');
                this.renderAvailableTable([]); // Render empty table to clear loading state
            }
        } catch (error) {
            console.error('Available positions load failed:', error);
            this.renderAvailableTable([]); // Render empty table to clear loading state
        }
    }

    updateHoldingsTable(holdings) {
        const tbody = document.querySelector('#holdings-tbody');
        if (!tbody) {
            console.debug('Holdings table body not found');
            return;
        }

        tbody.innerHTML = '';
        
        holdings.forEach(holding => {
            const row = this.createHoldingRow(holding);
            tbody.appendChild(row);
        });
    }

    createHoldingRow(holding) {
        const row = document.createElement('tr');
        const pnlClass = (holding.pnl_percent || 0) >= 0 ? 'text-success' : 'text-danger';
        const pnlSign = (holding.pnl_percent || 0) >= 0 ? '+' : '';
        
        // Calculate additional fields for full 13-column table
        const avgEntryPrice = (holding.cost_basis || 0) / (holding.quantity || 1);
        const targetValue = (holding.current_value || 0) * 1.04; // 4% target
        const targetProfit = targetValue - (holding.current_value || 0);
        const targetProfitPercent = 4.0; // Enhanced Bollinger Bands 4% target
        const holdPeriod = '—'; // Would need trade history data
        
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    ${this.getCryptoIcon(holding.symbol)}
                    <div>
                        <strong>${holding.symbol}</strong>
                        <small class="text-muted d-block">${AppUtils.getCoinDisplay(holding.symbol)}</small>
                    </div>
                </div>
            </td>
            <td class="text-end">${AppUtils.safeNum(holding.quantity, 0).toFixed(8)}</td>
            <td class="text-end">${AppUtils.formatCurrency(avgEntryPrice)}</td>
            <td class="text-end">${AppUtils.formatCurrency(holding.current_price)}</td>
            <td class="text-end">${AppUtils.formatCurrency(holding.current_value)}</td>
            <td class="text-end ${pnlClass}">
                ${pnlSign}${AppUtils.formatCurrency(holding.pnl_amount || 0)}
            </td>
            <td class="text-end ${pnlClass}">
                ${pnlSign}${((holding.pnl_percent || 0)).toFixed(2)}%
            </td>
            <td class="text-end">${AppUtils.formatCurrency(targetValue)}</td>
            <td class="text-end text-success">+${AppUtils.formatCurrency(targetProfit)}</td>
            <td class="text-end text-success">+${targetProfitPercent.toFixed(1)}%</td>
            <td class="text-center text-muted">${holdPeriod}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-primary" onclick="tradeManager.showSellDialog('${holding.symbol}', ${holding.quantity}, ${holding.current_price})">
                    Sell
                </button>
            </td>
        `;
        
        return row;
    }

    renderAvailableTable(positions) {
        console.log('renderAvailableTable called with:', positions);
        
        const tbody = document.querySelector('#available-tbody');
        if (!tbody) {
            console.debug('Available positions table body not found');
            return;
        }

        tbody.innerHTML = '';
        
        if (!positions || positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No positions available</td></tr>';
            return;
        }
        
        positions.forEach(position => {
            const row = this.createAvailableRow(position);
            tbody.appendChild(row);
        });
    }

    createAvailableRow(position) {
        const row = document.createElement('tr');
        const hasBalance = AppUtils.safeNum(position.current_balance) > 0;
        const confidenceClass = this.getConfidenceClass(position.entry_confidence?.level);
        const timingClass = this.getTimingClass(position.entry_confidence?.timing_signal);
        const riskClass = this.getRiskClass(position.entry_confidence?.score);
        
        // Calculate price difference percentage
        const priceDiff = position.price_diff_percent || 0;
        const priceDiffClass = priceDiff >= 0 ? 'text-success' : 'text-danger';
        const priceDiffSign = priceDiff >= 0 ? '+' : '';
        
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    ${this.getCryptoIcon(position.symbol)}
                    <strong>${position.symbol}</strong>
                </div>
            </td>
            <td class="text-end">${AppUtils.formatCurrency(position.current_balance || 0)}</td>
            <td class="text-end">${AppUtils.formatCurrency(position.current_price)}</td>
            <td class="text-end">${AppUtils.formatCurrency(position.target_buy_price)}</td>
            <td class="text-end ${priceDiffClass}">${priceDiffSign}${priceDiff.toFixed(2)}%</td>
            <td>
                <span class="badge bg-${confidenceClass}">
                    ${position.entry_confidence?.level || 'N/A'}
                </span>
            </td>
            <td>
                <span class="badge bg-${timingClass}">
                    ${position.entry_confidence?.timing_signal || 'WAIT'}
                </span>
            </td>
            <td>
                <span class="badge bg-${riskClass}">
                    ${this.getRiskLevel(position.entry_confidence?.score)}
                </span>
            </td>
            <td>${position.buy_signal || 'NO DATA'}</td>
            <td>${position.bollinger_analysis?.strategy || position.bb_strategy || 'Enhanced BB'}</td>
            <td>
                <div class="d-flex gap-1">
                    <button class="btn btn-sm btn-outline-info" onclick="showConfidenceDetails('${position.symbol}')" title="View Details">
                        <i class="fa fa-info-circle"></i>
                    </button>
                    ${hasBalance ? 
                        `<button class="btn btn-sm btn-success" onclick="tradeManager.showSellDialog('${position.symbol}', ${position.current_balance}, ${position.current_price})">Sell</button>` :
                        `<button class="btn btn-sm btn-primary" onclick="tradeManager.showBuyDialog('${position.symbol}', ${position.current_price}, ${position.target_buy_price})">Buy</button>`
                    }
                </div>
            </td>
        `;
        
        return row;
    }

    getConfidenceClass(level) {
        switch(level?.toUpperCase()) {
            case 'STRONG': return 'success';
            case 'GOOD': return 'success';
            case 'FAIR': return 'warning';
            case 'WEAK': return 'danger';
            default: return 'secondary';
        }
    }

    // Get cryptocurrency icon - uses CoinGecko API for authentic logos
    getCryptoIcon(symbol) {
        if (!symbol || symbol === 'N/A') {
            return '<i class="fa-solid fa-coins text-muted me-2" style="width: 24px; height: 24px; font-size: 18px;"></i>';
        }
        
        // Map symbol to CoinGecko ID for accurate logos
        const coinGeckoIds = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'SOL': 'solana',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'AVAX': 'avalanche-2',
            'MATIC': 'polygon',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'LTC': 'litecoin',
            'XRP': 'ripple',
            'DOGE': 'dogecoin',
            'SHIB': 'shiba-inu',
            'GALA': 'gala',
            'TRX': 'tron',
            'PEPE': 'pepe',
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'BNB': 'binancecoin',
            'AUD': 'australian-dollar',
            'USD': 'us-dollar'
        };
        
        const coinId = coinGeckoIds[symbol.toUpperCase()] || symbol.toLowerCase();
        const imageId = this.getCoinGeckoImageId(coinId);
        
        return `<img src="https://assets.coingecko.com/coins/images/${imageId}/small/${coinId}.png" 
                     alt="${symbol}" 
                     class="crypto-icon crypto-icon-img me-2" 
                     style="width: 24px; height: 24px; border-radius: 50%;"
                     onerror="this.outerHTML='<i class=\\'fa-solid fa-coins text-warning me-2\\' style=\\'width: 24px; height: 24px; font-size: 18px;\\'></i>'">`;
    }
    
    // Get CoinGecko image IDs for major cryptocurrencies
    getCoinGeckoImageId(coinId) {
        const imageIds = {
            'bitcoin': '1',
            'ethereum': '279', 
            'solana': '4128',
            'cardano': '975',
            'polkadot': '12171',
            'avalanche-2': '12559',
            'polygon': '4713',
            'chainlink': '877',
            'uniswap': '12504',
            'litecoin': '2',
            'ripple': '44',
            'dogecoin': '5',
            'shiba-inu': '11939',
            'gala': '12493',
            'tron': '1094',
            'pepe': '29850',
            'tether': '325',
            'usd-coin': '6319',
            'binancecoin': '825',
            'australian-dollar': '325',  // Fallback to Tether logo for AUD
            'us-dollar': '325'           // Fallback to Tether logo for USD
        };
        
        return imageIds[coinId] || '1'; // Default to Bitcoin ID if not found
    }

    getTimingClass(signal) {
        switch(signal?.toUpperCase()) {
            case 'BUY': return 'success';
            case 'CAUTIOUS_BUY': return 'info';
            case 'SELL': return 'danger';
            case 'WAIT': return 'warning';
            default: return 'secondary';
        }
    }

    getRiskClass(score) {
        const numScore = AppUtils.safeNum(score, 0);
        if (numScore >= 80) return 'success';
        if (numScore >= 60) return 'warning';
        if (numScore >= 40) return 'danger';
        return 'secondary';
    }

    getRiskLevel(score) {
        const numScore = AppUtils.safeNum(score, 0);
        if (numScore >= 80) return 'LOW';
        if (numScore >= 60) return 'MED';
        if (numScore >= 40) return 'HIGH';
        return 'N/A';
    }

    updateTradesTable(trades) {
        const tbody = document.querySelector('#trades-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        trades.forEach(trade => {
            const row = this.createTradeRow(trade);
            tbody.appendChild(row);
        });
    }

    createTradeRow(trade) {
        const row = document.createElement('tr');
        const sideClass = trade.side === 'buy' ? 'text-success' : 'text-danger';
        
        row.innerHTML = `
            <td>${AppUtils.formatDateTime(trade.timestamp)}</td>
            <td>${trade.symbol}</td>
            <td class="${sideClass}">${trade.side?.toUpperCase()}</td>
            <td>${AppUtils.safeNum(trade.amount, 0).toFixed(8)}</td>
            <td>${AppUtils.formatCurrency(trade.price)}</td>
            <td>${AppUtils.formatCurrency(trade.cost)}</td>
        `;
        
        return row;
    }

    // Legacy function initialization for backward compatibility
}

// Show detailed confidence analysis - Global function for onclick handlers
async function showConfidenceDetails(symbol) {
    try {
        const response = await fetch(`/api/entry-confidence/${symbol}`, { cache: 'no-cache' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        if (data.status === 'success') {
            const info = data.data;
            const breakdown = info.breakdown;
            
            const modalHtml = `
                <div class="modal fade" id="confidenceModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Entry Confidence Analysis - ${symbol}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <h6>Overall Confidence</h6>
                                        <div class="progress mb-2">
                                            <div class="progress-bar bg-${info.score >= 70 ? 'success' : info.score >= 50 ? 'warning' : 'danger'}" 
                                                 style="width: ${info.score}%">${info.score.toFixed(1)}%</div>
                                        </div>
                                        <p><strong>Level:</strong> ${info.level}</p>
                                        <p><strong>Timing Signal:</strong> ${info.timing_signal}</p>
                                    </div>
                                    <div class="col-md-6">
                                        <h6>Current Market Data</h6>
                                        <p><strong>Price:</strong> $${parseFloat(info.current_price || 0).toFixed(6)}</p>
                                        <p><strong>Target:</strong> $${parseFloat(info.target_price || 0).toFixed(6)}</p>
                                        <p><strong>Opportunity:</strong> ${parseFloat(info.price_opportunity || 0).toFixed(2)}%</p>
                                    </div>
                                </div>
                                
                                <h6>Confidence Breakdown</h6>
                                <div class="list-group">
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <span>Technical Analysis</span>
                                        <span class="badge bg-${breakdown.technical >= 60 ? 'success' : breakdown.technical >= 40 ? 'warning' : 'danger'}">${breakdown.technical.toFixed(1)}%</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <span>Market Momentum</span>
                                        <span class="badge bg-${breakdown.momentum >= 60 ? 'success' : breakdown.momentum >= 40 ? 'warning' : 'danger'}">${breakdown.momentum.toFixed(1)}%</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <span>Risk Assessment</span>
                                        <span class="badge bg-${breakdown.risk >= 60 ? 'success' : breakdown.risk >= 40 ? 'warning' : 'danger'}">${breakdown.risk.toFixed(1)}%</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <span>Volume Profile</span>
                                        <span class="badge bg-${breakdown.volume >= 60 ? 'success' : breakdown.volume >= 40 ? 'warning' : 'danger'}">${breakdown.volume.toFixed(1)}%</span>
                                    </div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if present
            const existingModal = document.getElementById('confidenceModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // Add modal to page
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // Show modal using Bootstrap
            const modal = new bootstrap.Modal(document.getElementById('confidenceModal'));
            modal.show();
            
        } else {
            throw new Error(data.message || 'Analysis failed');
        }
    } catch (error) {
        console.error('Confidence details error:', error);
        alert(`Unable to load confidence details for ${symbol}: ${error.message}`);
    }
}

// Make function globally available for onclick handlers
window.showConfidenceDetails = showConfidenceDetails;

class TradingApp {
    initLegacyTableFunctions() {
        // Maintain namespace compatibility with existing code
        window.Utils = this.utils;
        window.UI = {
            toast: AppUtils.showToast,
            setConn: this.setConnectionStatus.bind(this),
            changeCurrency: this.changeCurrency.bind(this)
        };
        window.Trading = {
            executeTakeProfit: this.trades.executeTakeProfit.bind(this.trades),
            showBuyDialog: this.trades.showBuyDialog.bind(this.trades),
            showSellDialog: this.trades.showSellDialog.bind(this.trades),
            confirmLiveTrading: this.trades.confirmLiveTrading.bind(this.trades)
        };
        window.Portfolio = {
            refreshCryptoPortfolio: this.refreshHoldingsData.bind(this),
            sortPortfolio: this.sortTable.bind(this),
            sortPerformanceTable: this.sortTable.bind(this)
        };
        
        // Global legacy functions
        window.refreshHoldingsData = this.refreshHoldingsData.bind(this);
        window.executeTakeProfit = this.trades.executeTakeProfit.bind(this.trades);
        window.showBuyDialog = this.trades.showBuyDialog.bind(this.trades);
        window.showSellDialog = this.trades.showSellDialog.bind(this.trades);
    }

    setConnectionStatus(isConnected) {
        // Update connection indicators
        const indicators = document.querySelectorAll('.connection-indicator');
        indicators.forEach(indicator => {
            indicator.className = isConnected ? 'connection-indicator connected' : 'connection-indicator disconnected';
        });
    }

    changeCurrency(newCurrency) {
        this.dashboard.selectedCurrency = newCurrency;
        const selector = document.getElementById('currency-selector');
        if (selector) {
            selector.value = newCurrency;
        }
        this.dashboard.updatePortfolioOverview();
    }

    sortTable(tableSelector, columnIndex) {
        const table = document.querySelector(tableSelector);
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isAscending = table.dataset.sortOrder !== 'asc';
        
        rows.sort((a, b) => {
            const aVal = a.cells[columnIndex]?.textContent.trim() || '';
            const bVal = b.cells[columnIndex]?.textContent.trim() || '';
            
            const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return isAscending ? aNum - bNum : bNum - aNum;
            }
            
            return isAscending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        });
        
        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));
        
        table.dataset.sortOrder = isAscending ? 'asc' : 'desc';
        AppUtils.showToast('Table sorted', 'success');
    }

    showToast(message, type = 'info') {
        AppUtils.showToast(message, type);
    }

    destroy() {
        // Clean up intervals and resources
        this.dashboard.stopAutoUpdate();
        this.charts.stopAutoUpdate();
        this.charts.destroyAllCharts();
    }
}

// Safer singleton initialization with boot wrapper
(function(){
    function boot() { 
        // Prevent double construction
        if (!window.tradingApp) { 
            // Verify critical libraries loaded before initialization
            if (!window.Chart) {
                console.warn('Chart.js not available - charts will be disabled');
            }
            if (!window.bootstrap) {
                console.warn('Bootstrap JS not available - modals may not work');
            }
            
            // Create main app instance (singleton)
            window.tradingApp = new ModularTradingApp();
            
            // Initialize scroll hints and other UI enhancements
            initializeScrollHints();
        }
    }
    
    // Boot when DOM is ready, handling both loading and loaded states
    if (document.readyState === 'loading') { 
        document.addEventListener('DOMContentLoaded', boot); 
    } else { 
        boot(); 
    }
})();

// Scroll hints for table navigation
function initializeScrollHints() {
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(tableContainer => {
        const table = tableContainer.querySelector('table');
        if (table && table.scrollWidth > tableContainer.clientWidth) {
            tableContainer.classList.add('scrollable-hint');
        }
    });
}

// Mobile data-labels helper function
function v02ApplyDataLabels(table) {
    const theadCells = Array.from(table.querySelectorAll('thead th'));
    if (!theadCells.length) return;
    
    const headers = theadCells.map(th => (th.innerText || th.textContent).trim());
    table.querySelectorAll('tbody tr').forEach(row => {
        Array.from(row.children).forEach((td, i) => {
            if (td && headers[i]) {
                td.setAttribute('data-label', headers[i]);
            }
        });
    });
}

// Robust mobile data-labels with MutationObserver
(function(){
    const apply = () => { 
        document.querySelectorAll('.table-v02').forEach(v02ApplyDataLabels); 
    };
    
    const targets = ['holdings-tbody', 'available-tbody', 'trades-tbody'];
    const mo = new MutationObserver(apply);
    
    targets.forEach(id => { 
        const el = document.getElementById(id); 
        if (el) {
            mo.observe(el, { childList: true }); 
        }
    });
    
    // Periodic fallback to catch any missed updates
    setInterval(apply, 3000);
})();

// Global legacy functions for backward compatibility
window.buyBackPosition = async function(symbol) {
    const tradeManager = window.tradeManager || window.tradingApp?.trades;
    if (tradeManager) {
        await tradeManager.buyBackPosition(symbol);
    }
};

window.sortPerformanceTable = function(columnIndex) {
    console.log(`Sorting performance table by column ${columnIndex}`);
    window.tradingApp?.sortTable('#trades-table', columnIndex);
};

window.sortTradesTable = function(columnIndex) {
    console.log(`Sorting trades table by column ${columnIndex}`);
    window.tradingApp?.sortTable('#trades-table', columnIndex);
};

// Debug functions
window.enableDebugFunctions = function() {
    console.log('Debug functions loaded.');
    window._debug = {
        dashboard: window.tradingApp?.dashboard,
        charts: window.tradingApp?.charts,
        trades: window.tradingApp?.trades,
        utils: AppUtils
    };
    console.log('Access debug via window._debug');
};