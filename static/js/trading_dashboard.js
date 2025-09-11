// Trading Dashboard Module
class TradingDashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = 30000; // 30 seconds
        this.init();
    }

    init() {
        console.log('🚀 Initializing Trading Intelligence Dashboard');
        this.loadAllData();
        this.startAutoRefresh();
        console.log('✅ Dashboard initialization complete');
    }

    async loadAllData() {
        this.showRefreshIndicator();
        this.showDashboardLoading();
        
        try {
            // Show loading states for all metric cards
            this.showMetricLoading();
            
            await Promise.all([
                this.loadPortfolioOverview(),
                this.loadMLSignals(),
                this.loadHoldings(),
                this.loadChartData(),
                this.loadRiskMetrics()
            ]);
            
            this.showDashboardLoaded();
        } catch (error) {
            console.error('❌ Error loading dashboard data:', error);
            this.showDashboardError();
        } finally {
            this.hideRefreshIndicator();
        }
    }

    async loadPortfolioOverview() {
        try {
            const response = await fetch('/api/performance-overview');
            const data = await response.json();
            this.updatePortfolioMetrics(data);
        } catch (error) {
            console.error('❌ Error loading portfolio overview:', error);
        }
    }

    async loadMLSignals() {
        try {
            const response = await fetch('/api/signal-tracking');
            const data = await response.json();
            this.updateMLSignalsTable(data.latest_signals || []);
        } catch (error) {
            console.error('❌ Error loading ML signals:', error);
        }
    }

    async loadHoldings() {
        try {
            const response = await fetch('/api/trades');
            const data = await response.json();
            console.log('✅ Holdings loaded successfully:', data.length, 'positions');
        } catch (error) {
            console.error('❌ Error loading holdings:', error);
        }
    }

    async loadChartData() {
        try {
            const response = await fetch('/api/performance-charts');
            const data = await response.json();
            this.updatePortfolioChart(data);
        } catch (error) {
            console.error('❌ Error loading chart data:', error);
        }
    }

    async loadRiskMetrics() {
        try {
            const response = await fetch('/api/trade-performance');
            const data = await response.json();
            this.updateRiskMetrics(data.summary);
        } catch (error) {
            console.error('❌ Error loading risk metrics:', error);
        }
    }

    showMetricLoading() {
        const metricCards = document.querySelectorAll('.metric-card');
        metricCards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('loading');
                card.style.opacity = '0.7';
            }, index * 100);
        });
    }

    updateMetricWithAnimation(elementId, value, isPercentage = false) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const skeletonEl = element.querySelector('.loading-skeleton');
        if (skeletonEl) {
            // Smooth transition from skeleton to actual data
            setTimeout(() => {
                skeletonEl.style.opacity = '0';
                setTimeout(() => {
                    skeletonEl.remove();
                    element.textContent = value;
                    element.style.opacity = '0';
                    element.style.transform = 'scale(0.9)';
                    
                    // Animate in the real value
                    setTimeout(() => {
                        element.style.transition = 'all 0.4s ease';
                        element.style.opacity = '1';
                        element.style.transform = 'scale(1)';
                    }, 50);
                }, 300);
            }, 150);
        } else {
            // No skeleton - just update directly
            element.textContent = value;
            element.style.opacity = '1';
            element.classList.add('metric-loaded');
        }
    }

    updatePortfolioMetrics(data) {
        const metrics = data.portfolio_metrics;
        const signals = data.signal_metrics;

        // Use animated updates for professional transitions
        this.updateMetricWithAnimation('portfolioValue', `$${metrics.total_value.toLocaleString()}`);
        
        const totalPnLEl = document.getElementById('totalPnL');
        this.updateMetricWithAnimation('totalPnL', `$${metrics.total_pnl.toFixed(2)}`);
        if (totalPnLEl) {
            totalPnLEl.className = `metric-value ${metrics.total_pnl >= 0 ? 'text-success' : 'text-danger'}`;
        }
        
        const pnlPercentEl = document.getElementById('pnlPercent');
        this.updateMetricWithAnimation('pnlPercent', `${metrics.total_pnl_percent.toFixed(2)}%`);
        if (pnlPercentEl) {
            pnlPercentEl.className = `metric-change ${metrics.total_pnl_percent >= 0 ? 'text-success' : 'text-danger'}`;
        }
        
        this.updateMetricWithAnimation('activePositions', metrics.total_positions);
        this.updateMetricWithAnimation('winRate', `${metrics.win_rate}% Win Rate`);
        
        this.updateMetricWithAnimation('mlAccuracy', `${signals.ml_accuracy}%`);
        this.updateMetricWithAnimation('signalsToday', `${signals.signals_today} Signals Today`);
    }

    updateMLSignalsTable(signals) {
        const tbody = document.getElementById('mlSignalsBody');
        
        if (!signals || signals.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="t-center text-muted">No recent ML signals</td></tr>';
            return;
        }

        tbody.innerHTML = signals.slice(0, 5).map(signal => {
            const hybridScore = (signal.hybrid_score || 0);
            return `
            <tr>
                <td><strong>${signal.symbol || 'N/A'}</strong></td>
                <td><span class="signal-badge signal-${signal.signal || 'WAIT'}">${signal.signal || 'WAIT'}</span></td>
                <td><span class="ml-confidence">${hybridScore.toFixed(1)}%</span></td>
                <td class="${signal.pnl_percent !== null ? (signal.pnl_percent >= 0 ? 'text-success' : 'text-danger') : 'text-muted'}">
                    ${(signal.outcome || 'pending').replace('_', ' ')}
                </td>
            </tr>
            `;
        }).join('');
    }

    updateRiskMetrics(summary) {
        if (summary) {
            this.updateMetricWithAnimation('maxDrawdown', `${summary.max_drawdown || 0}%`);
            this.updateMetricWithAnimation('sharpeRatio', `${summary.sharpe_ratio || 0}`);
            this.updateMetricWithAnimation('volatility', `${(Math.abs(summary.avg_pnl_percent) * 2).toFixed(1)}%`);
            this.updateMetricWithAnimation('exposureRisk', summary.total_trades > 15 ? 'HIGH' : 'MODERATE');
        }
    }

    updatePortfolioChart(data) {
        const ctx = document.getElementById('portfolioChart');
        if (!ctx) return;
        
        try {
            if (this.charts.portfolio) {
                this.charts.portfolio.destroy();
            }

            this.charts.portfolio = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels || ['No Data'],
                    datasets: [{
                        label: 'Portfolio Value',
                        data: data.values || [0],
                        borderColor: '#36A2EB',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        fill: true,
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: false }
                    }
                }
            });
        } catch (error) {
            console.warn('Chart.js not available:', error);
        }
    }

    showDashboardLoading() {
        const statusEl = document.getElementById('dashboard-status');
        if (statusEl) {
            statusEl.className = 'dashboard-status status-loading';
            statusEl.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading dashboard data...';
        }
    }

    showDashboardLoaded() {
        const statusEl = document.getElementById('dashboard-status');
        if (statusEl) {
            statusEl.className = 'dashboard-status status-loaded';
            const now = new Date();
            statusEl.innerHTML = `<i class="fas fa-check-circle me-2"></i>Dashboard loaded successfully - Last updated: ${now.toLocaleTimeString()}`;
        }
    }

    showDashboardError() {
        const statusEl = document.getElementById('dashboard-status');
        if (statusEl) {
            statusEl.className = 'dashboard-status status-error';
            statusEl.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Error loading dashboard - Retrying...';
        }
    }

    showRefreshIndicator() {
        const indicator = document.getElementById('refreshIndicator');
        if (indicator) indicator.classList.add('show');
    }

    hideRefreshIndicator() {
        const indicator = document.getElementById('refreshIndicator');
        if (indicator) indicator.classList.remove('show');
    }

    updateLastUpdateTime() {
        const element = document.getElementById('lastUpdate');
        if (element) {
            const now = new Date();
            element.textContent = `Last updated: ${now.toLocaleTimeString()}`;
        }
    }

    startAutoRefresh() {
        setInterval(() => {
            this.loadAllData();
        }, this.refreshInterval);
    }
}

// Export for bootstrap
export function initDashboard() {
    return new TradingDashboard();
}