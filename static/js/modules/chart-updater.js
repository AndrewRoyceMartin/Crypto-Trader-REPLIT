// Chart management module
import { AppUtils } from './utils.js';

export class ChartUpdater {
    
    // Centralized fallback renderer for charts
    static createChartFallback(elementId, fallbackText, fallbackType = 'info') {
        const canvas = document.getElementById(elementId);
        if (!canvas) {
            // Silently skip fallback creation if element doesn't exist
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
            riskChart: null,
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
            // Destroy any existing charts to prevent canvas reuse errors
            this.destroyAllCharts();
            
            this.initPortfolioChart();
            this.initAllocationChart();
            this.initEquityChart();
            this.initRiskChart(); // Updated to match HTML (riskChart not drawdownChart)
        }, 300);
    }

    initPortfolioChart() {
        // Destroy existing chart before creating new one
        if (this.charts.portfolioChart) {
            this.charts.portfolioChart.destroy();
            this.charts.portfolioChart = null;
        }
        
        const ctx = document.getElementById('portfolioChart');
        if (!ctx) {
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
            ChartUpdater.createChartFallback('riskChart', 'Portfolio Analytics Chart', 'info');
            return;
        }

        this.charts.riskChart = new Chart(ctx, {
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
            return;
        }
        
        try {
            const data = await AppUtils.fetchJSON('/api/portfolio-history?timeframe=7d');
            if (!data || !data.history) {
                ChartUpdater.createChartFallback('portfolioChart', 'No portfolio data available', 'warning');
                return;
            }
            
            const labels = data.history.map(item => AppUtils.formatDateTime(item.timestamp));
            const values = data.history.map(item => AppUtils.safeNum(item.value));
            
            this.charts.portfolioChart.data.labels = labels;
            this.charts.portfolioChart.data.datasets[0].data = values;
            this.charts.portfolioChart.update('none');
        } catch (error) {
            ChartUpdater.createChartFallback('portfolioChart', 'Failed to load portfolio data', 'warning');
        }
    }

    async updateAllocationChart() {
        if (!this.charts.allocationChart) {
            return;
        }
        
        try {
            const data = await AppUtils.fetchJSON('/api/asset-allocation');
            if (!data || !data.allocation) {
                ChartUpdater.createChartFallback('allocationChart', 'No allocation data available', 'warning');
                return;
            }
            
            const labels = data.allocation.map(item => item.symbol);
            const values = data.allocation.map(item => AppUtils.safeNum(item.allocation_percent));
            
            this.charts.allocationChart.data.labels = labels;
            this.charts.allocationChart.data.datasets[0].data = values;
            this.charts.allocationChart.update('none');
        } catch (error) {
            ChartUpdater.createChartFallback('allocationChart', 'Failed to load allocation data', 'warning');
        }
    }

    async updateEquityChart() {
        if (!this.charts.equityChart) {
            console.debug('Equity chart not initialized, skipping update');
            return;
        }
        
        try {
            const data = await AppUtils.fetchJSON('/api/equity-curve?timeframe=30d');
            console.debug('Equity chart data received:', data);
            
            if (!data || !data.equity_curve || !Array.isArray(data.equity_curve)) {
                console.debug('Invalid equity data structure, creating fallback');
                ChartUpdater.createChartFallback('equityChart', 'No equity data available', 'warning');
                return;
            }
            
            if (data.equity_curve.length === 0) {
                console.debug('Empty equity data array, creating fallback');
                ChartUpdater.createChartFallback('equityChart', 'No equity data available', 'warning');
                return;
            }
            
            const labels = data.equity_curve.map(item => AppUtils.formatDateTime(item.timestamp));
            const values = data.equity_curve.map(item => AppUtils.safeNum(item.equity));
            
            console.debug(`Updating equity chart with ${labels.length} data points`);
            
            this.charts.equityChart.data.labels = labels;
            this.charts.equityChart.data.datasets[0].data = values;
            this.charts.equityChart.update('none');
        } catch (error) {
            console.error('Equity chart update error:', error);
            ChartUpdater.createChartFallback('equityChart', 'Failed to load equity data', 'warning');
        }
    }

    async updateRiskChart() {
        if (!this.charts.riskChart) {
            console.debug('Risk chart not initialized, skipping update');
            return;
        }
        
        try {
            // Use shorter timeout for risk chart to prevent hanging
            const data = await AppUtils.fetchJSON('/api/drawdown-analysis?timeframe=30d', { timeout: 8000 });
            console.debug('Risk chart data received:', data);
            
            // Handle both drawdown_history and drawdown_data structure  
            const drawdownData = data?.drawdown_history || data?.drawdown_data || data;
            
            if (!drawdownData || !Array.isArray(drawdownData)) {
                console.debug('Invalid risk data structure, creating fallback. Expected drawdown_history or drawdown_data array');
                ChartUpdater.createChartFallback('riskChart', 'No risk data available', 'warning');
                return;
            }
            
            if (drawdownData.length === 0) {
                console.debug('Empty drawdown data array, creating fallback');
                ChartUpdater.createChartFallback('riskChart', 'No risk data available', 'warning');
                return;
            }
            
            const labels = drawdownData.map(item => AppUtils.formatDateTime(item.timestamp || item.date));
            const values = drawdownData.map(item => Math.abs(AppUtils.safeNum(item.drawdown_percent, 0)));
            
            console.debug(`Updating risk chart with ${labels.length} data points`);
            
            this.charts.riskChart.data.labels = labels;
            this.charts.riskChart.data.datasets[0].data = values;
            this.charts.riskChart.update('none');
        } catch (error) {
            console.debug('Risk chart update failed (expected for performance):', error.message);
            ChartUpdater.createChartFallback('riskChart', 'Risk analysis unavailable', 'info');
        }
    }

    async updateAllCharts() {
        // Prevent overlapping updates
        if (this.isUpdating) {
            console.debug('Chart update already in progress, skipping...');
            return;
        }
        
        this.isUpdating = true;
        
        try {
            console.debug('Starting chart updates...');
            // Update charts sequentially to avoid API overload
            await this.updatePortfolioChart().catch(e => console.debug('Portfolio chart update failed:', e));
            await new Promise(resolve => setTimeout(resolve, 500)); // Small delay between requests
            
            await this.updateAllocationChart().catch(e => console.debug('Allocation chart update failed:', e));
            await new Promise(resolve => setTimeout(resolve, 500));
            
            await this.updateEquityChart().catch(e => console.debug('Equity chart update failed:', e));
            await new Promise(resolve => setTimeout(resolve, 500));
            
            await this.updateRiskChart().catch(e => console.debug('Risk chart update failed:', e));
            
            console.debug('Chart updates completed');
        } catch (error) {
            console.debug('Chart update error:', error);
        } finally {
            this.isUpdating = false;
        }
    }

    startAutoUpdate() {
        // Stop any existing interval first
        if (this.chartUpdateInterval) {
            clearInterval(this.chartUpdateInterval);
        }
        
        // Update charts every 2 minutes to avoid overwhelming API
        this.chartUpdateInterval = setInterval(() => {
            console.debug('Auto-updating charts...');
            this.updateAllCharts();
        }, 120000); // 2 minutes
        
        // Initial update with longer delay to avoid race conditions
        setTimeout(() => {
            console.debug('Initial chart update...');
            this.updateAllCharts();
        }, 3000); // 3 seconds delay
    }

    stopAutoUpdate() {
        if (this.chartUpdateInterval) {
            clearInterval(this.chartUpdateInterval);
            this.chartUpdateInterval = null;
        }
    }

    destroyAllCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                try {
                    chart.destroy();
                } catch (e) {
                    // Silently handle chart destruction errors
                }
            }
        });
        
        this.charts = {
            portfolioChart: null,
            pnlChart: null,
            performersChart: null,
            miniPortfolioChart: null,
            equityChart: null,
            riskChart: null,
            allocationChart: null
        };
    }

}