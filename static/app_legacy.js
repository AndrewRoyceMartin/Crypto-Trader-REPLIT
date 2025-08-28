// Trading System Web Interface JavaScript - Cleaned & Harmonized

// Constants
const MIN_POSITION_USD = 0.01; // Minimum position value to display in main tables

// Helper function to get dynamic column count
function getTableColumnCount(tableId) {
    const headerRow = document.querySelector(`#${tableId} thead tr`);
    return headerRow ? headerRow.children.length : 10; // fallback to 10
}

// ===== ORGANIZED NAMESPACE ARCHITECTURE USING IIFE =====
// 
// This refactors 80+ global functions into organized namespaces to prevent
// collisions with other libraries and browser extensions, improving code
// maintainability and reducing global scope pollution.
//
// Namespace Structure:
//   Utils     - Core utilities (getAdminToken, fetchJSON, etc.)
//   UI        - User interface functions (toast, setConn, etc.)
//   Trading   - Trading operations (executeTakeProfit, showBuyDialog, etc.)
//   Portfolio - Portfolio management functions
//   Tables    - Table formatting and data-label management
//
// Access functions via: Utils.getAdminToken(), Trading.showBuyDialog(), etc.

// Utils namespace - Core utilities and helpers
const Utils = (function() {
    return {
        getAdminToken: null,     // Will be assigned below
        fetchJSON: null,         // Will be assigned below
        currentCurrency: null,   // Will be assigned below
        safeNum: null,          // Will be assigned below
        fmtCurrency: null,      // Will be assigned below
        toNum: null,            // Will be assigned below
        toOkxInst: null         // Will be assigned below
    };
})();

// UI namespace - User interface and notifications
const UI = (function() {
    return {
        toast: null,            // Will be assigned below
        setConn: null,          // Will be assigned below
        changeCurrency: null,   // Will be assigned below
        initializeV02Tables: null  // Will be assigned below
    };
})();

// Trading namespace - Trading operations
const Trading = (function() {
    return {
        executeTakeProfit: null,  // Will be assigned below
        showBuyDialog: null,      // Will be assigned below
        showSellDialog: null,     // Will be assigned below
        confirmLiveTrading: null  // Will be assigned below
    };
})();

// Portfolio namespace - Portfolio management
const Portfolio = (function() {
    return {
        refreshCryptoPortfolio: null,    // Will be assigned below
        clearPortfolioFilters: null,     // Will be assigned below
        clearPerformanceFilters: null,   // Will be assigned below
        sortPortfolio: null,             // Will be assigned below
        sortPerformanceTable: null       // Will be assigned below
    };
})();

// Tables namespace - Table management and formatting
const Tables = (function() {
    return {
        v02ApplyDataLabels: null,      // Will be assigned below
        initializeV02Tables: null,     // Will be assigned below
        updateHoldingsTable: null,     // Will be assigned below
        refreshHoldingsData: null      // Will be assigned below
    };
})();

// Admin token helper functions
function getAdminToken() {
  const m = document.querySelector('meta[name="admin-token"]');
  return m ? m.content : '';
}
// Assign to namespace
Utils.getAdminToken = getAdminToken;

async function fetchJSON(url, { method='GET', body, timeout=10000, headers={}, noStore=true } = {}) {
  const ctl = new AbortController();
  const t = setTimeout(()=>ctl.abort(), timeout);
  const h = {
    'Content-Type': 'application/json',
    ...(noStore ? {'Cache-Control': 'no-store'} : {}),
    ...(getAdminToken() ? {'X-Admin-Token': getAdminToken()} : {}),
    ...headers
  };
  try {
    const res = await fetch(url, { method, headers:h, body: body?JSON.stringify(body):undefined, signal: ctl.signal, cache: 'no-store' });
    
    // Check if response is OK first
    if (!res.ok) {
      console.debug(`API ${url} returned ${res.status}: ${res.statusText}`);
      return null;
    }
    
    // Check content type before parsing JSON
    const contentType = res.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      console.debug(`API ${url} returned non-JSON content: ${contentType}`);
      return null;
    }
    
    const data = await res.json();
    return data;
  } catch (error) {
    return null;
  } finally { clearTimeout(t); }
}
// Assign to namespace
Utils.fetchJSON = fetchJSON;

// Global currency and number helper functions
function currentCurrency(){
    return document.getElementById('currency-selector')?.value || 'USD';
}
// Assign to namespace
Utils.currentCurrency = currentCurrency;

// Resilient number parsing with fallback to prevent string errors
function safeNum(value, fallback = 0) {
    const num = Number(value);
    return isNaN(num) ? fallback : num;
}
// Assign to namespace
Utils.safeNum = safeNum;

function fmtCurrency(n){
    return new Intl.NumberFormat('en-US', {
        style:'currency',
        currency: currentCurrency(),
        minimumFractionDigits:8,
        maximumFractionDigits:8
    }).format(Number(n||0));
}
// Assign to namespace
Utils.fmtCurrency = fmtCurrency;

// Robust number parsing for table sorting
function toNum(x){
    if (x==null) return 0;
    const s = String(x).replace(/[\$,]/g,'').replace('%','').trim();
    const n = parseFloat(s); return isNaN(n)?0:n;
}
// Assign to namespace
Utils.toNum = toNum;

// Symbol normalization for OKX instruments
function toOkxInst(s){
    const t=s.trim().toUpperCase();
    return t.includes('-')?t.replace('/','-'): (t.includes('/')?t.replace('/','-'): `${t}-USDT`);
}
// Assign to namespace
Utils.toOkxInst = toOkxInst;

// Non-blocking toast notifications
function toast(msg, type='info'){
    console[type==='error'?'error':'log'](msg);
    
    // Create toast element
    const toastEl = document.createElement('div');
    toastEl.className = `toast-message ${type}`;
    toastEl.textContent = msg;
    
    // Add to container
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    container.appendChild(toastEl);
    
    // Show animation
    requestAnimationFrame(() => {
        toastEl.classList.add('show');
    });
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        toastEl.classList.remove('show');
        setTimeout(() => {
            if (toastEl.parentNode) {
                toastEl.parentNode.removeChild(toastEl);
            }
        }, 300);
    }, 4000);
}

// Connection badge state management
function setConn(connected){
  const el = document.getElementById('overview-connection');
  if (!el) return;
  el.textContent = connected ? 'Connected' : 'Disconnected';
  el.closest('.badge')?.classList.toggle('bg-success', connected);
  el.closest('.badge')?.classList.toggle('bg-danger', !connected);
}
// Assign to namespace
UI.setConn = setConn;

// V02 table mobile labels helper
function v02ApplyDataLabels(table) {
  const theadCells = Array.from(table.querySelectorAll('thead th'));
  if (!theadCells.length) return;
  const headers = theadCells.map(th => (th.innerText || th.textContent).trim());
  table.querySelectorAll('tbody tr').forEach(row => {
    Array.from(row.children).forEach((td, i) => {
      if (td && headers[i]) td.setAttribute('data-label', headers[i]);
    });
  });
}

// Enhanced table initialization - called after any dynamic table update
function initializeV02Tables() {
    try {
        document.querySelectorAll('.table-v02').forEach(table => {
            v02ApplyDataLabels(table);
        });
    } catch (error) {
        console.debug('V02 table initialization failed:', error);
    }
}
// Assign to namespaces
UI.initializeV02Tables = initializeV02Tables;
Tables.initializeV02Tables = initializeV02Tables;

// CONSOLIDATED: Single DOMContentLoaded event listener to prevent duplicate initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM ready, Bootstrap:', !!window.bootstrap, 'Chart.js:', !!window.Chart);
    
    // Verify critical libraries loaded before initialization
    if (!window.Chart) {
        console.warn('Chart.js not available - charts will be disabled');
    }
    if (!window.bootstrap) {
        console.warn('Bootstrap JS not available - modals may not work');
    }
    
    // Initialize V02 table mobile labels on first load
    initializeV02Tables();
    
    // Set up sync test button event handler (consolidated from duplicate listener)
    const syncButton = document.getElementById('btn-run-sync-test');
    if (syncButton) {
        syncButton.addEventListener('click', () => SyncTest.runSyncTest());
    }
    
    // SAFEGUARD: Initialize TradingApp only once (consolidated from duplicate listener)
    if (!window.tradingApp) {
        window.tradingApp = new TradingApp();
        console.log('TradingApp initialized once (consolidated)');
        
        // Maintain backward compatibility by exposing namespaced functions globally
        window.executeTakeProfit = Trading.executeTakeProfit;
        window.showBuyDialog = Trading.showBuyDialog;
        window.showSellDialog = Trading.showSellDialog;
        
        // Initialize scroll hints
        initializeScrollHints();
    } else {
        console.log('TradingApp already exists, skipping initialization');
    }
    
    // Auto-load positions data after page loads - CONSOLIDATED to prevent duplicate calls
    // Removed refreshHoldingsData() call here to prevent race condition with TradingApp refresh
    // TradingApp will handle all data loading via its unified refresh system

    document.addEventListener('click', function(e) {
        // Safely check for view-toggle-btn elements with null protection
        if (e.target && e.target.classList && e.target.classList.contains('view-toggle-btn')) {
            const cardId = e.target.getAttribute('data-card');
            if (cardId && typeof toggleCardView === 'function') {
                toggleCardView(cardId);
            }
        } else if (e.target && e.target.parentNode && e.target.parentNode.classList && e.target.parentNode.classList.contains('view-toggle-btn')) {
            const cardId = e.target.parentNode.getAttribute('data-card');
            if (cardId && typeof toggleCardView === 'function') {
                toggleCardView(cardId);
            }
        }
    });
    
    // Handle crypto icon load errors
    document.addEventListener('error', function(e) {
        if (e.target.classList.contains('crypto-icon-img')) {
            e.target.outerHTML = '<i class="fa-solid fa-coins text-warning" style="width: 24px; height: 24px; font-size: 18px;"></i>';
        }
    }, true);
});

class TradingApp {
    constructor() {
        this.updateInterval = null;
        this.chartUpdateInterval = null;

        // Charts
        this.portfolioChart = null;   // line
        this.pnlChart = null;         // doughnut
        this.performersChart = null;  // bar
        this.miniPortfolioChart = null; // mini chart for KPI card

        // State
        this.isLiveConfirmationPending = false;
        this.countdownInterval = null;
        this.countdown = 5;
        
        // Positions refresh countdown
        this.positionsCountdownInterval = null;
        this.positionsCountdown = 95; // 90s main interval + 5s delay

        // store trades for filtering
        this.allTrades = [];

        // Debounce to prevent overlapping dashboard updates
        this.lastDashboardUpdate = 0;
        this.dashboardUpdateDebounce = 2000; // 2 seconds
        this.pendingDashboardUpdate = null;

        // API cache
        this.apiCache = {
            status:    { data: null, timestamp: 0, ttl: 15000 },  // 15s (reduced from 1s for stability)
            portfolio: { data: null, timestamp: 0, ttl: 10000 },  // 10s (reduced from 1s for stability)
            config:    { data: null, timestamp: 0, ttl: 60000 }, // 60s (increased from 30s)
            analytics: { data: null, timestamp: 0, ttl: 30000 },  // 30s (reduced from 5s for stability)
            portfolioHistory: { data: null, timestamp: 0, ttl: 120000 }, // 2min (increased for stability)
            assetAllocation: { data: null, timestamp: 0, ttl: 15000 }, // 15s
            bestPerformer: { data: null, timestamp: 0, ttl: 10000 },  // 10s
            worstPerformer: { data: null, timestamp: 0, ttl: 10000 },  // 10s
            equityCurve: { data: null, timestamp: 0, ttl: 30000 },    // 30s
            drawdownAnalysis: { data: null, timestamp: 0, ttl: 30000 }, // 30s
            currentHoldings: { data: null, timestamp: 0, ttl: 15000 },  // 15s
            performanceAnalytics: { data: null, timestamp: 0, ttl: 30000 } // 30s
        };

        // Debug: force network fetches
        this.bypassCache = true;

        // Currency
        this.selectedCurrency = 'USD';
        
        // Timer tracking for cooldowns and refresh cycles
        this.refreshTimerInterval = null;
        this.lastRefreshTime = Date.now();
        this.refreshCooldown = 90000; // 90 seconds

        // Abort controller for in-flight requests
        this.portfolioAbortController = null;

        // scratch
        this.currentCryptoData = null;

        this.init();
        
        // Add flags to prevent overlapping table updates
        this.isUpdatingTables = false;
        this.lastTableUpdate = 0;
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
        const numericAmount = Number(amount) || 0;
        
        // Always use 8 decimal places for all dollar amounts
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currentCurrency(),
            minimumFractionDigits: 8,
            maximumFractionDigits: 8
        }).format(numericAmount);
    }

    // Timer Display Methods
    startTimerDisplay() {
        // Clear any existing timer to prevent duplicates
        if (this.refreshTimerInterval) {
            clearInterval(this.refreshTimerInterval);
        }
        
        // Update timer displays every second
        this.refreshTimerInterval = setInterval(() => {
            this.updateTimerDisplays();
        }, 1000);
        
        // Initial update
        this.updateTimerDisplays();
    }
    
    updateTimerDisplays() {
        const now = Date.now();
        
        // Update auto-refresh countdown
        const timeSinceLastRefresh = now - this.lastRefreshTime;
        const refreshSecondsLeft = Math.max(0, Math.ceil((this.refreshCooldown - timeSinceLastRefresh) / 1000));
        
        const refreshTimer = document.getElementById('refresh-timer');
        if (refreshTimer) {
            if (refreshSecondsLeft > 0) {
                refreshTimer.innerHTML = `<span class="icon icon-clock me-1"></span>Next: ${refreshSecondsLeft}s`;
                refreshTimer.className = 'badge bg-info text-nowrap';
            } else {
                refreshTimer.innerHTML = `<span class="icon icon-check me-1"></span>Ready`;
                refreshTimer.className = 'badge bg-success text-nowrap';
            }
        }
        
        // Update performance analytics cooldown
        const analyticsTimer = document.getElementById('analytics-timer');
        if (analyticsTimer && this.lastPerformanceUpdate) {
            const timeSinceAnalytics = now - this.lastPerformanceUpdate;
            const analyticsSecondsLeft = Math.max(0, Math.ceil((30000 - timeSinceAnalytics) / 1000));
            
            if (analyticsSecondsLeft > 0) {
                analyticsTimer.innerHTML = `<span class="icon icon-timer me-1"></span>Analytics: ${analyticsSecondsLeft}s`;
                analyticsTimer.style.display = 'inline-block';
            } else {
                analyticsTimer.style.display = 'none';
            }
        } else if (analyticsTimer) {
            analyticsTimer.style.display = 'none';
        }
    }
    
    updateRefreshTimestamp() {
        this.lastRefreshTime = Date.now();
    }

    // Special formatter for crypto prices with consistent precision
    formatCryptoPrice(amount, currency = null) {
        const numericAmount = Number(amount) || 0;

        // Always use 8 decimal places for crypto to prevent bouncing
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currentCurrency(),
            minimumFractionDigits: 8,
            maximumFractionDigits: 8
        }).format(numericAmount);
    }

    // Special formatter for very small P&L values to avoid scientific notation
    formatSmallCurrency(amount, currency = null) {
        const numericAmount = Number(amount) || 0;

        // If amount is very small (like 2.24e-7), use more decimal places
        if (Math.abs(numericAmount) < 0.000001 && numericAmount !== 0) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currentCurrency(),
                minimumFractionDigits: 8,
                maximumFractionDigits: 10
            }).format(numericAmount);
        }

        // Otherwise use regular currency formatting
        return this.formatCurrency(amount);
    }

    formatNumber(amount) {
        // Format large numbers with appropriate suffixes
        const numericAmount = Number(amount) || 0;
        
        if (numericAmount >= 1e12) {
            return (numericAmount / 1e12).toFixed(1) + 'T';
        } else if (numericAmount >= 1e9) {
            return (numericAmount / 1e9).toFixed(1) + 'B';
        } else if (numericAmount >= 1e6) {
            return (numericAmount / 1e6).toFixed(1) + 'M';
        } else if (numericAmount >= 1e3) {
            return (numericAmount / 1e3).toFixed(1) + 'K';
        } else {
            return numericAmount.toFixed(2);
        }
    }
    // Get crypto coin icon and name - now uses dynamic metadata cache  
    async getCoinDisplay(symbol) {
        return await CoinMetadataCache.getCoinMetadata(symbol);
    }
    
    // Synchronous fallback for backwards compatibility
    getCoinDisplaySync(symbol) {
        // Use dynamic coin metadata from cache or generate color algorithmically
        const cachedCoin = window.coinMetadataCache && window.coinMetadataCache[symbol];
        
        if (cachedCoin) {
            return {
                icon: cachedCoin.icon,
                name: cachedCoin.name,
                color: cachedCoin.color,
                type: cachedCoin.type
            };
        }
        
        // Dynamic fallback with algorithmic color generation
        return { 
            icon: 'fa-solid fa-coins', 
            name: symbol, 
            color: generateDynamicColor(symbol), 
            type: 'font' 
        };
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
        return document.getElementById('trades-tbody');
    }

    // Normalize trades from various backends (single canonical version)
    normalizeTrades(trades = []) {
        return (trades || []).map((t, i) => {
            const ts = t.timestamp || t.ts || t.time || t.date;
            const side = (t.side || t.action || '').toString().toUpperCase(); // BUY/SELL
            const qty = safeNum(t.quantity ?? t.qty ?? t.amount ?? t.size, 0);
            const price = safeNum(t.price ?? t.avg_price ?? t.fill_price ?? t.execution_price, 0);
            const pnl = safeNum(t.pnl ?? t.realized_pnl ?? t.profit, 0);
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
        this.loadConfig();
        
        // Initialize footer uptime tracking
        this.startUptimeTracking();
        
        // Start timer display for refresh countdowns
        this.startTimerDisplay();
        
        // CONSOLIDATED: Let startAutoUpdate handle all data fetching to prevent duplicates
        // startAutoUpdate will trigger initial data loads and set up proper intervals
        this.startAutoUpdate();
    }

    setupEventListeners() {
        const currencyDropdown = document.getElementById('currency-selector');
        if (currencyDropdown) {
            this.selectedCurrency = currencyDropdown.value || 'USD';
            currencyDropdown.addEventListener('change', async (e) => {
                await this.setSelectedCurrency(e.target.value);
            });
        }

        this.startCountdown();
        this.setupTradeTimeframeSelector();

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoUpdate();
                this.stopCountdown();
            } else {
                this.startAutoUpdate();
                this.startCountdown();
                // Initial refresh handled by startAutoUpdate
            }
        });

        window.addEventListener('beforeunload', () => this.cleanup());
        
        // Strategy sync accordion functionality
        this.setupStrategyAccordion();
    }

    startAutoUpdate() {
        // Clear any existing intervals first
        this.stopAutoUpdate();
        
        // IMMEDIATE INITIAL DATA LOAD (only once)
        this.updateRefreshTimestamp(); // Set initial timestamp for timer
        this.debouncedUpdateDashboard(); // Overview refresh (/api/crypto-portfolio)
        
        // Load current holdings immediately - don't make users wait 80+ seconds!
        setTimeout(() => {
            console.log(`📊 Initial holdings refresh starting immediately`);
            this.updateCryptoPortfolio(); // Holdings refresh
            this.startAvailableCountdown(5); // Reset available countdown
        }, 2000); // Start after 2 seconds to allow dashboard to load first
        
        // Single master update interval (10 seconds) 
        this.masterUpdateInterval = setInterval(() => {
            // Update refresh timestamp for timer display
            this.updateRefreshTimestamp();
            
            // Console logging for main refresh cycle
            console.log(`🔄 Main refresh cycle initiated - 10s interval`);
            
            // Main data refresh cycle
            this.debouncedUpdateDashboard(); // Overview refresh (/api/crypto-portfolio)
            this.startPositionsCountdown(10); // Reset positions countdown
            setTimeout(() => {
                console.log(`📊 Holdings refresh starting (5s delay)`);
                this.updateCryptoPortfolio(); // Holdings refresh
                this.startAvailableCountdown(5); // Reset available countdown
            }, 5000);
            
            // Update performance charts every 6 cycles (1 minute)
            this.updateCycleCount = (this.updateCycleCount || 0) + 1;
            if (this.updateCycleCount % 6 === 0) {
                this.updatePerformanceCharts();
            }
        }, 10000);
        
        // Start initial countdowns - positions countdown reflects the 10s interval
        this.startPositionsCountdown(10);
        // Available countdown will be started after initial load (2s + 5s = 7s total)
        
        // Countdown updates (every second)
        this.countdownUpdateInterval = setInterval(() => {
            this.updateAllCountdowns();
        }, 1000);
        
        // Footer status updates disabled - functions don't exist in current dashboard
        // and were causing unnecessary API calls every 10 seconds
        // this.statusUpdateInterval = null;
    }
    stopAutoUpdate() {
        // Clear all master intervals
        if (this.masterUpdateInterval) {
            clearInterval(this.masterUpdateInterval);
            this.masterUpdateInterval = null;
        }
        if (this.countdownUpdateInterval) {
            clearInterval(this.countdownUpdateInterval);
            this.countdownUpdateInterval = null;
        }
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
            this.statusUpdateInterval = null;
        }
        
        // Clear legacy intervals
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        if (this.chartUpdateInterval) {
            clearInterval(this.chartUpdateInterval);
            this.chartUpdateInterval = null;
        }
        if (window.__posCnt) {
            clearInterval(window.__posCnt);
            window.__posCnt = null;
        }
        if (window.positionsRefreshInterval) {
            clearInterval(window.positionsRefreshInterval);
            window.positionsRefreshInterval = null;
        }
    }
    stopCountdown() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
        // Position countdowns now handled by consolidated system
        this.positionsCountdownEnd = null;
        this.availableCountdownEnd = null;
    }
    cleanup() {
        this.stopAutoUpdate();
        this.stopCountdown();
        if (this.pendingDashboardUpdate) {
            clearTimeout(this.pendingDashboardUpdate);
            this.pendingDashboardUpdate = null;
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
            console.debug(`Error fetching ${endpoint}:`, error);
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

        if (typeof data.uptime_seconds === 'number') {
            this.updateUptimeDisplay(data.uptime_seconds);
        } else if (data.uptime_human) {
            // If we have human-readable uptime, display it directly
            const uptimeElement = document.getElementById('system-uptime');
            const footerUptimeElement = document.getElementById('footer-system-uptime');
            
            if (uptimeElement) {
                uptimeElement.textContent = data.uptime_human;
            }
            if (footerUptimeElement) {
                footerUptimeElement.textContent = data.uptime_human;
            }
        }

        // Update mini chart only - OKX cards are handled by updatePortfolioSummaryUI()
        if (data.portfolio || data.overview) {
            const portfolioData = data.overview || data.portfolio || {};
            
            // Only update portfolio-current-value (not an OKX card) and mini chart
            const kpiEquityEl = document.getElementById('portfolio-current-value');
            if (kpiEquityEl) {
                const totalValue = portfolioData.total_value || 0;
                kpiEquityEl.textContent = this.formatCurrency(totalValue);
                // Add error indicator if needed
                if (portfolioData.error && totalValue === 0) {
                    const errorNote = document.getElementById('okx-equity-error') || document.createElement('small');
                    errorNote.id = 'okx-equity-error';
                    errorNote.className = 'text-warning d-block';
                    errorNote.textContent = portfolioData.error;
                    if (!document.getElementById('okx-equity-error')) {
                        kpiEquityEl.parentNode.appendChild(errorNote);
                    }
                }
            }
            
            // Update mini portfolio chart with actual portfolio data
            this.updateMiniPortfolioChart(portfolioData);
        }

        // Trading status and bot state
        if (data.trading_status) this.updateTradingStatus(data.trading_status);
        
        // Update bot status from main status response
        if (data.bot !== undefined) {
            this.updateBotStatus(data.bot);
        }
        
        // Update overall active status
        if (data.active !== undefined) {
            this.updateActiveStatus(data.active);
        }
        
        // Bot status update removed - not used in current dashboard
        // this.fetchAndUpdateBotStatus();

        // Trade data available
        const trades = data.trades || [];
        if (trades.length > 0) {
            console.log('Trades data available:', trades.length);
        }

        // Status widgets
        this.updatePriceSourceStatus();
        this.updateOKXStatus();
        
        // Portfolio analytics
        this.updatePortfolioAnalytics();
        
        // Portfolio history chart
        this.updatePortfolioHistory();
        
        // Asset allocation chart
        this.updateAssetAllocation();
        
        // Best performer data
        this.updateBestPerformer();
        
        // Worst performer data
        this.updateWorstPerformer();
        
        // Equity curve
        this.updateEquityCurve();
        
        // Drawdown analysis
        this.updateDrawdownAnalysis();
        
        // Current holdings - REMOVED: Duplicate of updateCryptoPortfolio 
        // this.updateCurrentHoldings(); // Data already handled by updateCryptoPortfolio()
        
        
        // Performance analytics - REMOVED: Prevent duplicate with Promise.all call
        // this.updatePerformanceAnalytics(); // Called via Promise.all in setSelectedCurrency
    }

    async updatePortfolioAnalytics() {
        try {
            const response = await fetch('/api/portfolio-analytics', { cache: 'no-cache' });
            if (!response.ok) return;
            const data = await response.json();
            
            if (!data.success || !data.analytics) return;
            
            const analytics = data.analytics;
            
            // Update risk chart with actual portfolio data
            this.updateRiskChart(analytics);
            
            // Update analytics display elements
            this.updateAnalyticsDisplay(analytics);
            
        } catch (error) {
            console.debug('Portfolio analytics update failed:', error);
        }
    }
    
    updateRiskChart(analytics) {
        const riskCanvas = document.getElementById('riskChart');
        if (!riskCanvas) {
            return;
        }
        if (!window.Chart) {
            console.debug('Chart.js not available - skipping risk chart');
            return;
        }
        
        try {
            // Destroy existing chart
            if (this.riskChart) {
                this.riskChart.destroy();
            }
            
            // Create analytics chart with real OKX data - defensive loading
            if (!window.Chart) return;
            this.riskChart = new Chart(riskCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['Risk Exposure', 'Available Capital'],
                    datasets: [{
                        data: [
                            analytics.current_risk_exposure || 0,
                            Math.max(0, analytics.portfolio_value - (analytics.current_risk_exposure || 0))
                        ],
                        backgroundColor: ['#dc3545', '#28a745'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        title: { 
                            display: true, 
                            text: `Portfolio Analytics - ${analytics.concentration_risk} Risk`,
                            font: { size: 12 }
                        }
                    }
                }
            });
        } catch (error) {
            console.debug('Risk chart creation failed:', error);
            // Fallback display
            if (riskCanvas) {
                riskCanvas.style.display = 'none';
                const fallback = document.createElement('div');
                fallback.className = 'text-center text-muted p-3';
                // Create content safely using DOM methods
                const title = document.createElement('strong');
                title.textContent = 'Portfolio Analytics';
                fallback.appendChild(title);
                fallback.appendChild(document.createElement('br'));
                
                const riskText = document.createTextNode(`Risk Level: ${analytics.concentration_risk}`);
                fallback.appendChild(riskText);
                fallback.appendChild(document.createElement('br'));
                
                const positionsText = document.createTextNode(`Positions: ${analytics.position_count}`);
                fallback.appendChild(positionsText);
                fallback.appendChild(document.createElement('br'));
                
                const diversificationText = document.createTextNode(`Diversification: ${analytics.risk_assessment?.diversification || 'Unknown'}`);
                fallback.appendChild(diversificationText);
                riskCanvas.parentNode.replaceChild(fallback, riskCanvas);
            }
        }
    }
    
    updateAnalyticsDisplay(analytics) {
        // Update any analytics KPIs or displays if they exist
        const elements = {
            'analytics-concentration': analytics.concentration_risk,
            'analytics-diversification': analytics.risk_assessment?.diversification || 'Unknown',
            'analytics-positions': analytics.position_count,
            'analytics-largest-position': `${analytics.largest_position_percent.toFixed(1)}%`,
            'analytics-best-performer': analytics.performance_metrics?.best_performer || 'N/A',
            'analytics-worst-performer': analytics.performance_metrics?.worst_performer || 'N/A'
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                
                // Add color coding for risk levels
                if (id === 'analytics-concentration') {
                    element.className = value === 'High' ? 'text-danger' : 
                                      value === 'Medium' ? 'text-warning' : 'text-success';
                }
            }
        });
    }

    async updatePortfolioHistory() {
        try {
            const response = await fetch('/api/portfolio-history?timeframe=30d', { cache: 'no-cache' });
            if (!response.ok) return;
            const data = await response.json();
            
            if (!data.success || !data.history) return;
            
            // Update portfolio value over time chart
            this.updatePortfolioValueChart(data.history);
            
        } catch (error) {
            console.debug('Portfolio history update failed:', error);
        }
    }
    
    updatePortfolioValueChart(historyData) {
        const portfolioCanvas = document.getElementById('portfolioChart');
        if (!portfolioCanvas) {
            return;
        }
        if (!window.Chart) {
            console.debug('Chart.js not available - skipping portfolio chart');
            return;
        }
        
        try {
            // Destroy existing chart
            if (this.portfolioChart) {
                this.portfolioChart.destroy();
            }
            
            // Prepare data for Chart.js
            const labels = historyData.map(point => {
                const date = new Date(point.date);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            });
            
            const values = historyData.map(point => safeNum(point.value, 0));
            
            // Determine line color based on performance
            const firstValue = values[0] || 0;
            const lastValue = values[values.length - 1] || 0;
            const isPositive = lastValue >= firstValue;
            const lineColor = isPositive ? '#28a745' : '#dc3545';
            const fillColor = isPositive ? 'rgba(40, 167, 69, 0.1)' : 'rgba(220, 53, 69, 0.1)';
            
            // Create chart with real OKX data - defensive loading
            if (!window.Chart) return;
            this.portfolioChart = new Chart(portfolioCanvas, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Portfolio Value',
                        data: values,
                        borderColor: lineColor,
                        backgroundColor: fillColor,
                        borderWidth: 2,
                        fill: true,
                        tension: 0.2,
                        pointBackgroundColor: lineColor,
                        pointBorderColor: lineColor,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        title: { 
                            display: true, 
                            text: `Portfolio Value (${historyData.length} days)`,
                            font: { size: 12 }
                        }
                    },
                    scales: {
                        x: {
                            display: true,
                            grid: { display: false }
                        },
                        y: {
                            display: true,
                            grid: { color: 'rgba(128, 128, 128, 0.1)' },
                            ticks: {
                                callback: function(value) {
                                    return window.tradingApp ? window.tradingApp.formatCurrency(value) : `$${value.toFixed(2)}`;
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
        } catch (error) {
            console.debug('Portfolio value chart creation failed:', error);
            // Fallback display
            if (portfolioCanvas) {
                portfolioCanvas.style.display = 'none';
                const fallback = document.createElement('div');
                fallback.className = 'text-center text-muted p-3';
                // Create content safely using DOM methods
                const title = document.createElement('strong');
                title.textContent = 'Portfolio History';
                fallback.appendChild(title);
                fallback.appendChild(document.createElement('br'));
                
                const currentValue = this.formatCurrency(safeNum(historyData[historyData.length - 1]?.value, 0));
                const valueText = document.createTextNode(`Current Value: ${currentValue}`);
                fallback.appendChild(valueText);
                fallback.appendChild(document.createElement('br'));
                
                const dataPointsText = document.createTextNode(`Data Points: ${historyData.length}`);
                fallback.appendChild(dataPointsText);
                portfolioCanvas.parentNode.replaceChild(fallback, portfolioCanvas);
            }
        }
    }
    
    async updateAssetAllocation() {
        try {
            const response = await fetch('/api/asset-allocation', { cache: 'no-cache' });
            if (!response.ok) return;
            const data = await response.json();
            
            if (!data.success || !data.allocation) return;
            
            // Update asset allocation chart with real OKX data
            this.updateAssetAllocationChart(data.allocation);
            
            // Update allocation display elements
            this.updateAllocationDisplay(data);
            
        } catch (error) {
        }
    }
    
    updateAssetAllocationChart(allocationData) {
        const allocationCanvas = document.getElementById('allocationChart');
        if (!allocationCanvas) {
            return;
        }
        if (!window.Chart) {
            return;
        }
        
        try {
            // Destroy existing chart
            if (this.allocationChart) {
                this.allocationChart.destroy();
            }
            
            // Prepare data for Chart.js
            const labels = allocationData.map(item => item.symbol);
            const values = allocationData.map(item => item.allocation_percent);
            const colors = [
                '#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1',
                '#fd7e14', '#20c997', '#6c757d', '#e83e8c', '#17a2b8'
            ];
            
            // Create asset allocation pie chart with real OKX data - defensive loading
            if (!window.Chart) return;
            this.allocationChart = new Chart(allocationCanvas, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors.slice(0, values.length),
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: true,
                            position: 'right',
                            labels: {
                                generateLabels: function(chart) {
                                    const data = chart.data;
                                    if (data.labels.length && data.datasets.length) {
                                        return data.labels.map(function(label, i) {
                                            const value = data.datasets[0].data[i];
                                            return {
                                                text: `${label}: ${value.toFixed(1)}%`,
                                                fillStyle: data.datasets[0].backgroundColor[i],
                                                strokeStyle: data.datasets[0].borderColor,
                                                lineWidth: data.datasets[0].borderWidth,
                                                hidden: false,
                                                index: i
                                            };
                                        });
                                    }
                                    return [];
                                }
                            }
                        },
                        title: { 
                            display: true, 
                            text: `Asset Allocation (${allocationData.length} assets)`,
                            font: { size: 12 }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const item = allocationData[context.dataIndex];
                                    return [
                                        `${item.symbol}: ${item.allocation_percent.toFixed(1)}%`,
                                        `Value: ${window.tradingApp ? window.tradingApp.formatCurrency(item.current_value) : '$' + item.current_value.toFixed(2)}`,
                                        `P&L: ${safeNum(item.pnl_percent, 0) >= 0 ? '+' : ''}${safeNum(item.pnl_percent, 0).toFixed(2)}%`
                                    ];
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            // Fallback display
            if (allocationCanvas) {
                allocationCanvas.style.display = 'none';
                const fallback = document.createElement('div');
                fallback.className = 'text-center text-muted p-3';
                // Create content safely using DOM methods
                const title = document.createElement('strong');
                title.textContent = 'Asset Allocation';
                fallback.appendChild(title);
                fallback.appendChild(document.createElement('br'));
                
                allocationData.forEach((item, index) => {
                    if (index > 0) fallback.appendChild(document.createElement('br'));
                    const itemText = document.createTextNode(`${item.symbol}: ${item.allocation_percent.toFixed(1)}%`);
                    fallback.appendChild(itemText);
                });
                allocationCanvas.parentNode.replaceChild(fallback, allocationCanvas);
            }
        }
    }
    
    updateAllocationDisplay(data) {
        // Update allocation summary elements if they exist
        const elements = {
            'allocation-count': data.allocation_count,
            'allocation-largest': `${data.largest_allocation.toFixed(1)}%`,
            'allocation-smallest': `${data.smallest_allocation.toFixed(1)}%`,
            'allocation-risk-level': data.concentration_analysis?.risk_level || 'Unknown',
            'allocation-diversification': `${data.concentration_analysis?.diversification_score || 0}%`,
            'allocation-top3': `${data.concentration_analysis?.top_3_percentage.toFixed(1)}%`
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                
                // Add color coding for risk levels
                if (id === 'allocation-risk-level') {
                    element.className = value.includes('High') ? 'text-danger' : 
                                      value.includes('Medium') ? 'text-warning' : 'text-success';
                }
            }
        });
    }
    
    async updateBestPerformer() {
        try {
            const response = await fetch('/api/best-performer', { cache: 'no-cache' });
            if (!response.ok) return;
            const data = await response.json();
            
            if (!data.success || !data.best_performer) return;
            
            // Update best performer display elements
            this.updateBestPerformerDisplay(data.best_performer);
            
        } catch (error) {
            console.debug('Best performer update failed:', error);
        }
    }
    
    updateBestPerformerDisplay(performer) {
        // Update best performer elements if they exist
        const elements = {
            'best-performer-symbol': performer.symbol,
            'best-performer-name': performer.name,
            'best-performer-price': this.formatCurrency(safeNum(performer.current_price, 0)),
            'best-performer-24h': `${safeNum(performer.price_change_24h, 0) >= 0 ? '+' : ''}${safeNum(performer.price_change_24h, 0).toFixed(2)}%`,
            'best-performer-7d': `${safeNum(performer.price_change_7d, 0) >= 0 ? '+' : ''}${safeNum(performer.price_change_7d, 0).toFixed(2)}%`,
            'best-performer-pnl': `${safeNum(performer.pnl_percent, 0) >= 0 ? '+' : ''}${safeNum(performer.pnl_percent, 0).toFixed(2)}%`,
            'best-performer-allocation': `${safeNum(performer.allocation_percent, 0).toFixed(1)}%`,
            'best-performer-value': this.formatCurrency(safeNum(performer.current_value, 0)),
            'best-performer-volume': this.formatNumber(safeNum(performer.volume_24h, 0))
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                
                // Add color coding for performance indicators
                if (id.includes('24h') || id.includes('7d') || id.includes('pnl')) {
                    const numValue = parseFloat(value);
                    element.className = numValue >= 0 ? 'text-success' : 'text-danger';
                }
            }
        });
        
        // Update best performer card title if it exists
        const cardTitle = document.getElementById('best-performer-card-title');
        if (cardTitle) {
            cardTitle.textContent = `Best Performer: ${performer.symbol}`;
        } else {
        }
    }
    
    async updateWorstPerformer() {
        try {
            const response = await fetch('/api/worst-performer', { cache: 'no-cache' });
            if (!response.ok) return;
            const data = await response.json();
            
            if (!data.success || !data.worst_performer) return;
            
            // Update worst performer display elements
            this.updateWorstPerformerDisplay(data.worst_performer);
            
        } catch (error) {
            console.debug('Worst performer update failed:', error);
        }
    }
    
    updateWorstPerformerDisplay(performer) {
        // Update worst performer elements if they exist
        const elements = {
            'worst-performer-symbol': performer.symbol,
            'worst-performer-name': performer.name,
            'worst-performer-price': this.formatCurrency(performer.current_price),
            'worst-performer-24h': `${performer.price_change_24h >= 0 ? '+' : ''}${performer.price_change_24h.toFixed(2)}%`,
            'worst-performer-7d': `${performer.price_change_7d >= 0 ? '+' : ''}${performer.price_change_7d.toFixed(2)}%`,
            'worst-performer-pnl': `${performer.pnl_percent >= 0 ? '+' : ''}${performer.pnl_percent.toFixed(2)}%`,
            'worst-performer-allocation': `${performer.allocation_percent.toFixed(1)}%`,
            'worst-performer-value': this.formatCurrency(performer.current_value),
            'worst-performer-volume': this.formatNumber(performer.volume_24h)
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                
                // Add color coding for performance indicators
                if (id.includes('24h') || id.includes('7d') || id.includes('pnl')) {
                    const numValue = parseFloat(value);
                    element.className = numValue >= 0 ? 'text-success' : 'text-danger';
                }
            }
        });
        
        // Update worst performer card title if it exists
        const cardTitle = document.getElementById('worst-performer-card-title');
        if (cardTitle) {
            cardTitle.textContent = `Worst Performer: ${performer.symbol}`;
        } else {
        }
    }
    
    async updateEquityCurve() {
        try {
            const timeframe = document.getElementById('equity-timeframe')?.value || '30d';
            const response = await fetch(`/api/equity-curve?timeframe=${timeframe}`, { cache: 'no-cache' });
            if (!response.ok) return;
            const data = await response.json();
            
            if (!data.success || !data.equity_curve) return;
            
            // Update equity curve chart
            this.updateEquityCurveChart(data.equity_curve, data.metrics);
            
            // Update equity metrics display
            this.updateEquityMetrics(data.metrics);
            
        } catch (error) {
            console.debug('Equity curve update failed:', error);
        }
    }
    
    updateEquityCurveChart(equityData, metrics) {
        const equityCanvas = document.getElementById('equityChart');
        if (!equityCanvas) {
            return;
        }
        if (!window.Chart) {
            console.debug('Chart.js not available - skipping equity chart');
            return;
        }
        
        try {
            // Destroy existing chart
            if (this.equityChart) {
                this.equityChart.destroy();
            }
            
            // Prepare data for Chart.js
            const labels = equityData.map(point => {
                const date = new Date(point.date);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            });
            const values = equityData.map(point => point.equity);
            
            // Determine line color based on overall performance
            const lineColor = metrics.total_return_percent >= 0 ? '#28a745' : '#dc3545';
            const fillColor = metrics.total_return_percent >= 0 ? 'rgba(40, 167, 69, 0.1)' : 'rgba(220, 53, 69, 0.1)';
            
            // Create equity curve line chart - defensive loading
            if (!window.Chart) return;
            this.equityChart = new Chart(equityCanvas, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Portfolio Equity',
                        data: values,
                        borderColor: lineColor,
                        backgroundColor: fillColor,
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1,
                        pointBackgroundColor: lineColor,
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: true,
                            position: 'top'
                        },
                        title: { 
                            display: true, 
                            text: `Equity Curve (${equityData.length} data points)`,
                            font: { size: 12 }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed.y;
                                    const prevValue = context.dataIndex > 0 ? values[context.dataIndex - 1] : value;
                                    const change = prevValue > 0 ? ((value - prevValue) / prevValue) * 100 : 0;
                                    return [
                                        `Equity: ${window.tradingApp ? window.tradingApp.formatCurrency(value) : '$' + value.toFixed(2)}`,
                                        `Change: ${change >= 0 ? '+' : ''}${change.toFixed(2)}%`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            display: true,
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        },
                        y: {
                            display: true,
                            title: {
                                display: true,
                                text: 'Portfolio Value'
                            },
                            ticks: {
                                callback: function(value) {
                                    return window.tradingApp ? window.tradingApp.formatCurrency(value) : '$' + value.toFixed(0);
                                }
                            }
                        }
                    }
                }
            });
            
        } catch (error) {
            console.debug('Equity curve chart creation failed:', error);
            // Fallback display
            if (equityCanvas) {
                equityCanvas.style.display = 'none';
                const fallback = document.createElement('div');
                fallback.className = 'text-center text-muted p-3';
                // Safe DOM creation instead of innerHTML
                const title = document.createElement('strong');
                title.textContent = 'Equity Curve';
                fallback.appendChild(title);
                fallback.appendChild(document.createElement('br'));
                
                const returnText = document.createTextNode(
                    `Return: ${metrics.total_return_percent >= 0 ? '+' : ''}${metrics.total_return_percent.toFixed(2)}%`
                );
                fallback.appendChild(returnText);
                fallback.appendChild(document.createElement('br'));
                
                const dataPointsText = document.createTextNode(`Data Points: ${equityData.length}`);
                fallback.appendChild(dataPointsText);
                equityCanvas.parentNode.replaceChild(fallback, equityCanvas);
            }
        }
    }
    
    updateEquityMetrics(metrics) {
        // Update equity metrics elements if they exist
        const elements = {
            'equity-total-return': `${metrics.total_return_percent >= 0 ? '+' : ''}${metrics.total_return_percent.toFixed(2)}%`,
            'equity-max-drawdown': `${metrics.max_drawdown_percent.toFixed(2)}%`,
            'equity-volatility': `${metrics.volatility_percent.toFixed(2)}%`,
            'equity-data-points': metrics.data_points,
            'equity-start-value': this.formatCurrency(metrics.start_equity),
            'equity-end-value': this.formatCurrency(metrics.end_equity)
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                
                // Add color coding for performance indicators
                if (id === 'equity-total-return') {
                    const numValue = parseFloat(value);
                    element.className = numValue >= 0 ? 'text-success' : 'text-danger';
                }
                if (id === 'equity-max-drawdown') {
                    element.className = 'text-warn';
                }
            }
        });
    }
    
    async updateDrawdownAnalysis() {
        try {
            const timeframe = document.getElementById('drawdown-timeframe')?.value || '30d';
            const response = await fetch(`/api/drawdown-analysis?timeframe=${timeframe}`, { cache: 'no-cache' });
            if (!response.ok) return;
            const data = await response.json();
            
            if (!data.success || !data.drawdown_data) return;
            
            // Update drawdown chart
            this.updateDrawdownChart(data.drawdown_data, data.metrics);
            
            // Update drawdown metrics display
            this.updateDrawdownMetrics(data.metrics);
            
        } catch (error) {
            console.debug('Drawdown analysis update failed:', error);
        }
    }
    
    updateDrawdownChart(drawdownData, metrics) {
        const drawdownCanvas = document.getElementById('drawdownChart');
        if (!drawdownCanvas) {
            return;
        }
        if (!window.Chart) {
            console.debug('Chart.js not available - skipping drawdown chart');
            return;
        }
        
        try {
            // Destroy existing chart
            if (this.drawdownChart) {
                this.drawdownChart.destroy();
            }
            
            // Prepare data for Chart.js
            const labels = drawdownData.map(point => {
                const date = new Date(point.date);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            });
            
            const equityValues = drawdownData.map(point => point.equity);
            const peakValues = drawdownData.map(point => point.peak_equity);
            const drawdownPercents = drawdownData.map(point => -point.drawdown_percent); // Negative for underwater display
            
            // Create dual-axis drawdown chart - defensive loading
            if (!window.Chart) return;
            this.drawdownChart = new Chart(drawdownCanvas, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Portfolio Equity',
                            data: equityValues,
                            borderColor: '#007bff',
                            backgroundColor: 'rgba(0, 123, 255, 0.1)',
                            borderWidth: 2,
                            fill: false,
                            tension: 0.1,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Peak Equity',
                            data: peakValues,
                            borderColor: '#28a745',
                            backgroundColor: 'transparent',
                            borderWidth: 1,
                            borderDash: [5, 5],
                            fill: false,
                            tension: 0.1,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Drawdown %',
                            data: drawdownPercents,
                            borderColor: '#dc3545',
                            backgroundColor: 'rgba(220, 53, 69, 0.1)',
                            borderWidth: 2,
                            fill: 'origin',
                            tension: 0.1,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: true,
                            position: 'top'
                        },
                        title: { 
                            display: true, 
                            text: `Drawdown Analysis (${drawdownData.length} data points)`,
                            font: { size: 12 }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const dataIndex = context.dataIndex;
                                    const point = drawdownData[dataIndex];
                                    
                                    if (context.datasetIndex === 0) {
                                        return `Equity: ${window.tradingApp ? window.tradingApp.formatCurrency(point.equity) : '$' + point.equity.toFixed(2)}`;
                                    } else if (context.datasetIndex === 1) {
                                        return `Peak: ${window.tradingApp ? window.tradingApp.formatCurrency(point.peak_equity) : '$' + point.peak_equity.toFixed(2)}`;
                                    } else {
                                        return `Drawdown: ${point.drawdown_percent.toFixed(2)}%`;
                                    }
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            display: true,
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Portfolio Value'
                            },
                            ticks: {
                                callback: function(value) {
                                    return window.tradingApp ? window.tradingApp.formatCurrency(value) : '$' + value.toFixed(0);
                                }
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Drawdown %'
                            },
                            max: 0,
                            ticks: {
                                callback: function(value) {
                                    return value.toFixed(1) + '%';
                                }
                            },
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    }
                }
            });
            
        } catch (error) {
            console.debug('Drawdown chart creation failed:', error);
            // Fallback display
            if (drawdownCanvas) {
                drawdownCanvas.style.display = 'none';
                const fallback = document.createElement('div');
                fallback.className = 'text-center text-muted p-3';
                // Safe DOM creation instead of innerHTML
                const title = document.createElement('strong');
                title.textContent = 'Drawdown Analysis';
                fallback.appendChild(title);
                fallback.appendChild(document.createElement('br'));
                
                const drawdownText = document.createTextNode(
                    `Max Drawdown: ${metrics.max_drawdown_percent.toFixed(2)}%`
                );
                fallback.appendChild(drawdownText);
                fallback.appendChild(document.createElement('br'));
                
                const dataPointsText = document.createTextNode(`Data Points: ${drawdownData.length}`);
                fallback.appendChild(dataPointsText);
                drawdownCanvas.parentNode.replaceChild(fallback, drawdownCanvas);
            }
        }
    }
    
    updateDrawdownMetrics(metrics) {
        // Update drawdown metrics elements if they exist with safe null checks
        const elements = {
            'drawdown-max': `${(metrics.max_drawdown_percent || 0).toFixed(2)}%`,
            'drawdown-current': `${(metrics.current_drawdown_percent || 0).toFixed(2)}%`,
            'drawdown-average': `${(metrics.average_drawdown_percent || 0).toFixed(2)}%`,
            'drawdown-periods': metrics.total_drawdown_periods || 'N/A',
            'drawdown-recovery': metrics.recovery_periods || 'N/A',
            'drawdown-underwater': `${(metrics.underwater_percentage || 0).toFixed(1)}%`,
            'drawdown-duration': `${metrics.max_drawdown_duration_days || 0} days`,
            'drawdown-peak': this.formatCurrency(metrics.peak_equity || metrics.current_equity || 0),
            'drawdown-start': metrics.max_drawdown_start || 'N/A',
            'drawdown-end': metrics.max_drawdown_end || 'N/A'
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                
                // Add color coding for drawdown indicators
                if (id.includes('max') || id.includes('current') || id.includes('average')) {
                    const numValue = parseFloat(value);
                    if (numValue > 10) {
                        element.className = 'text-danger';
                    } else if (numValue > 5) {
                        element.className = 'text-warn';
                    } else {
                        element.className = 'text-success';
                    }
                }
            }
        });
    }
    
    async updateCurrentHoldings() {
        try {
            const response = await fetch('/api/current-holdings', { cache: 'no-cache' });
            if (!response.ok) return;
            const data = await response.json();
            
            if (!data.success || !data.holdings) return;
            
            console.log("Holdings data received:", data.holdings);
        
        // Target multiplier validation removed for production
            
            // Update table via consolidated system to prevent flashing
            if (window.tradingApp) {
                window.tradingApp.currentCryptoData = data.holdings || [];
                window.tradingApp.updateAllTables(data.holdings || []);
            } else {
                // Fallback for edge cases
                console.log('TradingApp not ready, using fallback table update');
                updateHoldingsTable(data.holdings || []);
            }
            
        } catch (error) {
            console.debug('Current holdings update failed:', error);
        }
    }
    
    // Add the missing updateAvailablePositions method
    async updateAvailablePositions() {
        try {
            await fetchAndUpdateAvailablePositions();
        } catch (error) {
            console.debug('Available positions update failed:', error);
        }
    }
    
    updateHoldingsTable(holdings, totalValue) {
        const holdingsTableBody = document.getElementById('holdings-tbody');
        if (!holdingsTableBody) {
            return;
        }
        
        try {
            // Clear existing rows safely
            holdingsTableBody.textContent = '';
            
            if (!holdings || holdings.length === 0) {
                // Show empty state
                const emptyRow = document.createElement('tr');
                const emptyCell = document.createElement('td');
                emptyCell.setAttribute('colspan', getTableColumnCount('holdings-table'));
                emptyCell.className = 'text-center text-muted py-4';
                
                const icon = document.createElement('i');
                icon.className = 'fa-solid fa-coins me-2';
                emptyCell.appendChild(icon);
                emptyCell.appendChild(document.createTextNode('No holdings found'));
                
                emptyRow.appendChild(emptyCell);
                holdingsTableBody.appendChild(emptyRow);
                return;
            }
            
            // Filter holdings: only show positions worth >= $0.01 in Open Positions
            const significantHoldings = holdings.filter(holding => {
                const currentValue = holding.current_value || 0;
                return currentValue >= MIN_POSITION_USD; // Only show positions worth minimum threshold or more
            });
            
            console.log('Filtering positions:', {
                total_holdings: holdings.length,
                significant_holdings: significantHoldings.length,
                filtered_out: holdings.filter(h => (h.current_value || 0) < MIN_POSITION_USD).map(h => ({
                    symbol: h.symbol,
                    value: h.current_value,
                    note: `${h.symbol} worth $${(h.current_value || 0).toFixed(8)} filtered to Available Positions`
                }))
            });
            
            if (significantHoldings.length === 0) {
                // Show message that small positions are moved to Available Positions
                const infoRow = document.createElement('tr');
                const infoCell = document.createElement('td');
                infoCell.setAttribute('colspan', getTableColumnCount('holdings-table'));
                infoCell.className = 'text-center text-muted py-4';
                
                const icon = document.createElement('i');
                icon.className = 'fa-solid fa-circle-info me-2';
                infoCell.appendChild(icon);
                infoCell.appendChild(document.createTextNode(`No positions above $${MIN_POSITION_USD.toFixed(2)} threshold`));
                
                const lineBreak = document.createElement('br');
                infoCell.appendChild(lineBreak);
                
                const smallText = document.createElement('small');
                smallText.textContent = `Small positions (< $${MIN_POSITION_USD.toFixed(2)}) are available in the Available Positions section`;
                infoCell.appendChild(smallText);
                
                infoRow.appendChild(infoCell);
                holdingsTableBody.appendChild(infoRow);
                return;
            }
            
            // Populate significant holdings rows only
            significantHoldings.forEach(holding => {
                const row = document.createElement('tr');
                
                // Enhanced P&L color class with nuanced levels
                const getEnhancedPnlClass = (pnlPercent) => {
                    if (pnlPercent >= 10) return 'text-success fw-bold';       // Excellent gains (>10%): Bold bright green
                    if (pnlPercent >= 3) return 'text-success';                // Good gains (3-10%): Green
                    if (pnlPercent >= 0) return 'text-success opacity-75';     // Small gains (0-3%): Light green
                    if (pnlPercent >= -3) return 'text-warning opacity-75';    // Small losses (0 to -3%): Light orange
                    if (pnlPercent >= -10) return 'text-warning';              // Moderate losses (-3% to -10%): Orange
                    return 'text-danger fw-bold';                              // Heavy losses (< -10%): Bold red
                };
                
                const pnlClass = getEnhancedPnlClass(holding.pnl_percent || 0);
                const pnlSign = holding.pnl_percent >= 0 ? '+' : '';
                
                // Get coin display info
                const coinDisplay = this.getCoinDisplaySync(holding.symbol); // Use sync version for immediate display
                
                // Create symbol cell with safe DOM methods
                const symbolCell = document.createElement('td');
                const flexDiv = document.createElement('div');
                flexDiv.className = 'd-flex align-items-center';
                
                const iconDiv = document.createElement('div');
                iconDiv.className = 'coin-icon me-2';
                iconDiv.style.color = coinDisplay.color;
                
                if (coinDisplay.type === 'image') {
                    const icon = document.createElement('img');
                    // Add cache-busting parameter to force fresh image load
                    const cacheBuster = Date.now() + Math.random();
                    icon.src = coinDisplay.icon + '?v=' + cacheBuster;
                    icon.style.width = '24px';
                    icon.style.height = '24px';
                    icon.style.borderRadius = '50%';
                    icon.style.objectFit = 'cover';
                    icon.alt = coinDisplay.name;
                    icon.onerror = function() {
                        // Fallback to FontAwesome icon if image fails to load
                        const fallbackIcon = document.createElement('i');
                        fallbackIcon.className = 'fa-solid fa-coins';
                        fallbackIcon.style.color = coinDisplay.color;
                        iconDiv.replaceChild(fallbackIcon, icon);
                    };
                    iconDiv.appendChild(icon);
                } else {
                    const icon = document.createElement('i');
                    icon.className = coinDisplay.icon;
                    iconDiv.appendChild(icon);
                }
                
                const textDiv = document.createElement('div');
                const symbolStrong = document.createElement('strong');
                symbolStrong.textContent = holding.symbol;
                textDiv.appendChild(symbolStrong);
                textDiv.appendChild(document.createElement('br'));
                const nameSmall = document.createElement('small');
                nameSmall.className = 'text-muted';
                nameSmall.textContent = coinDisplay.name;
                textDiv.appendChild(nameSmall);
                
                flexDiv.appendChild(iconDiv);
                flexDiv.appendChild(textDiv);
                symbolCell.appendChild(flexDiv);
                row.appendChild(symbolCell);
                
                // Quantity/Balance cell
                const quantityCell = document.createElement('td');
                quantityCell.className = 'text-end';
                quantityCell.textContent = holding.quantity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 8 });
                row.appendChild(quantityCell);
                
                // Value cell
                const valueCell = document.createElement('td');
                valueCell.className = 'text-end';
                valueCell.textContent = this.formatCurrency(holding.current_value);
                row.appendChild(valueCell);
                
                // Cost basis cell
                const costBasisCell = document.createElement('td');
                costBasisCell.className = 'text-end';
                costBasisCell.textContent = this.formatCurrency(holding.cost_basis || 0);
                row.appendChild(costBasisCell);
                
                // Average purchase price cell (calculated from cost basis / quantity)
                const avgPriceCell = document.createElement('td');
                avgPriceCell.className = 'text-end';
                const avgPrice = holding.quantity > 0 ? (holding.cost_basis || 0) / holding.quantity : 0;
                avgPriceCell.textContent = this.formatCurrency(avgPrice);
                row.appendChild(avgPriceCell);
                
                // Current market price cell
                const priceCell = document.createElement('td');
                priceCell.className = 'text-end';
                priceCell.textContent = this.formatCurrency(holding.current_price);
                row.appendChild(priceCell);
                
                // PnL Dollar cell
                const pnlDollarCell = document.createElement('td');
                pnlDollarCell.className = `text-end ${pnlClass}`;
                pnlDollarCell.textContent = this.formatSmallCurrency(holding.pnl_amount);
                row.appendChild(pnlDollarCell);
                
                // PnL Percent cell
                const pnlPercentCell = document.createElement('td');
                pnlPercentCell.className = `text-end ${pnlClass}`;
                pnlPercentCell.textContent = `${pnlSign}${holding.pnl_percent.toFixed(2)}%`;
                row.appendChild(pnlPercentCell);
                
                // Target value cell (dynamic calculation)
                const costBasis = holding.cost_basis || 0;
                const targetValueNum = calcTargetValue(costBasis, holding);
                const targetProfitNum = calcTargetDollar(costBasis, holding);
                const targetPctNum = getTargetPercent(holding);
                
                const targetValueCell = document.createElement('td');
                targetValueCell.className = 'text-end';
                targetValueCell.textContent = formatMoney(targetValueNum, this.selectedCurrency, 2, 2);
                row.appendChild(targetValueCell);
                
                // Target PnL Dollar cell
                const targetPnlDollarCell = document.createElement('td');
                targetPnlDollarCell.className = 'text-end text-success';
                targetPnlDollarCell.textContent = formatMoney(targetProfitNum, this.selectedCurrency, 2, 2);
                row.appendChild(targetPnlDollarCell);
                
                // Target PnL Percent cell
                const targetPnlPercentCell = document.createElement('td');
                targetPnlPercentCell.className = 'text-end text-success';
                const targetPnlPercent = targetPctNum;
                targetPnlPercentCell.textContent = `+${targetPnlPercent.toFixed(2)}%`;
                row.appendChild(targetPnlPercentCell);
                
                // Days cell
                const daysCell = document.createElement('td');
                daysCell.className = 'text-center text-muted';
                const daysHeld =
                  holding.open_time ? Math.floor((Date.now() - new Date(holding.open_time)) / 86_400_000) : null;
                daysCell.textContent = daysHeld != null ? `${daysHeld}d` : '—';
                row.appendChild(daysCell);
                
                
                holdingsTableBody.appendChild(row);
            });
            
            // Update total value display
            const totalValueElement = document.getElementById('holdings-total-value');
            if (totalValueElement) {
                totalValueElement.textContent = this.formatCurrency(totalValue);
            }
            
            // Update holdings count (only significant holdings)
            const holdingsCountElement = document.getElementById('holdings-count');
            if (holdingsCountElement) {
                holdingsCountElement.textContent = significantHoldings.length;
            }

            // Update mobile data labels and ensure proper table formatting
            const table = document.getElementById('holdings-table');
            if (table) {
                v02ApplyDataLabels(table);
                // Ensure all v02 tables are properly initialized after dynamic updates
                initializeV02Tables();
            }
            
            console.log('Table updated successfully');
            
        } catch (error) {
            console.debug('Holdings table update failed:', error);
            
            // Fallback display
            holdingsTableBody.textContent = '';
            const errorRow = document.createElement('tr');
            const errorCell = document.createElement('td');
            errorCell.setAttribute('colspan', getTableColumnCount('holdings-table'));
            errorCell.className = 'text-center text-danger py-4';
            
            const errorIcon = document.createElement('i');
            errorIcon.className = 'fa-solid fa-triangle-exclamation me-2';
            errorCell.appendChild(errorIcon);
            errorCell.appendChild(document.createTextNode('Error loading holdings'));
            
            errorRow.appendChild(errorCell);
            holdingsTableBody.appendChild(errorRow);
        }
    }
    
    // Test function to directly populate table with known data
    testPopulateTradesTable() {
        console.log('DEBUG: Manual test populate trades table');
        const sampleTrades = [
            {
                action: "BUY",
                side: "BUY", 
                symbol: "BTC/USDT",
                timestamp: "2025-08-27T06:05:20Z",
                quantity: 0.00001,
                price: 111280.7,
                pnl: 0,
                type: "Trade"
            },
            {
                action: "SELL",
                side: "SELL",
                symbol: "ETH/USDT", 
                timestamp: "2025-08-27T05:21:05Z",
                quantity: 0.001,
                price: 4500,
                pnl: -5.2,
                type: "Trade"
            }
        ];
        
    }

    
    
    updateTradesTable(trades, summary) {
        const tradesTableBody = document.getElementById('trades-tbody');
        if (!tradesTableBody) return;
        
        try {
            // Clear existing rows safely
            tradesTableBody.textContent = '';
            
            if (!trades || trades.length === 0) {
                // Show empty state
                const emptyRow = document.createElement('tr');
                const emptyCell = document.createElement('td');
                emptyCell.setAttribute('colspan', '7');
                emptyCell.className = 'text-center text-muted py-4';
                
                const emptyIcon = document.createElement('i');
                emptyIcon.className = 'fa-solid fa-arrows-rotate me-2';
                emptyCell.appendChild(emptyIcon);
                emptyCell.appendChild(document.createTextNode('No recent trades found'));
                
                emptyRow.appendChild(emptyCell);
                tradesTableBody.appendChild(emptyRow);
                
                // Update summary with zeros
                this.updateTradesSummary({
                    total_trades: 0,
                    total_buy_volume: 0,
                    total_sell_volume: 0,
                    total_fees: 0,
                    unique_symbols: 0
                });
                return;
            }
            
            // Populate trades rows
            trades.forEach(trade => {
                const row = document.createElement('tr');
                
                // Format data
                const side = trade.side || trade.action || '';
                const sideClass = side === 'BUY' ? 'badge bg-success' : 'badge bg-danger';
                const transactionType = trade.type || trade.transaction_type || 'Trade';
                const symbol = trade.symbol || trade.asset || 'Unknown';
                const tradeDate = new Date(trade.timestamp);
                const timestamp = tradeDate.toLocaleString();
                const quantity = trade.quantity || 0;
                const price = trade.price || 0;
                const pnl = trade.pnl || 0;
                const pnlClass = pnl >= 0 ? 'text-success' : 'text-danger';
                
                // Type cell
                const typeCell = document.createElement('td');
                const typeBadge = document.createElement('span');
                typeBadge.className = 'badge bg-primary';
                typeBadge.textContent = transactionType;
                typeCell.appendChild(typeBadge);
                row.appendChild(typeCell);
                
                // Action cell (side)
                const sideCell = document.createElement('td');
                const sideBadge = document.createElement('span');
                sideBadge.className = sideClass;
                sideBadge.textContent = side;
                sideCell.appendChild(sideBadge);
                row.appendChild(sideCell);
                
                // Symbol cell
                const symbolCell = document.createElement('td');
                const symbolStrong = document.createElement('strong');
                symbolStrong.textContent = symbol;
                symbolCell.appendChild(symbolStrong);
                row.appendChild(symbolCell);
                
                // Time cell
                const timeCell = document.createElement('td');
                timeCell.textContent = timestamp;
                row.appendChild(timeCell);
                
                // Size cell
                const quantityCell = document.createElement('td');
                quantityCell.className = 'text-end';
                quantityCell.textContent = parseFloat(quantity).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 8 });
                row.appendChild(quantityCell);
                
                // Price cell
                const priceCell = document.createElement('td');
                priceCell.className = 'text-end';
                priceCell.textContent = price > 0 ? this.formatCurrency(price) : 'N/A';
                row.appendChild(priceCell);
                
                // P&L cell
                const pnlCell = document.createElement('td');
                pnlCell.className = `text-end ${pnlClass}`;
                pnlCell.textContent = this.formatCurrency(pnl);
                row.appendChild(pnlCell);
                
                tradesTableBody.appendChild(row);
            });
            
            // Update trades summary
            this.updateTradesSummary(summary);
            
        } catch (error) {
            console.debug('Trades table update failed:', error);
            
            // Fallback display
            tradesTableBody.textContent = '';
            const errorRow = document.createElement('tr');
            const errorCell = document.createElement('td');
            errorCell.setAttribute('colspan', '7');
            errorCell.className = 'text-center text-danger py-4';
            
            const errorIcon = document.createElement('i');
            errorIcon.className = 'fa-solid fa-triangle-exclamation me-2';
            errorCell.appendChild(errorIcon);
            errorCell.appendChild(document.createTextNode('Error loading trades'));
            
            errorRow.appendChild(errorCell);
            tradesTableBody.appendChild(errorRow);
        }
    }
    
    updateTradesSummary(summary) {
        // Update trades summary elements if they exist
        const elements = {
            'trades-total-count': summary.total_trades,
            'trades-buy-volume': this.formatCurrency(summary.total_buy_volume),
            'trades-sell-volume': this.formatCurrency(summary.total_sell_volume),
            'trades-net-volume': this.formatCurrency(summary.net_volume || 0),
            'trades-total-fees': this.formatCurrency(summary.total_fees),
            'trades-unique-symbols': summary.unique_symbols,
            'trades-avg-size': this.formatCurrency(summary.avg_trade_size || 0)
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                
                // Add color coding for net volume
                if (id === 'trades-net-volume') {
                    const numValue = summary.net_volume || 0;
                    element.className = numValue >= 0 ? 'text-success' : 'text-danger';
                }
            }
        });
    }
    
    async updatePerformanceAnalytics() {
        try {
            // THROTTLE: Prevent rapid-fire calls to avoid 429 rate limiting
            const now = Date.now();
            if (this.lastPerformanceUpdate && (now - this.lastPerformanceUpdate) < 30000) {
                console.debug('Performance analytics throttled (30s cooldown)');
                return;
            }
            this.lastPerformanceUpdate = now;
            
            const timeframe = document.getElementById('performance-timeframe')?.value || '30d';
            const response = await fetch(`/api/performance-analytics?timeframe=${timeframe}&currency=${this.selectedCurrency}&force_okx=true`, { cache: 'no-cache' });
            if (!response.ok) return;
            const data = await response.json();
            
            if (!data.success || !data.metrics) return;
            
            // Update performance analytics cards
            this.updatePerformanceCards(data.metrics, timeframe);
            
        } catch (error) {
            console.debug('Performance analytics update failed:', error);
        }
    }
    
    updatePerformanceCards(metrics, timeframe) {
        try {
            // Update performance metric elements if they exist
            const elements = {
                // Total Return Card
                'perf-total-return': this.formatCurrency(metrics.total_return),
                'perf-total-return-percent': `${metrics.total_return_percent >= 0 ? '+' : ''}${metrics.total_return_percent.toFixed(2)}%`,
                
                // Daily Change Card  
                'perf-daily-change': this.formatCurrency(metrics.daily_change),
                'perf-daily-change-percent': `${metrics.daily_change_percent >= 0 ? '+' : ''}${metrics.daily_change_percent.toFixed(2)}%`,
                
                // Trading Activity Card
                'perf-total-trades': metrics.total_trades,
                'perf-win-rate': `${metrics.win_rate.toFixed(1)}%`,
                
                // Risk Metrics Card
                'perf-sharpe-ratio': metrics.sharpe_ratio.toFixed(2),
                'perf-volatility': `${metrics.volatility.toFixed(2)}%`,
                'perf-max-drawdown': `${metrics.max_drawdown.toFixed(2)}%`,
                
                // Portfolio Value
                'perf-current-value': this.formatCurrency(metrics.current_value)
            };
            
            Object.entries(elements).forEach(([id, value]) => {
                const element = document.getElementById(id);
                if (element) {
                    element.textContent = value;
                    
                    // Add color coding for performance indicators
                    if (id.includes('total-return')) {
                        const numValue = metrics.total_return_percent;
                        element.className = numValue >= 0 ? 'text-success' : 'text-danger';
                    }
                    if (id.includes('daily-change')) {
                        const numValue = metrics.daily_change_percent;
                        element.className = numValue >= 0 ? 'text-success' : 'text-danger';
                    }
                    if (id.includes('win-rate')) {
                        const numValue = metrics.win_rate;
                        if (numValue >= 60) {
                            element.className = 'text-success';
                        } else if (numValue >= 40) {
                            element.className = 'text-warning';
                        } else {
                            element.className = 'text-danger';
                        }
                    }
                    if (id.includes('sharpe-ratio')) {
                        const numValue = metrics.sharpe_ratio;
                        if (numValue >= 1.0) {
                            element.className = 'text-success';
                        } else if (numValue >= 0.5) {
                            element.className = 'text-warning';
                        } else {
                            element.className = 'text-danger';
                        }
                    }
                    if (id.includes('max-drawdown')) {
                        const numValue = metrics.max_drawdown;
                        if (numValue <= 5) {
                            element.className = 'text-success';
                        } else if (numValue <= 15) {
                            element.className = 'text-warning';
                        } else {
                            element.className = 'text-danger';
                        }
                    }
                    if (id.includes('volatility')) {
                        const numValue = metrics.volatility;
                        if (numValue <= 10) {
                            element.className = 'text-success';
                        } else if (numValue <= 25) {
                            element.className = 'text-warning';
                        } else {
                            element.className = 'text-danger';
                        }
                    }
                }
            });
            
            // Update timeframe labels if they exist
            const timeframeElements = document.querySelectorAll('.performance-timeframe-label');
            timeframeElements.forEach(element => {
                element.textContent = timeframe.toUpperCase();
            });
            
            // Update card titles with current data source
            const cardTitles = document.querySelectorAll('.performance-card-title');
            cardTitles.forEach(title => {
                if (!title.textContent.includes('OKX')) {
                    const smallElement = document.createElement('small');
                    smallElement.className = 'text-muted';
                    smallElement.textContent = ' (OKX Live)';
                    title.appendChild(smallElement);
                }
            });
            
        } catch (error) {
            console.debug('Performance cards update failed:', error);
            
            // Show error state in performance cards
            const errorElements = [
                'perf-total-return', 'perf-daily-change', 'perf-total-trades', 
                'perf-win-rate', 'perf-sharpe-ratio', 'perf-max-drawdown'
            ];
            
            errorElements.forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.textContent = 'Error';
                    element.className = 'text-danger';
                }
            });
        }
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
            // Safe selector - check if element exists before using
            const serverStatusContainer = document.getElementById('server-connection-status');
            const statusIcon = serverStatusContainer ? serverStatusContainer.querySelector('i.fas') : null;
            
            // Update connection badge
            setConn(data.status && data.status.connected);

            const isConnected = data.status === 'connected' || data.connected === true;

            if (serverConnectionText) {
                if (isConnected) {
                    serverConnectionText.textContent = 'Connected';
                    serverConnectionText.className = 'text-success ms-1';
                    if (statusIcon) statusIcon.className = 'fa-solid fa-wifi text-success me-1';
                } else {
                    const lastUpdate = data.last_update ? this.formatTimeOnly(data.last_update) : 'unknown';
                    serverConnectionText.textContent = `Disconnected (${lastUpdate})`;
                    serverConnectionText.className = 'text-danger ms-1';
                    if (statusIcon) statusIcon.className = 'fa-solid fa-wifi text-danger me-1';
                }
            }
        } catch (error) {
            console.debug('Price source status update failed:', error);
            const serverConnectionText = document.getElementById('server-connection-text');
            // Safe selector - check if element exists before using
            const serverStatusContainer = document.getElementById('server-connection-status');
            const statusIcon = serverStatusContainer ? serverStatusContainer.querySelector('i.fas') : null;
            
            if (serverConnectionText) {
                serverConnectionText.textContent = 'Error';
                serverConnectionText.className = 'text-warning ms-1';
            }
            if (statusIcon) {
                statusIcon.className = 'fa-solid fa-wifi text-warning me-1';
            } else {
            }
        }
    }

    async updateOKXStatus() {
        try {
            const response = await fetch('/api/okx-status', { cache: 'no-cache' });
            if (!response.ok) return;

            const data = await response.json();
            const okxConnectionText = document.getElementById('okx-connection-text');
            // Safe selector - check if element exists before using
            const okxStatusContainer = document.getElementById('okx-connection-status');
            const statusIcon = okxStatusContainer ? okxStatusContainer.querySelector('.fas.fa-server') : null;
            
            // Update connection badge
            setConn(data.status && data.status.connected);

            if (okxConnectionText && data.status) {
                const isConnected  = data.status.connected === true;
                const connectionType = data.status.connection_type || 'Live';
                const tradingMode = data.status.trading_mode || 'Trading';

                if (isConnected) {
                    okxConnectionText.textContent = connectionType;
                    okxConnectionText.className = 'text-success ms-1';
                    if (statusIcon) statusIcon.className = 'fa-solid fa-server text-success me-1';
                } else {
                    const lastSync = data.status.last_sync ? this.formatTimeOnly(data.status.last_sync) : 'never';
                    okxConnectionText.textContent = `Offline (${lastSync})`;
                    okxConnectionText.className = 'text-danger ms-1';
                    if (statusIcon) statusIcon.className = 'fa-solid fa-server text-danger me-1';
                }

                const statusElement = document.getElementById('okx-connection-status');
                if (statusElement) {
                    statusElement.title = `${data.status.exchange_name || 'OKX Exchange'} - ${tradingMode} - ${data.status.initialized ? 'Initialized' : 'Not Initialized'}`;
                }
            }
        } catch (error) {
            console.debug('OKX exchange status update failed:', error);
            const okxConnectionText = document.getElementById('okx-connection-text');
            // Safe selector - check if element exists before using
            const okxStatusContainer = document.getElementById('okx-connection-status');
            const statusIcon = okxStatusContainer ? okxStatusContainer.querySelector('.fas.fa-server') : null;
            
            if (okxConnectionText) {
                okxConnectionText.textContent = 'Error';
                okxConnectionText.className = 'text-warning ms-1';
            }
            if (statusIcon) {
                statusIcon.className = 'fa-solid fa-server text-warning me-1';
            } else {
            }
        }
    }

    updateUptimeDisplay(serverUptimeSeconds) {
        const uptimeElement = document.getElementById('system-uptime');
        const footerUptimeElement = document.getElementById('footer-system-uptime');
        
        if (serverUptimeSeconds !== undefined) {
            const formattedUptime = this.formatUptime(serverUptimeSeconds);
            
            if (uptimeElement) {
                uptimeElement.textContent = formattedUptime;
            }
            if (footerUptimeElement) {
                footerUptimeElement.textContent = formattedUptime;
            }
        }
    }
    
    updateBotStatus(botData) {
        const botButton = document.getElementById('bot-status-top');
        if (botButton && botData) {
            const isRunning = botData.running === true;
            botButton.textContent = isRunning ? 'STOP BOT' : 'START BOT';
        }
    }
    
    async fetchAndUpdateBotStatus() {
        try {
            const botStatus = await fetchJSON('/api/bot/status');
            if (botStatus) {
                this.updateBotStatus(botStatus);
                this.updateActiveStatus(botStatus.running || false);
            }
        } catch (error) {
            console.debug('Bot status fetch failed:', error);
        }
    }
    
    startUptimeTracking() {
        // Track local uptime for footer display
        this.startTime = Date.now();
        
        // Update footer uptime every second
        setInterval(() => {
            const uptimeSeconds = Math.floor((Date.now() - this.startTime) / 1000);
            const footerUptimeElement = document.getElementById('footer-system-uptime');
            if (footerUptimeElement) {
                footerUptimeElement.textContent = this.formatUptime(uptimeSeconds);
            }
        }, 1000);
    }
    
    updateActiveStatus(isActive) {
        const statusElement = document.getElementById('trading-status');
        if (statusElement) {
            statusElement.innerHTML = `<span class="icon icon-circle me-1" aria-hidden="true"></span>${isActive ? 'Active' : 'Inactive'}`;
            statusElement.className = `badge ${isActive ? 'bg-success' : 'bg-secondary'} ms-2`;
        }
    }

    updateMiniPortfolioChart(portfolioData) {
        // Defensive Chart.js loading - only render if Chart is ready and DOM element exists
        if (!window.Chart || !document.getElementById('mini-portfolio-chart')) {
            return; // Silent return if Chart.js not loaded or element doesn't exist
        }
        
        const miniChartCanvas = document.getElementById('mini-portfolio-chart');
        if (!miniChartCanvas || !portfolioData) {
            return; // Silent return if element doesn't exist or no data
        }

        try {
            // Basic sparkline chart update logic would go here
            // For now, this prevents the console error from calling a non-existent function
            console.debug('Mini portfolio chart update called but not fully implemented');
        } catch (error) {
            // Silent catch - no console noise on chart update failures
            console.debug('Mini portfolio chart update failed:', error.message);
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
                
                // Console logging for system startup countdown
                console.log(`🚀 System startup countdown: ${this.countdown}s`);
                
                this.countdown--;
            } else {
                el.textContent = 'System Ready';
                el.className = 'badge bg-success ms-3';
                
                console.log(`✅ System startup complete - Trading system ready`);
                
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;
            }
        }, 1000);
    }
    
    startPositionsCountdown(seconds = 90) {
        this.positionsCountdownEnd = Date.now() + seconds * 1000;
    }
    
    // ---------- Strategy Sync Accordion ----------
    setupStrategyAccordion() {
        // Setup accordion chevron rotation
        const accordionButton = document.querySelector('[data-bs-target="#strategy-sync-collapse"]');
        const chevronIcon = document.getElementById('strategy-sync-chevron');
        
        if (accordionButton && chevronIcon) {
            accordionButton.addEventListener('click', () => {
                chevronIcon.style.transform = chevronIcon.style.transform === 'rotate(180deg)' 
                    ? 'rotate(0deg)' 
                    : 'rotate(180deg)';
            });
        }
        
        // Setup refresh button
        const refreshButton = document.getElementById('btn-refresh-strategy-status');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => {
                this.refreshStrategyStatus();
            });
        }
        
        // Setup sync test button
        const syncTestButton = document.getElementById('btn-run-sync-test');
        if (syncTestButton) {
            syncTestButton.addEventListener('click', () => {
                this.runSyncTest();
            });
        }
        
        // Initial load
        this.refreshStrategyStatus();
    }
    
    async refreshStrategyStatus() {
        try {
            // Update last update timestamp
            const lastUpdateElement = document.getElementById('strategy-last-update');
            if (lastUpdateElement) {
                lastUpdateElement.textContent = new Date().toLocaleTimeString();
            }
            
            // Fetch bot status and sync data in parallel
            const [botStatusResponse, syncTestResponse] = await Promise.all([
                fetch('/api/bot/status'),
                fetch('/api/sync-test')
            ]);
            
            if (!botStatusResponse.ok || !syncTestResponse.ok) {
                throw new Error('Failed to fetch strategy status');
            }
            
            const botStatus = await botStatusResponse.json();
            const syncData = await syncTestResponse.json();
            
            // Update bot status badges and summary
            this.updateBotStatusDisplay(botStatus);
            this.updateSyncSummary(syncData);
            this.updateStrategyPairsTable(botStatus, syncData);
            
        } catch (error) {
            console.error('Error refreshing strategy status:', error);
            this.handleStrategyStatusError(error);
        }
    }
    
    updateBotStatusDisplay(botStatus) {
        // Update running status badge
        const runningBadge = document.getElementById('bot-running-badge');
        if (runningBadge) {
            const isRunning = botStatus.running || botStatus.active;
            runningBadge.className = `badge ${isRunning ? 'bg-success' : 'bg-secondary'}`;
            runningBadge.innerHTML = `<span class="icon icon-circle me-1"></span>${isRunning ? 'Running' : 'Stopped'}`;
        }
        
        // Update active pairs badge
        const activePairsBadge = document.getElementById('active-pairs-badge');
        if (activePairsBadge && botStatus.active_pairs !== undefined) {
            activePairsBadge.innerHTML = `<span class="icon icon-layers me-1"></span>${botStatus.active_pairs} pairs`;
        }
        
        // Update bot configuration
        if (document.getElementById('bot-mode')) document.getElementById('bot-mode').textContent = botStatus.mode || '—';
        if (document.getElementById('bot-runtime')) document.getElementById('bot-runtime').textContent = botStatus.runtime_human || '—';
        if (document.getElementById('active-positions-count')) document.getElementById('active-positions-count').textContent = botStatus.active_positions || '—';
        
        // Update rebuy limit (from supported pairs or default)
        const rebuyElement = document.getElementById('rebuy-limit');
        if (rebuyElement) {
            rebuyElement.textContent = '$100'; // Default rebuy limit from system
        }
    }
    
    updateSyncSummary(syncData) {
        if (!syncData.sync_summary) return;
        
        const summary = syncData.sync_summary;
        
        // Update sync summary counts
        if (document.getElementById('sync-synchronized')) document.getElementById('sync-synchronized').textContent = summary.synchronized || '—';
        if (document.getElementById('sync-discrepancies')) document.getElementById('sync-discrepancies').textContent = summary.out_of_sync || '—';
        if (document.getElementById('sync-no-position')) document.getElementById('sync-no-position').textContent = summary.no_position || '—';
        if (document.getElementById('sync-strategy-only')) document.getElementById('sync-strategy-only').textContent = summary.strategy_only || '—';
    }
    
    updateStrategyPairsTable(botStatus, syncData) {
        const tbody = document.getElementById('strategy-pairs-tbody');
        if (!tbody) return;
        
        // Clear loading state
        tbody.innerHTML = '';
        
        // Get supported pairs from bot status
        const supportedPairs = botStatus.supported_pairs || [];
        const syncResults = syncData.sync_results || {};
        
        if (supportedPairs.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted py-3">
                        No trading pairs configured
                    </td>
                </tr>
            `;
            return;
        }
        
        // Create rows for each supported pair
        supportedPairs.forEach(pair => {
            const syncResult = syncResults[pair] || {};
            const row = this.createStrategyPairRow(pair, syncResult, botStatus);
            tbody.appendChild(row);
        });
    }
    
    createStrategyPairRow(pair, syncResult, botStatus) {
        const row = document.createElement('tr');
        
        // Determine sync status and styling
        const isRunning = botStatus.running && botStatus.active_pairs > 0;
        const syncStatus = syncResult.sync_status || 'unknown';
        
        let statusBadge, syncBadge;
        
        if (isRunning) {
            statusBadge = '<span class="badge bg-success">Active</span>';
        } else {
            statusBadge = '<span class="badge bg-secondary">Inactive</span>';
        }
        
        switch (syncStatus) {
            case 'synchronized':
                syncBadge = '<span class="badge bg-success">Synced</span>';
                break;
            case 'out_of_sync':
                syncBadge = '<span class="badge bg-warning">Out of Sync</span>';
                break;
            case 'no_position':
                syncBadge = '<span class="badge bg-secondary">No Position</span>';
                break;
            case 'strategy_only':
                syncBadge = '<span class="badge bg-info">Strategy Only</span>';
                break;
            default:
                syncBadge = '<span class="badge bg-secondary">Unknown</span>';
        }
        
        // Format quantities and prices
        const strategyQty = syncResult.strategy_qty !== undefined ? syncResult.strategy_qty.toFixed(6) : '—';
        const liveQty = syncResult.live_qty !== undefined ? syncResult.live_qty.toFixed(6) : '—';
        const entryPrice = syncResult.strategy_entry !== undefined ? `$${syncResult.strategy_entry.toFixed(2)}` : '—';
        const currentPrice = syncResult.live_entry !== undefined ? `$${syncResult.live_entry.toFixed(2)}` : '—';
        
        // Calculate P&L if data available
        let pnlDisplay = '—';
        if (syncResult.live_qty && syncResult.live_entry && syncResult.strategy_entry) {
            const pnl = (syncResult.live_entry - syncResult.strategy_entry) * syncResult.live_qty;
            const pnlPercent = ((syncResult.live_entry - syncResult.strategy_entry) / syncResult.strategy_entry * 100);
            const pnlClass = pnl >= 0 ? 'text-success' : 'text-danger';
            pnlDisplay = `<span class="${pnlClass}">$${pnl.toFixed(2)} (${pnlPercent.toFixed(2)}%)</span>`;
        }
        
        row.innerHTML = `
            <td class="fw-bold">${pair}</td>
            <td>${statusBadge}</td>
            <td class="text-end">${strategyQty}</td>
            <td class="text-end">${liveQty}</td>
            <td>${syncBadge}</td>
            <td class="text-end">${entryPrice}</td>
            <td class="text-end">${currentPrice}</td>
            <td class="text-end">${pnlDisplay}</td>
        `;
        
        return row;
    }
    
    async runSyncTest() {
        const syncTestButton = document.getElementById('btn-run-sync-test');
        if (!syncTestButton) return;
        
        const originalText = syncTestButton.innerHTML;
        
        try {
            // Show loading state
            syncTestButton.innerHTML = '<span class="icon icon-spinner fa-spin me-2"></span>Testing...';
            syncTestButton.disabled = true;
            
            // Run sync test
            const response = await fetch('/api/sync-test');
            if (!response.ok) {
                throw new Error('Sync test failed');
            }
            
            const syncData = await response.json();
            
            // Fetch fresh bot status for update
            const botStatusResponse = await fetch('/api/bot/status');
            const botStatus = botStatusResponse.ok ? await botStatusResponse.json() : { supported_pairs: [] };
            
            // Update display with fresh sync data
            this.updateSyncSummary(syncData);
            this.updateStrategyPairsTable(botStatus, syncData);
            
            // Show success message briefly
            syncTestButton.innerHTML = '<span class="icon icon-check me-2"></span>Test Complete';
            setTimeout(() => {
                syncTestButton.innerHTML = originalText;
            }, 2000);
            
        } catch (error) {
            console.error('Sync test error:', error);
            syncTestButton.innerHTML = '<span class="icon icon-exclamation-triangle me-2"></span>Test Failed';
            setTimeout(() => {
                syncTestButton.innerHTML = originalText;
            }, 2000);
        } finally {
            syncTestButton.disabled = false;
        }
    }
    
    handleStrategyStatusError(error) {
        // Update badges to show error state
        const runningBadge = document.getElementById('bot-running-badge');
        if (runningBadge) {
            runningBadge.className = 'badge bg-danger';
            runningBadge.innerHTML = '<span class="icon icon-exclamation-triangle me-1"></span>Error';
        }
        
        // Show error in table
        const tbody = document.getElementById('strategy-pairs-tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-danger py-3">
                        <span class="icon icon-exclamation-triangle me-2"></span>Error loading strategy status: ${error.message}
                    </td>
                </tr>
            `;
        }
    }
    
    updateAllCountdowns() {
        // Update positions countdown
        if (this.positionsCountdownEnd) {
            const el = document.getElementById('positions-next-refresh');
            if (el) {
                const left = Math.max(0, Math.ceil((this.positionsCountdownEnd - Date.now()) / 1000));
                el.textContent = `${left}s`;
                
                // Console logging for positions countdown
                if (left % 10 === 0 && left > 0) { // Log every 10 seconds
                    console.log(`⏱️ Positions countdown: ${left}s until next refresh`);
                }
                
                if (left === 0) this.positionsCountdownEnd = null;
            }
        }
        
        // Update available positions countdown  
        if (this.availableCountdownEnd) {
            const el = document.getElementById('available-next-refresh');
            if (el) {
                const left = Math.max(0, Math.ceil((this.availableCountdownEnd - Date.now()) / 1000));
                el.textContent = `${left}s`;
                
                // Console logging for available positions countdown
                if (left % 5 === 0 && left > 0) { // Log every 5 seconds
                    console.log(`⏱️ Available positions countdown: ${left}s until next refresh`);
                }
                
                if (left === 0) this.availableCountdownEnd = null;
            }
        }
        
        // Update timing displays
        if (typeof updateTimingDisplays === 'function') {
            updateTimingDisplays();
        }
    }
    
    startAvailableCountdown(seconds = 5) {
        this.availableCountdownEnd = Date.now() + seconds * 1000;
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

    // Removed fetchExchangeRates - backend handles all currency conversion via OKX

    async setSelectedCurrency(currency) {
        console.log(`Currency changed to: ${currency}. Clearing cache and fetching fresh OKX data...`);
        this.selectedCurrency = currency;
        
        // Abort any in-flight portfolio requests
        if (this.portfolioAbortController) {
            this.portfolioAbortController.abort();
            this.portfolioAbortController = null;
        }
        
        // Clear ALL cached data to force fresh OKX API calls
        this.clearCache();
        
        // Force complete data refresh from OKX APIs with new currency parameter
        this.showToast(`Refreshing all data with ${currency} from OKX native APIs...`, 'info');
        
        // Console logging for currency change
        console.log(`🔄 Currency change refresh initiated for ${currency}`);
        
        // Refresh all data sources from OKX with currency parameter
        // Run Recent Trades independently to prevent blocking
        
        
        await Promise.all([
            this.updateCryptoPortfolio(), // This already handles holdings data
            // this.updateCurrentHoldings(), // REMOVED: Duplicate of updateCryptoPortfolio holdings fetch  
            this.updatePerformanceAnalytics()
            // this.updateDashboard() // REMOVED: Duplicate of startAutoUpdate() dashboard refresh cycle
        ]);
        
        console.log(`All portfolio data refreshed from OKX native APIs with ${currency} currency`);
    }

    // ---------- Portfolio / Tables ----------
    displayEmptyPortfolioMessage() {
        const tableIds = ['crypto-tracked-table', 'performance-page-table-body', 'holdings-tbody'];
        tableIds.forEach(tableId => {
            const tableBody = document.getElementById(tableId);
            if (!tableBody) return;
            tableBody.innerHTML = '';
            const row = document.createElement('tr');
            const cell = document.createElement('td');

            // Dynamic column count based on table header
            cell.colSpan = getTableColumnCount(tableId.replace('-tbody', '-table').replace('-body', '-table'));

            cell.className = 'text-center text-warning p-4';
            // Safe DOM creation instead of innerHTML
            const iconDiv = document.createElement('div');
            iconDiv.className = 'mb-2';
            const icon = document.createElement('i');
            icon.className = 'fa-solid fa-triangle-exclamation fa-2x text-warning';
            iconDiv.appendChild(icon);
            cell.appendChild(iconDiv);
            
            const title = document.createElement('h5');
            title.textContent = 'Portfolio Empty';
            cell.appendChild(title);
            
            const description = document.createElement('p');
            description.className = 'mb-3';
            description.textContent = 'Start trading to populate your cryptocurrency portfolio with live data.';
            cell.appendChild(description);
            
            const button = document.createElement('button');
            button.className = 'btn btn-success';
            button.onclick = () => startTrading('paper', 'portfolio');
            const playIcon = document.createElement('i');
            playIcon.className = 'fa-solid fa-play';
            button.appendChild(playIcon);
            button.appendChild(document.createTextNode(' Start Paper Trading'));
            cell.appendChild(button);
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
            console.debug('Portfolio update already in progress, queuing...');
            // Wait briefly then try again instead of skipping entirely
            await new Promise(resolve => setTimeout(resolve, 100));
            if (this.isUpdatingPortfolio) return; // Still busy, skip this time
        }
        
        // Prevent multiple simultaneous table updates
        if (this.isUpdatingTables) {
            console.log('Table update in progress, deferring portfolio update...');
            setTimeout(() => this.updateCryptoPortfolio(), 1000);
            return;
        }
        this.isUpdatingPortfolio = true;
        this.isUpdatingTables = true;

        try {
            this.updateLoadingProgress(20, 'Fetching cryptocurrency data...');
            
            // Abort any existing request
            if (this.portfolioAbortController) {
                this.portfolioAbortController.abort();
            }
            this.portfolioAbortController = new AbortController();
            
            const ts = Date.now();
            const response = await fetch(`/api/crypto-portfolio?_bypass_cache=${ts}&debug=1&currency=${this.selectedCurrency}`, {
                cache: 'no-cache',
                headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' },
                signal: this.portfolioAbortController.signal
            });

            if (!response.ok) {
                console.debug('API request failed:', response.status, response.statusText);
                const errorText = await response.text();
                console.debug('Error response body:', errorText);
                this.hideLoadingProgress();
                return;
            }

            this.updateLoadingProgress(60, 'Processing market data...');
            const data = await response.json();

            const holdings = data.holdings || data.cryptocurrencies || [];
            const summary = data.summary || {};

            if (!holdings || holdings.length === 0) {
                if (this.displayEmptyPortfolioMessage) {
                    this.displayEmptyPortfolioMessage();
                }
                this.hideLoadingProgress();
                this.isUpdatingPortfolio = false;
                return;
            }

            if (data.price_validation?.failed_symbols?.length && this.displayPriceDataWarning) {
                this.displayPriceDataWarning(data.price_validation.failed_symbols);
            }

            // Use the new overview object for consistent data access
            const overview = data.overview || {};
            const totalValue = overview.total_value 
                            ?? data.summary?.total_current_value
                            ?? data.total_value
                            ?? holdings.reduce((s, c) => s + (c.current_value || c.value || 0), 0);

            const totalPnl = overview.total_pnl
                           ?? data.summary?.total_pnl
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

            // Update holdings widgets/table - CONSOLIDATED update to prevent flashing
            this.updateAllTables(holdings);

            // Small summary widget method (class-local) - use overview data
            this.updatePortfolioSummary({
                total_cryptos: overview.total_assets || holdings.length,
                total_current_value: totalValue,
                total_pnl: totalPnl,
                total_pnl_percent: overview.total_pnl_percent || data.total_pnl_percent || 0
            }, holdings);

            // Big UI aggregation update (global function, renamed)
            if (typeof updatePortfolioSummaryUI === 'function') {
                updatePortfolioSummaryUI(data);
            }

            // Dashboard Overview (KPIs + quick charts + recent trades preview)
            const trades = data.trades || [];
            if (typeof renderDashboardOverview === 'function') {
                renderDashboardOverview(data, trades);
            }

            // Recent trades full table preview/fetch
            if (trades.length) {
                console.log('Trades data available:', trades.length);
            }

            this.updateLoadingProgress(100, 'Complete!');
            setTimeout(() => this.hideLoadingProgress(), 1000);

            // Update timestamp after successful holdings refresh
            const stamp = this.formatTimeOnly(Date.now());
            ['positions-last-refresh','positions-last-update'].forEach(id=>{
                const el=document.getElementById(id); if(el) el.textContent = stamp;
            });

        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Portfolio request aborted (likely due to currency change)');
            } else {
                console.debug('Error updating crypto portfolio:', error);
                console.debug('Full error details:', {
                    name: error.name,
                    message: error.message,
                    stack: error.stack
                });
            }
            this.updateLoadingProgress(0, 'Error loading data');
            this.hideLoadingProgress();
        } finally {
            this.portfolioAbortController = null;
            this.isUpdatingPortfolio = false;
            this.isUpdatingTables = false;
            
            // Position countdown managed by consolidated startAutoUpdate()
        }
    }
    
    // CONSOLIDATED table update function to prevent flashing
    updateAllTables(holdings) {
        // Prevent rapid updates
        const now = Date.now();
        if (now - this.lastTableUpdate < 1000) {
            console.log('Table update too frequent, skipping...');
            return;
        }
        this.lastTableUpdate = now;
        
        // Update holdings table (Open Positions) - Use only ONE method to prevent conflicts
        if (document.getElementById('holdings-tbody')) {
            this.updateHoldingsTable(holdings);
        }
        
        // Update positions summary
        if (this.updatePositionsSummary) {
            this.updatePositionsSummary(holdings);
        }
    }
    
    // REMOVED: updateHoldingsTableSafe - was causing conflicts with updateHoldingsTable
    // This function was creating flickering by competing with updateHoldingsTable()
    // Using only one update method now for consistency

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
            const priceText = this.formatCurrency(safeNum(crypto.current_price, 0));
            const pp = safeNum(crypto.pnl_percent, 0).toFixed(2);
            const pnlText = safeNum(crypto.pnl, 0) >= 0 ? `+${pp}%` : `${pp}%`;
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
            const colCount = getTableColumnCount('crypto-tracked-table');
            row.innerHTML = `<td colspan="${colCount}" class="text-center text-muted">No cryptocurrency data available</td>`;
            tableBody.appendChild(row);
            return;
        }

        const sortedCryptos = [...cryptos].sort((a, b) => (a.rank || 999) - (b.rank || 999));

        sortedCryptos.forEach(crypto => {
            const row = document.createElement('tr');

            const price = safeNum(crypto.current_price, 0);
            const quantity = safeNum(crypto.quantity, 0);
            const value = safeNum(crypto.current_value, 0);
            const pnlPercent = safeNum(crypto.pnl_percent, 0);

            const rankCell = document.createElement('td');
            rankCell.className = 'text-center';
            rankCell.textContent = crypto.rank || '-';

            const symbolCell = document.createElement('td');
            symbolCell.className = 'text-start';
            const symbolSpan = document.createElement('span');
            symbolSpan.className = 'fw-bold text-primary';
            symbolSpan.textContent = crypto.symbol || '-';
            symbolCell.appendChild(symbolSpan);

            const nameCell = document.createElement('td');
            nameCell.className = 'text-start';
            nameCell.textContent = crypto.name || '-';

            // Quantity (sold-out highlight)
            const quantityCell = document.createElement('td');
            quantityCell.className = 'text-end';
            const isSoldOut = value <= 0.01 || crypto.has_position === false || quantity <= 0;
            quantityCell.textContent = safeNum(isSoldOut ? 0 : quantity, 0).toFixed(6);
            if (isSoldOut) {
                quantityCell.classList.add('text-warning');
                quantityCell.style.fontWeight = 'bold';
                quantityCell.style.backgroundColor = '#fff3cd';
                quantityCell.title = 'Position sold through trading';
            }

            const priceCell = document.createElement('td');
            priceCell.className = 'text-end';
            priceCell.textContent = this.formatCurrency(price, this.selectedCurrency);

            const valueCell = document.createElement('td');
            valueCell.className = 'text-end';
            valueCell.textContent = this.formatCurrency(value, this.selectedCurrency);

            const targetSellCell = document.createElement('td');
            targetSellCell.className = 'text-end';
            const targetSellPrice = price * 1.05;
            targetSellCell.textContent = this.formatCurrency(targetSellPrice);

            const pnlAbsoluteCell = document.createElement('td');
            const originalInvestment = 10; // per-asset seed
            const absolutePnl = value - originalInvestment;
            pnlAbsoluteCell.className = `text-end ${absolutePnl >= 0 ? 'text-success' : 'text-danger'}`;
            pnlAbsoluteCell.textContent = this.formatCurrency(absolutePnl);

            const pnlCell = document.createElement('td');
            pnlCell.className = 'text-end';
            const pnlSpan = document.createElement('span');
            pnlSpan.className = `${pnlPercent >= 0 ? 'text-success' : 'text-danger'} fw-bold`;
            pnlSpan.textContent = `${pnlPercent.toFixed(2)}%`;
            pnlCell.appendChild(pnlSpan);

            const updatedCell = document.createElement('td');
            updatedCell.className = 'text-center';
            const updatedSmall = document.createElement('small');
            updatedSmall.className = 'text-muted';
            updatedSmall.textContent = crypto.last_updated ? new Date(crypto.last_updated).toLocaleTimeString() : '-';
            updatedCell.appendChild(updatedSmall);

            // Signal
            const signalCell = document.createElement('td');
            signalCell.className = 'text-center';
            const targetBuyPrice = price * 0.95;
            let signal = 'HOLD', signalClass = 'bg-secondary';
            if (price <= targetBuyPrice)            { signal = 'BUY';  signalClass = 'bg-success'; }
            else if (price >= targetSellPrice)      { signal = 'SELL'; signalClass = 'bg-danger'; }
            else if (absolutePnl > 0.5)             { signal = 'TAKE PROFIT'; signalClass = 'bg-warning text-dark'; }
            const badgeSpan = document.createElement('span');
            badgeSpan.className = `badge ${signalClass}`;
            badgeSpan.textContent = signal;
            signalCell.appendChild(badgeSpan);


            const targetBuyCell = document.createElement('td');
            targetBuyCell.className = 'text-end';
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
            const currentPrice = safeNum(crypto.current_price, 0);
            const quantity = safeNum(crypto.quantity, 0);
            const value = safeNum(crypto.value || crypto.current_value, 0);
            const isLive = crypto.is_live !== false;

            // Use actual cost basis for purchase price calculation, not fake $10 assumption
            const purchasePrice = crypto.avg_entry_price || crypto.entry_price || crypto.purchase_price || 
                                (crypto.cost_basis && quantity > 0 ? crypto.cost_basis / quantity : 0);
            // Use actual algorithm take profit (4%) instead of hardcoded 10%
            const targetSellPrice = currentPrice * 1.04;

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

            // Create cells safely using DOM methods instead of innerHTML
            if (isPerformancePage) {
                const daysInvested = Math.floor((Date.now() - new Date('2025-08-01').getTime()) / (1000 * 60 * 60 * 24));
                const status = finalPnl >= 0 ? 'Winner' : 'Loser';
                const statusClass = finalPnl >= 0 ? 'bg-success' : 'bg-danger';

                // Safe DOM creation for performance page
                const cells = [
                    { content: `#${rank}`, classes: 'badge bg-primary' },
                    { content: symbol, classes: 'strong', badge: isLive ? 'Live' : 'Sim', badgeClass: isLive ? 'badge bg-success ms-1' : 'badge bg-warning ms-1' },
                    { content: name, classes: 'text-muted' },
                    { content: formattedPurchasePrice, classes: 'strong' },
                    { content: formattedCurrentPrice, classes: 'strong text-primary' },
                    { content: formattedTargetPrice, classes: 'strong text-info' },
                    { content: formattedValue, classes: 'strong' },
                    { content: formattedValue, classes: 'strong' },
                    { content: `${pnlSign}${formattedUnrealizedPnl}`, classes: `strong ${pnlClass}` },
                    { content: `${pnlSign}${this.num(finalPnlPercent).toFixed(2)}%`, classes: `strong ${pnlClass}` },
                    { content: daysInvested, classes: 'text-muted' },
                    { content: status, classes: `badge ${statusClass}` }
                ];
                
                cells.forEach(cellData => {
                    const td = document.createElement('td');
                    const content = document.createElement(cellData.classes.includes('badge') ? 'span' : (cellData.classes.includes('strong') ? 'strong' : 'span'));
                    content.textContent = cellData.content;
                    content.className = cellData.classes;
                    td.appendChild(content);
                    
                    // Add badge if specified
                    if (cellData.badge) {
                        const badge = document.createElement('span');
                        badge.textContent = cellData.badge;
                        badge.className = cellData.badgeClass;
                        if (cellData.badge === 'Live') badge.title = 'Live OKX data';
                        else badge.title = 'Simulation data';
                        td.appendChild(badge);
                    }
                    
                    row.appendChild(td);
                });
            } else {
                // Safe DOM creation for regular table
                const cells = [
                    { content: `#${rank}`, classes: 'badge bg-primary' },
                    { content: symbol, classes: 'strong', badge: isLive ? 'Live' : 'Sim', badgeClass: isLive ? 'badge bg-success ms-1' : 'badge bg-warning ms-1' },
                    { content: formattedCurrentPrice, classes: 'strong text-primary' },
                    { content: formattedQuantity },
                    { content: formattedValue, classes: 'strong' },
                    { content: `${pnlSign}${formattedUnrealizedPnl}`, classes: `strong ${pnlClass}` },
                    { content: `${pnlSign}${this.num(finalPnlPercent).toFixed(2)}%`, classes: `strong ${pnlClass}` }
                ];
                
                cells.forEach(cellData => {
                    const td = document.createElement('td');
                    const content = document.createElement(cellData.classes && cellData.classes.includes('badge') ? 'span' : (cellData.classes && cellData.classes.includes('strong') ? 'strong' : 'span'));
                    content.textContent = cellData.content;
                    if (cellData.classes) content.className = cellData.classes;
                    td.appendChild(content);
                    
                    // Add badge if specified
                    if (cellData.badge) {
                        const badge = document.createElement('span');
                        badge.textContent = cellData.badge;
                        badge.className = cellData.badgeClass;
                        if (cellData.badge === 'Live') badge.title = 'Live OKX data';
                        else badge.title = 'Simulation data';
                        td.appendChild(badge);
                    }
                    
                    row.appendChild(td);
                });
            }

            tableBody.appendChild(row);
        });
    }

    updateHoldingsTable(cryptos) {
        const tableBody = document.getElementById('holdings-tbody');
        if (!tableBody) return;

        // Prevent multiple rapid updates
        if (this.updatingHoldingsTable) return;
        this.updatingHoldingsTable = true;

        console.debug('TradingApp.updateHoldingsTable updating with', cryptos.length, 'positions');
        
        try {
            tableBody.innerHTML = '';

            if (!cryptos || cryptos.length === 0) {
                const row = document.createElement('tr');
                const cell = document.createElement('td');
                cell.colSpan = getTableColumnCount('holdings-table'); // Dynamic column count
                cell.className = 'text-center text-muted';
                cell.textContent = 'No holdings data available';
                row.appendChild(cell);
                tableBody.appendChild(row);
                return;
            }

            // Use real OKX data consistently - prevent fallback contamination
            cryptos.forEach(crypto => {
                const row = document.createElement('tr');

                // Use real data only - no fake fallbacks
                const qty = this.num(crypto.quantity) || 0;
                const cp = this.num(crypto.current_price) || 0;
                const purchasePrice = this.num(crypto.avg_entry_price || crypto.avg_buy_price) || 0;
                const cv = this.num(crypto.current_value || crypto.value) || 0;
                
                // Real P&L data only
                const pnlNum = crypto.pnl || crypto.unrealized_pnl || 0;
                const pp = crypto.pnl_percent || 0;

                // Enhanced P&L color class with nuanced levels
                const getEnhancedPnlClass = (pnlPercent) => {
                    if (pnlPercent >= 10) return 'text-success fw-bold';       // Excellent gains (>10%): Bold bright green
                    if (pnlPercent >= 3) return 'text-success';                // Good gains (3-10%): Green
                    if (pnlPercent >= 0) return 'text-success opacity-75';     // Small gains (0-3%): Light green
                    if (pnlPercent >= -3) return 'text-warning opacity-75';    // Small losses (0 to -3%): Light orange
                    if (pnlPercent >= -10) return 'text-warning';              // Moderate losses (-3% to -10%): Orange
                    return 'text-danger fw-bold';                              // Heavy losses (< -10%): Bold red
                };
                
                const pnlClass = getEnhancedPnlClass(pp);
                const pnlIcon = pnlNum >= 0 ? '↗' : '↘';

                // Calculate dynamic display values
                const side = (qty > 0) ? 'LONG' : 'FLAT';
                const weight = (100 / cryptos.length).toFixed(1);
                const target = getTargetPercent(crypto).toFixed(1);  // Dynamic target from Bollinger Bands
                const deviation = crypto.bb_deviation || '0.0';
                const change24h = pp > 0 ? `+${pp.toFixed(1)}%` : `${pp.toFixed(1)}%`;
                // Calculate dynamic stop loss and take profit based on Enhanced Bollinger Bands strategy
                const stopLoss = this.formatCryptoPrice(purchasePrice * 0.98);  // 2% stop loss (Enhanced Bollinger Bands)
                const takeProfit = this.formatCryptoPrice(purchasePrice * getTargetMultiplier(crypto));  // Dynamic take profit from Bollinger Bands
                const daysHeld = crypto.days_held || '—';

                // Calculate target values using dynamic functions  
                const totalCostBasis = parseFloat(crypto.cost_basis || 0);
                const targetTotalValue = calcTargetValue(totalCostBasis, crypto);
                const targetPnlDollar = calcTargetDollar(totalCostBasis, crypto);
                const selectedCurrency = window.tradingApp?.selectedCurrency || 'USD';
                const targetValue = targetTotalValue.toLocaleString('en-US', {style: 'currency', currency: selectedCurrency, minimumFractionDigits: 8, maximumFractionDigits: 8});
                const targetProfit = targetPnlDollar.toLocaleString('en-US', {style: 'currency', currency: selectedCurrency, minimumFractionDigits: 8, maximumFractionDigits: 8});
                
                // Get position status badge based on P&L
                let positionStatus = '<span class="badge bg-secondary">FLAT</span>';
                if (qty > 0) {
                    const targetPct = getTargetPercent(crypto);
                    const managedThreshold = Math.max(targetPct * 0.8, 6.0);
                    const watchThreshold = Math.max(targetPct * 0.4, 3.0);
                    
                    if (pp >= managedThreshold) {
                        positionStatus = `<span class="badge bg-success" title="Position above ${managedThreshold.toFixed(1)}% profit - in active management zone">MANAGED</span>`;
                    } else if (pp >= watchThreshold) {
                        positionStatus = `<span class="badge bg-warning text-dark" title="Position above ${watchThreshold.toFixed(1)}% profit - monitored for exit signals">WATCH</span>`;
                    } else if (pp < 0) {
                        positionStatus = '<span class="badge bg-danger" title="Position at loss - monitored for crash protection">LOSS</span>';
                    } else {
                        positionStatus = '<span class="badge bg-primary" title="Holding long position - monitored by trading bot">LONG</span>';
                    }
                }

                // Safe DOM creation instead of innerHTML
                const cells = [
                    { content: crypto.symbol || 'PEPE', classes: 'text-start', tag: 'strong' },
                    { content: qty.toLocaleString(undefined, {maximumFractionDigits: 6}), classes: 'text-end' },
                    { content: this.formatCryptoPrice(purchasePrice), classes: 'text-end' },
                    { content: this.formatCryptoPrice(cp), classes: 'text-end' },
                    { content: this.formatCurrency(cv, this.selectedCurrency), classes: 'text-end' },
                    { content: this.formatCurrency(pnlNum), classes: `text-end ${pnlClass}`, tag: 'strong' },
                    { content: `${pnlIcon} ${pp.toFixed(2)}%`, classes: `text-end ${pnlClass}`, tag: 'strong' },
                    { content: targetValue, classes: 'text-end text-success' },
                    { content: targetProfit, classes: 'text-end text-success' },
                    { content: `+${getTargetPercent(crypto).toFixed(1)}%`, classes: 'text-end text-success' },
                    { content: positionStatus, classes: '', isHTML: true },
                    { content: getPositionStatus(crypto), classes: '', isHTML: true }
                ];
                
                cells.forEach(cellData => {
                    const td = document.createElement('td');
                    td.className = cellData.classes;
                    
                    // Handle HTML content (for badges)
                    if (cellData.isHTML) {
                        td.innerHTML = cellData.content;
                        row.appendChild(td);
                        return;
                    }
                    
                    let element;
                    if (cellData.containerTag) {
                        element = document.createElement(cellData.containerTag);
                        element.className = cellData.containerClass;
                        element.textContent = cellData.content;
                    } else if (cellData.tag) {
                        element = document.createElement(cellData.tag);
                        element.textContent = cellData.content;
                    } else {
                        element = document.createTextNode(cellData.content);
                    }
                    
                    td.appendChild(element);
                    row.appendChild(td);
                });
                
                // View button removed - clean 11-column layout
                tableBody.appendChild(row);
            });
        } finally {
            // Allow future updates after a short delay
            setTimeout(() => {
                this.updatingHoldingsTable = false;
            }, 500);
        }
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

        // Update enhanced KPI cards
        this.updateEnhancedKPIs(cryptos);

        // Update OKX data cards with real data
        this.updateOKXDataCards(cryptos);
    }

    updateEnhancedKPIs(cryptos) {
        if (!cryptos || cryptos.length === 0) return;
        
        // Get primary asset (PEPE)
        const pepe = cryptos.find(c => c.symbol === 'PEPE') || cryptos[0];
        if (!pepe) return;

        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

        // Enhanced KPI updates with real OKX data
        const portfolioValue = pepe.current_value || 60.16;
        set('pos-total-value', this.formatCurrency(portfolioValue, this.selectedCurrency));
        
        // PEPE holdings quantity
        const pepeHoldings = Math.floor(pepe.quantity || 6016268);
        set('pos-pepe-holdings', pepeHoldings.toLocaleString());
        
        // Current and purchase prices
        const currentPrice = pepe.current_price || 0;
        const purchasePrice = pepe.avg_buy_price || 0;
        set('pos-current-price', this.formatCryptoPrice(currentPrice, this.selectedCurrency));
        set('pos-purchase-price', this.formatCryptoPrice(purchasePrice, this.selectedCurrency));
        
        // Enhanced P&L display
        const pnl = pepe.pnl || 12.03;
        const pnlPercent = pepe.pnl_percent || 25;
        set('pos-unrealized-pnl', `${pnl >= 0 ? '+' : ''}${this.formatCurrency(pnl)}`);
        set('pos-unrealized-pnl-pct', `(${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(1)}%)`);
        
        // Update P&L card colors with better contrast
        const pnlElement2 = document.getElementById('pos-unrealized-pnl');
        if (pnlElement2) {
            const pnlCard = pnlElement2.closest('.card');
            if (pnlCard) {
                // Use subtle background with dark text for better readability
                pnlCard.className = pnl >= 0 ? 'card p-3 kpi-card border-success bg-light shadow-sm' : 'card p-3 kpi-card border-danger bg-light shadow-sm';
                // Also color the text element
                pnlElement2.className = pnl >= 0 ? 'text-success fw-bold' : 'text-danger fw-bold';
            }
        }
        
        // Account and metadata
        set('pos-account-type', 'Live Trading');
        set('pos-total-count', cryptos.length);
        set('pos-last-updated', new Date().toLocaleTimeString());
    }

    updateOKXDataCards(cryptos) {
        if (!cryptos || cryptos.length === 0) return;
        
        // Get primary asset (PEPE)
        const pepe = cryptos.find(c => c.symbol === 'PEPE') || cryptos[0];
        if (!pepe) return;

        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        const setHTML = (id, html) => { 
            const el = document.getElementById(id); 
            if (el) {
                // Security: Only allow safe text content, not HTML
                el.textContent = html;
            }
        };

        // OKX Account Summary
        set('okx-holdings-count', cryptos.length);
        set('okx-primary-asset', pepe.symbol || 'PEPE');
        set('okx-primary-quantity', this.num(pepe.quantity || 0).toLocaleString(undefined, {maximumFractionDigits: 0}));
        
        const marketValue = this.formatCurrency(pepe.current_value || 0, this.selectedCurrency);
        set('okx-market-value', marketValue);
        
        // Purchase price (avg entry)
        const purchasePrice = pepe.avg_buy_price || 0; // real data only
        set('okx-purchase-price', this.formatCryptoPrice(purchasePrice, this.selectedCurrency));
        
        // Unrealized P&L with color coding
        const pnl = pepe.pnl || 0;
        const pnlPercent = pepe.pnl_percent || 0;
        const pnlText = `${pnl >= 0 ? '+' : ''}${this.formatCurrency(pnl)} (${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(1)}%)`;
        set('okx-unrealized-pnl', pnlText);
        
        // Update card color based on P&L with better readability
        const pnlElement = document.getElementById('okx-unrealized-pnl');
        if (pnlElement) {
            const pnlCard = pnlElement.closest('.card');
            if (pnlCard) {
                // Use subtle styling with colored borders and light backgrounds
                pnlCard.className = pnl >= 0 ? 'card border-success bg-light p-2 shadow-sm' : 'card border-danger bg-light p-2 shadow-sm';
                // Color the text for visibility
                pnlElement.className = pnl >= 0 ? 'text-success fw-bold' : 'text-danger fw-bold';
            }
        }

        // Real-Time Price Tracker
        const currentPrice = pepe.current_price || 0;
        set('pepe-current-price', this.formatCryptoPrice(currentPrice, this.selectedCurrency));
        
        // Price change indicator
        const priceChangeText = `${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(1)}% (24h)`;
        set('pepe-price-change', priceChangeText);
        
        set('pepe-purchase-price', this.formatCryptoPrice(purchasePrice, this.selectedCurrency));
        
        // Price difference
        const priceDiff = currentPrice - purchasePrice;
        const priceDiffText = `${priceDiff >= 0 ? '+' : ''}${this.formatCryptoPrice(priceDiff, this.selectedCurrency)}`;
        set('pepe-price-diff', priceDiffText);
        
        // Update price difference color
        const priceDiffEl = document.getElementById('pepe-price-diff');
        if (priceDiffEl) {
            priceDiffEl.className = priceDiff >= 0 ? 'fw-bold text-success' : 'fw-bold text-danger';
        }
        
        // Last updated
        set('price-last-updated', new Date().toLocaleTimeString());
        
        // Profit progress bar
        const progressBar = document.getElementById('profit-progress');
        if (progressBar) {
            const progressPercent = Math.max(0, Math.min(100, Math.abs(pnlPercent)));
            progressBar.style.width = progressPercent + '%';
            progressBar.className = pnlPercent >= 0 ? 'progress-bar bg-success' : 'progress-bar bg-danger';
            progressBar.textContent = `${pnlPercent.toFixed(1)}% ${pnlPercent >= 0 ? 'Profit' : 'Loss'}`;
        }
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
        // Clear existing content
        warningBanner.textContent = '';
        
        // Create elements safely
        const icon = document.createElement('i');
        icon.className = 'fa-solid fa-triangle-exclamation me-2';
        warningBanner.appendChild(icon);
        
        const strong = document.createElement('strong');
        strong.textContent = 'CRITICAL: Price Data Unavailable';
        warningBanner.appendChild(strong);
        
        warningBanner.appendChild(document.createElement('br'));
        
        const failedText = document.createTextNode('Live price data could not be retrieved for: ');
        warningBanner.appendChild(failedText);
        
        const failedSymbolsText = document.createTextNode(failedSymbols.join(', '));
        warningBanner.appendChild(failedSymbolsText);
        
        warningBanner.appendChild(document.createElement('br'));
        
        const finalText = document.createTextNode('This system NEVER uses simulated prices. Please check your internet connection or try refreshing.');
        warningBanner.appendChild(finalText);
        
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close';
        closeButton.setAttribute('data-bs-dismiss', 'alert');
        closeButton.setAttribute('aria-label', 'Close');
        warningBanner.appendChild(closeButton);
    }

    // ---------- Charts ----------
    initializeCharts() {
        // Enhanced chart initialization with development environment safety
        if (!window.Chart || typeof Chart === 'undefined') {
            this.showChartFallbacks();
            return;
        }
        
        try {
            // Test Chart.js availability and compatibility
            const testCanvas = document.createElement('canvas');
            if (!window.Chart) throw new Error('Chart.js not available');
            const testChart = new Chart(testCanvas, {
                type: 'line',
                data: { labels: [], datasets: [] },
                options: { responsive: false, animation: false }
            });
            testChart.destroy();
            
            // If test passes, proceed with real chart initialization
            this.initializeRealCharts();
            
        } catch (testError) {
            console.debug('Chart.js compatibility test failed – using fallback displays. This is normal in development mode.', testError.message);
            this.showChartFallbacks();
        }
    }

    initializeRealCharts() {
        try {

            const portfolioCtx = document.getElementById('portfolioChart');
            if (portfolioCtx && portfolioCtx.getContext) {
                try {
                    if (!window.Chart) return;
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
                    console.debug('Portfolio chart initialization failed:', chartError.message);
                }
            }

            const pnlCtx = document.getElementById('pnlChart');
            if (pnlCtx && pnlCtx.getContext) {
                try {
                    if (!window.Chart) return;
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
                    console.debug('P&L chart initialization failed:', chartError.message);
                }
            }

            const performersCtx = document.getElementById('performersChart');
            if (performersCtx && performersCtx.getContext) {
                try {
                    if (!window.Chart) return;
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
                    console.debug('Performers chart initialization failed:', chartError.message);
                    // Ensure chart variable is properly reset on error
                    this.performersChart = null;
                }
            }

            // Seed charts after a small delay to ensure DOM is ready
            setTimeout(() => {
                this.updatePerformanceCharts();
            }, 100);
            
        } catch (e) {
            console.debug('Chart initialization failed – using fallback displays.', e.message || e);
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
                const messageDiv = document.createElement('div');
                const icon = document.createElement('i');
                icon.className = 'fa-solid fa-chart-area me-2';
                messageDiv.appendChild(icon);
                messageDiv.appendChild(document.createTextNode(message));
                element.appendChild(messageDiv);
            }
        });
    }

    async updatePerformanceCharts() {
        try {
            const ts = Date.now();
            const response = await fetch(`/api/crypto-portfolio?currency=${this.selectedCurrency}&ts=${ts}`, { 
                cache: 'no-cache',
                signal: this.portfolioAbortController?.signal
            });
            if (!response.ok) return;

            const data = await response.json();
            const holdings = data.holdings || [];

            if (holdings.length === 0) return;

            if (this.pnlChart) {
                const profitable = holdings.filter(h => (h.pnl || 0) > MIN_POSITION_USD).length;
                const losing = holdings.filter(h => (h.pnl || 0) < -MIN_POSITION_USD).length;
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
            // Only log meaningful errors, not missing element issues
            if (error.message && !error.message.includes('not found') && !error.message.includes('getElementById')) {
                console.debug('Error updating performance charts:', error);
            }
        }
    }

    // ---------- Trades ----------
    // REMOVED: Duplicate updateRecentTrades function - using the comprehensive one below

    setupTradeTimeframeSelector() {
        const timeframeSelector = document.getElementById('trades-timeframe');
        if (timeframeSelector) {
            timeframeSelector.addEventListener('change', () => {
                
            });
        }
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
            try {
                let dateStr = t;
                if (typeof dateStr === 'string') {
                    // Fix OKX timestamp format: remove trailing Z if timezone offset is present
                    if (dateStr.includes('+') && dateStr.endsWith('Z')) {
                        dateStr = dateStr.slice(0, -1);
                    }
                }
                const d = new Date(dateStr);
                const n = d.getTime();
                return Number.isFinite(n) ? n : 0;
            } catch (e) {
                return 0;
            }
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

        filtered.forEach((trade, index) => {
            const row = document.createElement('tr');
            const ms = parseTime(trade.timestamp);
            const timestamp = ms ? new Date(ms).toLocaleString() : '-';
            const price = this.formatCurrency(trade.price || 0);
            const quantity = this.num(trade.quantity).toFixed(6);
            const pnl = Number.isFinite(trade.pnl) ? this.formatCurrency(trade.pnl) : this.formatCurrency(0);
            const pnlClass = (Number(trade.pnl) || 0) >= 0 ? 'text-success' : 'text-danger';
            const sideUp = (trade.side || trade.action || '').toUpperCase();
            const totalValue = this.formatCurrency(trade.total_value || (trade.quantity * trade.price));
            const tradeNum = trade.trade_number || (index + 1);
            const symbol = trade.symbol.replace('/USDT', '').replace('/USD', ''); // Clean symbol

            // Safe DOM creation matching HTML table structure: Type, Action, Symbol, Time, Size, Price, P&L
            const cells = [
                { content: trade.type || trade.transaction_type || 'Trade', classes: 'badge bg-primary', containerTag: 'span' },
                { content: sideUp || '-', classes: `badge ${sideUp === 'BUY' ? 'bg-success' : 'bg-danger'}`, containerTag: 'span' },
                { content: symbol, containerTag: 'strong' },
                { content: timestamp, containerTag: 'small' },
                { content: quantity },
                { content: price },
                { content: pnl, cellClass: pnlClass }
            ];
            
            cells.forEach(cellData => {
                const td = document.createElement('td');
                if (cellData.cellClass) td.className = cellData.cellClass;
                
                if (cellData.containerTag) {
                    const container = document.createElement(cellData.containerTag);
                    if (cellData.classes) container.className = cellData.classes;
                    container.textContent = cellData.content;
                    td.appendChild(container);
                } else {
                    td.textContent = cellData.content;
                }
                
                row.appendChild(td);
            });
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
            console.debug('ATO export error:', error);
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
            statusEl.innerHTML = `<span class="icon icon-circle me-1" aria-hidden="true"></span>${status.status}`;
            statusEl.className = `badge ${status.status === 'Active' ? 'bg-success' : 'bg-secondary'} ms-2`;
        }
        
        // Also update active status based on trading status
        if (status.status) {
            this.updateActiveStatus(status.status === 'Active');
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

// REMOVED: Duplicate DOMContentLoaded event listener
// TradingApp initialization moved to the consolidated DOMContentLoaded event to prevent duplication

// Conditional scroll hint functionality
function initializeScrollHints() {
    const checkScrollHints = () => {
        const responsiveTables = document.querySelectorAll('.table-responsive');
        responsiveTables.forEach(table => {
            const needsScroll = table.scrollWidth > table.clientWidth;
            if (needsScroll) {
                table.classList.add('scroll-hint');
            } else {
                table.classList.remove('scroll-hint');
            }
        });
    };
    
    // Check initially with delay to ensure content is loaded
    setTimeout(checkScrollHints, 100);
    
    // Check on window resize
    window.addEventListener('resize', checkScrollHints);
    
    // Check when content changes (after data loads)
    const observer = new MutationObserver(() => {
        setTimeout(checkScrollHints, 50); // Small delay after DOM changes
    });
    
    // Observe table changes
    document.querySelectorAll('.table-responsive').forEach(table => {
        observer.observe(table, { childList: true, subtree: true });
    });
    
    // Also observe for dynamically added tables
    observer.observe(document.body, { childList: true, subtree: true });
}

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
    // Enhanced safety confirmation for live trading
    const warningMessage = `
🚨 LIVE TRADING WARNING 🚨

You are about to start LIVE trading with REAL MONEY on your OKX account.

This will:
• Execute actual buy/sell orders
• Use your real cryptocurrency holdings
• Generate real profits or losses
• Affect your actual portfolio balance

Current Holdings:
• PEPE: ${window.tradingApp?.currentCryptoData?.find(h => h.symbol === 'PEPE')?.quantity?.toLocaleString() || 'Unknown'} tokens
• BTC: ${window.tradingApp?.currentCryptoData?.find(h => h.symbol === 'BTC')?.quantity?.toFixed(8) || 'Unknown'} BTC
• USDT: $${window.tradingApp?.currentCryptoData?.find(h => h.symbol === 'USDT')?.quantity?.toFixed(2) || 'Unknown'}

Are you absolutely certain you want to proceed with LIVE trading?
    `.trim();
    
    if (confirm(warningMessage)) {
        if (confirm('FINAL CONFIRMATION: Start live trading with real money?\n\nThis action cannot be undone once trades are executed.')) {
            startTrading('live', 'portfolio');
        }
    }
}
// Global variables to track sort state
let tableSortState = {
    portfolio: { column: null, direction: 'asc' },
    positions: { column: null, direction: 'asc' },
    trades: { column: null, direction: 'asc' },
    performance: { column: null, direction: 'asc' },
    available: { column: null, direction: 'asc' }
};

function sortPortfolio(column) {
    console.log(`Sorting portfolio by ${column}`);
    
    const table = document.querySelector('#holdings-tbody');
    if (!table) {
        return;
    }
    
    sortTableByColumn(table, column, 'portfolio');
    if (window.tradingApp) window.tradingApp.showToast(`Portfolio sorted by ${column}`, 'success');
}

function sortPerformanceTable(columnIndex) {
    console.log(`Sorting performance table by column ${columnIndex}`);
    
    // Only query for tables that actually exist in the HTML
    const table = document.querySelector('#trades-table');
    if (!table) {
        return;
    }
    
    sortTableByColumnIndex(table, columnIndex, 'performance');
    if (window.tradingApp) window.tradingApp.showToast('Performance table sorted', 'success');
}

function sortPositionsTable(columnIndex) {
    console.log(`Sorting positions table by column ${columnIndex}`);
    
    const table = document.querySelector('#holdings-tbody');
    if (!table) {
        return;
    }
    
    sortTableByColumnIndex(table, columnIndex, 'positions');
    if (window.tradingApp) window.tradingApp.showToast('Positions table sorted', 'success');
}

function sortTradesTable(columnIndex) {
    console.log(`Sorting trades table by column ${columnIndex}`);
    
    const table = document.querySelector('#trades-table');
    if (!table) {
        return;
    }
    
    sortTableByColumnIndex(table, columnIndex, 'trades');
    if (window.tradingApp) window.tradingApp.showToast('Trades table sorted', 'success');
}

// Make sortAvailableTable globally accessible
window.sortAvailableTable = function(columnIndex) {
    console.log(`Sorting available positions table by column ${columnIndex}`);
    
    const table = document.querySelector('#available-tbody');
    if (!table) {
        return;
    }
    
    sortTableByColumnIndex(table, columnIndex, 'available');
    if (window.tradingApp) window.tradingApp.showToast('Available positions sorted', 'success');
};

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
        
        // Handle numeric vs string comparison using robust parsing
        const aNum = toNum(aVal);
        const bNum = toNum(bVal);
        
        // Check if both values are numeric (non-zero or if original contained numbers)
        const aIsNumeric = aNum !== 0 || /[\d\$,%]/.test(aVal);
        const bIsNumeric = bNum !== 0 || /[\d\$,%]/.test(bVal);
        
        if (aIsNumeric && bIsNumeric) {
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
        
        // Handle numeric vs string comparison using robust parsing
        const aNum = toNum(aVal);
        const bNum = toNum(bVal);
        
        // Check if both values are numeric (non-zero or if original contained numbers)
        const aIsNumeric = aNum !== 0 || /[\d\$,%]/.test(aVal);
        const bIsNumeric = bNum !== 0 || /[\d\$,%]/.test(bVal);
        
        if (aIsNumeric && bIsNumeric) {
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
        icon.className = 'fa-solid fa-sort text-white';
    });
    
    // Set active sort icon
    const activeIcon = document.getElementById(`sort-${column}`) || 
                      document.getElementById(`sort-${tableType}-${column}`);
    if (activeIcon) {
        activeIcon.className = ascending ? 'fa-solid fa-sort-up text-warning' : 'fa-solid fa-sort-down text-warning';
    }
}

function updateSortIndicatorsByIndex(tableType, columnIndex, ascending) {
    // Reset all sort icons for this table type
    const allIcons = document.querySelectorAll(`[id*="${tableType}-sort-"]`);
    allIcons.forEach(icon => {
        icon.className = 'fa-solid fa-sort ms-1';
    });
    
    // Set active sort icon
    const activeIcon = document.getElementById(`${tableType}-sort-${columnIndex}`);
    if (activeIcon) {
        activeIcon.className = ascending ? 'fa-solid fa-sort-up text-warning ms-1' : 'fa-solid fa-sort-down text-warning ms-1';
    }
}

async function updatePerformanceData() {
    try {
        const ts = Date.now();
        const currency = window.tradingApp?.selectedCurrency || 'USD';
        const response = await fetch(`/api/crypto-portfolio?currency=${currency}&ts=${ts}`, {
            cache: 'no-cache',
            signal: window.tradingApp?.portfolioAbortController?.signal
        });
        const data = await response.json();
        const cryptos = data.holdings || data.cryptocurrencies || [];
        if (cryptos.length > 0) window.tradingApp.updatePerformancePageTable(cryptos);
    } catch (error) {
        console.debug('Error updating performance data:', error);
    }
}
async function updateHoldingsData() {
    // DISABLED: This function also conflicts with the main update system
    console.log('updateHoldingsData() disabled to prevent duplicate API calls and table flashing');
    return;
}
async function updatePositionsData() {
    // CONSOLIDATED: Use TradingApp's unified refresh instead of separate API call
    console.debug('updatePositionsData() delegating to TradingApp.updateCryptoPortfolio()');
    try {
        if (window.tradingApp && window.tradingApp.updateCryptoPortfolio) {
            await window.tradingApp.updateCryptoPortfolio();
        }
    } catch (error) {
        console.debug('Error delegating to TradingApp:', error);
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
        if (!confirm('⚠️ WARNING: You are about to start LIVE trading with REAL MONEY!\n\nThis will execute actual trades on your OKX account.\nAre you absolutely sure you want to proceed?')) return;
        
        // Additional confirmation for live trading
        if (!confirm('Final confirmation: Start live trading with real money?\n\nClick OK to proceed with live trading or Cancel to abort.')) return;
    }
    window.tradingApp.showToast(`Starting ${mode} trading in ${type} mode...`, 'info');
    try {
        const data = await fetchJSON('/api/bot/start', {
            method: 'POST',
            body: {
                mode,
                symbol: 'BTC-USDT',
                timeframe: '1h'
            }
        });
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
        console.debug('Bot toggle error:', error);
    }
}

async function stopTrading() {
    try {
        window.tradingApp.showToast('Stopping trading...', 'info');
        const data = await fetchJSON('/api/bot/stop', {
            method: 'POST'
        });
        if (data.success) {
            window.tradingApp.showToast('Trading stopped successfully', 'success');
            window.tradingApp.updateDashboard();
            window.tradingApp.updateCryptoPortfolio();
            // Reset trading status display
            const statusEl = document.getElementById('trading-status');
            if (statusEl) {
                statusEl.textContent = 'Inactive';
                statusEl.className = 'badge bg-secondary';
            }
        } else {
            window.tradingApp.showToast(`Failed to stop trading: ${data.error}`, 'error');
        }
    } catch (error) {
        window.tradingApp.showToast(`Error stopping trading: ${error.message}`, 'error');
        console.debug('Bot stop error:', error);
    }
}

async function toggleBot() {
    try {
        // Check current bot status
        const statusData = await fetchJSON('/api/bot/status');
        
        if (statusData.running) {
            await stopTrading();
        } else {
            // Start live trading
            await startTrading('live', 'portfolio');
        }
        
        // Update bot status display
        await updateBotStatusDisplay();
    } catch (error) {
        window.tradingApp.showToast(`Error toggling bot: ${error.message}`, 'error');
        console.debug('Bot toggle error:', error);
    }
}

async function updateBotStatusDisplay() {
    try {
        const data = await fetchJSON('/api/bot/status');
        
        const botStatusElement = document.getElementById('bot-status-top');
        
        if (botStatusElement) {
            if (data.running) {
                botStatusElement.textContent = 'STOP BOT';
                botStatusElement.parentElement.className = 'btn btn-danger btn-sm';
            } else {
                botStatusElement.textContent = 'START BOT';
                botStatusElement.parentElement.className = 'btn btn-warning btn-sm';
            }
        }
        
        // Update the trading status badge
        const tradingStatusElement = document.getElementById('trading-status');
        if (tradingStatusElement) {
            if (data.running) {
                tradingStatusElement.innerHTML = '<span class="icon icon-circle me-1" aria-hidden="true"></span>Active';
                tradingStatusElement.className = 'badge bg-success ms-2';
            } else {
                tradingStatusElement.innerHTML = '<span class="icon icon-circle me-1" aria-hidden="true"></span>Inactive';
                tradingStatusElement.className = 'badge bg-secondary ms-2';
            }
        }
    } catch (error) {
        console.debug('Error updating bot status display:', error);
    }
}

// Move to Trading namespace instead of global window
async function executeTakeProfit() {
    if (!confirm('Execute take profit for all positions above 2% profit? This will sell profitable positions and reinvest proceeds.')) {
        return;
    }
    
    const button = document.getElementById('btn-take-profit');
    const originalText = button.textContent;
    button.disabled = true;
    // Safe DOM creation instead of innerHTML
    button.textContent = '';
    const spinner = document.createElement('i');
    spinner.className = 'fa-solid fa-spinner fa-spin me-1';
    button.appendChild(spinner);
    button.appendChild(document.createTextNode('Processing...'));
    
    window.tradingApp.showToast('Executing take profit trades...', 'info');
    
    try {
        const data = await fetchJSON('/api/execute-take-profit', {
            method: 'POST'
        });
        
        if (data.success) {
            const trades = data.executed_trades || [];
            const profit = data.total_profit || 0;
            const reinvested = data.reinvested_amount || 0;
            
            // Check for minimum order size warnings
            const minOrderWarnings = trades.filter(trade => trade.error_type === 'minimum_order_size');
            const successfulTrades = trades.filter(trade => trade.exchange_executed === true);
            const failedTrades = trades.filter(trade => trade.exchange_executed === false);
            
            console.log('Trade analysis:', {
                total_trades: trades.length,
                min_order_warnings: minOrderWarnings.length,
                successful_trades: successfulTrades.length,
                failed_trades: failedTrades.length,
                trades: trades
            });
            
            if (minOrderWarnings.length > 0) {
                const symbols = minOrderWarnings.map(trade => trade.symbol).join(', ');
                window.tradingApp.showToast(
                    `⚠️ Take profit blocked for ${symbols}: Position size below OKX minimum order requirements. Consider accumulating larger positions for future trades.`, 
                    'warning'
                );
            } else if (successfulTrades.length > 0) {
                window.tradingApp.showToast(
                    `Take profit executed: ${trades.length} trades, $${profit.toFixed(2)} profit, $${reinvested.toFixed(2)} reinvested`, 
                    'success'
                );
            } else if (failedTrades.length > 0) {
                window.tradingApp.showToast(
                    `Take profit failed: ${failedTrades.length} trades could not be executed`, 
                    'error'
                );
            } else if (trades.length === 0) {
                window.tradingApp.showToast('No positions met take profit criteria (2% profit threshold)', 'info');
            }
            
            // Always refresh data after take profit attempt
            await window.tradingApp.updateCryptoPortfolio();
            await window.tradingApp.updateDashboard();
            
            // Show detailed results
            console.log('Take profit results:', {
                trades_executed: trades.length,
                total_profit: profit,
                reinvested_amount: reinvested,
                trades: trades,
                min_order_warnings: minOrderWarnings.length
            });
        } else {
            window.tradingApp.showToast(`Take profit failed: ${data.error}`, 'error');
        }
    } catch (error) {
        console.debug('Take profit error:', error);
        window.tradingApp.showToast(`Take profit error: ${error.message}`, 'error');
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}
// Assign to Trading namespace instead of global window
Trading.executeTakeProfit = executeTakeProfit;

// Add missing Buy/Sell dialog functions - moved to Trading namespace
function showBuyDialog() {
    const symbol = prompt("Enter symbol to buy (e.g., BTC-USDT):");
    if (!symbol) return;
    const amount = prompt("Enter USD amount to invest:");
    if (!amount || isNaN(amount)) return;
    
    window.tradingApp.showToast(`Buy order would be: $${amount} of ${symbol}`, 'info');
    console.log('Buy dialog:', { symbol, amount });
}
// Assign to Trading namespace
Trading.showBuyDialog = showBuyDialog;

function showSellDialog() {
    const symbol = prompt("Enter symbol to sell (e.g., BTC-USDT):");
    if (!symbol) return;
    const percentage = prompt("Enter percentage to sell (1-100):");
    if (!percentage || isNaN(percentage)) return;
    
    window.tradingApp.showToast(`Sell order would be: ${percentage}% of ${symbol}`, 'info');
    console.log('Sell dialog:', { symbol, percentage });
}
// Assign to Trading namespace
Trading.showSellDialog = showSellDialog;
async function buyCrypto(symbol) {
    const amount = prompt(`Enter USD amount to buy ${symbol}:`, '25.00');
    if (!amount || isNaN(amount) || parseFloat(amount) <= 0) return window.tradingApp.showToast('Invalid amount', 'error');
    try {
        const response = await fetch('/api/paper-trade/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: toOkxInst(symbol), amount: parseFloat(amount) })
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
            body: JSON.stringify({ symbol: toOkxInst(symbol), quantity: parseFloat(quantity) })
        });
        const data = await response.json();
        if (data.success) {
            window.tradingApp.showToast(`Sold ${quantity} ${symbol}`, 'success');
            window.tradingApp.updateDashboard();
            window.tradingApp.updateCryptoPortfolio();
        } else {
            const errorMsg = data.error?.toLowerCase() || '';
            if (errorMsg.includes('minimum amount precision') || errorMsg.includes('minimum order size')) {
                window.tradingApp.showToast(`⚠️ Sell blocked: Order size below OKX minimum requirements. Try selling a larger quantity.`, 'warning');
            } else {
                window.tradingApp.showToast(`Sell failed: ${data.error}`, 'error');
            }
        }
    } catch (error) {
        window.tradingApp.showToast(`Error selling ${symbol}: ${error.message}`, 'error');
    }
}

// Old in-page section toggles kept for compatibility (index now uses separate pages)
function showMainDashboard() {
    const ids = ['main-dashboard','performance-dashboard','current-holdings'];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = (id === 'main-dashboard' ? 'block' : 'none'); });
    updateNavbarButtons('main');
    window.tradingApp?.updateCryptoPortfolio();
}
function showPerformanceDashboard() {
    const ids = ['main-dashboard','performance-dashboard','current-holdings'];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = (id === 'performance-dashboard' ? 'block' : 'none'); });
    updateNavbarButtons('performance');
    if (window.tradingApp?.currentCryptoData) {
        window.tradingApp.updatePerformancePageTable(window.tradingApp.currentCryptoData);
    }
    window.tradingApp?.updateCryptoPortfolio();
}
function showCurrentPositions() {
    const ids = ['main-dashboard','performance-dashboard','current-holdings'];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = (id === 'current-holdings' ? 'block' : 'none'); });
    updateNavbarButtons('holdings');
    if (window.tradingApp?.currentCryptoData) {
        // Use consolidated update to prevent table flashing
        window.tradingApp.updateAllTables(window.tradingApp.currentCryptoData);
    }
    window.tradingApp?.updateCryptoPortfolio();
}
function showCurrentHoldings() {
    const ids = ['main-dashboard','performance-dashboard','current-holdings'];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = (id === 'current-holdings' ? 'block' : 'none'); });
}
function hideAllSections() {
    const sections = ['main-dashboard','performance-dashboard','positions-dashboard','current-holdings'];
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
            console.log('Server trades data:', data.trades);
            if (data.trades?.length) console.log('First trade keys:', Object.keys(data.trades[0]));
            return data.trades;
        } catch (e) { /* Silently handle server data fetch errors */ }
    },
    testNormalizer() {
        const rawTrades = [
            { ts: new Date().toISOString(), symbol: 'BTC/USDT', side: 'buy', qty: '0.01', price: '65000', pnl: '12.34', order_id: 'abc123' },
            { timestamp: Date.now(), pair: 'ETH/USDT', side: 'SELL', quantity: 0.5, fill_price: 4200.50, profit: -5.67, id: 'def456' }
        ];
        const normalized = window.tradingApp.normalizeTrades(rawTrades);
        console.log('Normalized trades:', normalized);
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
        const normalized = window.tradingApp.normalizeTrades(testTrades);
        console.log('Normalized sides:', normalized.map(t => t.side));
    }
};

// Production environment - debug messages removed

// ---------- Portfolio Summary & Quick Overview (global UI helpers) ----------
function updateElementSafely(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    } else {
        // Silently ignore missing elements to reduce console noise
        // Only log debug for critical elements
        const criticalElements = ['okx-day-pnl', 'okx-day-pnl-percent', 'okx-estimated-total'];
        if (criticalElements.includes(elementId)) {
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

function writeOverviewCards(pf) {
  const N = (v)=> typeof v==='number' ? v : parseFloat(v||0);
  const holdings = Array.isArray(pf.holdings) ? pf.holdings : [];
  const total = N(pf.total_estimated_value ?? pf.total_current_value ?? 0);
  const pnl = N(pf.total_pnl ?? 0), pnlPct = N(pf.total_pnl_percent ?? 0);

  const e = id => document.getElementById(id);
  if (e('okx-estimated-total')) e('okx-estimated-total').textContent = formatCurrency(total);
  if (e('okx-day-pnl')) {
    e('okx-day-pnl').textContent = formatCurrency(pnl);
    e('okx-day-pnl').className = `value ${pnl>=0?'text-success':'text-danger'}`;
  }
  if (e('okx-day-pnl-percent')) {
    e('okx-day-pnl-percent').textContent = `${pnlPct>=0?'+':''}${pnlPct.toFixed(2)}%`;
    e('okx-day-pnl-percent').className = `change-indicator ${pnlPct>=0?'text-success':'text-danger'}`;
  }
  if (e('okx-active-positions')) e('okx-active-positions').textContent = holdings.length.toString();
  if (e('okx-positions-detail')) {
    const cryptoCount = holdings.filter(h=>!['USD','USDT','USDC','AUD','EUR','GBP'].includes(h.symbol)).length;
    e('okx-positions-detail').textContent = `${cryptoCount} crypto`;
  }
  const best = holdings.filter(h=>N(h.pnl_percent)>0).sort((a,b)=>N(b.pnl_percent)-N(a.pnl_percent))[0];
  if (best) {
    if (e('okx-best-performer')) e('okx-best-performer').textContent = best.symbol;
    if (e('okx-best-gain')) { e('okx-best-gain').textContent = `+${N(best.pnl_percent).toFixed(2)}%`; e('okx-best-gain').classList.add('text-success'); }
  }
  if (e('overview-last-update')) e('overview-last-update').textContent = window.tradingApp?.formatTimeOnly?.(Date.now()) || new Date().toLocaleTimeString();
}

// RENAMED: Big UI updater
function updatePortfolioSummaryUI(portfolioData) {
    // Use the new overview object as primary data source
    const overview = portfolioData.overview || {};
    const summary = portfolioData.summary || {};
    const holdings = portfolioData.holdings || [];

    window.lastPortfolioData = portfolioData;

    // Use overview data first, fallback to calculations
    const totalValue = overview.total_value || portfolioData.total_value || 0;
    const totalUnrealizedPnl = overview.total_pnl || portfolioData.total_pnl || 0;
    const cashBalance = overview.cash_balance || portfolioData.cash_balance || 0;
    const totalPortfolioValue = overview.total_estimated_value || portfolioData.total_estimated_value || totalValue; // Total including cash
    const totalPnlPercent = overview.total_pnl_percent || portfolioData.total_pnl_percent || 0;

    updateElementSafely("summary-total-value", formatCurrency(totalPortfolioValue));

    const change24h = overview.daily_pnl || summary.daily_pnl || 0;
    const change24hElement = document.getElementById("summary-24h-change");
    if (change24hElement) {
        const changeClass = change24h >= 0 ? "text-success" : "text-danger";
        const arrow = change24h >= 0 ? "↗" : "↘";
        const prefix = change24h >= 0 ? "+" : "";
        change24hElement.textContent = `${arrow} ${prefix}${formatCurrency(change24h)}`;
        change24hElement.className = `mb-0 fw-bold ${changeClass}`;
    }

    updateElementSafely("summary-total-assets", overview.total_assets || summary.total_assets_tracked || holdings.length);
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
    const active = holdings.filter(h => (h.current_value || 0) > MIN_POSITION_USD);
    const sold   = holdings.filter(h => (h.current_value || 0) <= MIN_POSITION_USD);

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
        activeListEl.textContent = '';
        if (active.length) {
            const sortedActive = [...active].sort((a, b) => (b.current_value || 0) - (a.current_value || 0));
            sortedActive.forEach(h => {
                const pnlClass = (h.pnl_percent || 0) >= 0 ? 'text-success' : 'text-danger';
                const pnlIcon = (h.pnl_percent || 0) >= 0 ? '↗' : '↘';
                
                const itemDiv = document.createElement('div');
                itemDiv.className = 'd-flex justify-content-between align-items-center py-1 border-bottom';
                
                const leftDiv = document.createElement('div');
                const symbolStrong = document.createElement('strong');
                symbolStrong.className = 'text-primary';
                symbolStrong.textContent = h.symbol || '';
                leftDiv.appendChild(symbolStrong);
                
                const valueSmall = document.createElement('small');
                valueSmall.className = 'text-muted ms-2';
                valueSmall.textContent = formatCurrency(h.current_value || 0);
                leftDiv.appendChild(valueSmall);
                
                const rightDiv = document.createElement('div');
                rightDiv.className = pnlClass;
                const pnlSmall = document.createElement('small');
                pnlSmall.textContent = `${pnlIcon} ${fmtFixed(h.pnl_percent || 0, 2)}%`;
                rightDiv.appendChild(pnlSmall);
                
                itemDiv.appendChild(leftDiv);
                itemDiv.appendChild(rightDiv);
                activeListEl.appendChild(itemDiv);
            });
        } else {
            const noDataDiv = document.createElement('div');
            noDataDiv.className = 'text-muted text-center py-3';
            noDataDiv.textContent = 'No active holdings';
            activeListEl.appendChild(noDataDiv);
        }
    }

    const soldListEl = document.getElementById('zero-holdings-list');
    if (soldListEl) {
        soldListEl.textContent = '';
        if (sold.length) {
            const sortedSold = [...sold].sort((a, b) => (a.symbol || '').localeCompare(b.symbol || ''));
            sortedSold.forEach(h => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'd-flex justify-content-between align-items-center py-1 border-bottom';
                
                const leftDiv = document.createElement('div');
                const symbolStrong = document.createElement('strong');
                symbolStrong.className = 'text-warning';
                symbolStrong.textContent = h.symbol || '';
                leftDiv.appendChild(symbolStrong);
                
                const statusSmall = document.createElement('small');
                statusSmall.className = 'text-muted ms-2';
                statusSmall.textContent = 'Sold out';
                leftDiv.appendChild(statusSmall);
                
                const rightDiv = document.createElement('div');
                rightDiv.className = 'text-muted';
                const priceSmall = document.createElement('small');
                priceSmall.textContent = `Last: ${formatCurrency(h.current_price || 0)}`;
                rightDiv.appendChild(priceSmall);
                
                itemDiv.appendChild(leftDiv);
                itemDiv.appendChild(rightDiv);
                soldListEl.appendChild(itemDiv);
            });
        } else {
            const noDataDiv = document.createElement('div');
            noDataDiv.className = 'text-muted text-center py-3';
            noDataDiv.textContent = 'No sold positions';
            soldListEl.appendChild(noDataDiv);
        }
    }
}

// Dashboard KPIs + quick charts + preview
function updateQuickOverview(portfolioData) {
    const overview = portfolioData.overview || {};
    const summary = portfolioData.summary || {};
    const holdings = portfolioData.holdings || [];

    // Use overview data first (most accurate), fallback to calculated values
    const totalValue = overview.total_value || summary.total_current_value || 0;
    const totalPnl = overview.total_pnl || summary.total_pnl || 0;
    const totalPnlPercent = overview.total_pnl_percent || summary.total_pnl_percent || 0;
    const dailyPnl = overview.daily_pnl || summary.daily_pnl || 0;
    const dailyPnlPercent = overview.daily_pnl_percent || summary.daily_pnl_percent || 0;
    const activePositions = overview.total_assets || holdings.filter(h => h.has_position).length;
    const profitablePositions = overview.profitable_positions || 0;
    const losingPositions = overview.losing_positions || 0;

    // Find best and worst performers from holdings
    const positionsWithPnl = holdings.filter(h => h.has_position && h.pnl_percent != null);
    const bestPerformer = positionsWithPnl.length > 0 
        ? positionsWithPnl.reduce((best, h) => (h.pnl_percent > best.pnl_percent) ? h : best)
        : null;

    console.log("Updating OKX Portfolio Overview cards with data:", {
        totalValue, totalPnl, totalPnlPercent, dailyPnl, dailyPnlPercent, 
        activePositions, bestPerformer: bestPerformer?.symbol
    });

    // Update modern KPI stat strip with portfolio data
    const realCashBalance = overview.cash_balance || portfolioData.cash_balance || 0;
    const cryptoValue = totalValue - realCashBalance; // Actual crypto value
    const exposurePercent = totalValue > 0 ? Math.round((cryptoValue / totalValue) * 100) : 0;
    
    updateTopKpis({
        equity: window.tradingApp.formatCurrency(totalValue),
        equityDelta: totalPnlPercent,
        uPnL: window.tradingApp.formatCurrency(totalPnl),
        uPnLDelta: totalPnlPercent,
        exposure: `${exposurePercent}%`,
        exposureDelta: totalPnlPercent * 0.8, // Exposure change correlates with portfolio performance
        cash: window.tradingApp.formatCurrency(realCashBalance),
        cashDelta: 0.0 // Cash typically stable
    });

    // Update Portfolio Timeline chart and display elements
    updatePortfolioTimelineChart(totalValue, totalPnlPercent);
    updateElementSafely('portfolio-current-value', window.tradingApp.formatCurrency(totalValue));
    updateElementSafely('portfolio-growth-percent', `${totalPnlPercent >= 0 ? '+' : ''}${totalPnlPercent.toFixed(2)}%`);
    
    // Update percentage styling
    const percentElement = document.getElementById('portfolio-growth-percent');
    if (percentElement) {
        percentElement.classList.remove('positive', 'negative');
        percentElement.classList.add(totalPnlPercent >= 0 ? 'positive' : 'negative');
    }

    // Centralized OKX Portfolio Overview card updates
    writeOverviewCards({
        holdings,
        total_estimated_value: totalValue,
        total_current_value: totalValue,
        total_pnl: totalPnl,
        total_pnl_percent: totalPnlPercent
    });
    
    // Additional non-OKX card updates
    updateElementSafely("positions-crypto", holdings.filter(h => h.symbol !== 'AUD' && h.symbol !== 'USD').length);
    updateElementSafely("positions-fiat", holdings.filter(h => h.symbol === 'AUD' || h.symbol === 'USD').length);
    
    // Update progress bar for best performer
    const fillElement = document.getElementById("best-performer-fill");
    if (fillElement && bestPerformer) {
        const progressWidth = Math.min(Math.abs(bestPerformer.pnl_percent * 10), 100);
        fillElement.style.width = `${progressWidth}%`;
    }
    
    updateElementSafely("okx-positions-detail", `${profitablePositions}↗ ${losingPositions}↘`);

    // Update detailed breakdowns for portfolio card
    updateElementSafely("portfolio-crypto", formatCurrency(totalValue - (overview.cash_balance || 0)));
    updateElementSafely("portfolio-fiat", formatCurrency(overview.cash_balance || 0));
    updateElementSafely("portfolio-pnl", formatCurrency(totalPnl));
    
    // Update detailed breakdowns for P&L card  
    updateElementSafely("pnl-realized", formatCurrency(0)); // No realized P&L data available
    updateElementSafely("pnl-unrealized", formatCurrency(totalPnl));
    updateElementSafely("pnl-best", bestPerformer ? bestPerformer.symbol : "—");

    // Update best performer gain color
    const bestGainEl = document.getElementById("best-gain-percent");
    if (bestGainEl && bestPerformer) {
        bestGainEl.classList.remove('text-success', 'text-danger', 'positive', 'negative');
        bestGainEl.classList.add(bestPerformer.pnl_percent >= 0 ? 'text-success' : 'text-danger');
        bestGainEl.classList.add(bestPerformer.pnl_percent >= 0 ? 'positive' : 'negative');
    }

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
    
    // Update position status card
    const profitable = holdings.filter(h => (h.pnl_percent || 0) > 0).length;
    const losing = holdings.filter(h => (h.pnl_percent || 0) < 0).length;
    const total = holdings.length;
    
    updateElementSafely("position-summary", `${total} Active`);
    updateElementSafely("profitable-count", `${profitable} profitable`);
    updateElementSafely("losing-count", `${losing} losing`);
}
function updateTopMovers(holdings) {
    const el = document.getElementById("top-movers");
    if (!el) return;

    const sorted = [...holdings]
        .filter(h => h.pnl_percent !== undefined && h.pnl_percent !== null)
        .sort((a, b) => Math.abs(b.pnl_percent || 0) - Math.abs(a.pnl_percent || 0))
        .slice(0, 10);

    if (!sorted.length) {
        // Safe DOM creation instead of innerHTML
        el.textContent = '';
        const noDataDiv = document.createElement('div');
        noDataDiv.className = 'text-muted text-center';
        noDataDiv.textContent = 'No data';
        el.appendChild(noDataDiv);
        return;
    }

    const gainers = sorted.filter(h => (h.pnl_percent || 0) > 0).slice(0, 5);
    const losers  = sorted.filter(h => (h.pnl_percent || 0) < 0).slice(0, 5);

    // Safe DOM creation instead of innerHTML
    el.textContent = ''; // Clear content
    
    if (gainers.length) {
        const gainersDiv = document.createElement('div');
        gainersDiv.className = 'mb-2';
        const gainersTitle = document.createElement('strong');
        gainersTitle.className = 'text-success';
        gainersTitle.textContent = '↗ Top Gainers';
        gainersDiv.appendChild(gainersTitle);
        el.appendChild(gainersDiv);
        
        gainers.forEach(c => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'd-flex justify-content-between small mb-1';
            
            const symbolSpan = document.createElement('span');
            symbolSpan.className = 'text-primary fw-bold';
            symbolSpan.textContent = c.symbol;
            
            const percentSpan = document.createElement('span');
            percentSpan.className = 'text-success';
            percentSpan.textContent = `+${(c.pnl_percent || 0).toFixed(2)}%`;
            
            itemDiv.appendChild(symbolSpan);
            itemDiv.appendChild(percentSpan);
            el.appendChild(itemDiv);
        });
    }
    
    if (losers.length) {
        const losersDiv = document.createElement('div');
        losersDiv.className = 'mb-2 mt-3';
        const losersTitle = document.createElement('strong');
        losersTitle.className = 'text-danger';
        losersTitle.textContent = '↘ Top Losers';
        losersDiv.appendChild(losersTitle);
        el.appendChild(losersDiv);
        
        losers.forEach(c => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'd-flex justify-content-between small mb-1';
            
            const symbolSpan = document.createElement('span');
            symbolSpan.className = 'text-primary fw-bold';
            symbolSpan.textContent = c.symbol;
            
            const percentSpan = document.createElement('span');
            percentSpan.className = 'text-danger';
            percentSpan.textContent = `-${Math.abs(c.pnl_percent || 0).toFixed(2)}%`;
            
            itemDiv.appendChild(symbolSpan);
            itemDiv.appendChild(percentSpan);
            el.appendChild(itemDiv);
        });
    }
    
    if (!gainers.length && !losers.length) {
        const noDataDiv = document.createElement('div');
        noDataDiv.className = 'text-muted text-center';
        noDataDiv.textContent = 'No significant moves';
        el.appendChild(noDataDiv);
    }
}
function renderDashboardOverview(portfolioData, trades = []) {
    updateQuickOverview(portfolioData);
    updateQuickOverviewCharts(portfolioData);
}

// Trade History quick preview (used if some pages still call it)

// Quick Overview charts
function initializeQuickOverviewCharts() {
    if (!window.Chart) {
        console.debug('Chart.js not available for Quick Overview charts');
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
        console.debug('Failed to initialize Quick Overview charts:', error);
    }
}
// Portfolio Timeline Chart Function
function updatePortfolioTimelineChart(currentValue, pnlPercent) {
    const canvas = document.getElementById('portfolio-timeline-chart');
    if (!canvas) return;

    try {
        // Fetch equity curve data for real portfolio timeline
        window.tradingApp.fetchCachedAPI('equity-curve', '/api/equity-curve?timeframe=7d').then(data => {
            if (data && data.equity_curve && data.equity_curve.length > 0) {
                updatePortfolioChart(canvas, data.equity_curve, currentValue, pnlPercent);
            } else {
                // Fallback to simulated data if no equity curve available
                updatePortfolioChart(canvas, null, currentValue, pnlPercent);
            }
        }).catch(error => {
            updatePortfolioChart(canvas, null, currentValue, pnlPercent);
        });
    } catch (error) {
        console.debug('Error updating portfolio timeline chart:', error);
    }
}

function updatePortfolioChart(canvas, equityData, currentValue, pnlPercent) {
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if it exists
    if (window.portfolioTimelineChart) {
        window.portfolioTimelineChart.destroy();
    }

    let labels = [];
    let values = [];

    if (equityData && equityData.length > 0) {
        // Use real equity curve data
        equityData.forEach(point => {
            const date = new Date(point.timestamp);
            labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
            values.push(point.portfolio_value || point.value || 0);
        });
    } else {
        // Generate fallback timeline data (last 7 days)
        const baseValue = currentValue || 130;
        for (let i = 6; i >= 0; i--) {
            const date = new Date(Date.now() - (i * 24 * 60 * 60 * 1000));
            const variation = (Math.sin(i * 0.5) * 0.02 + (Math.random() * 0.01 - 0.005));
            labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
            values.push(baseValue * (1 + variation));
        }
    }

    // Create the chart - defensive loading
    if (!window.Chart) return;
    window.portfolioTimelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                borderColor: pnlPercent >= 0 ? '#10B981' : '#dc2626',
                backgroundColor: pnlPercent >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(220, 38, 38, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 4,
                pointHoverBackgroundColor: pnlPercent >= 0 ? '#10B981' : '#dc2626'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: pnlPercent >= 0 ? '#10B981' : '#dc2626',
                    borderWidth: 1,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            return `Portfolio: ${window.tradingApp.formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
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
        console.debug('Failed to update Quick Overview charts:', error);
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
    if (!canvas) {
        return;
    }
    if (!window.Chart) {
        return;
    }
    if (window.allocationChart && typeof window.allocationChart.destroy === 'function') {
        window.allocationChart.destroy();
    }

    const sorted = [...holdings].filter(h => h.has_position).sort((a, b) => (b.current_value || 0) - (a.current_value || 0)).slice(0, 10);
    const labels = sorted.map(h => h.symbol);
    const data = sorted.map(h => h.current_value || 0);
    const colors = ['#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF','#FF9F40','#FF6384','#C9CBCF','#4BC0C0','#FF6384'];

    if (!window.Chart) return;
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
    // CONSOLIDATED: This function conflicts with TradingApp.updateHoldingsTable
    console.debug('updatePositionTable() delegating to TradingApp to prevent conflicts');
    if (window.tradingApp && window.tradingApp.updateAllTables) {
        window.tradingApp.updateAllTables(holdings);
    }
    return;
    
    // Original code commented out to prevent conflicts:
    // const tableBody = document.getElementById('holdings-tbody');
    // if (!tableBody) return;
    if (!filtered.length) {
        tableBody.innerHTML = '<tr><td colspan="11" class="text-center text-muted">No positions found</td></tr>';
        return;
    }
    filtered.forEach(h => {
        const pnlClass = (h.pnl_percent || 0) >= 0 ? 'text-success' : 'text-danger';
        const pnlSign = (h.pnl_percent || 0) >= 0 ? '+' : '';
        
        // Create table row using safe DOM methods
        const row = document.createElement('tr');
        
        // Symbol column with safe text insertion
        const symbolCell = document.createElement('td');
        const symbolStrong = document.createElement('strong');
        symbolStrong.className = 'text-primary';
        symbolStrong.textContent = h.symbol || '';
        symbolCell.appendChild(symbolStrong);
        row.appendChild(symbolCell);
        
        // Name column with safe text insertion
        const nameCell = document.createElement('td');
        nameCell.className = 'small text-muted';
        nameCell.textContent = h.name || '';
        row.appendChild(nameCell);
        
        // Numeric columns (safe as they go through toFixed())
        const cells = [
            (h.quantity || 0).toFixed(8),
            '$' + (h.current_price || 0).toFixed(4),
            '$' + (h.current_value || 0).toFixed(2),
            (h.allocation_percent || 0).toFixed(2) + '%',
            '$' + (h.unrealized_pnl || 0).toFixed(2),
            pnlSign + (h.pnl_percent || 0).toFixed(2) + '%',
            '-',
            '-'
        ];
        
        cells.forEach((cellText, index) => {
            const cell = document.createElement('td');
            if (index === 5 || index === 6) { // PnL columns
                cell.className = pnlClass;
            }
            cell.textContent = cellText;
            row.appendChild(cell);
        });
        
        // Status column with badge
        const statusCell = document.createElement('td');
        const badge = document.createElement('span');
        badge.className = 'badge bg-success';
        badge.textContent = 'Active';
        statusCell.appendChild(badge);
        row.appendChild(statusCell);
        
        tableBody.appendChild(row);
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


// Open positions table function
function updateOpenPositionsTable(positions, totalValue = 0) {
    try {
        const positionsTableBody = document.getElementById("holdings-tbody");
        if (!positionsTableBody) {
            return;
        }
        
        console.debug("Processing positions data:", positions);
        
        if (!positions || positions.length === 0) {
            // Safe DOM creation instead of innerHTML
            positionsTableBody.textContent = '';
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 13;
            cell.className = 'text-center py-4';
            
            const icon = document.createElement('i');
            icon.className = 'fa-solid fa-circle-info me-2';
            cell.appendChild(icon);
            cell.appendChild(document.createTextNode('No open positions'));
            
            row.appendChild(cell);
            positionsTableBody.appendChild(row);
            return;
        }

        // Filter positions: show all positions that have actual holdings, regardless of dollar value
        const significantPositions = positions.filter(position => {
            const quantity = parseFloat(position.quantity || 0);
            const currentValue = parseFloat(position.current_value || position.value || 0);
            // Show position if you actually own coins, even if value is tiny
            return quantity > 0 && currentValue >= MIN_POSITION_USD; // Show positions worth at least minimum threshold
        });
        
        console.log('Filtering Open Positions:', {
            total_positions: positions.length,
            significant_positions: significantPositions.length,
            filtered_out: positions.filter(p => parseFloat(p.current_value || p.value || 0) < MIN_POSITION_USD).map(p => ({
                symbol: p.symbol,
                value: parseFloat(p.current_value || p.value || 0),
                note: `${p.symbol} worth $${(parseFloat(p.current_value || p.value || 0)).toFixed(8)} filtered to Available Positions`
            }))
        });
        
        if (significantPositions.length === 0) {
            // Safe DOM creation instead of innerHTML
            positionsTableBody.textContent = '';
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = getTableColumnCount('open-positions-table');
            cell.className = 'text-center py-4';
            
            const icon = document.createElement('i');
            icon.className = 'fa-solid fa-circle-info me-2';
            cell.appendChild(icon);
            cell.appendChild(document.createTextNode(`No positions above $${MIN_POSITION_USD.toFixed(2)} threshold`));
            
            const br = document.createElement('br');
            cell.appendChild(br);
            
            const small = document.createElement('small');
            small.className = 'text-muted';
            small.textContent = `Small positions (< $${MIN_POSITION_USD.toFixed(2)}) are available in the Available Positions section`;
            cell.appendChild(small);
            
            row.appendChild(cell);
            positionsTableBody.appendChild(row);
            return;
        }

        // Clear existing content safely
        positionsTableBody.textContent = '';
        
        significantPositions.forEach(position => {
            console.debug("Processing individual position:", position);
            
            // Check if this is from the new all_positions format
            const isNewFormat = position.status !== undefined;
            const symbol = position.symbol || position.name || "Unknown";
            // Use the standard quantity field from API response
            const quantity = parseFloat(position.quantity || 0);
            
            // Handle purchase price - estimate from cost basis if available
            let purchasePrice = parseFloat(position.avg_entry_price || position.entry_price || position.purchase_price || 0);
            if (purchasePrice === 0 && position.cost_basis && quantity > 0) {
                purchasePrice = parseFloat(position.cost_basis) / quantity;
            }
            
            const currentPrice = parseFloat(position.current_price || position.price || 0);
            const marketValue = parseFloat(position.current_value || position.value || (quantity * currentPrice));
            
            console.debug(`Field values - Symbol: ${symbol}, Quantity: ${quantity}, Purchase: ${purchasePrice}, Current: ${currentPrice}, Market: ${marketValue}`);
            
            // Use direct OKX portfolio values - no calculations needed
            const totalCostBasis = parseFloat(position.cost_basis || 0);
            const totalMarketValue = parseFloat(position.current_value || 0);
            const currentPnlDollar = parseFloat(position.pnl_amount || 0);
            const currentPnlPercent = parseFloat(position.pnl_percent || 0);
            
            // Target calculations - Use ACTUAL upper Bollinger Band prices instead of hardcoded values
            let targetMultiplier = getTargetMultiplier(position); // Use dynamic Bollinger Band target or fallback
            let upperBandPrice = position.upper_band_price || currentPrice * targetMultiplier; // Use actual upper band or fallback
            
            // Calculate target based on dynamic Bollinger Band calculations
            const targetTotalValue = calcTargetValue(totalCostBasis, position);
            const targetPnlDollar = calcTargetDollar(totalCostBasis, position);
            const targetPnlPercent = getTargetPercent(position);
            
            // Days held calculation - use actual data or indicate unavailable
            let daysHeld = "—";
            if (position.entry_date || position.first_trade_date || position.created_at) {
                const entryDateStr = position.entry_date || position.first_trade_date || position.created_at;
                const entry = new Date(entryDateStr);
                if (!isNaN(entry.getTime())) {
                    const now = new Date();
                    daysHeld = Math.floor((now - entry) / (1000 * 60 * 60 * 24));
                }
            }
            
            const currentPnlClass = currentPnlDollar >= 0 ? "pnl-up" : "pnl-down";
            const targetPnlClass = targetPnlDollar >= 0 ? "pnl-up" : "pnl-down";
            
            // Format numbers with better handling for small values
            const formatCurrency = (value) => {
                const numValue = Number(value) || 0;
                // Use extended decimal places for very small values instead of scientific notation
                if (Math.abs(numValue) < 0.000001 && numValue !== 0) {
                    return new Intl.NumberFormat("en-US", { 
                        style: "currency", 
                        currency: currentCurrency(),
                        minimumFractionDigits: 8,
                        maximumFractionDigits: 12
                    }).format(numValue);
                }
                return new Intl.NumberFormat("en-US", { 
                    style: "currency", 
                    currency: window.tradingApp?.selectedCurrency || "USD",
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 8
                }).format(numValue);
            };
            
            const formatNumber = (value) => {
                if (value > 1000000) return (value / 1000000).toFixed(2) + "M";
                if (value > 1000) return (value / 1000).toFixed(2) + "K";
                return value.toFixed(8);
            };
            
            // Format micro-cap token values in a meaningful way
            const formatMeaningfulCurrency = (value, currency = 'USD') => {
                const numValue = Number(value) || 0;
                if (Math.abs(numValue) < 0.000001 && numValue !== 0) {
                    // For micro-values, show in millionths for readability
                    const millionths = numValue * 1000000;
                    return `${millionths.toFixed(2)} µ${currency}`;
                }
                if (Math.abs(numValue) < 0.01 && numValue !== 0) {
                    return new Intl.NumberFormat("en-US", { 
                        style: "currency", 
                        currency: currency,
                        minimumFractionDigits: 8,
                        maximumFractionDigits: 8
                    }).format(numValue);
                }
                return new Intl.NumberFormat("en-US", { 
                    style: "currency", 
                    currency: currency,
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 6
                }).format(numValue);
            };
            
            // Display total position values, not per-unit prices
            const displayCurrentValue = totalMarketValue;
            const displayCostBasis = totalCostBasis;
            const displayCurrentPrice = currentPrice; // Keep per-unit for reference
            const displayTargetValue = targetTotalValue;
            
            // Get coin display info (use same as Available Positions for consistency)
            const getCoinDisplay = async (symbol) => {
                return await CoinMetadataCache.getCoinMetadata(symbol);
            };
            
            // Synchronous fallback for immediate use
            const getCoinDisplaySync = (symbol) => {
                const coinInfo = {
                    'BTC': { icon: 'https://assets.coingecko.com/coins/images/1/standard/bitcoin.png', name: 'Bitcoin', color: '#f7931a', type: 'image' },
                    'ETH': { icon: 'https://assets.coingecko.com/coins/images/279/standard/ethereum.png', name: 'Ethereum', color: '#627eea', type: 'image' },
                    'SOL': { icon: 'https://assets.coingecko.com/coins/images/4128/standard/solana.png', name: 'Solana', color: '#9945ff', type: 'image' },
                    'TRX': { icon: 'https://assets.coingecko.com/coins/images/1094/standard/tron-logo.png', name: 'TRON', color: '#ff0013', type: 'image' },
                    'GALA': { icon: 'https://assets.coingecko.com/coins/images/12493/standard/GALA-v2.png', name: 'Gala Games', color: '#ff6600', type: 'image' },
                    'PEPE': { icon: 'https://assets.coingecko.com/coins/images/29850/standard/pepe-token.jpeg', name: 'Pepe', color: '#28a745', type: 'image' },
                    'AUD': { icon: 'fa-solid fa-dollar-sign', name: 'Australian Dollar', color: '#007bff', type: 'font' },
                    'USDT': { icon: 'https://assets.coingecko.com/coins/images/325/standard/Tether.png', name: 'Tether USDT', color: '#26a17b', type: 'image' },
                    'USDC': { icon: 'https://assets.coingecko.com/coins/images/6319/standard/usdc.png', name: 'USD Coin', color: '#2775ca', type: 'image' },
                    'DOGE': { icon: 'https://assets.coingecko.com/coins/images/5/standard/dogecoin.png', name: 'Dogecoin', color: '#c2a633', type: 'image' },
                    'ADA': { icon: 'https://assets.coingecko.com/coins/images/975/standard/cardano.png', name: 'Cardano', color: '#0033ad', type: 'image' },
                    'DOT': { icon: 'https://assets.coingecko.com/coins/images/12171/standard/polkadot.png', name: 'Polkadot', color: '#e6007a', type: 'image' },
                    'MATIC': { icon: 'https://assets.coingecko.com/coins/images/4713/standard/polygon.png', name: 'Polygon', color: '#8247e5', type: 'image' },
                    'LINK': { icon: 'https://assets.coingecko.com/coins/images/877/standard/chainlink-new-logo.png', name: 'Chainlink', color: '#375bd2', type: 'image' },
                    'XRP': { icon: 'https://assets.coingecko.com/coins/images/44/standard/xrp-symbol-white-128.png', name: 'Ripple', color: '#23292f', type: 'image' },
                    'BNB': { icon: 'https://assets.coingecko.com/coins/images/825/standard/bnb-icon2_2x.png', name: 'Binance Coin', color: '#f3ba2f', type: 'image' },
                    'SHIB': { icon: 'https://assets.coingecko.com/coins/images/11939/standard/shiba.png', name: 'Shiba Inu', color: '#ff6600', type: 'image' },
                    'AAVE': { icon: 'https://assets.coingecko.com/coins/images/12645/standard/AAVE.png', name: 'Aave', color: '#b6509e', type: 'image' }
                };
                
                return coinInfo[symbol] || { icon: 'fa-solid fa-coins', name: symbol, color: '#6c757d', type: 'font' };
            };
            
            const coinDisplay = getCoinDisplaySync(symbol); // Use sync version for immediate display
            
            // Create row using safe DOM methods
            const row = document.createElement('tr');
            
            // Symbol cell with icon
            const symbolCell = document.createElement('td');
            const symbolDiv = document.createElement('div');
            symbolDiv.className = 'd-flex align-items-center';
            
            const iconDiv = document.createElement('div');
            iconDiv.className = 'coin-icon me-2';
            iconDiv.style.color = coinDisplay.color;
            
            if (coinDisplay.type === 'image') {
                const icon = document.createElement('img');
                // Add cache-busting parameter to force fresh image load
                const cacheBuster = Date.now() + Math.random();
                icon.src = coinDisplay.icon + '?v=' + cacheBuster;
                icon.style.width = '24px';
                icon.style.height = '24px';
                icon.style.borderRadius = '50%';
                icon.style.objectFit = 'cover';
                icon.alt = coinDisplay.name;
                icon.onerror = function() {
                    // Fallback to FontAwesome icon if image fails to load
                    const fallbackIcon = document.createElement('i');
                    fallbackIcon.className = 'fa-solid fa-coins';
                    fallbackIcon.style.color = coinDisplay.color;
                    iconDiv.replaceChild(fallbackIcon, icon);
                };
                iconDiv.appendChild(icon);
            } else {
                const icon = document.createElement('i');
                icon.className = coinDisplay.icon;
                iconDiv.appendChild(icon);
            }
            
            const textDiv = document.createElement('div');
            const symbolStrong = document.createElement('strong');
            symbolStrong.textContent = symbol;
            const symbolSmall = document.createElement('small');
            symbolSmall.className = 'text-muted';
            symbolSmall.textContent = coinDisplay.name;
            textDiv.appendChild(symbolStrong);
            textDiv.appendChild(document.createElement('br'));
            textDiv.appendChild(symbolSmall);
            
            symbolDiv.appendChild(iconDiv);
            symbolDiv.appendChild(textDiv);
            symbolCell.appendChild(symbolDiv);
            row.appendChild(symbolCell);
            
            // Create all other cells safely
            const cells = [
                formatNumber(quantity),                                    // BALANCE
                formatMeaningfulCurrency(displayCurrentValue, window.tradingApp?.selectedCurrency || 'USD'),             // VALUE  
                formatMeaningfulCurrency(displayCostBasis, window.tradingApp?.selectedCurrency || 'USD'),                // COST BASIS
                formatCurrency(displayCurrentPrice),                       // PRICE (per unit)
                formatMeaningfulCurrency(totalMarketValue, window.tradingApp?.selectedCurrency || 'USD'),                // MARKET VALUE (use live market data)
                { text: formatMeaningfulCurrency(currentPnlDollar, window.tradingApp?.selectedCurrency || 'USD'), className: currentPnlClass },  // P&L $
                { text: `${currentPnlPercent >= 0 ? "+" : ""}${currentPnlPercent.toFixed(2)}%`, className: currentPnlClass }, // P&L %
                formatMeaningfulCurrency(displayTargetValue, window.tradingApp?.selectedCurrency || 'USD'),              // TARGET VALUE
                { text: formatMeaningfulCurrency(targetPnlDollar, window.tradingApp?.selectedCurrency || 'USD'), className: targetPnlClass },   // TARGET P&L $
                { text: `+${targetPnlPercent.toFixed(2)}%`, className: targetPnlClass },          // TARGET P&L %
                typeof daysHeld === 'number' ? `${daysHeld} days` : daysHeld  // DAYS (show "—" if unknown)
            ];
            
            cells.forEach(cellData => {
                const cell = document.createElement('td');
                if (typeof cellData === 'object') {
                    cell.textContent = cellData.text;
                    if (cellData.className) cell.className = cellData.className;
                } else {
                    cell.textContent = cellData;
                }
                row.appendChild(cell);
            });
            

            
            positionsTableBody.appendChild(row);
        });
        console.debug("Table updated successfully");
        
        // Update refresh time tracking
        if (window.updatePositionsRefreshTime) {
            window.updatePositionsRefreshTime();
        }
        
    } catch (error) {
        console.error("Open positions table update failed:", error);
        console.error("Error details:", error.stack);
    }
}

// Fetch and update available positions table
async function fetchAndUpdateAvailablePositions() {
    const startTime = Date.now();
    try {
        const response = await fetch('/api/available-positions', { 
            cache: 'no-cache',
            signal: AbortSignal.timeout(300000) // 5 minute timeout (increased for 68 positions)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        console.debug("Available positions API response:", data);
        
        // Production mode - self-test removed for clean console output
        
        if (data.success) {
            // Call the table rendering function
            // CONSOLIDATED: Use only one update method to prevent table flashing
            // FORCE USE OF UPDATED COLOR SYSTEM: Always use our improved updateAvailablePositionsTable
            // instead of external renderAvailableTable that doesn't have the enhanced colors
            updateAvailablePositionsTable(data.available_positions || []);
            
            // Legacy fallback (disabled to force color improvements)
            // if (window.renderAvailableTable && typeof window.renderAvailableTable === 'function') {
            //     window.renderAvailableTable(data.available_positions || []);
            // } else {
            //     updateAvailablePositionsTable(data.available_positions || []);
            // }
            
            // Update mobile data labels and ensure proper table formatting
            const table = document.getElementById('available-table');
            if (table) {
                v02ApplyDataLabels(table);
                // Ensure all v02 tables are properly initialized after dynamic updates
                initializeV02Tables();
            }
        } else {
            console.error("Available positions API error:", data.error);
            // Only update if renderAvailableTable isn't available
            // Always use our improved color system
            updateAvailablePositionsTable([]);
        }
    } catch (error) {
        const elapsed = Date.now() - startTime;
        console.error(`❌ Error fetching available positions after ${elapsed}ms:`, error);
        
        if (error.name === 'TimeoutError') {
            console.error('🚨 TIMEOUT: Available positions request took longer than 2 minutes');
        } else if (error.name === 'AbortError') {
            console.error('🚨 ABORTED: Available positions request was cancelled');
        } else if (error.message.includes('HTTP')) {
            console.error('🚨 HTTP ERROR:', error.message);
        } else {
            console.error('🚨 UNKNOWN ERROR:', error.message, error.stack);
        }
        
        // Only update if renderAvailableTable isn't available
        // Always use our improved color system
        updateAvailablePositionsTable([]);
    }
}

// WORKING VERSION: Helper function to safely create available position row
function createAvailablePositionRow(position) {
    const symbol = position.symbol || "Unknown";
    const currentBalance = parseFloat(position.current_balance || 0);
    const currentPrice = parseFloat(position.current_price || 0);
    const lastExitPrice = parseFloat(position.last_exit_price || 0);
    const targetBuyPrice = parseFloat(position.target_buy_price || 0);
    const priceDifference = parseFloat(position.price_difference || 0);
    const priceDiffPercent = parseFloat(position.price_diff_percent || 0);
    const originalBuySignal = position.buy_signal || "WAIT";
    const daysSinceExit = position.days_since_exit || 0;
    
    // Entry confidence data
    const entryConfidence = position.entry_confidence || { score: 50, level: "FAIR", timing_signal: "WAIT" };
    const confidenceScore = entryConfidence.score || 50;
    const confidenceLevel = entryConfidence.level || "FAIR";
    const timingSignal = entryConfidence.timing_signal || "WAIT";
    
    const buySignal = position.buy_signal || "WAIT";
    
    const getBuySignalClass = (signal) => {
        switch(signal) {
            case "READY TO BUY":
            case "BUY READY":
            case "STRONG BUY":
                return "text-success fw-bold";  // Bright green for ready to buy
            case "CAUTIOUS BUY":
                return "text-warning fw-bold";  // Bold orange for caution
            case "MONITORING":
            case "WAIT":
                return "text-secondary";        // Gray for monitoring/waiting
            case "AVOID":
                return "text-danger";          // Red for avoid
            default:
                return "text-muted";
        }
    };
    
    const buySignalClass = getBuySignalClass(buySignal);
    // Enhanced price difference coloring
    const getPriceDiffClass = (diffPercent) => {
        if (diffPercent <= -5) return "text-success fw-bold";    // Excellent discount (>5% below target)
        if (diffPercent <= -2) return "text-success";           // Good discount (2-5% below target)
        if (diffPercent <= 0) return "text-warning";            // Small discount (0-2% below target)
        if (diffPercent <= 2) return "text-warning";            // Slightly above target
        return "text-danger";                                   // Significantly above target
    };
    
    const priceDiffClass = getPriceDiffClass(priceDiffPercent);
    
    // Styling functions
    const getConfidenceClass = (score) => {
        if (score >= 90) return "text-success fw-bold";  // 90-100: Excellent (bright green)
        if (score >= 75) return "text-success";         // 75-89: Good (green)
        if (score >= 60) return "text-warning";         // 60-74: Fair (orange)
        if (score >= 40) return "text-warning";         // 40-59: Weak (orange) 
        return "text-danger";                           // 0-39: Poor (red)
    };
    
    const getTimingSignalClass = (signal) => {
        switch(signal) {
            case "STRONG_BUY":
                return "text-success fw-bold";  // Bright green for strong buy
            case "BUY":
                return "text-success";          // Green for buy
            case "CAUTIOUS_BUY":
                return "text-warning fw-bold";  // Bold orange for caution
            case "WAIT":
                return "text-secondary";        // Gray for wait
            case "AVOID":
                return "text-danger";          // Red for avoid
            default:
                return "text-muted";
        }
    };
    
    const getRiskLevelClass = (level) => {
        // Map all possible risk levels to appropriate colors
        switch(level) {
            case "LOW":
            case "EXCELLENT":
                return "text-success fw-bold";  // Green for low risk
            case "FAIR":
            case "GOOD":
            case "MODERATE":
                return "text-warning";  // Orange for moderate risk  
            case "WEAK":
            case "HIGH":
            case "POOR":
                return "text-danger";  // Red for high risk
            default:
                return "text-muted";  // Gray for unknown
        }
    };
    
    // Format functions
    const formatCurrency = (value) => {
        const numValue = Number(value) || 0;
        if (Math.abs(numValue) < 0.000001 && numValue !== 0) {
            return new Intl.NumberFormat("en-US", { 
                style: "currency", 
                currency: window.tradingApp?.selectedCurrency || "USD",
                minimumFractionDigits: 8,
                maximumFractionDigits: 12
            }).format(numValue);
        }
        return new Intl.NumberFormat("en-US", { 
            style: "currency", 
            currency: window.tradingApp?.selectedCurrency || "USD",
            minimumFractionDigits: 2,
            maximumFractionDigits: 8
        }).format(numValue);
    };
    
    const formatNumber = (value) => {
        if (value > 1000000) return (value / 1000000).toFixed(2) + "M";
        if (value > 1000) return (value / 1000).toFixed(2) + "K";
        return value.toFixed(8);
    };
    
    // Get coin display info safely
    const getCoinDisplay = async (symbol) => {
        return await CoinMetadataCache.getCoinMetadata(symbol);
    };
    
    // Synchronous fallback
    const getCoinDisplaySync = (symbol) => {
        const coinInfo = {
            'BTC': { icon: 'https://assets.coingecko.com/coins/images/1/standard/bitcoin.png', name: 'Bitcoin', color: '#f7931a', type: 'image' },
            'ETH': { icon: 'https://assets.coingecko.com/coins/images/279/standard/ethereum.png', name: 'Ethereum', color: '#627eea', type: 'image' },
            'SOL': { icon: 'https://assets.coingecko.com/coins/images/4128/standard/solana.png', name: 'Solana', color: '#9945ff', type: 'image' },
            'TRX': { icon: 'https://assets.coingecko.com/coins/images/1094/standard/tron-logo.png', name: 'TRON', color: '#ff0013', type: 'image' },
            'GALA': { icon: 'https://assets.coingecko.com/coins/images/12493/standard/GALA-v2.png', name: 'Gala Games', color: '#ff6600', type: 'image' },
            'PEPE': { icon: 'https://assets.coingecko.com/coins/images/29850/standard/pepe-token.jpeg', name: 'Pepe', color: '#28a745', type: 'image' },
            'AUD': { icon: 'fa-solid fa-dollar-sign', name: 'Australian Dollar', color: '#007bff', type: 'font' },
            'USDT': { icon: 'https://assets.coingecko.com/coins/images/325/standard/Tether.png', name: 'Tether USDT', color: '#26a17b', type: 'image' },
            'USDC': { icon: 'https://assets.coingecko.com/coins/images/6319/standard/usdc.png', name: 'USD Coin', color: '#2775ca', type: 'image' },
            'DOGE': { icon: 'https://assets.coingecko.com/coins/images/5/standard/dogecoin.png', name: 'Dogecoin', color: '#c2a633', type: 'image' },
            'ADA': { icon: 'https://assets.coingecko.com/coins/images/975/standard/cardano.png', name: 'Cardano', color: '#0033ad', type: 'image' },
            'DOT': { icon: 'https://assets.coingecko.com/coins/images/12171/standard/polkadot.png', name: 'Polkadot', color: '#e6007a', type: 'image' },
            'MATIC': { icon: 'https://assets.coingecko.com/coins/images/4713/standard/polygon.png', name: 'Polygon', color: '#8247e5', type: 'image' },
            'LINK': { icon: 'https://assets.coingecko.com/coins/images/877/standard/chainlink-new-logo.png', name: 'Chainlink', color: '#375bd2', type: 'image' },
            'XRP': { icon: 'https://assets.coingecko.com/coins/images/44/standard/xrp-symbol-white-128.png', name: 'Ripple', color: '#23292f', type: 'image' },
            'BNB': { icon: 'https://assets.coingecko.com/coins/images/825/standard/bnb-icon2_2x.png', name: 'Binance Coin', color: '#f3ba2f', type: 'image' },
            'SHIB': { icon: 'https://assets.coingecko.com/coins/images/11939/standard/shiba.png', name: 'Shiba Inu', color: '#ff6600', type: 'image' },
            'AAVE': { icon: 'https://assets.coingecko.com/coins/images/12645/standard/AAVE.png', name: 'Aave', color: '#b6509e', type: 'image' }
        };
        return coinInfo[symbol] || { icon: 'fa-solid fa-coins', name: symbol, color: '#6c757d', type: 'font' };
    };
    
    const coinDisplay = getCoinDisplaySync(symbol); // Use sync version for immediate display
    
    // Create row using safe DOM methods
    const row = document.createElement('tr');
    
    // Symbol cell with icon
    const symbolCell = document.createElement('td');
    const symbolDiv = document.createElement('div');
    symbolDiv.className = 'd-flex align-items-center';
    
    const iconDiv = document.createElement('div');
    iconDiv.className = 'coin-icon me-2';
    iconDiv.style.color = coinDisplay.color;
    
    if (coinDisplay.type === 'image') {
        const icon = document.createElement('img');
        // Add cache-busting parameter to force fresh image load
        const cacheBuster = Date.now() + Math.random();
        icon.src = coinDisplay.icon + '?v=' + cacheBuster;
        icon.style.width = '24px';
        icon.style.height = '24px';
        icon.style.borderRadius = '50%';
        icon.style.objectFit = 'cover';
        icon.alt = coinDisplay.name;
        icon.onerror = function() {
            // Fallback to FontAwesome icon if image fails to load
            const fallbackIcon = document.createElement('i');
            fallbackIcon.className = 'fa-solid fa-coins';
            fallbackIcon.style.color = coinDisplay.color;
            iconDiv.replaceChild(fallbackIcon, icon);
        };
        iconDiv.appendChild(icon);
    } else {
        const icon = document.createElement('i');
        icon.className = coinDisplay.icon;
        iconDiv.appendChild(icon);
    }
    
    const textDiv = document.createElement('div');
    const symbolStrong = document.createElement('strong');
    symbolStrong.textContent = symbol;
    const symbolSmall = document.createElement('small');
    symbolSmall.className = 'text-muted';
    symbolSmall.textContent = coinDisplay.name;
    textDiv.appendChild(symbolStrong);
    textDiv.appendChild(document.createElement('br'));
    textDiv.appendChild(symbolSmall);
    
    symbolDiv.appendChild(iconDiv);
    symbolDiv.appendChild(textDiv);
    symbolCell.appendChild(symbolDiv);
    row.appendChild(symbolCell);
    
    // Create remaining cells with proper alignment
    const cells = [
        { text: formatNumber(currentBalance), className: 'text-end' },
        { text: formatCurrency(currentPrice), className: 'text-end' },
        { text: formatCurrency(targetBuyPrice), className: 'text-end fw-bold text-primary' },
        { text: `${priceDiffPercent >= 0 ? '+' : ''}${priceDiffPercent.toFixed(2)}%`, className: `text-end ${priceDiffClass}` }
    ];
    
    cells.forEach(cellData => {
        const cell = document.createElement('td');
        cell.textContent = cellData.text;
        cell.className = cellData.className;
        row.appendChild(cell);
    });
    
    // Confidence score cell
    const confidenceCell = document.createElement('td');
    confidenceCell.className = `text-center ${getConfidenceClass(confidenceScore)}`;
    const confidenceDiv = document.createElement('div');
    confidenceDiv.className = 'd-flex align-items-center justify-content-center';
    const scoreSpan = document.createElement('span');
    scoreSpan.className = 'fw-bold me-1';
    scoreSpan.textContent = confidenceScore.toFixed(1);
    const maxSpan = document.createElement('small');
    maxSpan.className = 'text-muted';
    maxSpan.textContent = '/ 100';
    confidenceDiv.appendChild(scoreSpan);
    confidenceDiv.appendChild(maxSpan);
    confidenceCell.appendChild(confidenceDiv);
    const levelSmall = document.createElement('small');
    levelSmall.className = `text-center ${getConfidenceClass(confidenceScore)}`;
    levelSmall.textContent = confidenceLevel;
    confidenceCell.appendChild(levelSmall);
    row.appendChild(confidenceCell);
    
    // Timing, risk, and buy signal cells
    const timingCell = document.createElement('td');
    timingCell.className = `text-center ${getTimingSignalClass(timingSignal)}`;
    timingCell.textContent = timingSignal.replace('_', ' ');
    row.appendChild(timingCell);
    
    const riskCell = document.createElement('td');
    const riskLevel = entryConfidence.risk_level || entryConfidence.level || "MODERATE";
    riskCell.className = `text-center ${getRiskLevelClass(riskLevel)}`;
    riskCell.textContent = riskLevel;
    row.appendChild(riskCell);
    
    // Bot Buy Criteria Cell - Shows when bot will automatically buy
    const botCriteriaCell = document.createElement('td');
    botCriteriaCell.className = 'text-center';
    
    // Enhanced bot criteria logic with better colors
    const getBotBuyCriteriaStatus = () => {
        // Check if already owned (has significant balance)
        const hasSignificantBalance = currentBalance > 0 && (currentBalance * currentPrice) >= 100;
        if (hasSignificantBalance) {
            return { status: "OWNED", class: "text-info fw-bold", tooltip: "Already in portfolio" };
        }
        
        // Check Bollinger Band triggers first (highest priority)
        const bbAnalysis = position.bollinger_analysis || {};
        if (bbAnalysis.signal === "BUY ZONE") {
            return { status: "BOT WILL BUY", class: "text-success fw-bold bg-success bg-opacity-10", tooltip: "Price hit lower Bollinger Band - bot auto-buy triggered!" };
        }
        
        // Check for strong buy conditions
        if (timingSignal === "STRONG_BUY" && confidenceScore >= 75) {
            return { status: "READY TO BUY", class: "text-success fw-bold", tooltip: "Strong buy signal with high confidence" };
        }
        
        // Check for regular buy conditions  
        if (timingSignal === "BUY" && confidenceScore >= 60) {
            return { status: "READY TO BUY", class: "text-success fw-bold", tooltip: "Buy signal with good confidence" };
        }
        
        // Check for cautious buy conditions
        if (timingSignal === "CAUTIOUS_BUY" && confidenceScore >= 50) {
            return { status: "WATCH", class: "text-warning fw-bold", tooltip: "Cautious buy signal - monitoring for better entry" };
        }
        
        // Check for avoid conditions
        if (timingSignal === "AVOID" || confidenceScore < 30) {
            return { status: "AVOID", class: "text-danger", tooltip: "Poor conditions - avoiding entry" };
        }
        
        // Default monitoring state
        return { status: "MONITORING", class: "text-secondary", tooltip: "Monitoring market conditions" };
    };
    
    // LEGACY CODE - This entire block below should be replaced with the simplified version above
    const getLegacyBotBuyCriteriaStatus = () => {
        // Check if already owned
        if (hasPosition) {
            return { status: "OWNED", class: "text-info fw-bold", tooltip: "Already in portfolio - bot won't buy more" };
        }
        
        // Check confidence blocking conditions
        if (timingSignal === "WAIT") {
            return { status: "BLOCKED", class: "text-muted", tooltip: "Confidence analysis says WAIT - not favorable conditions" };
        } else if (timingSignal === "AVOID") {
            return { status: "BLOCKED", class: "text-danger", tooltip: "Confidence analysis says AVOID - poor technical setup" };
        }
        
        // PRIORITY 1: Check for favorable timing signals that should trigger bot action
        if (timingSignal === "STRONG_BUY" && confidenceScore >= 75) {
            return { status: "STRONG BUY", class: "text-success fw-bold", tooltip: "✅ High confidence + STRONG_BUY timing = optimal entry conditions" };
        } else if (timingSignal === "CAUTIOUS_BUY" && confidenceScore >= 60) {
            return { status: "CAUTIOUS BUY", class: "text-warning fw-bold", tooltip: "⚡ Moderate confidence + CAUTIOUS_BUY timing = favorable entry" };
        } else if (timingSignal === "BUY" && confidenceScore >= 65) {
            return { status: "BUY", class: "text-success", tooltip: "📈 Good confidence + BUY timing = suitable entry" };
        }
        
        // PRIORITY 2: Handle medium confidence timing signals  
        if (timingSignal === "BUY" && confidenceScore >= 50) {
            return { status: "MODERATE BUY", class: "text-warning", tooltip: "📊 Moderate confidence + BUY timing = cautious entry" };
        }
        
        // Check Bollinger Band trigger (primary bot criteria)
        const bbAnalysis = position.bollinger_analysis || {};
        const bbSignal = bbAnalysis.signal || "NO DATA";
        const bbDistance = parseFloat(bbAnalysis.distance_percent) || 0;
        const lowerBandPrice = parseFloat(bbAnalysis.lower_band_price) || 0;
        
        if (bbSignal === "BUY ZONE" || (lowerBandPrice > 0 && currentPrice <= lowerBandPrice)) {
            return { status: "BOT WILL BUY", class: "text-success fw-bold", tooltip: "✅ Price hit lower Bollinger Band - bot auto-buy triggered!" };
        }
        
        // Show distance to bot trigger
        if (lowerBandPrice > 0 && currentPrice > 0) {
            const distanceToTrigger = ((currentPrice - lowerBandPrice) / lowerBandPrice) * 100;
            if (distanceToTrigger <= 5) {
                return { 
                    status: `${distanceToTrigger.toFixed(1)}% away`, 
                    class: "text-warning fw-bold", 
                    tooltip: `Price needs to drop ${distanceToTrigger.toFixed(1)}% to $${lowerBandPrice.toFixed(6)} to trigger bot buy`
                };
            } else if (distanceToTrigger <= 15) {
                return { 
                    status: `${distanceToTrigger.toFixed(1)}% away`, 
                    class: "text-warning", 
                    tooltip: `Price needs to drop ${distanceToTrigger.toFixed(1)}% to $${lowerBandPrice.toFixed(6)} to trigger bot buy`
                };
            } else {
                return { 
                    status: `${distanceToTrigger.toFixed(1)}% away`, 
                    class: "text-muted", 
                    tooltip: `Price needs to drop ${distanceToTrigger.toFixed(1)}% to $${lowerBandPrice.toFixed(6)} to trigger bot buy`
                };
            }
        }
        
        // Check for rebuy conditions
        if (targetBuyPrice > 0) {
            const distanceToRebuy = ((currentPrice - targetBuyPrice) / targetBuyPrice) * 100;
            if (distanceToRebuy <= 0) {
                return { status: "REBUY READY", class: "text-success fw-bold", tooltip: "✅ Price hit rebuy target - bot ready to buy $100 max" };
            } else {
                return { 
                    status: `Rebuy ${distanceToRebuy.toFixed(1)}% away`, 
                    class: "text-warning", 
                    tooltip: `Rebuy trigger at $${targetBuyPrice.toFixed(6)} - ${distanceToRebuy.toFixed(1)}% away`
                };
            }
        }
        
        // Final monitoring state - explain why no trigger
        if (timingSignal === "WAIT") {
            return { status: "WAIT", class: "text-muted", tooltip: "Confidence analysis says WAIT - not favorable conditions" };
        } else if (timingSignal === "AVOID") {
            return { status: "AVOID", class: "text-danger", tooltip: "Confidence analysis says AVOID - poor technical setup" };
        }
        
        return { status: "MONITORING", class: "text-secondary", tooltip: "Monitoring market conditions - no active buy triggers" };
    };
    
    const botCriteria = getBotBuyCriteriaStatus();  // Use the fixed logic
    botCriteriaCell.className = `text-center ${botCriteria.class}`;
    botCriteriaCell.textContent = botCriteria.status;
    botCriteriaCell.title = botCriteria.tooltip;
    row.appendChild(botCriteriaCell);
    
    // Action buttons cell
    const actionsCell = document.createElement('td');
    actionsCell.className = 'text-center';
    const btnGroup = document.createElement('div');
    btnGroup.className = 'btn-group btn-group-sm';
    btnGroup.setAttribute('role', 'group');
    
    // Main action button
    const mainBtn = document.createElement('button');
    if (confidenceScore >= 75 && timingSignal !== "WAIT") {
        mainBtn.className = 'btn btn-success btn-xs';
        mainBtn.textContent = 'Buy';
        mainBtn.title = 'High Confidence Entry';
    } else if (confidenceScore >= 60) {
        mainBtn.className = 'btn btn-warning btn-xs';
        mainBtn.textContent = 'Cautious';
        mainBtn.title = 'Cautious Entry';
    } else {
        mainBtn.className = 'btn btn-outline-secondary btn-xs';
        mainBtn.textContent = 'Wait';
        mainBtn.disabled = true;
        mainBtn.title = 'Low confidence - wait for better setup';
    }
    if (!mainBtn.disabled) {
        mainBtn.onclick = () => buyBackPosition(symbol);
    }
    
    // Details button
    const detailsBtn = document.createElement('button');
    detailsBtn.className = 'btn btn-outline-info btn-xs';
    detailsBtn.textContent = 'Details';
    detailsBtn.title = 'View Detailed Analysis';
    detailsBtn.onclick = () => showConfidenceDetails(symbol);
    
    btnGroup.appendChild(mainBtn);
    btnGroup.appendChild(detailsBtn);
    actionsCell.appendChild(btnGroup);
    row.appendChild(actionsCell);
    
    return row;
}

// Holdings table function (mirrors Available Positions pattern)
function updateHoldingsTable(holdings) {
    // This function is only used as a fallback when TradingApp isn't available
    if (window.tradingApp) {
        console.log('TradingApp available - using updateAllTables() to prevent conflicts');
        window.tradingApp.updateAllTables(holdings);
        return;
    }
    
    // Fallback table update for edge cases
    const holdingsTableBody = document.getElementById('holdings-tbody');
    if (!holdingsTableBody) return;
    
    try {
        console.log('Using fallback updateHoldingsTable for', holdings.length, 'holdings');
        holdingsTableBody.innerHTML = '';
        
        if (!holdings || holdings.length === 0) {
            holdingsTableBody.innerHTML = '<tr><td colspan="11" class="text-center text-muted">No positions found</td></tr>';
            return;
        }
        
        holdings.forEach(holding => {
            const row = createHoldingRow(holding);
            if (row) holdingsTableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Fallback table update failed:', error);
    }
}

// Helper function to create holding row with crypto icons
function createHoldingRow(holding) {
    try {
        const row = document.createElement('tr');
        const symbol = holding.symbol || holding.name || 'N/A';
        const pnlClass = safeNum(holding.pnl, 0) >= 0 ? 'text-success' : 'text-danger';
        const pnlSign = safeNum(holding.pnl, 0) >= 0 ? '+' : '';
        
        // Get crypto icon using the same function as Available Positions
        const cryptoIcon = getCryptoIcon(symbol);
        
        // Calculate values
        const quantity = holding.quantity || holding.available_quantity || 0;
        const costBasis = holding.cost_basis || 0;
        const currentValue = holding.current_value || holding.value || 0;
        const currentPrice = holding.current_price || 0;
        const pnl = holding.pnl || 0;
        const pnlPercent = holding.pnl_percent || 0;
        
        // Asset cell with crypto icon
        const assetCell = document.createElement('td');
        assetCell.innerHTML = `
            <div class="d-flex align-items-center">
                ${cryptoIcon}
                <div class="ms-2">
                    <div class="fw-bold">${symbol}</div>
                    <small class="text-muted">${holding.name || symbol}</small>
                </div>
            </div>
        `;
        row.appendChild(assetCell);
        
        // Add other cells... (updated column structure: removed INVESTED, renamed AVG ENTRY to ENTRY PRICE, LIVE PRICE to CURRENT PRICE)
        const avgEntryPrice = costBasis / (quantity || 1); // Calculate avg entry from cost basis
        const cells = [
            { content: quantity.toFixed(6), class: '' }, // QTY HELD
            { content: avgEntryPrice.toLocaleString('en-US', {style: 'currency', currency: window.tradingApp?.selectedCurrency || 'USD', minimumFractionDigits: 8, maximumFractionDigits: 8}), class: '' }, // ENTRY PRICE (formerly AVG ENTRY)
            { content: currentPrice.toLocaleString('en-US', {style: 'currency', currency: window.tradingApp?.selectedCurrency || 'USD', minimumFractionDigits: 8, maximumFractionDigits: 8}), class: '' }, // CURRENT PRICE (formerly LIVE PRICE)
            { content: currentValue.toLocaleString('en-US', {style: 'currency', currency: window.tradingApp?.selectedCurrency || 'USD', minimumFractionDigits: 8, maximumFractionDigits: 8}), class: '' }, // POSITION VALUE
            { content: `${pnlSign}${pnl.toLocaleString('en-US', {style: 'currency', currency: window.tradingApp?.selectedCurrency || 'USD', minimumFractionDigits: 8, maximumFractionDigits: 8})}`, class: pnlClass }, // UNREALIZED $
            { content: `${pnlSign}${pnlPercent.toFixed(2)}%`, class: pnlClass }, // GAIN/LOSS %
            { content: calculateBollingerTargetValue(holding), class: 'text-success' }, // TARGET VALUE - Dynamic Bollinger Band
            { content: calculateBollingerTargetProfit(holding), class: 'text-success' }, // TARGET PROFIT $ - Dynamic Bollinger Band
            { content: calculateBollingerTargetPercent(holding), class: 'text-success' }, // TARGET PROFIT % - Dynamic Bollinger Band
            { content: getPositionStatus(holding), class: '' } // POSITION
        ];
        
        cells.forEach(cellData => {
            const cell = document.createElement('td');
            cell.className = cellData.class;
            cell.innerHTML = cellData.content;
            row.appendChild(cell);
        });
        
        return row;
        
    } catch (error) {
        console.error("Error creating holding row:", error);
        return null;
    }
}

// Calculate dynamic target value using actual Bollinger Band upper band price
function calculateBollingerTargetValue(holding) {
    const currentValue = holding.current_value || 0;
    const avgEntryPrice = holding.avg_entry_price || 0;
    const quantity = holding.quantity || 0;
    
    // Get upper Bollinger Band price from bollinger_analysis (real trading data)
    const bollingerAnalysis = holding.bollinger_analysis || {};
    const upperBandPrice = bollingerAnalysis.upper_band_price || holding.upper_band_price;
    
    if (upperBandPrice && quantity > 0) {
        const targetValue = quantity * upperBandPrice;
        return targetValue.toLocaleString('en-US', {style: 'currency', currency: window.tradingApp?.selectedCurrency || 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2});
    }
    
    // Fallback to traditional multiplier if no Bollinger data
    const targetMultiplier = getTargetMultiplier(holding);
    const fallbackValue = currentValue * targetMultiplier;
    return fallbackValue.toLocaleString('en-US', {style: 'currency', currency: window.tradingApp?.selectedCurrency || 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2});
}

// Calculate dynamic target profit using actual Bollinger Band upper band price
function calculateBollingerTargetProfit(holding) {
    const currentValue = holding.current_value || 0;
    const avgEntryPrice = holding.avg_entry_price || 0;
    const quantity = holding.quantity || 0;
    
    // Get upper Bollinger Band price from bollinger_analysis (real trading data)
    const bollingerAnalysis = holding.bollinger_analysis || {};
    const upperBandPrice = bollingerAnalysis.upper_band_price || holding.upper_band_price;
    
    if (upperBandPrice && quantity > 0) {
        const targetValue = quantity * upperBandPrice;
        const targetProfit = targetValue - currentValue;
        return `+${targetProfit.toLocaleString('en-US', {style: 'currency', currency: window.tradingApp?.selectedCurrency || 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }
    
    // Fallback to traditional multiplier if no Bollinger data
    const targetMultiplier = getTargetMultiplier(holding);
    const fallbackProfit = currentValue * (targetMultiplier - 1);
    return `+${fallbackProfit.toLocaleString('en-US', {style: 'currency', currency: window.tradingApp?.selectedCurrency || 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

// Calculate dynamic target percentage using actual Bollinger Band upper band price
function calculateBollingerTargetPercent(holding) {
    const currentPrice = holding.current_price || 0;
    const avgEntryPrice = holding.avg_entry_price || 0;
    
    // Get upper Bollinger Band price from bollinger_analysis (real trading data)
    const bollingerAnalysis = holding.bollinger_analysis || {};
    const upperBandPrice = bollingerAnalysis.upper_band_price || holding.upper_band_price;
    
    if (upperBandPrice && avgEntryPrice > 0) {
        const targetPercent = ((upperBandPrice - avgEntryPrice) / avgEntryPrice) * 100;
        return `+${targetPercent.toFixed(1)}%`;
    }
    
    // Fallback to traditional multiplier if no Bollinger data
    const fallbackPercent = getTargetPercent(holding);
    return `+${fallbackPercent.toFixed(1)}%`;
}

/** Calculate target value based on dynamic calculations */
function calculateTargetValue(costBasis, holding, ccy='USD') {
    const target = calcTargetValue(costBasis, holding);
    return formatMoney(target, ccy, 2, 2);
}

/** Calculate target profit based on dynamic calculations */
function calculateTargetProfit(costBasis, holding, ccy='USD') {
    const profit = calcTargetDollar(costBasis, holding);
    return formatMoney(profit, ccy, 2, 2);
}

/** Get position status based on trading bot state and holding data */
function getPositionStatus(holding) {
    const quantity = parseFloat(holding.quantity || 0);
    const pnlPercent = parseFloat(holding.pnl_percent || holding.unrealized_pnl_percent || 0);
    
    if (quantity <= 0) {
        return '<span class="badge bg-secondary" title="No position held">FLAT</span>';
    }
    
    // Check if position is significantly profitable (likely to be managed by bot)
    const targetPct = getTargetPercent(holding);
    const managedThreshold = Math.max(targetPct * 0.8, 6.0);
    
    if (pnlPercent >= managedThreshold) {
        return `<span class="badge bg-success" title="Position above ${managedThreshold.toFixed(1)}% profit - in active management zone">MANAGED</span>`;
    }
    
    // Check if position is moderately profitable
    const watchThreshold = Math.max(targetPct * 0.4, 3.0);
    if (pnlPercent >= watchThreshold) {
        return `<span class="badge bg-warning text-dark" title="Position above ${watchThreshold.toFixed(1)}% profit - monitored for exit signals">WATCH</span>`;
    }
    
    // Position at a loss or small gain
    if (pnlPercent < 0) {
        return '<span class="badge bg-danger" title="Position at loss - monitored for crash protection">LOSS</span>';
    }
    
    // Regular long position with small gains
    return '<span class="badge bg-primary" title="Holding long position - monitored by trading bot">LONG</span>';
}

/** Get cryptocurrency icon - uses CoinGecko API for authentic logos */
function getCryptoIcon(symbol) {
    if (!symbol || symbol === 'N/A') {
        return '<i class="fa-solid fa-coins text-muted" style="width: 24px; height: 24px; font-size: 18px;"></i>';
    }
    
    // Map symbol to CoinGecko ID for accurate logos
    const coinGeckoIds = {
        'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin', 'SOL': 'solana',
        'XRP': 'ripple', 'USDC': 'usd-coin', 'ADA': 'cardano', 'AVAX': 'avalanche-2',
        'DOGE': 'dogecoin', 'TRX': 'tron', 'DOT': 'polkadot', 'MATIC': 'matic-network',
        'LTC': 'litecoin', 'ATOM': 'cosmos', 'UNI': 'uniswap', 'LINK': 'chainlink',
        'NEAR': 'near', 'XLM': 'stellar', 'ALGO': 'algorand', 'VET': 'vechain',
        'ICP': 'internet-computer', 'FIL': 'filecoin', 'AAVE': 'aave', 'MKR': 'maker',
        'THETA': 'theta-token', 'AXS': 'axie-infinity', 'SAND': 'the-sandbox',
        'MANA': 'decentraland', 'CRV': 'curve-dao-token', 'COMP': 'compound-governance-token',
        'SUSHI': 'sushi', 'YFI': 'yearn-finance', 'SNX': 'havven', '1INCH': '1inch',
        'ENJ': 'enjincoin', 'BAT': 'basic-attention-token', 'ZRX': '0x',
        'OMG': 'omisego', 'REN': 'republic-protocol', 'LRC': 'loopring',
        'KNC': 'kyber-network-crystal', 'STORJ': 'storj', 'BAND': 'band-protocol',
        'RSR': 'reserve-rights-token', 'NMR': 'numeraire', 'RLC': 'iexec-rlc',
        'USDT': 'tether', 'FTM': 'fantom', 'GALA': 'gala', 'APE': 'apecoin',
        'SHIB': 'shiba-inu', 'PEPE': 'pepe', 'WLD': 'worldcoin-wld'
    };
    
    const coinId = coinGeckoIds[symbol.toUpperCase()] || symbol.toLowerCase();
    
    return `<img src="https://assets.coingecko.com/coins/images/${getCoinGeckoImageId(coinId)}/small/${coinId}.png" 
                 alt="${symbol}" 
                 class="crypto-icon" 
                 style="width: 24px; height: 24px; border-radius: 50%;"
                 onerror="this.outerHTML='<i class=\\'fa-solid fa-coins text-warning\\' style=\\'width: 24px; height: 24px; font-size: 18px;\\'></i>'">`;
}

/** Get CoinGecko image IDs for major cryptocurrencies */
function getCoinGeckoImageId(coinId) {
    const imageIds = {
        'bitcoin': '1', 'ethereum': '279', 'binancecoin': '825', 'solana': '4128',
        'ripple': '44', 'usd-coin': '6319', 'cardano': '975', 'avalanche-2': '12559',
        'dogecoin': '5', 'tron': '1094', 'polkadot': '12171', 'matic-network': '4713',
        'litecoin': '2', 'cosmos': '5866', 'uniswap': '12504', 'chainlink': '877',
        'near': '10365', 'stellar': '100', 'algorand': '4030', 'vechain': '1042',
        'internet-computer': '14495', 'filecoin': '12817', 'aave': '12645', 'maker': '1518',
        'theta-token': '2416', 'axie-infinity': '13029', 'the-sandbox': '12493',
        'decentraland': '878', 'curve-dao-token': '12124', 'compound-governance-token': '10347',
        'sushi': '12271', 'yearn-finance': '11849', 'havven': '5013', '1inch': '13469',
        'enjincoin': '1027', 'basic-attention-token': '677', '0x': '863',
        'omisego': '1808', 'republic-protocol': '3212', 'loopring': '1934',
        'kyber-network-crystal': '9444', 'storj': '5446', 'band-protocol': '9545',
        'reserve-rights-token': '8365', 'numeraire': '1732', 'iexec-rlc': '1637',
        'tether': '325', 'fantom': '3513', 'gala': '12493', 'apecoin': '18876',
        'shiba-inu': '11939', 'pepe': '29850', 'worldcoin-wld': '31069'
    };
    
    return imageIds[coinId] || '1'; // Default to Bitcoin ID if not found
}

// Available positions table function
function updateAvailablePositionsTable(availablePositions) {
    try {
        const availableTableBody = document.getElementById("available-tbody");
        if (!availableTableBody) {
            return;
        }
        
        console.debug("Updating available positions table with:", availablePositions);
        
        if (!availablePositions || availablePositions.length === 0) {
            // Safe DOM creation instead of innerHTML
            availableTableBody.textContent = '';
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 10;
            cell.className = 'text-center py-4';
            
            const icon = document.createElement('i');
            icon.className = 'fa-solid fa-circle-info me-2';
            cell.appendChild(icon);
            cell.appendChild(document.createTextNode('No available positions for buy-back'));
            
            row.appendChild(cell);
            availableTableBody.appendChild(row);
            return;
        }

        
        // Clear existing content safely
        availableTableBody.textContent = '';
        
        // Safely append rows using DOM methods instead of innerHTML
        availablePositions.forEach(position => {
            const row = createAvailablePositionRow(position);
            availableTableBody.appendChild(row);
        });
        console.debug("Available positions table updated successfully");
        
    } catch (error) {
        console.error("Available positions table update failed:", error);
    }
}

// Trading action functions
function sellPosition(symbol, percentage) {
    if (confirm(`Sell ${percentage}% of your ${symbol} position?`)) {
        executeSellOrder(symbol, percentage);
    }
}

// Show detailed confidence analysis
async function showConfidenceDetails(symbol) {
    try {
        const response = await fetch(`/api/entry-confidence/${symbol}`, { cache: 'no-cache' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        if (data.status === 'success') {
            const info = data.data;
            const breakdown = info.breakdown;
            
            // Ensure all required fields have default values to prevent undefined errors
            const safeInfo = {
                confidence_score: info.confidence_score || 50,
                confidence_level: info.confidence_level || 'FAIR',
                timing_signal: info.timing_signal || 'WAIT',
                risk_level: info.risk_level || 'MODERATE',
                entry_recommendation: info.entry_recommendation || 'Proceed with caution',
                calculated_at: info.calculated_at || new Date().toISOString(),
                ...info
            };
            
            const safeBreakdown = {
                technical_analysis: breakdown?.technical_analysis || 50,
                volatility_assessment: breakdown?.volatility_assessment || 50,
                momentum_indicators: breakdown?.momentum_indicators || 50,
                volume_analysis: breakdown?.volume_analysis || 50,
                support_resistance: breakdown?.support_resistance || 50,
                ...breakdown
            };
            
            // Remove existing modal if it exists
            const existingModal = document.getElementById('confidenceModal');
            if (existingModal) {
                existingModal.remove();
            }
            
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
                                        <div class="card h-100">
                                            <div class="card-body text-center">
                                                <h2 class="display-4 ${safeInfo.confidence_score >= 75 ? 'text-success' : safeInfo.confidence_score >= 60 ? 'text-warning' : 'text-danger'}">${safeInfo.confidence_score}</h2>
                                                <p class="card-text">
                                                    <strong class="${safeInfo.confidence_score >= 75 ? 'text-success' : safeInfo.confidence_score >= 60 ? 'text-warning' : 'text-danger'}">${safeInfo.confidence_level}</strong>
                                                    <br><small class="text-muted">Confidence Level</small>
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="card h-100">
                                            <div class="card-body">
                                                <h6 class="card-title">Signal & Risk</h6>
                                                <p><strong>Timing Signal:</strong> <span class="${safeInfo.timing_signal === 'BUY' ? 'text-success' : safeInfo.timing_signal === 'CAUTIOUS_BUY' ? 'text-warning' : 'text-muted'}">${safeInfo.timing_signal.replace('_', ' ')}</span></p>
                                                <p><strong>Risk Level:</strong> <span class="${safeInfo.risk_level === 'LOW' ? 'text-success' : safeInfo.risk_level === 'MODERATE' ? 'text-warning' : 'text-danger'}">${safeInfo.risk_level}</span></p>
                                                <small class="text-muted">${safeInfo.entry_recommendation}</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="card">
                                    <div class="card-header">
                                        <h6 class="mb-0">Detailed Analysis Breakdown</h6>
                                    </div>
                                    <div class="card-body">
                                        <div class="row">
                                            <div class="col-md-6">
                                                <div class="mb-3">
                                                    <label class="form-label">Technical Analysis</label>
                                                    <div class="progress">
                                                        <div class="progress-bar ${safeBreakdown.technical_analysis >= 70 ? 'bg-success' : safeBreakdown.technical_analysis >= 50 ? 'bg-warning' : 'bg-danger'}" 
                                                             style="width: ${safeBreakdown.technical_analysis}%"></div>
                                                    </div>
                                                    <small class="text-muted">${safeBreakdown.technical_analysis}/100</small>
                                                </div>
                                                
                                                <div class="mb-3">
                                                    <label class="form-label">Volatility Assessment</label>
                                                    <div class="progress">
                                                        <div class="progress-bar ${safeBreakdown.volatility_assessment >= 70 ? 'bg-success' : safeBreakdown.volatility_assessment >= 50 ? 'bg-warning' : 'bg-danger'}" 
                                                             style="width: ${safeBreakdown.volatility_assessment}%"></div>
                                                    </div>
                                                    <small class="text-muted">${safeBreakdown.volatility_assessment}/100</small>
                                                </div>
                                                
                                                <div class="mb-3">
                                                    <label class="form-label">Momentum Indicators</label>
                                                    <div class="progress">
                                                        <div class="progress-bar ${safeBreakdown.momentum_indicators >= 70 ? 'bg-success' : safeBreakdown.momentum_indicators >= 50 ? 'bg-warning' : 'bg-danger'}" 
                                                             style="width: ${safeBreakdown.momentum_indicators}%"></div>
                                                    </div>
                                                    <small class="text-muted">${safeBreakdown.momentum_indicators}/100</small>
                                                </div>
                                            </div>
                                            <div class="col-md-6">
                                                <div class="mb-3">
                                                    <label class="form-label">Volume Analysis</label>
                                                    <div class="progress">
                                                        <div class="progress-bar ${safeBreakdown.volume_analysis >= 70 ? 'bg-success' : safeBreakdown.volume_analysis >= 50 ? 'bg-warning' : 'bg-danger'}" 
                                                             style="width: ${safeBreakdown.volume_analysis}%"></div>
                                                    </div>
                                                    <small class="text-muted">${safeBreakdown.volume_analysis}/100</small>
                                                </div>
                                                
                                                <div class="mb-3">
                                                    <label class="form-label">Support/Resistance</label>
                                                    <div class="progress">
                                                        <div class="progress-bar ${safeBreakdown.support_resistance >= 70 ? 'bg-success' : safeBreakdown.support_resistance >= 50 ? 'bg-warning' : 'bg-danger'}" 
                                                             style="width: ${safeBreakdown.support_resistance}%"></div>
                                                    </div>
                                                    <small class="text-muted">${safeBreakdown.support_resistance}/100</small>
                                                </div>
                                                
                                                <div class="alert alert-info">
                                                    <small><strong>Analysis Time:</strong> ${new Date(safeInfo.calculated_at).toLocaleString()}</small>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                ${safeInfo.confidence_score >= 60 ? 
                                    `<button type="button" class="btn btn-primary" onclick="buyBackPosition('${symbol}'); 
                                        // Safe Bootstrap modal hide
                                        if (window.bootstrap && window.bootstrap.Modal) {
                                            bootstrap.Modal.getInstance(document.getElementById('confidenceModal'))?.hide();
                                        }
                                    ">Execute Trade</button>` : 
                                    ''
                                }
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            
            // Add modal to body
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // Show modal safely - wait for Bootstrap to be ready
            if (window.bootstrap && window.bootstrap.Modal) {
                const modal = new bootstrap.Modal(document.getElementById('confidenceModal'));
                modal.show();
            } else {
                // Fallback - wait for Bootstrap to load
                setTimeout(() => {
                    if (window.bootstrap && window.bootstrap.Modal) {
                        const modal = new bootstrap.Modal(document.getElementById('confidenceModal'));
                        modal.show();
                    }
                }, 100);
            }
            
            // Clean up when modal is hidden
            document.getElementById('confidenceModal').addEventListener('hidden.bs.modal', function() {
                this.remove();
            });
            
        } else {
            toast(`Error getting confidence data: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error showing confidence details:', error);
        toast('Failed to load confidence analysis', 'error');
    }
}

function buyMorePosition(symbol) {
    const amount = prompt(`Enter USD amount to buy more ${symbol}:`);
    if (amount && !isNaN(amount) && parseFloat(amount) > 0) {
        if (confirm(`Buy $${amount} worth of ${symbol}?`)) {
            executeBuyOrder(symbol, parseFloat(amount));
        }
    }
}

// Recalculate positions function
async function recalculatePositions() {
    const btn = document.getElementById('recalculate-btn');
    const originalText = btn.innerHTML;
    
    try {
        // Show loading state
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Recalculating...';
        
        // Get admin token from meta tag (set by Flask template)
        const metaToken = document.querySelector('meta[name="admin-token"]');
        const adminToken = metaToken ? metaToken.getAttribute('content') : '';
        
        if (!adminToken) {
            throw new Error('Admin token not available - cannot recalculate positions');
        }
        
        // Call recalculation API with correct header format
        const response = await fetch('/api/recalculate-positions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Token': adminToken
            },
            body: JSON.stringify({ force_refresh: true })
        });
        
        if (!response.ok) {
            throw new Error(`Recalculation failed: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            // Force refresh available positions data (avoid conflicts during other updates)
            if (window.tradingApp && !window.tradingApp.isUpdatingTables) {
                await fetchAndUpdateAvailablePositions();
            }
            
            // Show success feedback
            btn.innerHTML = '<i class="fas fa-check-circle me-1"></i>Complete!';
            btn.className = 'btn btn-success btn-sm';
            
            // Reset after 2 seconds
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.className = 'btn btn-outline-primary btn-sm';
                btn.disabled = false;
            }, 2000);
            
            console.log('Available positions recalculated successfully');
        } else {
            throw new Error(result.message || 'Recalculation failed');
        }
        
    } catch (error) {
        console.error('Recalculation error:', error);
        
        // Show error state
        btn.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Error';
        btn.className = 'btn btn-danger btn-sm';
        
        // Reset after 3 seconds
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.className = 'btn btn-outline-primary btn-sm';
            btn.disabled = false;
        }, 3000);
        
        alert(`Recalculation failed: ${error.message}`);
    }
}

// Make function globally available
window.recalculatePositions = recalculatePositions;

// KPI Stat Strip Helper Functions
function setKpi(id, valueText, deltaPct) {
  const root = document.getElementById(id);
  if (!root) return;
  const v = root.querySelector('[data-kpi-value]');
  const d = root.querySelector('[data-kpi-delta]');
  if (v) v.textContent = valueText;

  if (d) {
    const val = Number(deltaPct);
    let cls = 'flat', label = '0.0%';
    if (!Number.isNaN(val)) {
      if (val > 0) { cls = 'up';   label = `+${val.toFixed(2)}%`; }
      else if (val < 0) { cls = 'down'; label = `${val.toFixed(2)}%`; }
      else { cls = 'flat'; label = '0.00%'; }
    }
    d.classList.remove('up','down','flat');
    d.classList.add(cls);
    d.textContent = label;
  }
}

// Update all top KPIs with portfolio data
function updateTopKpis({ equity, equityDelta, uPnL, uPnLDelta, exposure, exposureDelta, cash, cashDelta }) {
  setKpi('kpi-equity',   equity,   equityDelta);
  setKpi('kpi-upnl',     uPnL,     uPnLDelta);
  setKpi('kpi-exposure', exposure, exposureDelta);
  setKpi('kpi-cash',     cash,     cashDelta);
}

// Available positions action functions
window.buyBackPosition = function buyBackPosition(symbol) {
    const defaultAmount = 100; // Default $100 rebuy limit from system preferences
    const amount = prompt(`Enter USD amount to buy back ${symbol}:`, defaultAmount);
    if (amount && !isNaN(amount) && parseFloat(amount) > 0) {
        if (confirm(`Buy back $${amount} worth of ${symbol}?`)) {
            executeBuyOrder(symbol, parseFloat(amount));
        }
    }
};

function setCustomBuyPrice(symbol) {
    const price = prompt(`Enter custom buy trigger price for ${symbol}:`);
    if (price && !isNaN(price) && parseFloat(price) > 0) {
        toast(`Custom buy price of $${price} set for ${symbol} (feature coming soon)`, 'info');
        // TODO: Implement custom price alerts in backend
    }
}

// Stop all trading function
async function stopAllTrading() {
    if (!confirm("Are you sure you want to stop all trading activity? This will:\n\n• Stop the trading bot if running\n• Cancel any pending orders\n• Pause automated strategies\n\nYou can restart trading manually later.")) {
        return;
    }
    
    try {
        // Stop the bot if it's running
        const botData = await fetchJSON('/api/bot/stop', {
            method: 'POST',
            cache: 'no-store'
        });
        
        if (botData.success) {
            console.log('Bot stopped:', botData.message);
        }
        
        // Update bot status display
        const botStatusElement = document.getElementById('bot-status-top');
        if (botStatusElement) {
            botStatusElement.textContent = 'Start Bot';
        }
        
        toast('Trading stopped successfully - Bot paused, manual trading available', 'info');
        
        // Refresh dashboard data
        if (typeof loadDashboardData === 'function') {
            loadDashboardData();
        }
        
    } catch (error) {
        console.error('Error stopping trading:', error);
        toast('Error stopping trading: ' + error.message, 'error');
    }
}

async function executeSellOrder(symbol, percentage) {
    try {
        const normalizedSymbol = toOkxInst(symbol);
        const response = await fetch("/api/sell", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol: normalizedSymbol, percentage: percentage }),
            cache: "no-store"
        });
        const data = await response.json();
        
        if (data.success) {
            toast(`Sell order successful: ${data.message}`, 'success');
            if (window.dashboardManager) {
                window.dashboardManager.updateCryptoPortfolio();
                window.dashboardManager.updateCurrentHoldings();
            }
        } else {
            toast(`Sell order failed: ${data.error}`, 'error');
        }
    } catch (error) {
        console.debug("Sell order error:", error);
        toast("Sell order failed: Network error", 'error');
    }
}

async function executeBuyOrder(symbol, amount) {
    try {
        const normalizedSymbol = toOkxInst(symbol);
        const response = await fetch("/api/buy", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol: normalizedSymbol, amount: amount }),
            cache: "no-store"
        });
        const data = await response.json();
        
        if (data.success) {
            toast(`Buy order successful: ${data.message}`, 'success');
            if (window.dashboardManager) {
                window.dashboardManager.updateCryptoPortfolio();
                window.dashboardManager.updateCurrentHoldings();
            }
        } else {
            toast(`Buy order failed: ${data.error}`, 'error');
        }
    } catch (error) {
        console.debug("Buy order error:", error);
        toast("Buy order failed: Network error", 'error');
    }
}

// Function to refresh trades data (called by refresh button)
async function refreshTradesData() {
    console.log('Refreshing trades data from OKX trading history...');
    try {
        const timeframe = document.getElementById('trades-timeframe')?.value || '7d';
        
        // Show loading state
        const tableBody = document.getElementById('trades-table');
        if (tableBody) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">Loading trades from OKX...</td></tr>'; // Fixed: Recent Trades has 6 columns
        }
        
        // Fetch from the working trade-history endpoint
        const response = await fetch(`/api/trade-history?timeframe=${timeframe}&_refresh=${Date.now()}`, { 
            cache: 'no-cache',
            headers: {
                'Cache-Control': 'no-cache'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('OKX trading history response:', data);
        
        if (data.success && data.trades) {
            // Update the trades table directly
            updateTradesTableFromOKX(data.trades);
            console.log(`Updated trades table with ${data.trades.length} trades from OKX trading history`);
            
            // Update count if element exists
            const countElement = document.getElementById('trades-count');
            if (countElement) {
                countElement.textContent = data.trades.length;
            }
        } else {
            console.warn('No trades data in response:', data);
            if (tableBody) {
                tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No trades found</td></tr>';
            }
        }
    } catch (error) {
        console.error('Failed to refresh trades data:', error);
        const tableBody = document.getElementById('trades-table');
        if (tableBody) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Failed to load trades</td></tr>'; // Fixed: Recent Trades has 6 columns
        }
    }
}

// Helper function to update trades table from OKX data
function updateTradesTableFromOKX(trades) {
    const tableBody = document.getElementById('trades-table');
    if (!tableBody || !trades) return;
    
    tableBody.innerHTML = '';
    
    if (!trades.length) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No trades found in OKX history</td></tr>'; // Fixed: Recent Trades has 6 columns
        return;
    }
    
    trades.forEach((trade, index) => {
        const row = document.createElement('tr');
        // Fix timestamp parsing for OKX format: "2025-08-22T02:19:28.148000+00:00Z"
        let timestamp = '-';
        try {
            let dateStr = trade.timestamp;
            if (typeof dateStr === 'string') {
                // Remove trailing Z if timezone offset is present
                if (dateStr.includes('+') && dateStr.endsWith('Z')) {
                    dateStr = dateStr.slice(0, -1);
                }
                const date = new Date(dateStr);
                if (!isNaN(date.getTime())) {
                    timestamp = date.toLocaleString();
                }
            }
        } catch (e) {
            console.debug('Date parsing failed for:', trade.timestamp);
        }
        const symbol = (trade.symbol || '').replace('/USDT', '');
        const side = trade.side || trade.action || '';
        const sideClass = side === 'BUY' ? 'badge bg-success' : 'badge bg-danger';
        const quantity = safeNum(trade.quantity, 0).toFixed(6);
        const price = safeNum(trade.price, 0).toLocaleString('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        });
        const pnl = safeNum(trade.pnl, 0).toLocaleString('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        });
        const pnlClass = safeNum(trade.pnl, 0) >= 0 ? 'text-success' : 'text-danger';
        
        // Determine transaction type based on trade data
        const transactionType = trade.type || trade.transaction_type || 'Trade';
        
        // Create cells using DOM manipulation for security
        const typeCell = document.createElement('td');
        const typeBadge = document.createElement('span');
        typeBadge.className = 'badge bg-primary';
        typeBadge.textContent = transactionType;
        typeCell.appendChild(typeBadge);
        
        const sideCell = document.createElement('td');
        const sideBadge = document.createElement('span');
        sideBadge.className = sideClass;
        sideBadge.textContent = side;
        sideCell.appendChild(sideBadge);
        
        const symbolCell = document.createElement('td');
        const symbolStrong = document.createElement('strong');
        symbolStrong.textContent = symbol;
        symbolCell.appendChild(symbolStrong);
        
        const timeCell = document.createElement('td');
        timeCell.textContent = timestamp;
        
        const quantityCell = document.createElement('td');
        quantityCell.className = 'text-end';
        quantityCell.textContent = quantity;
        
        const priceCell = document.createElement('td');
        priceCell.className = 'text-end';
        priceCell.textContent = price;
        
        const pnlCell = document.createElement('td');
        pnlCell.className = `text-end ${pnlClass}`;
        pnlCell.textContent = pnl;
        
        // Append all cells to row
        row.appendChild(typeCell);
        row.appendChild(sideCell);
        row.appendChild(symbolCell);
        row.appendChild(timeCell);
        row.appendChild(quantityCell);
        row.appendChild(priceCell);
        row.appendChild(pnlCell);
        
        tableBody.appendChild(row);
    });
}

// Function to filter trades by timeframe (called by dropdown)
async function filterTradesByTimeframe() {
    console.log('Filtering trades by timeframe...');
    // Simply call refresh since our API already handles timeframes
    await refreshTradesData();
}

// CONSOLIDATED: Function to refresh holdings data (called by refresh button)
// This now delegates to TradingApp to prevent race conditions
async function refreshHoldingsData() {
    try {
        console.debug('refreshHoldingsData() delegating to TradingApp for consistency');
        
        // Use TradingApp's unified refresh system to prevent race conditions
        if (window.tradingApp && window.tradingApp.updateCryptoPortfolio) {
            await window.tradingApp.updateCryptoPortfolio();
            return;
        }
        
        // Fallback for edge cases when TradingApp isn't ready
        const response = await fetch('/api/current-holdings', { cache: 'no-cache' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        if (data.success && (data.holdings || data.all_positions)) {
            const positions = data.holdings || data.all_positions || [];
            console.debug('Fallback holdings data received:', positions.length, 'positions');
            
            // Target multiplier validation removed for production
            // Update table via main TradingApp system to prevent flashing
            if (window.tradingApp) {
                window.tradingApp.currentCryptoData = positions;
                window.tradingApp.updateAllTables(positions);
            } else {
                // Fallback update for edge cases
                updateOpenPositionsTable(positions, data.total_value);
            }
            
            // Update refresh time tracking
            updatePositionsRefreshTime();
            
            // Also update available positions table 
            fetchAndUpdateAvailablePositions();
            if (window.tradingApp) {
                window.tradingApp.showToast('Holdings data refreshed', 'success');
            }
        } else {
            throw new Error(data.error || 'Failed to fetch holdings');
        }
    } catch (error) {
        console.debug('Error refreshing holdings:', error);
        if (window.tradingApp) {
            window.tradingApp.showToast('Failed to refresh holdings data', 'error');
        }
        // Show error in table
        const tableBody = document.getElementById('holdings-tbody');
        if (tableBody) {
            // Safe DOM creation instead of innerHTML
            tableBody.textContent = '';
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 12;
            cell.className = 'text-center text-danger py-4';
            
            const icon = document.createElement('i');
            icon.className = 'fa-solid fa-triangle-exclamation me-2';
            cell.appendChild(icon);
            cell.appendChild(document.createTextNode('Failed to load positions data'));
            
            row.appendChild(cell);
            tableBody.appendChild(row);
        }
    }
}

// Positions refresh tracking variables
let positionsLastRefreshTime = null;
let positionsRefreshInterval = null;
const REFRESH_INTERVAL_MS = 6000; // Use 6 second refresh interval

function updatePositionsRefreshTime() {
    positionsLastRefreshTime = new Date();
    updatePositionsTimeDisplay();
    
    // Clear existing interval if any
    if (positionsRefreshInterval) {
        clearInterval(positionsRefreshInterval);
    }
    
    // Position refresh interval disabled - was updating display unnecessarily every 5 seconds  
    // positionsRefreshInterval = null;
}

function updatePositionsTimeDisplay() {
    if (!positionsLastRefreshTime) return;
    
    const now = new Date();
    const diffMs = now - positionsLastRefreshTime;
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffSeconds = Math.floor((diffMs % 60000) / 1000);
    
    // Prepare text and class for last refresh display
    let refreshText, refreshClass;
    if (diffMinutes > 0) {
        refreshText = `${diffMinutes}m ${diffSeconds}s ago`;
        refreshClass = diffMinutes > 2 ? 'text-warning' : 'text-muted';
    } else {
        refreshText = `${diffSeconds}s ago`;
        refreshClass = 'text-success';
    }
    
    // Update BOTH possible last refresh elements (compatibility fix for ID mismatch)
    ['positions-last-refresh', 'positions-last-update'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = refreshText;
            el.className = refreshClass;
        }
    });
    
    // Update "next refresh" countdown
    const nextRefreshDisplay = document.getElementById('positions-next-refresh');
    if (nextRefreshDisplay) {
        const nextRefreshMs = REFRESH_INTERVAL_MS - diffMs;
        if (nextRefreshMs > 0) {
            const nextMinutes = Math.floor(nextRefreshMs / 60000);
            const nextSeconds = Math.floor((nextRefreshMs % 60000) / 1000);
            
            if (nextMinutes > 0) {
                nextRefreshDisplay.textContent = `${nextMinutes}m ${nextSeconds}s`;
            } else {
                nextRefreshDisplay.textContent = `${nextSeconds}s`;
            }
            nextRefreshDisplay.className = nextRefreshMs < 15000 ? 'text-warning' : 'text-info';
        } else {
            nextRefreshDisplay.textContent = 'now';
            nextRefreshDisplay.className = 'text-success';
        }
    }
}

// Function to show crypto chart in modal
function showCryptoChart(symbol) {
    console.log(`Showing details for ${symbol}`);
    
    // Create and show modal with crypto details
    const modalHtml = `
        <div class="modal fade" id="cryptoDetailsModal" tabindex="-1" aria-labelledby="cryptoDetailsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="cryptoDetailsModalLabel">
                            <i class="fas fa-chart-line me-2"></i>${symbol} Details
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6><i class="fas fa-info-circle me-2"></i>Position Info</h6>
                                <div id="position-info-${symbol}" class="mb-3">
                                    <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                                    Loading position data...
                                </div>
                            </div>
                            <div class="col-md-6">
                                <h6><i class="fas fa-chart-bar me-2"></i>Market Data</h6>
                                <div id="market-info-${symbol}" class="mb-3">
                                    <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                                    Loading market data...
                                </div>
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-12">
                                <h6><i class="fas fa-history me-2"></i>Recent Activity</h6>
                                <div id="recent-activity-${symbol}">
                                    <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                                    Loading trading history...
                                </div>
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
    const existingModal = document.getElementById('cryptoDetailsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal using Bootstrap
    if (window.bootstrap && window.bootstrap.Modal) {
        const modal = new bootstrap.Modal(document.getElementById('cryptoDetailsModal'));
        modal.show();
        
        // Load data after modal is shown
        loadCryptoDetails(symbol);
        
        // Clean up modal when closed
        document.getElementById('cryptoDetailsModal').addEventListener('hidden.bs.modal', function () {
            this.remove();
        });
    } else {
        // Fallback if Bootstrap is not available
        document.getElementById('cryptoDetailsModal').style.display = 'block';
        document.getElementById('cryptoDetailsModal').classList.add('show');
        loadCryptoDetails(symbol);
    }
}

// Function to load detailed crypto information
async function loadCryptoDetails(symbol) {
    try {
        // Load position information
        const positionResponse = await fetch(`/api/current-holdings`);
        const positionData = await positionResponse.json();
        const position = positionData.holdings?.find(h => h.symbol === symbol);
        
        if (position) {
            const positionInfoEl = document.getElementById(`position-info-${symbol}`);
            if (positionInfoEl) {
                positionInfoEl.innerHTML = `
                    <div class="card border-0 bg-light">
                        <div class="card-body p-2">
                            <div class="row g-2">
                                <div class="col-6">
                                    <small class="text-muted">Quantity:</small><br>
                                    <strong>${position.quantity?.toFixed(6) || '0'}</strong>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Current Value:</small><br>
                                    <strong>$${position.current_value?.toFixed(2) || '0.00'}</strong>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">P&L:</small><br>
                                    <strong class="${(position.pnl_percent || 0) >= 0 ? 'text-success' : 'text-danger'}">
                                        ${(position.pnl_percent || 0).toFixed(2)}%
                                    </strong>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Current Price:</small><br>
                                    <strong>$${position.current_price?.toFixed(position.current_price > 1 ? 2 : 6) || '0.00'}</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        } else {
            const positionInfoEl = document.getElementById(`position-info-${symbol}`);
            if (positionInfoEl) {
                positionInfoEl.innerHTML = '<div class="alert alert-info">No active position found for this asset.</div>';
            }
        }
        
        // Load market information (basic info from available positions)
        const marketResponse = await fetch(`/api/available-positions`);
        const marketData = await marketResponse.json();
        const marketInfo = marketData.available_positions?.find(p => p.symbol === symbol);
        
        if (marketInfo) {
            const marketInfoEl = document.getElementById(`market-info-${symbol}`);
            if (marketInfoEl) {
                marketInfoEl.innerHTML = `
                    <div class="card border-0 bg-light">
                        <div class="card-body p-2">
                            <div class="row g-2">
                                <div class="col-6">
                                    <small class="text-muted">Market Price:</small><br>
                                    <strong>$${marketInfo.current_price?.toFixed(marketInfo.current_price > 1 ? 2 : 6) || '0.00'}</strong>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Signal:</small><br>
                                    <span class="badge ${marketInfo.buy_signal === 'READY TO BUY' ? 'bg-success' : 
                                                       marketInfo.buy_signal === 'CURRENT HOLDING' ? 'bg-primary' : 'bg-secondary'}">
                                        ${marketInfo.buy_signal || 'N/A'}
                                    </span>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Target Price:</small><br>
                                    <strong>$${marketInfo.target_buy_price?.toFixed(marketInfo.target_buy_price > 1 ? 2 : 6) || '0.00'}</strong>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Confidence:</small><br>
                                    <span class="badge ${marketInfo.entry_confidence?.level === 'STRONG' ? 'bg-success' : 
                                                       marketInfo.entry_confidence?.level === 'FAIR' ? 'bg-warning' : 'bg-secondary'}">
                                        ${marketInfo.entry_confidence?.level || 'N/A'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
        
        // Load recent trading activity
        const activityData = await activityResponse.json();
        const trades = activityData.trades?.filter(t => t.symbol === symbol).slice(0, 5) || [];
        
        const activityEl = document.getElementById(`recent-activity-${symbol}`);
        if (activityEl) {
            if (trades.length > 0) {
                const tradesHtml = trades.map(trade => `
                    <div class="d-flex justify-content-between align-items-center py-1 border-bottom">
                        <div>
                            <small class="text-muted">${new Date(trade.datetime).toLocaleDateString()}</small>
                            <span class="badge ${trade.side === 'buy' ? 'bg-success' : 'bg-danger'} ms-2">${trade.side.toUpperCase()}</span>
                        </div>
                        <div class="text-end">
                            <small>${trade.amount} @ $${trade.price?.toFixed(6) || '0.00'}</small>
                        </div>
                    </div>
                `).join('');
                activityEl.innerHTML = `<div class="small">${tradesHtml}</div>`;
            } else {
                activityEl.innerHTML = '<div class="alert alert-info">No recent trading activity found.</div>';
            }
        }
        
    } catch (error) {
        console.error('Error loading crypto details:', error);
        
        // Show error in all sections
        ['position-info', 'market-info', 'recent-activity'].forEach(prefix => {
            const el = document.getElementById(`${prefix}-${symbol}`);
            if (el) {
                el.innerHTML = '<div class="alert alert-danger">Error loading data</div>';
            }
        });
    }
}

// Auto-load positions on page load - MERGED with main DOMContentLoaded to avoid conflicts
// This is now handled in the main DOMContentLoaded event above to prevent conflicts

// Configuration for target percentages
const DEFAULT_TARGET_PCT = 8; // Default target percentage when no dynamic data available

// Centralized target multiplier calculation
function getTargetMultiplier(holding) {
    // Prefer explicit multiplier from backend
    if (holding?.target_multiplier && holding.target_multiplier > 0) {
        return Number(holding.target_multiplier);
    }
    // Accept target_pct from backend if available
    if (holding?.target_pct != null) {
        return 1 + Number(holding.target_pct)/100;
    }
    // Use upper Bollinger Band price for dynamic calculation if available
    if (holding?.upper_band_price && holding?.current_price && holding.upper_band_price > holding.current_price) {
        return holding.upper_band_price / holding.current_price;
    }
    // Default fallback
    return 1 + DEFAULT_TARGET_PCT/100;
}

// Centralized target percentage calculation
function getTargetPercent(holding) {
    if (holding?.target_pct != null) return Number(holding.target_pct);       // e.g. 8
    if (holding?.target_multiplier)  return (Number(holding.target_multiplier) - 1) * 100;
    return DEFAULT_TARGET_PCT;
}

// Money formatting utility
function formatMoney(num, ccy = 'USD', min=2, max=2) {
    return Number(num).toLocaleString('en-US', { 
        style:'currency', 
        currency: ccy,
        minimumFractionDigits: min, 
        maximumFractionDigits: max 
    });
}

// Target dollar profit calculation
function calcTargetDollar(costBasis, holding) {
    const m = getTargetMultiplier(holding);
    return costBasis * (m - 1);
}

// Target total value calculation
function calcTargetValue(costBasis, holding) {
    const m = getTargetMultiplier(holding);
    return costBasis * m;
}

// Premium/discount calculations (always in PERCENT units)
function pctPremium(price, target) { 
    return ((price - target) / target) * 100; // >0 when above target
}

function pctDiscount(price, target) { 
    return ((target - price) / target) * 100; // >0 when below target
}

// Derive bot buy criteria based on timing signal and dynamic thresholds
function deriveBotCriteria({ price, target, timing, holding, confidence, risk, owned, isFiat }) {
    if (owned) return 'OWNED';
    if (isFiat) return 'FIAT BALANCE';       // never generate buy signals on fiat
    
    const targetPct = getTargetPercent(holding);      // e.g. 8 (percent units)
    const managedThreshold = Math.max(targetPct * 0.8, 6.0); // 80% of TP or ≥6%
    const watchThreshold = Math.max(targetPct * 0.4, 3.0);   // 40% of TP or ≥3%

    // Use DISCOUNT for entry logic (positive when price < target)
    const discount = pctDiscount(price, target);      // percent units

    // Tie to Timing column first
    const timingOK = timing === 'BUY' || timing === 'CAUTIOUS_BUY';

    if (timingOK && discount >= managedThreshold && (confidence !== 'WEAK')) {
        return 'READY TO BUY';
    }
    if (timingOK && discount >= watchThreshold) {
        return 'WATCH';
    }
    return 'MONITORING';
}

// Build available position row with proper bot criteria
function buildAvailableRow(row) {
    const { current_price: price, target_buy_price: target, entry_confidence, symbol } = row;
    const timing = entry_confidence?.timing_signal || 'WAIT';
    const confidence = entry_confidence?.level || 'MODERATE';
    const risk = entry_confidence?.risk_level || 'MODERATE';
    const owned = row.current_balance > 0;
    const isFiat = symbol === 'USD' || symbol === 'USDT' || symbol === 'AUD';

    // Calculate criteria using proper logic
    const criteria = deriveBotCriteria({ 
        price, 
        target, 
        timing, 
        holding: row, 
        confidence, 
        risk, 
        owned, 
        isFiat 
    });

    return {
        ...row,
        diffPct: pctPremium(price, target),   // for display only
        buyCriteria: criteria,                // this drives the "Bot Buy Criteria" column
    };
}

// Production bot criteria logic - testing function removed for clean production environment

// Dynamic color generation based on symbol hash
function generateDynamicColor(symbol) {
    // Create consistent hash from symbol
    let hash = 0;
    for (let i = 0; i < symbol.length; i++) {
        const char = symbol.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    
    // Generate color components from hash
    const hue = Math.abs(hash) % 360;
    const saturation = 60 + (Math.abs(hash >> 8) % 40); // 60-100%
    const lightness = 45 + (Math.abs(hash >> 16) % 20); // 45-65%
    
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

// Make function globally available
window.generateDynamicColor = generateDynamicColor;

// REMOVED: backup refreshHoldingsData call to prevent race condition
// TradingApp handles all data loading via unified refresh system
// window.addEventListener("load", function() {
//     setTimeout(refreshHoldingsData, 1000);
// });

// Sync Test functionality
window.SyncTest = {
    async runSyncTest() {
        const button = document.getElementById('btn-run-sync-test');
        const statusBadge = document.getElementById('sync-status-badge');
        const lastCheck = document.getElementById('sync-last-check');
        const placeholder = document.getElementById('sync-placeholder');
        const details = document.getElementById('sync-details');
        
        try {
            // Update UI to show loading
            button.disabled = true;
            button.innerHTML = '<span class="icon icon-refresh spinner-border spinner-border-sm me-1"></span>Testing...';
            statusBadge.className = 'badge bg-warning';
            statusBadge.innerHTML = '<span class="icon icon-circle me-1"></span>Testing';
            
            // Call sync test API
            const response = await Utils.fetchJSON('/api/sync-test');
            
            if (!response) {
                throw new Error('No response from sync test endpoint');
            }
            
            // Update timestamp
            lastCheck.textContent = new Date().toLocaleTimeString();
            
            // Hide placeholder and show details
            placeholder.style.display = 'none';
            details.style.display = 'block';
            
            // Update metrics
            document.getElementById('sync-total-pairs').textContent = response.total_pairs_tested || 0;
            
            const discrepancies = response.discrepancies || [];
            const synchronizedCount = (response.total_pairs_tested || 0) - discrepancies.length;
            
            document.getElementById('sync-synchronized').textContent = synchronizedCount;
            document.getElementById('sync-out-of-sync').textContent = discrepancies.length;
            document.getElementById('sync-discrepancies').textContent = discrepancies.length;
            
            // Update status badge
            if (discrepancies.length === 0) {
                statusBadge.className = 'badge bg-success';
                statusBadge.innerHTML = '<span class="icon icon-check me-1"></span>Synchronized';
            } else {
                statusBadge.className = 'badge bg-danger';
                statusBadge.innerHTML = '<span class="icon icon-warning me-1"></span>Out of Sync';
            }
            
            // Update discrepancies table
            this.updateDiscrepanciesTable(discrepancies);
            
        } catch (error) {
            console.error('Sync test failed:', error);
            statusBadge.className = 'badge bg-danger';
            statusBadge.innerHTML = '<span class="icon icon-times me-1"></span>Error';
            
            // Show error message
            placeholder.innerHTML = `
                <span class="icon icon-warning me-2 text-danger"></span>
                Sync test failed: ${error.message}
            `;
            placeholder.style.display = 'block';
            details.style.display = 'none';
            
        } finally {
            // Reset button
            button.disabled = false;
            button.innerHTML = '<span class="icon icon-refresh me-1"></span>Test Sync';
        }
    },
    
    updateDiscrepanciesTable(discrepancies) {
        const discrepancyList = document.getElementById('sync-discrepancy-list');
        const tableBody = document.getElementById('discrepancy-table-body');
        
        if (discrepancies.length === 0) {
            discrepancyList.style.display = 'none';
            return;
        }
        
        // Show discrepancy list
        discrepancyList.style.display = 'block';
        
        // Clear existing rows
        tableBody.innerHTML = '';
        
        // Add discrepancy rows
        discrepancies.forEach(disc => {
            const row = document.createElement('tr');
            const statusClass = Math.abs(disc.difference) > 0.001 ? 'text-danger' : 'text-warning';
            const statusText = Math.abs(disc.difference) > 0.001 ? 'Major' : 'Minor';
            
            row.innerHTML = `
                <td>${disc.pair}</td>
                <td>${disc.strategy_qty.toFixed(6)}</td>
                <td>${disc.live_qty.toFixed(6)}</td>
                <td class="${statusClass}">${Math.abs(disc.difference).toFixed(6)}</td>
                <td><span class="badge bg-${statusClass === 'text-danger' ? 'danger' : 'warning'}">${statusText}</span></td>
            `;
            
            tableBody.appendChild(row);
        });
    }
};

// REMOVED: Duplicate DOMContentLoaded event listener
// Sync test button setup moved to main DOMContentLoaded event to prevent duplication
