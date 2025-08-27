// Trading System Web Interface - Modular ES6 Architecture
import { AppUtils } from './js/modules/utils.js';
import { DashboardManager } from './js/modules/dashboard-manager.js';
import { ChartUpdater } from './js/modules/chart-updater.js';
import { TradeManager } from './js/modules/trade-manager.js';

// Progress Bar Management for Table Loading
class TableProgressManager {
    static updateProgress(tableId, percent, text = '') {
        const progressBar = document.getElementById(`${tableId}-progress-bar`);
        const progressText = document.getElementById(`${tableId}-progress-text`);
        
        if (progressBar) {
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', percent);
            progressBar.classList.toggle('progress-bar-striped', percent < 100);
        }
        
        if (progressText && text) {
            progressText.textContent = text;
        }
    }
    
    static showLoading(tableId, initialText = 'Starting...') {
        this.updateProgress(tableId, 0, initialText);
    }
    
    static showProgress(tableId, percent, text) {
        this.updateProgress(tableId, percent, text);
    }
    
    static hideProgress(tableId) {
        // Progress bars will be hidden when table content is populated
        this.updateProgress(tableId, 100, 'Complete');
    }
}

// Make the TableProgressManager globally available for compatibility
window.TableProgressManager = TableProgressManager;

// Global error handlers - Allow errors to be detected by tests but log them properly
let recentErrors = [];
const MAX_RECENT_ERRORS = 10;

window.addEventListener('unhandledrejection', (event) => {
    // Log for debugging and test detection
    console.warn('Unhandled Promise Rejection:', event.reason);
    
    // Store for potential test access
    recentErrors.push({
        type: 'unhandledrejection',
        message: event.reason?.toString() || 'Unknown promise rejection',
        timestamp: Date.now()
    });
    
    // Keep only recent errors
    if (recentErrors.length > MAX_RECENT_ERRORS) {
        recentErrors.shift();
    }
    
    // Only prevent default for network-related promises to avoid spam
    if (event.reason && typeof event.reason === 'string' && 
        (event.reason.includes('Failed to fetch') || event.reason.includes('NetworkError'))) {
        event.preventDefault();
    }
});

window.addEventListener('error', (event) => {
    // Log for debugging and test detection
    console.error('JavaScript Error:', event.message, 'at', event.filename + ':' + event.lineno);
    
    // Store for potential test access
    recentErrors.push({
        type: 'javascript',
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        timestamp: Date.now()
    });
    
    // Keep only recent errors
    if (recentErrors.length > MAX_RECENT_ERRORS) {
        recentErrors.shift();
    }
    
    // Don't prevent default - let errors be visible for testing
    // Only silence generic "Script error" messages from external sources
    if (event.message === 'Script error.' && event.filename === '') {
        event.preventDefault();
    }
});

// Make error data available globally for tests
window.getRecentErrors = () => [...recentErrors];
window.clearRecentErrors = () => { recentErrors.length = 0; };

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

    // Add the missing method to prevent TypeError
    initLegacyTableFunctions() {
        // Maintain namespace compatibility with existing code
        if (this.utils) {
            window.Utils = this.utils;
        }
        
        window.UI = {
            toast: AppUtils.showToast,
            setConn: () => {}, // No-op for compatibility
            changeCurrency: (currency) => {
                if (this.dashboard) {
                    this.dashboard.selectedCurrency = currency;
                    this.dashboard.updatePortfolioOverview();
                }
            }
        };
        
        // Global legacy functions for backward compatibility
        if (this.trades) {
            window.executeTakeProfit = this.trades.executeTakeProfit?.bind(this.trades) || (() => {});
            window.showBuyDialog = this.trades.showBuyDialog?.bind(this.trades) || (() => {});
            window.showSellDialog = this.trades.showSellDialog?.bind(this.trades) || (() => {});
        }
        
        // Make the app instance globally available
        window.tradingApp = this;
        console.log('Legacy table functions initialized');
    }

    async refreshHoldingsData() {
        try {
            // Show progress
            TableProgressManager.showLoading('holdings', 'Fetching current holdings...');
            TableProgressManager.showProgress('holdings', 20, 'Loading OKX data...');
            
            const data = await AppUtils.fetchJSON('/api/current-holdings', {
                cache: 'no-store',
                timeout: 45000  // Extended timeout for complex OKX calculations
            });
            
            TableProgressManager.showProgress('holdings', 80, 'Processing holdings...');
            
            if (data && data.holdings) {
                console.log('Holdings data received:', data.holdings);
                this.updateHoldingsTable(data.holdings);
                TableProgressManager.hideProgress('holdings');
            }
        } catch (error) {
            console.debug('Holdings refresh failed:', error);
            TableProgressManager.showProgress('holdings', 0, 'Failed to load holdings');
        }
    }

    async loadAvailablePositions() {
        try {
            // Show initial progress
            TableProgressManager.showLoading('available', 'Loading available positions...');
            TableProgressManager.showProgress('available', 10, 'Fetching market data...');
            
            const data = await AppUtils.fetchJSON('/api/available-positions');
            
            TableProgressManager.showProgress('available', 60, 'Processing positions...');
            
            // Handle both direct array response and wrapped object response
            let positions = null;
            if (Array.isArray(data)) {
                positions = data;
            } else if (data && data.available_positions) {
                positions = data.available_positions;
            } else if (data && Array.isArray(data.positions)) {
                positions = data.positions;
            }
            
            TableProgressManager.showProgress('available', 90, 'Rendering table...');
            
            if (positions && positions.length > 0) {
                console.log('Available positions loaded:', positions.length, 'positions');
                this.renderAvailableTable(positions);
                TableProgressManager.hideProgress('available');
            } else {
                console.debug('No available positions data found');
                this.renderAvailableTable([]); // Render empty table to clear loading state
            }
        } catch (error) {
            console.error('Available positions load failed:', error);
            TableProgressManager.showProgress('available', 0, 'Failed to load positions');
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
        // Use OKX avg_entry_price directly if available, fallback to cost_basis calculation
        const avgEntryPrice = holding.avg_entry_price || ((holding.cost_basis || 0) / (holding.quantity || 1));
        
        // Enhanced Bollinger Bands strategy profit target calculation
        // PRIORITY 1: Try to get Bollinger Bands upper band target (if available)
        // PRIORITY 2: Use strategy's 4% take profit (primary setting)
        // PRIORITY 3: Fall back to 6% safety net only if needed
        let targetMultiplier = 1.04; // Enhanced Bollinger Bands primary target: 4%
        let targetProfitPercent = 4.0;
        let targetMethod = "Strategy 4%";
        
        // Check if we have Bollinger Bands data for dynamic target
        if (holding.bollinger_upper_band && avgEntryPrice > 0) {
            const bollingerTarget = holding.bollinger_upper_band / avgEntryPrice;
            if (bollingerTarget > 1.01 && bollingerTarget < 1.20) { // Reasonable range
                targetMultiplier = bollingerTarget;
                targetProfitPercent = (bollingerTarget - 1) * 100;
                targetMethod = "Bollinger Upper";
            }
        }
        
        // Apply safety net only if strategy targets fail
        if (targetMultiplier < 1.01) {
            targetMultiplier = 1.06; // 6% safety fallback
            targetProfitPercent = 6.0;
            targetMethod = "Safety Net 6%";
        }
        
        const targetValue = (holding.current_value || 0) * targetMultiplier;
        const targetProfit = targetValue - (holding.current_value || 0);
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
            <td class="text-center">${this.getPositionStatusBadge(holding)}</td>
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
            <td>
                <span class="badge ${
                    position.buy_signal === 'CURRENT HOLDING' ? 'bg-primary' :
                    position.buy_signal === 'READY TO BUY' ? 'bg-success' :
                    'bg-secondary'
                }">
                    ${position.buy_signal || 'NO DATA'}
                </span>
            </td>
            <td class="text-center">
                ${hasBalance ? 
                    '<span class="text-info fw-bold">OWNED</span>' :
                    `<span class="text-${priceDiff >= 0 ? 'danger' : 'success'}">${Math.abs(priceDiff).toFixed(1)}% ${priceDiff >= 0 ? 'above' : 'below'} target</span>`
                }
            </td>
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

    getPositionStatusBadge(holding) {
        const pnlPercent = holding.pnl_percent || 0;
        const quantity = holding.quantity || 0;
        
        if (quantity <= 0) {
            return '<span class="badge bg-secondary" title="No position held">FLAT</span>';
        }
        
        if (pnlPercent >= 8.0) {
            return '<span class="badge bg-success" title="Position above 8% profit - in active management zone">MANAGED</span>';
        } else if (pnlPercent >= 3.0) {
            return '<span class="badge bg-warning text-dark" title="Position above 3% profit - monitored for exit signals">WATCH</span>';
        } else if (pnlPercent < 0) {
            return '<span class="badge bg-danger" title="Position at loss - monitored for crash protection">LOSS</span>';
        } else {
            return '<span class="badge bg-primary" title="Holding long position - monitored by trading bot">LONG</span>';
        }
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
        // First fetch confidence data quickly
        const confidenceResponse = await fetch(`/api/entry-confidence/${symbol}`, { cache: 'no-cache' });
        if (!confidenceResponse.ok) throw new Error(`HTTP ${confidenceResponse.status}`);
        
        const confidenceData = await confidenceResponse.json();
        
        if (confidenceData.status === 'success') {
            const info = confidenceData.data;
            const breakdown = info.breakdown;
            
            // Show modal immediately with loading state for market data
            let marketData = { 
                current_price: 'Loading...', 
                target_buy_price: 'Loading...', 
                price_opportunity: 'Loading...' 
            };
            
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
                                            <div class="progress-bar bg-${(info.confidence_score || 0) >= 70 ? 'success' : (info.confidence_score || 0) >= 50 ? 'warning' : 'danger'}" 
                                                 style="width: ${info.confidence_score || 0}%">${(info.confidence_score || 0).toFixed(1)}%</div>
                                        </div>
                                        <p><strong>Level:</strong> ${info.confidence_level}</p>
                                        <p><strong>Timing Signal:</strong> ${info.timing_signal}</p>
                                    </div>
                                    <div class="col-md-6">
                                        <h6>Current Market Data</h6>
                                        <div id="market-data-${symbol}">
                                            <p><strong>Price:</strong> <span id="current-price-${symbol}">${typeof marketData.current_price === 'string' ? marketData.current_price : '$' + parseFloat(marketData.current_price).toFixed(6)}</span></p>
                                            <p><strong>Target:</strong> <span id="target-price-${symbol}">${typeof marketData.target_buy_price === 'string' ? marketData.target_buy_price : '$' + parseFloat(marketData.target_buy_price).toFixed(6)}</span></p>
                                            <p><strong>Opportunity:</strong> <span id="opportunity-${symbol}">${typeof marketData.price_opportunity === 'string' ? marketData.price_opportunity : parseFloat(marketData.price_opportunity).toFixed(2) + '%'}</span></p>
                                        </div>
                                        <p><strong>Risk Level:</strong> <span class="${info.risk_level === 'LOW' ? 'text-success' : info.risk_level === 'MODERATE' ? 'text-warning' : 'text-danger'}">${info.risk_level}</span></p>
                                    </div>
                                </div>
                                
                                <h6>Confidence Breakdown</h6>
                                <div class="list-group">
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <span>Technical Analysis</span>
                                        <span class="badge bg-${(breakdown.technical_analysis || 0) >= 60 ? 'success' : (breakdown.technical_analysis || 0) >= 40 ? 'warning' : 'danger'}">${(breakdown.technical_analysis || 0).toFixed(1)}%</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <span>Market Momentum</span>
                                        <span class="badge bg-${(breakdown.momentum_indicators || 0) >= 60 ? 'success' : (breakdown.momentum_indicators || 0) >= 40 ? 'warning' : 'danger'}">${(breakdown.momentum_indicators || 0).toFixed(1)}%</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <span>Risk Assessment</span>
                                        <span class="badge bg-${(breakdown.volatility_assessment || 0) >= 60 ? 'success' : (breakdown.volatility_assessment || 0) >= 40 ? 'warning' : 'danger'}">${(breakdown.volatility_assessment || 0).toFixed(1)}%</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <span>Volume Profile</span>
                                        <span class="badge bg-${(breakdown.volume_analysis || 0) >= 60 ? 'success' : (breakdown.volume_analysis || 0) >= 40 ? 'warning' : 'danger'}">${(breakdown.volume_analysis || 0).toFixed(1)}%</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <span>Support/Resistance</span>
                                        <span class="badge bg-${(breakdown.support_resistance || 0) >= 60 ? 'success' : (breakdown.support_resistance || 0) >= 40 ? 'warning' : 'danger'}">${(breakdown.support_resistance || 0).toFixed(1)}%</span>
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
            
            // Now fetch market data in the background and update the modal
            try {
                const positionsResponse = await fetch(`/api/available-positions`, { cache: 'no-cache' });
                if (positionsResponse.ok) {
                    const positionsData = await positionsResponse.json();
                    const position = positionsData.data?.find(p => p.symbol === symbol);
                    
                    if (position) {
                        // Update the market data in the already-shown modal
                        const currentPriceEl = document.getElementById(`current-price-${symbol}`);
                        const targetPriceEl = document.getElementById(`target-price-${symbol}`);
                        const opportunityEl = document.getElementById(`opportunity-${symbol}`);
                        
                        if (currentPriceEl) currentPriceEl.textContent = '$' + parseFloat(position.current_price || 0).toFixed(6);
                        if (targetPriceEl) targetPriceEl.textContent = '$' + parseFloat(position.target_buy_price || 0).toFixed(6);
                        if (opportunityEl) opportunityEl.textContent = parseFloat(position.price_diff_percent || 0).toFixed(2) + '%';
                    } else {
                        // Try to find price data from portfolio API as fallback
                        try {
                            const portfolioResponse = await fetch(`/api/crypto-portfolio?currency=USD`, { cache: 'no-cache' });
                            if (portfolioResponse.ok) {
                                const portfolioData = await portfolioResponse.json();
                                const portfolioPosition = portfolioData.holdings?.find(p => p.symbol === symbol);
                                
                                if (portfolioPosition) {
                                    const currentPriceEl = document.getElementById(`current-price-${symbol}`);
                                    const targetPriceEl = document.getElementById(`target-price-${symbol}`);
                                    const opportunityEl = document.getElementById(`opportunity-${symbol}`);
                                    
                                    if (currentPriceEl) currentPriceEl.textContent = '$' + parseFloat(portfolioPosition.current_price || 0).toFixed(6);
                                    if (targetPriceEl) targetPriceEl.textContent = 'Portfolio Asset';
                                    if (opportunityEl) opportunityEl.textContent = parseFloat(portfolioPosition.pnl_percent || 0).toFixed(2) + '%';
                                } else {
                                    // Update with "Not Available" if position not found
                                    const currentPriceEl = document.getElementById(`current-price-${symbol}`);
                                    const targetPriceEl = document.getElementById(`target-price-${symbol}`);
                                    const opportunityEl = document.getElementById(`opportunity-${symbol}`);
                                    
                                    if (currentPriceEl) currentPriceEl.textContent = 'Not Available';
                                    if (targetPriceEl) targetPriceEl.textContent = 'Not Available';
                                    if (opportunityEl) opportunityEl.textContent = 'Not Available';
                                }
                            }
                        } catch (portfolioError) {
                            // Portfolio API fallback failed
                        }
                    }
                }
            } catch (marketError) {
                // Update with error state
                const currentPriceEl = document.getElementById(`current-price-${symbol}`);
                const targetPriceEl = document.getElementById(`target-price-${symbol}`);
                const opportunityEl = document.getElementById(`opportunity-${symbol}`);
                
                if (currentPriceEl) currentPriceEl.textContent = 'Error loading';
                if (targetPriceEl) targetPriceEl.textContent = 'Error loading';
                if (opportunityEl) opportunityEl.textContent = 'Error loading';
            }
            
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
    
    // Periodic fallback reduced frequency to prevent unnecessary DOM updates
    setInterval(apply, 15000); // Reduced from 3s to 15s
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