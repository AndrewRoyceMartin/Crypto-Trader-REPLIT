# Algorithmic Trading System

## Overview

This Python-based algorithmic trading system is designed for cryptocurrency markets, offering backtesting, paper trading, and live trading capabilities. Its purpose is to automate trading strategies, manage risk, and provide a web-based dashboard for real-time monitoring and control. The system integrates a Bollinger Bands mean reversion strategy and comprehensive risk management controls. It includes a robust cryptocurrency portfolio system with realistic price simulation and tax compliance features for Australian reporting (ATO).

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Trading Framework
A modular architecture supports CLI operations via `main.py` and a web interface via Flask (`web_interface.py`). It includes `BacktestEngine`, `PaperTrader`, and `LiveTrader` classes for different trading modes.

### Deployment Configuration (Updated: 2025-08-14)
- **Primary Entry Point**: `app.py` - Direct Flask application entry for deployment
- **WSGI Support**: `wsgi.py` - Production WSGI configuration with Gunicorn
- **Development Entry**: `main.py` - CLI-based entry with multiple modes
- **Port Configuration**: Uses PORT environment variable (defaults to 5000, maps to 80 for deployment)
- **Health Endpoints**: `/health`, `/ready`, and root `/` endpoint with intelligent health check detection
- **Root Route Intelligence**: Detects curl/JSON requests and returns health status automatically
- **Deployment Files**: `Procfile`, `deployment.json`, and proper requirements.txt for cloud deployment
- **Production Server**: Gunicorn configuration with proper worker settings

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

#### Connection Management & Monitoring (Updated: 2025-08-14)
- **Intelligent Uptime Tracking**: System uptime counter waits for CoinGecko connection confirmation before starting, displaying "Waiting..." until connected
- **Connection-Aware Trading Controls**: Trading countdown stops during connection outages and automatically resumes when reconnected
- **Enhanced Status Display**: Connection status with reconnection countdown timers (30-second intervals) and visual feedback
- **Trading Countdown Relocation**: Moved from navbar to Portfolio Overview section for better contextual relevance
- **Robust Error Handling**: Connection loss displays "Connection Lost" status with automatic recovery mechanisms

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