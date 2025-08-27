// Trade management module  
import { AppUtils } from './utils.js';

export class TradeManager {
    constructor() {
        this.isLiveConfirmationPending = false;
        this.countdownInterval = null;
        this.countdown = 5;
        this.allTrades = [];
    }

    async executeTakeProfit(symbol, quantity, expectedProfit) {
        if (!symbol || !quantity) {
            AppUtils.showToast('Invalid trade parameters', 'error');
            return;
        }

        try {
            const payload = {
                symbol,
                quantity: parseFloat(quantity),
                expected_profit: parseFloat(expectedProfit) || 0,
                action: 'take_profit'
            };

            AppUtils.showToast(`Executing take profit for ${symbol}...`, 'info');
            
            const result = await AppUtils.fetchJSON('/api/execute-trade', {
                method: 'POST',
                body: payload
            });

            if (result && result.success) {
                AppUtils.showToast(`Take profit executed successfully for ${symbol}`, 'success');
                // Refresh data after successful trade
                await this.refreshTradeData();
            } else {
                const errorMsg = result?.message || 'Trade execution failed';
                AppUtils.showToast(errorMsg, 'error');
            }
        } catch (error) {
            console.error('Take profit execution error:', error);
            AppUtils.showToast('Failed to execute take profit', 'error');
        }
    }

    async buyBackPosition(symbol) {
        if (!symbol) {
            AppUtils.showToast('Invalid symbol for buy back', 'error');
            return;
        }

        try {
            const payload = {
                symbol,
                amount: 100 // Default $100 rebuy
            };

            AppUtils.showToast(`Buying back position for ${symbol}...`, 'info');
            
            const result = await AppUtils.fetchJSON('/api/buy', {
                method: 'POST', 
                body: payload
            });

            if (result && result.success) {
                AppUtils.showToast(`Buy back executed successfully for ${symbol}`, 'success');
                await this.refreshTradeData();
            } else {
                const errorMsg = result?.message || 'Buy back failed';
                AppUtils.showToast(errorMsg, 'error');
            }
        } catch (error) {
            console.error('Buy back error:', error);
            AppUtils.showToast('Failed to execute buy back', 'error');
        }
    }

    showBuyDialog(symbol, price, targetBuyPrice) {
        // Safe Bootstrap modal creation with library verification (handles defer loading)
        if (!window.bootstrap || !window.bootstrap.Modal) {
            console.warn('Bootstrap not ready - cannot show buy dialog');
            AppUtils.showToast('UI components not ready, please try again', 'error');
            
            // Retry after a short delay for deferred loading
            setTimeout(() => {
                if (window.bootstrap && window.bootstrap.Modal) {
                    this.showBuyDialog(symbol, price, targetBuyPrice);
                }
            }, 100);
            return;
        }

        const modalHtml = `
            <div class="modal fade" id="buyModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Buy ${symbol}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">Current Price</label>
                                <input type="text" class="form-control" value="${AppUtils.formatCurrency(price)}" readonly>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Target Buy Price</label>
                                <input type="text" class="form-control" value="${AppUtils.formatCurrency(targetBuyPrice)}" readonly>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Amount ($)</label>
                                <input type="number" class="form-control" id="buyAmount" value="100" min="10" max="1000">
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" onclick="confirmBuyOrder('${symbol}')">Place Buy Order</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if present
        const existingModal = document.getElementById('buyModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal safely
        const modal = new bootstrap.Modal(document.getElementById('buyModal'));
        modal.show();
    }

    showSellDialog(symbol, quantity, currentPrice) {
        // Safe Bootstrap modal creation (handles defer loading)
        if (!window.bootstrap || !window.bootstrap.Modal) {
            console.warn('Bootstrap not ready - cannot show sell dialog');
            AppUtils.showToast('UI components not ready, please try again', 'error');
            
            // Retry after a short delay for deferred loading
            setTimeout(() => {
                if (window.bootstrap && window.bootstrap.Modal) {
                    this.showSellDialog(symbol, quantity, currentPrice);
                }
            }, 100);
            return;
        }

        const totalValue = quantity * currentPrice;
        
        const modalHtml = `
            <div class="modal fade" id="sellModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Sell ${symbol}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">Available Quantity</label>
                                <input type="text" class="form-control" value="${quantity}" readonly>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Current Price</label>
                                <input type="text" class="form-control" value="${AppUtils.formatCurrency(currentPrice)}" readonly>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Quantity to Sell</label>
                                <input type="number" class="form-control" id="sellQuantity" value="${quantity}" min="0" max="${quantity}" step="0.00000001">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Estimated Value</label>
                                <input type="text" class="form-control" value="${AppUtils.formatCurrency(totalValue)}" readonly>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-danger" onclick="confirmSellOrder('${symbol}')">Place Sell Order</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if present
        const existingModal = document.getElementById('sellModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to page  
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal safely
        const modal = new bootstrap.Modal(document.getElementById('sellModal'));
        modal.show();
    }

    async confirmLiveTrading(action, symbol, params = {}) {
        if (this.isLiveConfirmationPending) {
            console.debug('Live confirmation already pending');
            return;
        }

        this.isLiveConfirmationPending = true;
        this.countdown = 5;

        const confirmationHtml = `
            <div class="modal fade" id="liveConfirmationModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-warning">
                            <h5 class="modal-title">⚠️ Live Trading Confirmation</h5>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-warning">
                                <strong>LIVE TRADING ALERT</strong><br>
                                You are about to execute a real trade on the live market.
                            </div>
                            <p><strong>Action:</strong> ${action}</p>
                            <p><strong>Symbol:</strong> ${symbol}</p>
                            ${Object.entries(params).map(([key, value]) => 
                                `<p><strong>${key}:</strong> ${value}</p>`
                            ).join('')}
                            <div class="text-center">
                                <button id="confirmLiveButton" class="btn btn-danger" disabled>
                                    Confirm in <span id="countdownTimer">${this.countdown}</span>s
                                </button>
                                <button type="button" class="btn btn-secondary ms-2" data-bs-dismiss="modal">Cancel</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal
        const existingModal = document.getElementById('liveConfirmationModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', confirmationHtml);
        
        if (window.bootstrap && window.bootstrap.Modal) {
            const modal = new bootstrap.Modal(document.getElementById('liveConfirmationModal'));
            modal.show();
            
            // Start countdown
            this.startConfirmationCountdown(action, symbol, params);
        }
    }

    startConfirmationCountdown(action, symbol, params) {
        const timer = document.getElementById('countdownTimer');
        const button = document.getElementById('confirmLiveButton');
        
        this.countdownInterval = setInterval(() => {
            this.countdown--;
            if (timer) timer.textContent = this.countdown;
            
            if (this.countdown <= 0) {
                clearInterval(this.countdownInterval);
                this.isLiveConfirmationPending = false;
                
                if (button) {
                    button.disabled = false;
                    button.innerHTML = 'Execute Live Trade';
                    button.onclick = () => this.executeLiveTrade(action, symbol, params);
                }
            }
        }, 1000);
    }

    async executeLiveTrade(action, symbol, params) {
        try {
            const payload = {
                action,
                symbol,
                ...params
            };

            const result = await AppUtils.fetchJSON('/api/execute-live-trade', {
                method: 'POST',
                body: payload
            });

            if (result && result.success) {
                AppUtils.showToast(`Live ${action} executed successfully for ${symbol}`, 'success');
                await this.refreshTradeData();
                
                // Hide confirmation modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('liveConfirmationModal'));
                if (modal) modal.hide();
            } else {
                const errorMsg = result?.message || 'Live trade execution failed';
                AppUtils.showToast(errorMsg, 'error');
            }
        } catch (error) {
            console.error('Live trade execution error:', error);
            AppUtils.showToast('Failed to execute live trade', 'error');
        } finally {
            this.isLiveConfirmationPending = false;
        }
    }

    async refreshTradeData() {
        // Refresh portfolio and trade data after trade execution
        const refreshPromises = [
            this.refreshPortfolioData(),
            this.refreshTradeHistory()
        ];
        
        try {
            await Promise.all(refreshPromises);
        } catch (error) {
            console.debug('Data refresh error:', error);
        }
    }

    async refreshPortfolioData() {
        try {
            const data = await AppUtils.fetchJSON('/api/current-holdings', { 
                cache: 'no-store' 
            });
            
            if (data && data.holdings) {
                // Update holdings table or trigger portfolio refresh
                window.dispatchEvent(new CustomEvent('portfolioUpdated', { 
                    detail: data 
                }));
            }
        } catch (error) {
            console.debug('Portfolio refresh failed:', error);
        }
    }

    async refreshTradeHistory() {
        try {
            const data = await AppUtils.fetchJSON('/api/recent-trades', { 
                cache: 'no-store' 
            });
            
            if (data && data.trades) {
                this.allTrades = data.trades;
                // Update trades table
                window.dispatchEvent(new CustomEvent('tradesUpdated', { 
                    detail: data 
                }));
            }
        } catch (error) {
            console.debug('Trade history refresh failed:', error);
        }
    }
}

// Global functions for modal callbacks (maintain backward compatibility)
window.confirmBuyOrder = async function(symbol) {
    const amount = document.getElementById('buyAmount')?.value || 100;
    const tradeManager = window.tradeManager;
    
    if (tradeManager) {
        await tradeManager.buyBackPosition(symbol);
    }
    
    // Hide modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('buyModal'));
    if (modal) modal.hide();
};

window.confirmSellOrder = async function(symbol) {
    const quantity = document.getElementById('sellQuantity')?.value || 0;
    const tradeManager = window.tradeManager;
    
    if (tradeManager && quantity > 0) {
        await tradeManager.executeTakeProfit(symbol, quantity);
    }
    
    // Hide modal  
    const modal = bootstrap.Modal.getInstance(document.getElementById('sellModal'));
    if (modal) modal.hide();
};