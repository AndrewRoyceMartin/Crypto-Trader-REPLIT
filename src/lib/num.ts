// REPAIR: Utility functions for robust number parsing and formatting
export const parseNumber = (s: string): number => {
    if (!s || typeof s !== 'string') return 0;
    const cleaned = s.replace(/[^\d.+-]/g, '');
    const parsed = parseFloat(cleaned);
    return isFinite(parsed) ? parsed : 0;
};

export const fmtCurrency = (n: number): string => {
    if (!isFinite(n)) return '—';
    return n.toLocaleString(undefined, {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
};

export const fmtPercent = (n: number): string => {
    if (!isFinite(n)) return '—';
    return `${n.toFixed(2)}%`;
};

export const fmtNumber = (n: number, decimals = 2): string => {
    if (!isFinite(n)) return '—';
    return n.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
};