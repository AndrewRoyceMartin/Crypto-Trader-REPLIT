# Algorithmic Trading System

## Overview
This Python-based algorithmic trading system automates cryptocurrency trading strategies, manages risk, and provides a web-based dashboard for real-time monitoring. It features live trading capabilities, focusing on an Enhanced Bollinger Bands mean reversion strategy. The system integrates directly with the user's live OKX trading account for authentic portfolio data and trading operations, aiming to provide a robust and compliant trading solution with a business vision to provide a secure and reliable automated trading solution for cryptocurrency enthusiasts.

## User Preferences
Preferred communication style: Simple, everyday language.
Trading preferences: Live trading enabled with comprehensive safety confirmations.
Rebuy mechanism: Universal $100 maximum purchase limit for all cryptocurrencies after sell/crash exit.

## System Architecture
The system utilizes a modular Flask-based web interface for live OKX trading, streamlined into a single-page dashboard application.

**Core Components & Features:**
-   **Main Application:** `app.py` serves as the Flask entry point.
-   **Web Interface:** A single-page dashboard (`unified_dashboard.html`) with minimal CSS styling (`style.css`) and JavaScript functionality (`app_clean.js`).
-   **Strategy:** Exclusively uses an Enhanced Bollinger Bands strategy with advanced crash protection, dynamic risk management, rebuy mechanisms, and peak tracking, tailored for live OKX integration. The buy-back algorithm uses an adaptive approach: 3% below exit price for patient entries, 2% below current price for moderate drops (4%+), and 1% below current for significant drops (8%+), including time-based adjustments.
-   **Data Management:** A two-tier caching system uses SQLite for raw market data to minimize API calls.
-   **Exchange Integration:** An `OKXAdapter` provides a unified interface for live OKX exchange, connecting directly to the user's real OKX trading account for portfolio data and trading operations. Centralized OKX API functions ensure consistent native API integration. A dedicated production-safe OKX native client (`src/utils/okx_native.py`) is used for improved performance and reliability.
-   **Risk Management:** The `RiskManager` enforces multiple safety layers, including portfolio-level limits, position sizing, daily loss limits, and emergency halts.
-   **Web Interface Design:** A Flask-based web interface offers real-time monitoring and portfolio visualization with Chart.js, featuring a unified single-page dashboard consolidating all functionality. It includes accurate KPI calculations, dynamic price displays, ATO tax export functionality, and professional visual design with unified card styling.
-   **Trading Price Calculations:** All buy and sell price calculations use the user's real OKX purchase price and current OKX market prices, prioritizing OKX pre-calculated fields for trade values and P&L.
-   **CSS Architecture:** Minimal trading UI design with modern design tokens, CSS variable-based spacing, a grayscale-first approach, automatic dark mode support, and mobile-responsive navigation. Colors are used strategically for financial information (green for profit, red for loss, orange for warnings). FontAwesome 6.4.0 is integrated.
-   **Currency Conversion:** Uses OKX's native exchange rates for real-time fiat conversion.
-   **Enhanced OKX Adapter:** Robust trade retrieval, improved error handling with retry logic, duplicate prevention, comprehensive data validation, and optimized balance retrieval.
-   **Production-Safe Testing:** The `/api/test-sync-data` endpoint is secured with production guards, using direct service function calls.
-   **Optimized Warmup System:** Background warmup focuses on connectivity testing and market validation using a simple OKX connectivity check.
-   **UTC-Aware DateTime Standardization:** All datetime operations use UTC-aware timestamps for consistency.
-   **Authentication Protection:** Mutating endpoints are protected by an `@require_admin` decorator using a shared secret authentication (`ADMIN_TOKEN`).
-   **Exchange Instance Optimization:** Uses a singleton exchange instance to prevent `load_markets()` churn, improving performance.
-   **Security Headers:** Updated security headers for modern best practices, including HSTS and a comprehensive Content Security Policy.
-   **Database Layer:** `DatabaseManager` uses SQLite for persistent storage of trades, portfolio history, and system state.
-   **Algorithmic Optimization:** Incorporates multi-timeframe momentum analysis, adaptive position sizing, enhanced risk-reward enforcement, progressive trailing stops, market volatility regime detection, and statistical arbitrage techniques.
-   **Live Data & Strategy P&L Testing Frameworks:** Comprehensive test suites validate live OKX data synchronization and the mathematical accuracy of P&L calculations.
-   **Optimized Performance Endpoints:** `/api/best-performer` and `/api/worst-performer` are rewritten using the OKX native client for streamlined calculations.
-   **Enhanced Current Holdings Endpoint:** `/api/current-holdings` uses a hybrid approach combining portfolio service reliability and native OKX price updates.
-   **Native OKX Equity Curve Endpoint:** `/api/equity-curve` uses the native OKX client with an intelligent fallback strategy (account bills + historical candles, or portfolio service data).
-   **Optimized Heavy Endpoints:** `/api/equity-curve`, `/api/drawdown-analysis`, and `/api/performance-analytics` are rebuilt using the OKXNative client to eliminate duplicate HMAC signing and CCXT dependencies.
-   **UI Improvements:** Includes a countdown timer for data refresh, refined P&L card display, and a redesigned sync test page with HTML format and tooltips.
-   **Open Positions Table Optimization:** Optimized layout for better page fitting with responsive CSS rules.
-   **Code Quality:** Comprehensive review and fix of all warnings and errors in `app.py`, including type compatibility, potential None objects, and missing parameters.
-   **Phase 2: Signal Logging System:** Implemented comprehensive CSV-based signal logging (`logger/signal_logger.py`) that captures every 6-factor buy prediction with 11 structured fields for ML/backtesting analysis.
-   **Phase 3: OKX Trade History Module:** Created audit-proof trade analysis system (`okx/trade_history.py`) that pulls actual executed trades from OKX's `/api/v5/trade/fills` endpoint, providing real performance data vs theoretical signals with comprehensive analytics including P&L tracking, trading patterns, and fee analysis.
-   **Service Layer Architecture:** Extracted business logic into dedicated service classes (`PortfolioBusinessService`, `MarketDataService`, `TradingBusinessService`, `AuthenticationService`) with clean dependency injection and separation of concerns.
-   **State Management Pattern:** Implemented centralized state management with thread-safe operations, observer pattern, type safety, and backward compatibility through migration adapters. Features persistent state storage and comprehensive change notifications.
-   **Missing API Endpoints Fix:** Implemented `/api/portfolio-analytics`, `/api/asset-allocation`, and `/api/portfolio-history` to resolve console 404 errors.
-   **Complete OKX Market Coverage:** Displays all 280+ active OKX trading pairs instead of just major cryptocurrencies, maximizing trading opportunities across the entire OKX ecosystem.
-   **Stable Target Price System:** Implements locked target buy prices that prevent exponential recalculation, ensuring orders can actually be executed. Target prices lock for 24 hours and only recalculate if market drops >5% from original price.
-   **Target Price Manager:** SQLite-based persistence for target prices with tier-based discounting (Large cap: 3-8%, Mid cap: 5-12%, Gaming/Meta: 8-15%, Meme coins: 10-20%).
-   **Centralized Exchange Access:** A `get_reusable_exchange()` function prioritizes using the existing portfolio service exchange instance to eliminate redundant re-authentication and market loading calls per request, improving performance and reliability.
-   **Environment-Dependent CSP:** Content Security Policy headers are dynamically configured for development vs production environments, allowing localhost connections for HMR during development while maintaining strict security in production.
-   **Thread-Safe State Management:** All shared state operations use centralized thread-safe helpers (`_set_warmup()`, `_set_bot_state()`, `_get_warmup_done()`, `_get_warmup_error()`) with RLock protection to prevent race conditions and ensure data consistency across concurrent requests.
-   **Code Quality Enhancement (August 2025):** Comprehensive removal of all Recent Trades UI functionality to establish a clean codebase foundation. Removed backend variables, frontend cache references, and template elements while preserving core trading and portfolio functionality.

## External Dependencies

### Market Data & Trading APIs
-   **CCXT Library**: Unified exchange interface.
-   **OKX Exchange**: Primary data source and live trading platform.

### Data Processing & Analysis
-   **Pandas**: Time series data manipulation.
-   **NumPy**: Numerical computations.
-   **SQLite**: Local database for caching and persistence.

### Web Interface & Visualization
-   **Flask**: Web framework.
-   **Chart.js**: Client-side charting.
-   **Bootstrap**: Frontend CSS framework.
-   **Font Awesome**: Icon library.

### Configuration & Logging
-   **ConfigParser**: Configuration management.
-   **Python Logging**: System-wide logging.
-   **Environment Variables**: Secure credential management.