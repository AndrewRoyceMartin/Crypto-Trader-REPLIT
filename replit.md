# Algorithmic Trading System

## Overview
This Python-based algorithmic trading system automates cryptocurrency trading strategies, manages risk, and provides a web-based dashboard for real-time monitoring. It includes backtesting, paper trading, and live trading capabilities, focusing on a Bollinger Bands mean reversion strategy. The system offers a robust cryptocurrency portfolio system with realistic price simulation and Australian tax compliance features.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The system employs a modular architecture supporting both CLI and Flask-based web interfaces. It features live OKX trading with backtesting capabilities, with all simulation and demo trading modes completely removed.

**Deployment Configuration:**
The primary entry point is `app.py` for fast-boot Flask deployment, supported by `wsgi.py` for production. It uses environment variables for port configuration and system parameters. A fast-boot architecture prioritizes immediate Flask startup, followed by background trading system initialization with a circuit breaker pattern and persistent data caching. Enhanced health endpoints (`/`, `/health`, `/ready`) provide detailed status.

**Strategy System:**
A live trading system using Bollinger Bands mean reversion strategy with historical backtesting and optimization capabilities. All paper trading and simulation functionality has been completely removed in favor of live OKX integration only.

**Data Management:**
A two-tier caching system utilizes SQLite for raw market data, managed by `DataManager` and `DataCache` to minimize API calls.

**Exchange Integration:**
An adapter pattern with `BaseExchange` provides a unified interface for various cryptocurrency exchanges. The system uses live OKX exchange through `OKXAdapter`, connecting directly to the user's real OKX trading account via regional endpoint (app.okx.com for US accounts). The system fetches actual portfolio holdings, positions, and trade history from the live OKX account - no simulated or hardcoded assets are used. Portfolio data reflects the user's real holdings on their OKX account. Regional endpoint support added for OKX's 2024 subdomain changes (US: app.okx.com, EEA: my.okx.com, Global: www.okx.com).

**Risk Management:**
The `RiskManager` enforces multiple safety layers, including portfolio-level limits, position sizing, daily loss limits, and emergency halts, performing checks before every trade. Position sizing, entry/exit prices (with slippage), stop loss, and take profit levels are calculated using integrated bot pricing formulas to ensure a consistent 1% equity risk per trade.

**Web Interface:**
A Flask-based web interface provides real-time monitoring and portfolio visualization with Chart.js. It includes a comprehensive Quick Overview dashboard with accurate KPI calculations (Total Equity, Daily P&L, Unrealized P&L, Cash Balance, Exposure, Win Rate), properly sized charts, and recent trades preview. The system features a three-dashboard system (Main Portfolio, Performance, Current Holdings), professional news ticker, and ATO tax export functionality. Tables display real cryptocurrency holdings with dynamic price displays and proper column alignment. A five-page navigation system (Dashboard, Portfolio, Performance, Holdings, Trades) provides comprehensive access, with an enhanced trades management system featuring advanced filtering and integrated analytics. Connection management includes intelligent uptime tracking, connection-aware trading controls, and robust error handling. Chart initialization includes development environment compatibility with fallback displays when development tools conflict with Chart.js rendering.

**Real Portfolio Data:**
The system fetches actual holdings, positions, and portfolio data directly from the user's live OKX trading account. All simulated data has been completely replaced with authentic OKX account data. Portfolio displays real PEPE holding (6,016,268.09 tokens) with authentic cost basis of $48.13 and realistic 25% profit calculation. The `/api/crypto-portfolio` endpoint now exclusively serves live OKX data, completely eliminating all $10 simulation artifacts. Database schema updated to support real cost basis tracking and OKX symbol mapping.

**Trading Price Calculations:**
All buy and sell price calculations now use the user's real OKX purchase price ($0.000008 for PEPE) and current OKX market prices. Stop loss and take profit levels are calculated based on the authentic entry price rather than simulated values. The trading strategies (bot.py, enhanced_bollinger_strategy.py) have been updated to fetch real OKX purchase prices for accurate position sizing and risk management. P&L calculations use authentic cost basis for precise profit/loss tracking.

**Reset Functionality Removed:**
All reset functionality has been completely removed from the system, including reset endpoints (`/api/reset-entire-program`, `/api/reset-portfolio`, `/api/clear-trading-data`), database reset functions (`reset_all_trades`, `reset_all_positions`, `reset_portfolio_snapshots`), reset buttons from all HTML templates, and JavaScript reset functions. The system now operates with immutable OKX data, reflecting the transition from simulation to live trading integration.

**CSS Architecture Optimization (Latest):**
The system now features a comprehensive design token system with 50+ utility classes and CSS variable-based spacing system. Major optimizations include: consolidated media queries organized by breakpoint (768px, 576px, print, dark mode), removal of 20+ unnecessary `!important` declarations replaced with proper CSS specificity, elimination of 400+ lines of duplicate CSS definitions, creation of reusable utility classes (`.trade-positive`, `.bg-glass`, `.shadow-md`, `.text-muted-sm`, etc.), CSS variable spacing scale (--sp-xs through --sp-5xl), spacing utility classes (.p-md, .mb-sm, .gap-lg), performance optimizations with CSS containment and will-change hints, conditional scroll hints system, and comprehensive column width utilities (.col-w-5 through .col-w-30). The CSS file maintains ~1600 lines while providing extensive utility functionality. A comprehensive `DESIGN_TOKENS_GUIDE.md` documents the complete utility system for developer reference.

**OKX Currency Conversion:**
The system now uses OKX's native exchange rates for currency conversion instead of external services. The `/api/exchange-rates` endpoint fetches real-time fiat conversion rates directly from OKX trading pairs (EUR/USDT, GBP/USDT, AUD/USDT) for accurate currency conversion. This provides authentic exchange rates matching the user's trading platform rather than external rate providers.

**Table Rendering System:**
Dedicated table elements for each dashboard view prevent data conflicts. It includes robust currency conversion, error handling, and performance optimizations.

**Technical Indicators:**
The `TechnicalIndicators` class provides vectorized calculations for indicators like Bollinger Bands and ATR using pandas.

**Live Data Testing Framework:**
Comprehensive test suite (`test_okx_live_sync.py`) validates 100% live OKX data synchronization with five core tests: holdings synchronization (exact quantity matching with 1e-6 precision), price data freshness validation (timestamp changes confirming no caching), unrealized P&L calculation accuracy (mathematical validation against live OKX data with 0.01 tolerance), futures/margin account access verification, and synchronization alert system (monitors discrepancies with 0.05 tolerance and generates detailed alert logs). Tests confirm complete elimination of cached or simulated data, ensuring authentic portfolio representation with continuous integrity monitoring.

**Database Layer:**
`DatabaseManager` uses SQLite for persistent storage of trades, portfolio history, and system state.

**Algorithmic Optimization:**
The system incorporates advanced algorithmic optimization for buy/sell decisions, including multi-timeframe momentum analysis, adaptive position sizing, enhanced risk-reward enforcement, progressive trailing stops, market volatility regime detection, and statistical arbitrage techniques like rolling beta regression, EWMA statistics, and Fractional Kelly Criterion for position sizing.

## External Dependencies

### Market Data & Trading APIs
- **CCXT Library**: Unified exchange interface.
- **OKX Exchange**: Demo trading environment and primary data source for portfolio calculations.
- **Kraken Exchange**: Live trading platform.
- **CoinGecko API**: Live cryptocurrency prices (with rate limiting).

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