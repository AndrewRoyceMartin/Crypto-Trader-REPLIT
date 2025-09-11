// REPAIR: Utility functions for robust number parsing and formatting
export const num = (v) => {
    if (typeof v === 'number') return v;
    if (typeof v === 'string') {
        const n = parseFloat(v.replace(/[^\d.+\-]/g,''));
        return Number.isFinite(n) ? n : NaN;
    }
    return NaN;
};

export const fmtCurrency = (n) => Number.isFinite(n) ? n.toLocaleString(undefined,{style:'currency',currency:'USD'}) : '—';
export const fmtPercent = (n) => Number.isFinite(n) ? `${n.toFixed(2)}%` : '—';
export const fmtNumber = (n, decimals = 2) => Number.isFinite(n) ? n.toFixed(decimals) : '—';