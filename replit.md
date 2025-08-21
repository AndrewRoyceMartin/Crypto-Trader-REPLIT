# Algorithmic Trading System

## Overview
This Python-based algorithmic trading system automates cryptocurrency trading strategies, manages risk, and provides a web-based dashboard for real-time monitoring. It features backtesting and live trading capabilities, focusing on an Enhanced Bollinger Bands mean reversion strategy. The system integrates directly with the user's live OKX trading account for authentic portfolio data and trading operations, aiming to provide a robust and compliant trading solution.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The system utilizes a modular architecture with a unified Flask-based web interface for live OKX trading. The architecture has been streamlined to use a single-page dashboard application with clean, minimal styling. All unused files have been archived to maintain a clean codebase structure.

**Current Active Structure:**
- **app.py** - Main Flask application entry point
- **templates/unified_dashboard.html** - Single-page dashboard interface  
- **static/style.css** - Minimal trading UI styling system
- **static/app_clean.js** - Dashboard functionality
- **src/** - Modular source code architecture
- **archive/** - Archived unused development files

**Strategy System:**
The system exclusively uses an Enhanced Bollinger Bands strategy across all modes, incorporating advanced crash protection, dynamic risk management, rebuy mechanisms, and peak tracking. All simulation and paper trading functionalities have been removed in favor of live OKX integration.

**Data Management:**
A two-tier caching system uses SQLite for raw market data, managed to minimize API calls.

**Exchange Integration:**
An adapter pattern, specifically `OKXAdapter`, provides a unified interface for live OKX exchange, connecting directly to the user's real OKX trading account via regional endpoints. It fetches actual portfolio holdings, positions, and trade history from the live OKX account, and all simulated data has been replaced with authentic OKX data.

**Risk Management:**
The `RiskManager` enforces multiple safety layers, including portfolio-level limits, position sizing, daily loss limits, and emergency halts, performing checks before every trade. Position sizing, entry/exit prices, stop loss, and take profit levels are calculated to ensure consistent equity risk per trade.

**Web Interface:**
A Flask-based web interface offers real-time monitoring and portfolio visualization with Chart.js. It features a unified single-page dashboard that consolidates all functionality (Overview, Portfolio, Performance, Holdings, and Trades) into one comprehensive view with smooth scrolling navigation. The interface includes accurate KPI calculations, dynamic price displays, ATO tax export functionality, and professional visual design with unified card styling. Connection management includes intelligent uptime tracking and robust error handling.

**Trading Price Calculations:**
All buy and sell price calculations use the user's real OKX purchase price and current OKX market prices. Stop loss and take profit levels are calculated based on authentic entry prices. The system prioritizes OKX pre-calculated fields for trade values and P&L over local calculations, ensuring alignment with the OKX platform.

**CSS Architecture Optimization:**
The system employs a minimal trading UI design with modern design tokens and CSS variable-based spacing. It features a grayscale-first approach with color reserved exclusively for profit/loss indicators and warnings, automatic dark mode support, mobile-responsive navigation with Bootstrap collapse toggle, and a dedicated sticky control bar beneath the navbar containing primary trading controls. The scoped `.theme-min` class system prevents Bootstrap color drift and ensures consistent minimal card aesthetics across all components.

**Meaningful Color System:**
Colors are used strategically only where they provide essential financial information:
- `.pnl-up` - Green for positive profit/loss values
- `.pnl-down` - Red for negative profit/loss values  
- `.text-warn` - Orange for warnings and high deviation alerts
- `.text-success` - Green for successful connections and positive states
- `.text-danger` - Red for errors and negative states
- Trading action buttons (Buy/Sell/Bot) maintain appropriate color coding
All other UI elements remain neutral grayscale to focus attention on meaningful data.

**OKX Currency Conversion:**
The system uses OKX's native exchange rates for currency conversion, fetching real-time fiat conversion rates directly from OKX trading pairs.

**Enhanced OKX Adapter:**
The `okx_adapter.py` is enhanced with robust trade retrieval, improved error handling with retry logic, duplicate prevention, and comprehensive data validation. It includes optimized balance retrieval, order book and ticker methods, and detailed logging. Critical fixes ensure correct position retrieval for spot trading, proper currency conversion mathematics, centralized client construction, robust retry mechanisms, and enhanced raw endpoint safety with precise typing and exception handling. It supports secure demo mode handling and improved logging.

**Table Rendering System:**
Dedicated table elements per dashboard view ensure no data conflicts, with robust currency conversion, error handling, and performance optimizations.

**Technical Indicators:**
The `TechnicalIndicators` class provides vectorized calculations for indicators like Bollinger Bands and ATR.

**Live Data Testing Framework:**
A comprehensive test suite validates 100% live OKX data synchronization, including holdings, price data freshness, unrealized P&L accuracy, and futures/margin account access verification. It includes a synchronization alert system to monitor discrepancies.

**Strategy P&L Testing Framework:**
An advanced test suite validates the mathematical accuracy of trading strategy P&L calculations using real OKX price data, including position sizing, P&L calculation precision, strategy scenario simulation, live OKX price integration, and risk management constraint validation.

**Database Layer:**
`DatabaseManager` uses SQLite for persistent storage of trades, portfolio history, and system state.

**Algorithmic Optimization:**
The system incorporates advanced algorithmic optimization for buy/sell decisions, including multi-timeframe momentum analysis, adaptive position sizing, enhanced risk-reward enforcement, progressive trailing stops, market volatility regime detection, and statistical arbitrage techniques.

## External Dependencies

### Market Data & Trading APIs
- **CCXT Library**: Unified exchange interface.
- **OKX Exchange**: Primary data source and live trading platform.
- **Kraken Exchange**: Live trading platform.
- **CoinGecko API**: Live cryptocurrency prices.

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