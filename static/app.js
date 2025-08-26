// Trading System Web Interface - Modular ES6 Architecture
import { AppUtils } from './js/modules/utils.js';
import { DashboardManager } from './js/modules/dashboard-manager.js';
import { ChartUpdater } from './js/modules/chart-updater.js';
import { TradeManager } from './js/modules/trade-manager.js';

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
                    if (elapsed >= maxWait) {
                        console.warn('Library loading timeout - some features may be limited');
                    }
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
                cache: 'no-store'
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
        
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    <img src="https://cryptologos.cc/logos/${holding.symbol.toLowerCase()}-${holding.name?.toLowerCase() || holding.symbol.toLowerCase()}-logo.png" 
                         alt="${holding.symbol}" class="crypto-icon-img me-2" width="24" height="24"
                         onerror="this.outerHTML='<i class=&quot;fa-solid fa-coins text-warning me-2&quot; style=&quot;width: 24px; height: 24px; font-size: 18px;&quot;></i>'">
                    <div>
                        <strong>${holding.symbol}</strong>
                        <small class="text-muted d-block">${AppUtils.getCoinDisplay(holding.symbol)}</small>
                    </div>
                </div>
            </td>
            <td>${AppUtils.safeNum(holding.quantity, 0).toFixed(8)}</td>
            <td>${AppUtils.formatCurrency(holding.current_price)}</td>
            <td>${AppUtils.formatCurrency(holding.current_value)}</td>
            <td class="${pnlClass}">
                ${pnlSign}${AppUtils.formatCurrency(holding.pnl_amount || 0)}<br>
                <small>(${pnlSign}${((holding.pnl_percent || 0) * 100).toFixed(2)}%)</small>
            </td>
            <td>
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
        
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    <img src="https://cryptologos.cc/logos/${position.symbol.toLowerCase()}-${position.symbol.toLowerCase()}-logo.png" 
                         alt="${position.symbol}" class="crypto-icon-img me-2" width="24" height="24"
                         onerror="this.outerHTML='<i class=&quot;fa-solid fa-coins text-warning me-2&quot; style=&quot;width: 24px; height: 24px; font-size: 18px;&quot;></i>'">
                    <strong>${position.symbol}</strong>
                </div>
            </td>
            <td>${AppUtils.formatCurrency(position.current_price)}</td>
            <td>${AppUtils.formatCurrency(position.target_buy_price)}</td>
            <td>
                <span class="badge bg-${confidenceClass}">
                    ${position.entry_confidence?.level || 'N/A'}
                </span>
            </td>
            <td>${position.bollinger_analysis?.signal || 'NO DATA'}</td>
            <td>
                ${hasBalance ? 
                    `<button class="btn btn-sm btn-success" onclick="tradeManager.showSellDialog('${position.symbol}', ${position.current_balance}, ${position.current_price})">Sell</button>` :
                    `<button class="btn btn-sm btn-primary" onclick="tradeManager.showBuyDialog('${position.symbol}', ${position.current_price}, ${position.target_buy_price})">Buy</button>`
                }
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