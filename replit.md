# Algorithmic Trading System

## Overview

This Python-based algorithmic trading system is designed for cryptocurrency markets, offering backtesting, paper trading, and live trading capabilities. Its purpose is to automate trading strategies, manage risk, and provide a web-based dashboard for real-time monitoring and control. The system integrates a Bollinger Bands mean reversion strategy and comprehensive risk management controls. It includes a robust cryptocurrency portfolio system with realistic price simulation and tax compliance features for Australian reporting (ATO).

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Trading Framework
A modular architecture supports CLI operations via `main.py` and a web interface via Flask (`web_interface.py`). It includes `BacktestEngine`, `PaperTrader`, and `LiveTrader` classes for different trading modes.

### Deployment Configuration (Updated: 2025-08-14)
- **Primary Entry Point**: `app.py` - Fast-boot Flask application with background initialization for ultra-fast deployment
- **WSGI Support**: `wsgi.py` - Enhanced production WSGI configuration with Flask environment settings  
- **Development Entry**: `main.py` - CLI-based entry with multiple modes
- **Port Configuration**: Uses PORT environment variable (defaults to 5000, maps to 80 for deployment)
- **Fast-Boot Architecture**: 
  - **Immediate Port Opening**: Flask server starts in <1 second with minimal initialization
  - **Background Warmup**: Trading system initializes in background thread with 8-second timeout
  - **Circuit Breaker Pattern**: Loading skeleton UI with automatic polling for readiness
  - **Persistent Cache**: OHLCV data cached to `warmup_cache.parquet` for instant subsequent boots
  - **Exponential Backoff**: API calls use retry logic with exponential backoff for reliability
- **Enhanced Health Endpoints**: 
  - `/` - Smart loading skeleton that polls `/ready` and auto-refreshes when system ready
  - `/health` - Instant health check responding immediately after Flask startup
  - `/ready` - Detailed readiness probe returning 200 only when warmup complete
  - `/api/warmup` - Real-time warmup status with elapsed time and loaded symbols
- **Hardened Configuration (Environment Variables)**:
  - `MAX_STARTUP_SYMBOLS=5` - Reduced symbol count for faster boot (was 10)
  - `STARTUP_OHLCV_LIMIT=150` - Reduced OHLCV bars per symbol (was 300)
  - `STARTUP_TIMEOUT_SEC=8` - Aggressive timeout to prevent deployment timeouts
  - `WARMUP_CHUNK_SIZE=2` - Smaller API request batches for rate limit compliance
- **Deployment Files**: `Procfile`, `deployment.json` with autoscaling configuration, and gunicorn settings
- **Production Server**: Gunicorn configuration optimized for Replit deployment with proper worker settings
- **Port Conflict Resolution**: Configured for single port mapping (5000→80) to resolve deployment conflicts  
- **Version Tracking**: Version numbering system with `version.py` displaying current version (v2.1.0) in footer
- **Deployment Ready**: All tables functioning, no JavaScript errors, complete 103-asset portfolio system

### Strategy System
A plugin-based system using abstract base classes (`BaseStrategy`) allows for flexible strategy implementation, such as `BollingerBandsStrategy`. Strategies generate `Signal` objects with trade actions and risk parameters.

### Data Management
A two-tier caching system uses SQLite to store raw market data fetched via exchange adapters. `DataManager` and `DataCache` manage data flow, caching, and persistence to minimize API calls.

### Exchange Integration
An adapter pattern with `BaseExchange` provides a unified interface for various cryptocurrency exchanges, including `OKXAdapter` for demo trading and `KrakenAdapter` for live trading, handling authentication, rate limiting, and data normalization.

### Risk Management
The `RiskManager` enforces multiple safety layers, including portfolio-level limits, position sizing, daily loss limits, and emergency halts, performing checks before every trade.

### Web Interface
A Flask-based web interface provides real-time monitoring, portfolio visualization with Chart.js, and user interaction capabilities. It features a streamlined three-dashboard system (Main Portfolio, Performance Dashboard, Current Holdings), professional news ticker with breaking crypto market updates, and a professional footer. ATO tax export functionality is prominent. Rate limiting ensures compliance with CoinGecko API limits (6-second update intervals).

#### Production-Ready Table System (Updated: 2025-08-16)
- **Complete Table Functionality**: All tables now loading correctly with 103 cryptocurrency assets
- **Main Dashboard Table**: Fixed 13-column structure mismatch and undefined variable errors
- **Holdings Page Table**: Fully operational "Current Market Positions - What You Actually Own" view
- **Exception-Safe Operations**: Comprehensive null-safe DOM operations and browser compatibility
- **Error Resolution**: Fixed JavaScript undefined variables (`pnl`, `pnlPercent`) in updateHoldingsTable
- **Cross-Browser Support**: Replaced `:has()` selector with universal `.closest()` method

### Current Holdings Page Enhancement (Updated: 2025-08-16)
- **Target Sell Price Column**: Changed "Avg Buy Price" to "Target Sell Price" in Current Holdings table
- **Dynamic Price Display**: Shows calculated target sell price (current price * 1.1) when no specific target is set
- **Enhanced Trading Strategy**: Holdings page now displays actionable sell targets rather than historical buy prices

### Bot Pricing Formula Integration (Updated: 2025-08-17)
- **Position Sizing**: All trading signals now use bot.py risk-based position sizing formulas
- **Entry Price Calculation**: Bot.py slippage formulas (0.05%) applied to all buy/sell orders
- **Risk Management**: Exact bot.py calculations for stop loss (1%) and take profit (2%) levels  
- **Formula Implementation**: `risk_per_unit = max(1e-12, px * P.sl)`, `qty = dollars / risk_per_unit`
- **Portfolio Risk**: Consistent 1% equity risk per trade across all strategies
- **Signal Generation**: BollingerBandsStrategy integrated with BotPricingCalculator for precise calculations
- **Trading Consistency**: Eliminates discrepancies between strategy signals and actual trade execution

### Complete Automated Trading Cycle (Updated: 2025-08-17)
- **Automatic Take Profit**: 2% profit threshold triggers sell orders for profitable positions using bot pricing
- **Intelligent Reinvestment**: Profits from sales automatically reinvested in oversold positions (down 0.04%+)
- **Contrarian Strategy**: System buys oversold assets and sells profitable ones for portfolio rebalancing
- **Smart Position Sizing**: Bot pricing formulas calculate exact entry/exit prices with slippage protection
- **Real Exchange Execution**: All trades execute through simulated OKX exchange with position synchronization
- **Complete Automation**: Single button triggers full trading cycle from profit-taking to reinvestment
- **Risk-Based Selection**: Oversold candidates ranked by loss percentage for optimal reinvestment targeting
- **Portfolio Rebalancing**: System continuously moves capital from winners to losers for mean reversion strategy
- **Position Synchronization**: Holdings properly reflect sold positions with `has_position = false` status
- **Trade Volume**: Latest cycle executed 46 sell orders generating $23.49 profit, reinvesting $23.54 in 5 buy orders

### Enhanced Recent Trades System (Updated: 2025-08-15)
- **Complete Trade Display**: Shows ALL trades without artificial limits (expanded from 10 to 50+ cryptocurrencies)
- **Unique Trade Identifiers**: Sequential trade numbers (#1, #2, #3...) for easy reference and tracking
- **Advanced Filtering System**: Time-based filters (24hrs, 3 days, 7 days, 1 month, 6 months, 1 year), symbol search, action filters (BUY/SELL), and P&L analysis
- **Professional Table Structure**: 7-column layout with Trade #, Time, Symbol, Action, Size, Price, and P&L
- **Real-time Updates**: Instant filtering and sorting with persistent filter states
- **Reset Compatibility**: Complete reset functionality that properly clears all trade history

### OKX Exchange Integration (Updated: 2025-08-17)
- **Primary Data Source**: Portfolio calculations now use simulated OKX exchange as the foundation for all operations
- **Pre-loaded Portfolio**: All 103 cryptocurrencies populate automatically without requiring trading initialization
- **Status Integration**: Replaced CoinGecko API status with OKX API status in interface
- **Clear Simulation Indicators**: Status displays show "Simulated" vs "Live" connection type for trading mode clarity
- **Exchange Status**: Connection type clearly states "OKX Exchange - Paper Trading" with simulation mode indication
- **Portfolio Service**: PortfolioService class manages all cryptocurrency data through simulated OKX exchange interface
- **Instant Portfolio Loading**: System displays complete portfolio immediately on dashboard load

#### Connection Management & Monitoring (Updated: 2025-08-14)
- **Intelligent Uptime Tracking**: System uptime counter tracks only connected time, automatically resetting on connection loss and restarting fresh on reconnection
- **Connection-Aware Trading Controls**: Trading countdown stops during connection outages, automatically resumes when reconnected, and trading buttons validate connection status before execution
- **Enhanced Status Display**: Connection status with reconnection countdown timers (30-second intervals) and visual feedback
- **Trading Countdown Relocation**: Moved from navbar to Portfolio Overview section for better contextual relevance
- **Robust Error Handling**: Connection loss displays "Connection Lost" status with automatic recovery mechanisms
- **Trading Validation**: All trading functions now prevent execution during API connection outages to ensure data integrity
- **News Interface Removal**: Breaking news ticker completely removed for cleaner, distraction-free interface

### Master Portfolio Assets (Updated: 2025-08-16)
- **Hardcoded Asset Universe**: Definitive list of 103 cryptocurrencies stored in `src/data/portfolio_assets.py`
- **Consistent Data Loading**: Eliminates API mapping uncertainties by using predetermined asset list
- **Portfolio Categories**: 8 distinct categories covering Top Market Cap (25), DeFi (15), Gaming/NFT (15), Layer 2 (12), Meme (10), Exchange Tokens (8), Privacy (8), Enterprise (10)
- **Investment Structure**: Each asset represents exactly $10 initial investment when trading begins
- **Future Compatibility**: Hardcoded list can be matched with live trading APIs during production deployment

### Table Rendering System (Completed: 2025-08-16)
- **Separated Table Bodies**: Each dashboard view targets dedicated table elements to prevent data conflicts
  - Main Dashboard: `updateCryptoTable()` → `#crypto-tracked-table`
  - Performance Dashboard: `updatePerformancePageTable()` → `#performance-page-table-body`
  - Current Holdings: `updateHoldingsTable()` → `#positions-table-body`
- **DOM ID Collision Resolution**: Fixed performance table conflicts with distinct tbody IDs and unified update functions
- **Array Mutation Protection**: Charts use `[...holdings].sort()` to prevent table reordering during chart updates
- **Currency Conversion**: All price displays use consistent `formatCurrency()` method with exchange rate conversion
- **Error Handling**: Proper empty state management and loading progress indicators with correct table targeting
- **Data Integrity**: Eliminated orphaned table references and incorrect DOM selectors
- **Exception Safety**: Added `num(v, d=0)` and `fmtFixed(v, p)` utility functions to protect all `.toFixed()` calls
- **Column Accuracy**: Correct colspan counts matching exact header counts (13, 10, 11 columns)
- **Code Quality**: Eliminated duplicate variable declarations and redundant DOM manipulation
- **Performance Optimization**: Streamlined table rendering with efficient innerHTML approach

### Technical Indicators
The `TechnicalIndicators` class provides vectorized calculations for indicators like Bollinger Bands and ATR, utilizing pandas for efficient time series data processing.

### Database Layer
The `DatabaseManager` uses SQLite for persistent storage of trades, portfolio history, and system state, ensuring proper connection handling and transaction management.

### Algorithmic Optimization
The system incorporates advanced algorithmic optimization for buy/sell decisions, including multi-timeframe momentum analysis, adaptive position sizing, enhanced risk-reward enforcement, progressive trailing stops, and market volatility regime detection. It also integrates statistical arbitrage techniques like rolling beta regression, EWMA statistics, and Fractional Kelly Criterion for position sizing.

## External Dependencies

### Market Data & Trading APIs
- **CCXT Library**: Unified exchange interface.
- **OKX Exchange**: Demo trading environment.
- **Kraken Exchange**: Live trading platform.
- **CoinGecko API**: Live cryptocurrency prices with rate limiting (10 requests/minute).
- **Crypto News Integration**: Real-time market news ticker with automatic updates.

### Data Processing & Analysis
- **Pandas**: Time series data manipulation.
- **NumPy**: Numerical computations.
- **SQLite**: Local database for caching and persistence.

### Web Interface & Visualization
- **Flask**: Web framework.
- **Chart.js**: Client-side charting.
- **Bootstrap**: Frontend CSS framework.
- **Font Awesome**: Icon library.

### Configuration & Logging
- **ConfigParser**: Configuration management.
- **Python Logging**: System-wide logging.
- **Environment Variables**: Secure credential management.