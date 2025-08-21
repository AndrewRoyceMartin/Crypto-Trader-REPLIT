# Algorithmic Trading System

## Overview
This Python-based algorithmic trading system automates cryptocurrency trading strategies, manages risk, and provides a web-based dashboard for real-time monitoring. It features live trading capabilities, focusing on an Enhanced Bollinger Bands mean reversion strategy. The system integrates directly with the user's live OKX trading account for authentic portfolio data and trading operations, aiming to provide a robust and compliant trading solution with a business vision to provide a secure and reliable automated trading solution for cryptocurrency enthusiasts.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The system utilizes a modular Flask-based web interface for live OKX trading, streamlined into a single-page dashboard application with minimal styling.

**Core Components & Features:**
-   **Main Application:** `app.py` serves as the Flask entry point.
-   **Web Interface:** A single-page dashboard (`unified_dashboard.html`) with a minimal CSS styling system (`style.css`) and JavaScript functionality (`app_clean.js`).
-   **Strategy:** Exclusively uses an Enhanced Bollinger Bands strategy with advanced crash protection, dynamic risk management, rebuy mechanisms, and peak tracking, tailored for live OKX integration.
-   **Data Management:** A two-tier caching system uses SQLite for raw market data to minimize API calls.
-   **Exchange Integration:** An `OKXAdapter` provides a unified interface for live OKX exchange, connecting directly to the user's real OKX trading account to fetch authentic portfolio holdings, positions, and trade history. Centralized OKX API functions ensure consistent native API integration.
-   **Risk Management:** The `RiskManager` enforces multiple safety layers, including portfolio-level limits, position sizing, daily loss limits, and emergency halts, calculating position sizing, entry/exit, stop loss, and take profit based on consistent equity risk.
-   **Web Interface Design:** A Flask-based web interface offers real-time monitoring and portfolio visualization with Chart.js, featuring a unified single-page dashboard consolidating all functionality (Overview, Portfolio, Performance, Holdings, Trades) into one comprehensive view. It includes accurate KPI calculations, dynamic price displays, ATO tax export functionality, and professional visual design with unified card styling.
-   **Trading Price Calculations:** All buy and sell price calculations use the user's real OKX purchase price and current OKX market prices, prioritizing OKX pre-calculated fields for trade values and P&L.
-   **CSS Architecture:** Minimal trading UI design with modern design tokens, CSS variable-based spacing, a grayscale-first approach, automatic dark mode support, and mobile-responsive navigation. A dedicated sticky control bar beneath the navbar contains primary trading controls.
-   **Color System:** Colors are used strategically for financial information (green for profit, red for loss, orange for warnings).
-   **FontAwesome Integration:** Uses FontAwesome 6.4.0 with `fa-solid` class syntax and updated icon names.
-   **Currency Conversion:** Uses OKX's native exchange rates for real-time fiat conversion.
-   **Enhanced OKX Adapter:** Robust trade retrieval, improved error handling with retry logic, duplicate prevention, comprehensive data validation, and optimized balance retrieval.
-   **Production-Safe Testing:** The `/api/test-sync-data` endpoint is secured with production guards, using direct service function calls.
-   **Optimized Warmup System:** Background warmup focuses on connectivity testing and market validation.
-   **UTC-Aware DateTime Standardization:** All datetime operations use UTC-aware timestamps for consistency.
-   **Authentication Protection:** Mutating endpoints are protected by an `@require_admin` decorator using a shared secret authentication (`ADMIN_TOKEN`).
-   **Exchange Instance Optimization:** Uses a singleton exchange instance to prevent `load_markets()` churn, improving performance.
-   **Security Headers:** Updated security headers for modern best practices, including HSTS and a comprehensive Content Security Policy.
-   **OKX Native Client:** Dedicated production-safe OKX native client (`src/utils/okx_native.py`) for improved performance and reliability, replacing duplicated signing logic.
-   **Database Layer:** `DatabaseManager` uses SQLite for persistent storage of trades, portfolio history, and system state.
-   **Algorithmic Optimization:** Incorporates multi-timeframe momentum analysis, adaptive position sizing, enhanced risk-reward enforcement, progressive trailing stops, market volatility regime detection, and statistical arbitrage techniques.
-   **Live Data & Strategy P&L Testing Frameworks:** Comprehensive test suites validate live OKX data synchronization and the mathematical accuracy of P&L calculations.
**Optimized Performance Endpoints (Latest):** Completely rewrote `/api/best-performer` and `/api/worst-performer` endpoints using OKX native client - replaced complex legacy implementation with streamlined native OKX API calls for accurate 24h/7d calculations, fixed percentage math using OKX's native fields, eliminated redundant API calls, enhanced performance scoring algorithm, and reduced code complexity from ~160 lines to ~50 lines per endpoint.

**Enhanced Current Holdings Endpoint:** Optimized `/api/current-holdings` with hybrid approach combining portfolio service reliability and native OKX price updates - leverages existing working portfolio data while enhancing with live OKX native ticker prices, provides comprehensive holding details including quantity, allocation percentages, P&L calculations, and proper error handling with graceful fallbacks for API limitations.

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