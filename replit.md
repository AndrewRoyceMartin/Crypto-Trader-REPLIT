# Algorithmic Trading System

## Overview
This Python-based algorithmic trading system automates cryptocurrency trading strategies, manages risk, and provides a web-based dashboard for real-time monitoring. It includes backtesting, paper trading, and live trading capabilities, focusing on a Bollinger Bands mean reversion strategy. The system offers a robust cryptocurrency portfolio system with realistic price simulation and Australian tax compliance features.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The system employs a modular architecture supporting both CLI and Flask-based web interfaces. It features `BacktestEngine`, `PaperTrader`, and `LiveTrader` classes for different trading modes.

**Deployment Configuration:**
The primary entry point is `app.py` for fast-boot Flask deployment, supported by `wsgi.py` for production. It uses environment variables for port configuration and system parameters. A fast-boot architecture prioritizes immediate Flask startup, followed by background trading system initialization with a circuit breaker pattern and persistent data caching. Enhanced health endpoints (`/`, `/health`, `/ready`) provide detailed status.

**Strategy System:**
A plugin-based system using `BaseStrategy` allows flexible strategy implementation, such as `BollingerBandsStrategy`, generating `Signal` objects with trade actions and risk parameters.

**Data Management:**
A two-tier caching system utilizes SQLite for raw market data, managed by `DataManager` and `DataCache` to minimize API calls.

**Exchange Integration:**
An adapter pattern with `BaseExchange` provides a unified interface for various cryptocurrency exchanges (e.g., `OKXAdapter`, `KrakenAdapter`), handling authentication, rate limiting, and data normalization.

**Risk Management:**
The `RiskManager` enforces multiple safety layers, including portfolio-level limits, position sizing, daily loss limits, and emergency halts, performing checks before every trade. Position sizing, entry/exit prices (with slippage), stop loss, and take profit levels are calculated using integrated bot pricing formulas to ensure a consistent 1% equity risk per trade.

**Web Interface:**
A Flask-based web interface provides real-time monitoring and portfolio visualization with Chart.js. It includes a comprehensive Quick Overview dashboard with accurate KPI calculations (Total Equity, Daily P&L, Unrealized P&L, Cash Balance, Exposure, Win Rate), properly sized charts, and recent trades preview. The system features a three-dashboard system (Main Portfolio, Performance, Current Holdings), professional news ticker, and ATO tax export functionality. Tables display complete data for 103 cryptocurrency assets with dynamic price displays and proper column alignment. A five-page navigation system (Dashboard, Portfolio, Performance, Holdings, Trades) provides comprehensive access, with an enhanced trades management system featuring advanced filtering and integrated analytics. Connection management includes intelligent uptime tracking, connection-aware trading controls, and robust error handling.

**Master Portfolio Assets:**
A hardcoded list of 103 cryptocurrencies is stored in `src/data/portfolio_assets.py`, categorized across 8 distinct areas, with each asset representing an initial $10 investment.

**Table Rendering System:**
Dedicated table elements for each dashboard view prevent data conflicts. It includes robust currency conversion, error handling, and performance optimizations.

**Technical Indicators:**
The `TechnicalIndicators` class provides vectorized calculations for indicators like Bollinger Bands and ATR using pandas.

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