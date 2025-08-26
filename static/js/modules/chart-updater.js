// Chart management module
import { AppUtils } from './utils.js';

export class ChartUpdater {
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
        
        this.initPortfolioChart();
        this.initAllocationChart();
        this.initEquityChart();
        this.initDrawdownChart();
    }

    initPortfolioChart() {
        const ctx = document.getElementById('portfolioChart');
        if (!ctx) {
            console.debug('Portfolio chart element not found - skipping chart update');
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
            console.debug('Allocation chart element not found - skipping chart update');
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
            console.debug('Equity chart element not found - skipping chart update');
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

    initDrawdownChart() {
        const ctx = document.getElementById('drawdownChart');
        if (!ctx) {
            console.debug('Drawdown chart element not found - skipping chart update');
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
        if (!this.charts.portfolioChart) return;
        
        try {
            const data = await AppUtils.fetchJSON('/api/portfolio-history?timeframe=7d');
            if (!data || !data.history) return;
            
            const labels = data.history.map(item => AppUtils.formatDateTime(item.timestamp));
            const values = data.history.map(item => AppUtils.safeNum(item.total_value));
            
            this.charts.portfolioChart.data.labels = labels;
            this.charts.portfolioChart.data.datasets[0].data = values;
            this.charts.portfolioChart.update('none');
        } catch (error) {
            console.debug('Portfolio chart update failed:', error);
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
                return;
            }
            
            const labels = data.allocations.map(item => item.symbol);
            const values = data.allocations.map(item => AppUtils.safeNum(item.percentage));
            
            this.charts.allocationChart.data.labels = labels;
            this.charts.allocationChart.data.datasets[0].data = values;
            this.charts.allocationChart.update('none');
        } catch (error) {
            console.debug('Allocation chart update failed:', error);
        }
    }

    async updateEquityChart() {
        if (!this.charts.equityChart) {
            console.debug('Equity chart element not found - skipping chart update');
            return;
        }
        
        try {
            const data = await AppUtils.fetchJSON('/api/equity-curve?timeframe=30d');
            if (!data || !data.equity_curve) return;
            
            const labels = data.equity_curve.map(item => AppUtils.formatDateTime(item.timestamp));
            const values = data.equity_curve.map(item => AppUtils.safeNum(item.equity));
            
            this.charts.equityChart.data.labels = labels;
            this.charts.equityChart.data.datasets[0].data = values;
            this.charts.equityChart.update('none');
        } catch (error) {
            console.debug('Equity chart update failed:', error);
        }
    }

    async updateDrawdownChart() {
        if (!this.charts.drawdownChart) {
            console.debug('Drawdown chart element not found - skipping chart update');
            return;
        }
        
        try {
            const data = await AppUtils.fetchJSON('/api/drawdown-analysis?timeframe=30d');
            if (!data || !data.drawdown_history) return;
            
            const labels = data.drawdown_history.map(item => AppUtils.formatDateTime(item.timestamp));
            const values = data.drawdown_history.map(item => AppUtils.safeNum(item.drawdown_percent));
            
            this.charts.drawdownChart.data.labels = labels;
            this.charts.drawdownChart.data.datasets[0].data = values;
            this.charts.drawdownChart.update('none');
        } catch (error) {
            console.debug('Drawdown chart update failed:', error);
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
}