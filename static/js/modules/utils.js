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
            
            // Check if response is OK first
            if (!res.ok) {
                console.debug(`API ${url} returned ${res.status}: ${res.statusText}`);
                return null;
            }
            
            // Check content type before parsing JSON
            const contentType = res.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.debug(`API ${url} returned non-JSON content: ${contentType}`);
                return null;
            }
            
            const data = await res.json();
            return data;
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
        const numericAmount = AppUtils.safeNum(amount, 0);
        const curr = currency || AppUtils.currentCurrency();
        
        // Handle very small amounts with extended decimal places
        if (Math.abs(numericAmount) < 0.000001 && numericAmount !== 0) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: curr,
                minimumFractionDigits: 8,
                maximumFractionDigits: 8
            }).format(numericAmount);
        }

        // Handle small amounts (under $0.01) with more decimal places
        if (Math.abs(numericAmount) < 0.01 && numericAmount !== 0) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: curr,
                minimumFractionDigits: 4,
                maximumFractionDigits: 6
            }).format(numericAmount);
        }
        
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
        console[type === 'error' ? 'error' : 'log'](message);
        
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        
        // Create toast element with improved animations
        const toastEl = document.createElement('div');
        toastEl.className = `toast-message ${type}`;
        toastEl.textContent = message;
        
        // Add to container
        toastContainer.appendChild(toastEl);
        
        // Show animation
        requestAnimationFrame(() => {
            toastEl.classList.add('show');
        });
        
        // Auto-remove after 4 seconds with fade animation
        setTimeout(() => {
            toastEl.classList.remove('show');
            setTimeout(() => {
                if (toastEl.parentNode) {
                    toastEl.parentNode.removeChild(toastEl);
                }
            }, 300);
        }, 4000);
    }

    static createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1080';
        document.body.appendChild(container);
        return container;
    }

    // Resilient number parsing for table sorting
    static toNum(x) {
        if (x == null) return 0;
        const s = String(x).replace(/[\$,]/g,'').replace('%','').trim();
        const n = parseFloat(s); 
        return isNaN(n) ? 0 : n;
    }

    // Enhanced number formatter with suffix support
    static formatNumber(amount) {
        const numericAmount = AppUtils.safeNum(amount, 0);
        
        if (numericAmount >= 1e12) {
            return (numericAmount / 1e12).toFixed(1) + 'T';
        } else if (numericAmount >= 1e9) {
            return (numericAmount / 1e9).toFixed(1) + 'B';
        } else if (numericAmount >= 1e6) {
            return (numericAmount / 1e6).toFixed(1) + 'M';
        } else if (numericAmount >= 1e3) {
            return (numericAmount / 1e3).toFixed(1) + 'K';
        } else {
            return numericAmount.toFixed(2);
        }
    }
}