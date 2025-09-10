// Filter function for available positions
function filterAvailablePositions() {
    const symbolFilter = document.getElementById('position-filter').value.toLowerCase();
    const balanceFilter = document.getElementById('balance-filter').value;
    const botCriteriaFilter = document.getElementById('bot-criteria-filter').value;
    const clearBtn = document.getElementById('clear-filter-btn');
    const table = document.getElementById('available-table');
    const tbody = table ? table.querySelector('tbody') : null;
    
    if (!tbody) return;
    
    const rows = tbody.querySelectorAll('tr[data-symbol]');
    
    let visibleCount = 0;
    const totalCount = rows.length;
    
    // Show/hide clear button
    if (symbolFilter || balanceFilter || botCriteriaFilter) {
        if (clearBtn) clearBtn.style.display = 'block';
    } else {
        if (clearBtn) clearBtn.style.display = 'none';
    }
    
    rows.forEach(row => {
        const symbol = row.getAttribute('data-symbol').toLowerCase();
        const hasBalance = row.getAttribute('data-has-balance') === 'true';
        const confidenceScore = parseFloat(row.getAttribute('data-confidence-score') || '0');
        const buySignal = row.getAttribute('data-buy-signal') || '';
        
        let showRow = true;
        
        // Apply symbol filter
        if (symbolFilter && !symbol.includes(symbolFilter)) {
            showRow = false;
        }
        
        // Apply balance filter
        if (balanceFilter === 'with-balance' && !hasBalance) {
            showRow = false;
        } else if (balanceFilter === 'zero-balance' && hasBalance) {
            showRow = false;
        }
        
        // Apply bot criteria filter - Enhanced for 6-Factor Analysis System
        if (botCriteriaFilter === 'bot-will-buy' && buySignal !== 'BOT WILL BUY') {
            showRow = false;
        } else if (botCriteriaFilter === 'strong-buy-setup' && confidenceScore < 70) {
            // Strong Buy Setup: 70%+ confidence (6-factor analysis indicates strong entry opportunity)
            showRow = false;
        } else if (botCriteriaFilter === 'good-entry' && confidenceScore < 60) {
            // Good Entry: 60-69% confidence (6-factor analysis shows favorable conditions)
            showRow = false;
        } else if (botCriteriaFilter === 'high-confidence' && confidenceScore < 75) {
            // Legacy high confidence filter (75%+) 
            showRow = false;
        } else if (botCriteriaFilter === 'excellent-confidence' && confidenceScore < 85) {
            // Legacy excellent confidence filter (85%+)
            showRow = false;
        } else if (botCriteriaFilter === 'buy-signal' && buySignal !== 'BUY') {
            // 6-Factor BUY timing signal
            showRow = false;
        } else if (botCriteriaFilter === 'strong-buy' && buySignal !== 'STRONG_BUY') {
            // Legacy strong buy filter
            showRow = false;
        } else if (botCriteriaFilter === 'buy' && buySignal !== 'BUY') {
            // Legacy buy filter
            showRow = false;
        } else if (botCriteriaFilter === 'cautious-buy' && buySignal !== 'CAUTIOUS_BUY') {
            // Legacy cautious buy filter
            showRow = false;
        } else if (botCriteriaFilter === 'wait-signal' && buySignal !== 'WAIT') {
            // 6-Factor WAIT timing signal
            showRow = false;
        } else if (botCriteriaFilter === 'wait' && buySignal !== 'WAIT') {
            // Legacy wait filter
            showRow = false;
        } else if (botCriteriaFilter === 'avoid-signal' && buySignal !== 'AVOID') {
            // 6-Factor AVOID timing signal
            showRow = false;
        } else if (botCriteriaFilter === 'avoid' && buySignal !== 'AVOID') {
            // Legacy avoid filter
            showRow = false;
        } else if (botCriteriaFilter === 'mixed-signals' && (confidenceScore < 45 || confidenceScore >= 60)) {
            // Mixed Signals: 45-59% confidence range
            showRow = false;
        } else if (botCriteriaFilter === 'poor-setup' && confidenceScore >= 45) {
            // Poor Setup: Below 45% confidence
            showRow = false;
        }
        
        // Show/hide row
        if (showRow) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Update count display
    const filteredCountEl = document.getElementById('filtered-count');
    const totalCountEl = document.getElementById('total-count');
    if (filteredCountEl) filteredCountEl.textContent = visibleCount;
    if (totalCountEl) totalCountEl.textContent = totalCount;
}

function clearPositionFilter() {
    document.getElementById('position-filter').value = '';
    document.getElementById('balance-filter').value = '';
    document.getElementById('bot-criteria-filter').value = '';
    filterAvailablePositions();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Position filters initialized');
    
    // Initial call to set up counts
    setTimeout(filterAvailablePositions, 1000);
});