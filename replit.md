# Algorithmic Trading System

## Overview

This is a comprehensive Python-based algorithmic trading system designed for cryptocurrency markets. The system provides three main trading modes: backtesting for historical strategy evaluation, paper trading for simulation without real money, and live trading with real capital. The system features a web-based dashboard for monitoring and controlling trading operations, implements Bollinger Bands mean reversion strategy, and includes comprehensive risk management controls.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Trading Framework
The system is built around a modular architecture with clear separation of concerns. The main entry point supports CLI operations through `main.py`, while the web interface is provided via Flask in `web_interface.py`. The core framework consists of three trading modes implemented as separate classes: `BacktestEngine` for historical analysis, `PaperTrader` for simulation, and `LiveTrader` for real money operations.

### Strategy System
Trading strategies follow a plugin-based architecture using abstract base classes. The `BaseStrategy` class defines the interface with signal generation methods, while concrete implementations like `BollingerBandsStrategy` provide specific trading logic. Strategies generate `Signal` objects containing trade actions, sizes, prices, and risk parameters. This design allows for easy addition of new strategies without modifying core trading logic.

### Data Management
The data layer implements a two-tier caching system. Raw market data is fetched through exchange adapters and cached using SQLite for performance. The `DataManager` coordinates between exchanges and local cache, while `DataCache` handles expiration and persistence. This approach reduces API calls and improves system responsiveness.

### Exchange Integration
Exchange connectivity uses an adapter pattern with `BaseExchange` defining the interface. Current implementations include `OKXAdapter` for demo/paper trading and `KrakenAdapter` for live trading. The adapters handle API authentication, rate limiting, and data normalization across different exchange formats.

### Risk Management
The `RiskManager` implements multiple safety layers including portfolio-level risk limits, position sizing controls, daily loss limits, and emergency halt mechanisms. Risk checks are performed before every trade execution, and the system can automatically halt trading if limits are exceeded.

### Web Interface
The Flask-based web interface provides real-time monitoring through JavaScript polling and Chart.js visualizations. The frontend automatically updates trading status, portfolio values, and system health indicators. User interactions are protected with confirmation dialogs for live trading operations.

### Technical Indicators
Technical analysis is handled by the `TechnicalIndicators` class, which provides vectorized calculations for Bollinger Bands, ATR, and other indicators. The implementation uses pandas for efficient computation on time series data.

### Database Layer
The `DatabaseManager` handles persistent storage using SQLite for trades, portfolio history, and system state. Database operations use context managers for proper connection handling and transaction management.

## External Dependencies

### Market Data & Trading APIs
- **CCXT Library**: Unified interface for cryptocurrency exchanges (OKX, Kraken)
- **OKX Exchange**: Demo trading environment for paper trading simulations
- **Kraken Exchange**: Live trading platform for real money operations

### Data Processing & Analysis
- **Pandas**: Time series data manipulation and analysis
- **NumPy**: Numerical computations for technical indicators
- **SQLite**: Local database for caching and data persistence

### Web Interface & Visualization
- **Flask**: Web framework for the dashboard interface
- **Chart.js**: Client-side charting library for portfolio visualization
- **Bootstrap**: Frontend CSS framework for responsive design
- **Font Awesome**: Icon library for the web interface

### Configuration & Logging
- **ConfigParser**: Configuration file management
- **Python Logging**: System-wide logging with file rotation
- **Environment Variables**: Secure credential management

### Development & Deployment
- **Python 3.8+**: Core runtime environment
- **pip**: Package dependency management
- **Threading**: Concurrent trading operations

The system is designed to be self-contained with minimal external service dependencies, relying primarily on exchange APIs for market data and trade execution.