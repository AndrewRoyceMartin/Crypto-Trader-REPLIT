// Core utilities module
export class AppUtils {
    static getAdminToken() {
        const m = document.querySelector('meta[name="admin-token"]');
        return m ? m.content : '';
    }

    static async fetchJSON(url, { method='GET', body, timeout=10000, headers={}, noStore=true } = {}) {
        const ctl = new AbortController();
        const t = setTimeout(()=>ctl.abort(), timeout);
        const h = {
            'Content-Type': 'application/json',
            ...(noStore ? {'Cache-Control': 'no-store'} : {}),
            ...(AppUtils.getAdminToken() ? {'X-Admin-Token': AppUtils.getAdminToken()} : {}),
            ...headers
        };
        
        try {
            const res = await fetch(url, { 
                method, 
                headers: h, 
                body: body ? JSON.stringify(body) : undefined, 
                signal: ctl.signal, 
                cache: 'no-store' 
            });
            
            if (!res.ok) {
                console.debug(`API ${url} returned ${res.status}: ${res.statusText}`);
                return null;
            }
            
            const contentType = res.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.debug(`API ${url} returned non-JSON content: ${contentType}`);
                return null;
            }
            
            return await res.json();
        } catch (error) {
            console.debug(`Failed to fetch ${url}:`, error.message);
            return null;
        } finally { 
            clearTimeout(t); 
        }
    }

    static currentCurrency() {
        return document.getElementById('currency-selector')?.value || 'USD';
    }

    static safeNum(value, fallback = 0) {
        const num = Number(value);
        return isNaN(num) ? fallback : num;
    }

    static formatCurrency(amount, currency = null) {
        const numericAmount = Number(amount) || 0;
        const curr = currency || AppUtils.currentCurrency();
        
        if (curr === 'USD') {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(numericAmount);
        }
        
        return `${numericAmount.toFixed(2)} ${curr}`;
    }

    static formatCryptoPrice(amount, currency = null) {
        const numericAmount = Number(amount) || 0;
        const curr = currency || AppUtils.currentCurrency();
        
        if (numericAmount < 0.01) {
            return `${numericAmount.toFixed(8)} ${curr}`;
        } else if (numericAmount < 1) {
            return `${numericAmount.toFixed(4)} ${curr}`;
        } else {
            return `${numericAmount.toFixed(2)} ${curr}`;
        }
    }

    static formatUptime(totalSeconds) {
        const days = Math.floor(totalSeconds / 86400);
        const hours = Math.floor((totalSeconds % 86400) / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = Math.floor(totalSeconds % 60);
        
        if (days > 0) return `${days}d ${hours}h ${minutes}m`;
        if (hours > 0) return `${hours}h ${minutes}m ${seconds}s`;
        if (minutes > 0) return `${minutes}m ${seconds}s`;
        return `${seconds}s`;
    }

    static formatDateTime(timestamp) {
        if (!timestamp) return 'N/A';
        try {
            const date = new Date(timestamp);
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return 'N/A';
        }
    }

    static getCoinDisplay(symbol) {
        const coinMap = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'SOL': 'Solana',
            'GALA': 'Gala',
            'TRX': 'TRON',
            'PEPE': 'Pepe'
        };
        return coinMap[symbol] || symbol;
    }

    static showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'} border-0 show`;
        toast.setAttribute('role', 'alert');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 4000);
    }

    static createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }
}