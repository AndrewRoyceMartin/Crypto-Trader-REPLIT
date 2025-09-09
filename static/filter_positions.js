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
        
        // Apply bot criteria filter
        if (botCriteriaFilter === 'bot-will-buy' && buySignal !== 'BOT WILL BUY') {
            showRow = false;
        } else if (botCriteriaFilter === 'high-confidence' && confidenceScore < 75) {
            showRow = false;
        } else if (botCriteriaFilter === 'excellent-confidence' && confidenceScore < 85) {
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