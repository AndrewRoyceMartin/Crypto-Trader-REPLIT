// Chart management module
import { AppUtils } from './utils.js';

export class ChartUpdater {
    
    // Centralized fallback renderer for charts
    static createChartFallback(elementId, fallbackText, fallbackType = 'info') {
        const canvas = document.getElementById(elementId);
        if (!canvas) {
            console.debug(`Chart element ${elementId} not found - cannot create fallback`);
            return null;
        }
        
        // Create fallback element
        const fallback = document.createElement('div');
        fallback.className = `chart-fallback d-flex align-items-center justify-content-center text-${fallbackType}`;
        fallback.style.cssText = `
            height: 300px;
            border: 2px dashed #dee2e6;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 500;
            background: #f8f9fa;
        `;
        
        // Add icon based on fallback type
        const iconMap = {
            'info': 'fa-chart-line',
            'warning': 'fa-exclamation-triangle', 
            'error': 'fa-times-circle',
            'loading': 'fa-spinner fa-spin'
        };
        
        const iconClass = iconMap[fallbackType] || 'fa-chart-line';
        fallback.innerHTML = `
            <div class="text-center">
                <i class="fas ${iconClass} fa-2x mb-2"></i>
                <div>${fallbackText}</div>
            </div>
        `;
        
        // Replace canvas with fallback
        canvas.parentNode.replaceChild(fallback, canvas);
        
        console.debug(`Chart fallback created for ${elementId}: ${fallbackText}`);
        return fallback;
    }
    
    // Restore chart canvas from fallback
    static restoreChartCanvas(containerId, canvasId) {
        const container = document.querySelector(`#${containerId} .chart-fallback`);
        if (!container) return null;
        
        const canvas = document.createElement('canvas');
        canvas.id = canvasId;
        container.parentNode.replaceChild(canvas, container);
        
        return canvas;
    }
    constructor() {
        this.charts = {
            portfolioChart: null,
            pnlChart: null, 
            performersChart: null,
            miniPortfolioChart: null,
            equityChart: null,
            drawdownChart: null,
            allocationChart: null
        };
        
        this.chartUpdateInterval = null;
        this.defaultColors = [
            '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
            '#ec4899', '#6b7280', '#14b8a6', '#f97316', '#84cc16'
        ];
    }

    initializeCharts() {
        if (!window.Chart) {
            console.warn('Chart.js not available - charts disabled');
            return;
        }
        
        // Add longer delay to ensure DOM elements are ready with deferred loading and patched HTML structure
        setTimeout(() => {
            console.debug('Initializing charts after DOM ready delay...');
            this.initPortfolioChart();
            this.initAllocationChart();
            this.initEquityChart();
            this.initRiskChart(); // Updated to match HTML (riskChart not drawdownChart)
        }, 300);
    }

    initPortfolioChart() {
        const ctx = document.getElementById('portfolioChart');
        if (!ctx) {
            console.debug('Portfolio chart element not found - creating fallback');
            ChartUpdater.createChartFallback('portfolioChart', 'Portfolio History Chart', 'info');
            return;
        }

        this.charts.portfolioChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: this.defaultColors[0],
                    backgroundColor: this.defaultColors[0] + '20',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: true,
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return AppUtils.formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });
    }

    initAllocationChart() {
        const ctx = document.getElementById('allocationChart');
        if (!ctx) {
            console.debug('Allocation chart element not found - creating fallback');
            ChartUpdater.createChartFallback('allocationChart', 'Asset Allocation Chart', 'info');
            return;
        }

        this.charts.allocationChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: this.defaultColors
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    initEquityChart() {
        const ctx = document.getElementById('equityChart');
        if (!ctx) {
            console.debug('Equity chart element not found - creating fallback');
            ChartUpdater.createChartFallback('equityChart', 'Equity Curve Chart', 'info');
            return;
        }

        this.charts.equityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Equity Curve',
                    data: [],
                    borderColor: this.defaultColors[2],
                    backgroundColor: this.defaultColors[2] + '20',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: true,
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return AppUtils.formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });
    }

    initRiskChart() {
        const ctx = document.getElementById('riskChart');
        if (!ctx) {
            console.debug('Risk chart element not found - creating fallback');
            ChartUpdater.createChartFallback('riskChart', 'Portfolio Analytics Chart', 'info');
            return;
        }

        this.charts.drawdownChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Drawdown %',
                    data: [],
                    borderColor: this.defaultColors[1],
                    backgroundColor: this.defaultColors[1] + '20',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: true,
                        max: 0,
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    async updatePortfolioChart() {
        if (!this.charts.portfolioChart) {
            console.debug('Portfolio chart element not found - skipping chart update');
            return;
        }
        
        try {
            const data = await AppUtils.fetchJSON('/api/portfolio-history?timeframe=7d');
            if (!data || !data.history) {
                this.handleChartUpdateError('portfolioChart', 'No portfolio data available');
                return;
            }
            
            const labels = data.history.map(item => AppUtils.formatDateTime(item.timestamp));
            const values = data.history.map(item => AppUtils.safeNum(item.total_value));
            
            this.charts.portfolioChart.data.labels = labels;
            this.charts.portfolioChart.data.datasets[0].data = values;
            this.charts.portfolioChart.update('none');
        } catch (error) {
            console.debug('Portfolio chart update failed:', error);
            this.handleChartUpdateError('portfolioChart', 'Failed to load portfolio data');
        }
    }

    async updateAllocationChart() {
        if (!this.charts.allocationChart) {
            console.debug('Allocation chart element not found - skipping chart update');
            return;
        }
        
        try {
            const data = await AppUtils.fetchJSON('/api/asset-allocation');
            if (!data || !data.allocations) {
                console.debug('Asset allocation update failed:', data);
                this.handleChartUpdateError('allocationChart', 'No allocation data available');
                return;
            }
            
            const labels = data.allocations.map(item => item.symbol);
            const values = data.allocations.map(item => AppUtils.safeNum(item.percentage));
            
            this.charts.allocationChart.data.labels = labels;
            this.charts.allocationChart.data.datasets[0].data = values;
            this.charts.allocationChart.update('none');
        } catch (error) {
            console.debug('Allocation chart update failed:', error);
            this.handleChartUpdateError('allocationChart', 'Failed to load allocation data');
        }
    }

    async updateEquityChart() {
        if (!this.charts.equityChart) {
            console.debug('Equity chart element not found - skipping chart update');
            return;
        }
        
        try {
            const data = await AppUtils.fetchJSON('/api/equity-curve?timeframe=30d');
            if (!data || !data.equity_curve) {
                this.handleChartUpdateError('equityChart', 'No equity data available');
                return;
            }
            
            const labels = data.equity_curve.map(item => AppUtils.formatDateTime(item.timestamp));
            const values = data.equity_curve.map(item => AppUtils.safeNum(item.equity));
            
            this.charts.equityChart.data.labels = labels;
            this.charts.equityChart.data.datasets[0].data = values;
            this.charts.equityChart.update('none');
        } catch (error) {
            console.debug('Equity chart update failed:', error);
            this.handleChartUpdateError('equityChart', 'Failed to load equity data');
        }
    }

    async updateDrawdownChart() {
        if (!this.charts.drawdownChart) {
            console.debug('Drawdown chart element not found - skipping chart update');
            return;
        }
        
        try {
            const data = await AppUtils.fetchJSON('/api/drawdown-analysis?timeframe=30d');
            if (!data || !data.drawdown_history) {
                this.handleChartUpdateError('drawdownChart', 'No drawdown data available');
                return;
            }
            
            const labels = data.drawdown_history.map(item => AppUtils.formatDateTime(item.timestamp));
            const values = data.drawdown_history.map(item => AppUtils.safeNum(item.drawdown_percent));
            
            this.charts.drawdownChart.data.labels = labels;
            this.charts.drawdownChart.data.datasets[0].data = values;
            this.charts.drawdownChart.update('none');
        } catch (error) {
            console.debug('Drawdown chart update failed:', error);
            this.handleChartUpdateError('drawdownChart', 'Failed to load drawdown data');
        }
    }

    async updateAllCharts() {
        await Promise.all([
            this.updatePortfolioChart(),
            this.updateAllocationChart(),
            this.updateEquityChart(),
            this.updateDrawdownChart()
        ]);
    }

    startAutoUpdate() {
        // Update charts every 60 seconds
        this.chartUpdateInterval = setInterval(() => {
            this.updateAllCharts();
        }, 60000);
        
        // Initial update
        setTimeout(() => this.updateAllCharts(), 1000);
    }

    stopAutoUpdate() {
        if (this.chartUpdateInterval) {
            clearInterval(this.chartUpdateInterval);
            this.chartUpdateInterval = null;
        }
    }

    destroyAllCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        
        this.charts = {
            portfolioChart: null,
            pnlChart: null,
            performersChart: null,
            miniPortfolioChart: null,
            equityChart: null,
            drawdownChart: null,
            allocationChart: null
        };
    }

    // Handle chart update errors with fallback display
    handleChartUpdateError(chartId, errorMessage) {
        // Destroy existing chart if present
        const chartInstance = this.charts[chartId];
        if (chartInstance) {
            chartInstance.destroy();
            this.charts[chartId] = null;
        }
        
        // Create error fallback
        ChartUpdater.createChartFallback(chartId, errorMessage, 'warning');
    }
}