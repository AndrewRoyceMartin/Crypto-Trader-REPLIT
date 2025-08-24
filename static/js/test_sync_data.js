let testData = null;

function runSyncTests() {
    console.log('🔥 runSyncTests() called!');
    
    // Update debug display
    const debugDiv = document.getElementById('button-debug');
    if (debugDiv) {
        debugDiv.innerHTML = '🔥 runSyncTests() called at ' + new Date().toLocaleTimeString();
    }
    
    const button = document.getElementById('run-tests-btn') || document.querySelector('.btn-primary');
    if (!button) {
        console.error('❌ Button not found in runSyncTests');
        if (debugDiv) debugDiv.innerHTML += '<br>❌ Button not found';
        return;
    }
    
    console.log('✅ Button found, starting tests...');
    if (debugDiv) debugDiv.innerHTML += '<br>✅ Button found, starting API call...';
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner refresh-icon me-2"></i>Running Tests...';

    fetch('/api/test-sync-data', {
        method: 'GET',
        cache: 'no-store',
        headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        testData = data;
        displayTestResults(data);
        updateOverview(data);
    })
    .catch(error => {
        console.error('Test execution failed:', error);
        document.getElementById('test-results-container').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Test Execution Failed:</strong> ${error.message}
            </div>
        `;
    })
    .finally(() => {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-play me-2"></i>Run All Tests';
    });
}

function updateOverview(data) {
    const testResults = data.test_results || {};
    const totalTests = Object.keys(testResults).length;
    const passedTests = Object.values(testResults).filter(t => t.status === 'pass').length;
    const failedTests = Object.values(testResults).filter(t => t.status === 'fail').length;

    document.getElementById('tests-run').textContent = totalTests;
    document.getElementById('tests-passed').textContent = passedTests;
    document.getElementById('tests-failed').textContent = failedTests;
    document.getElementById('last-run').textContent = new Date(data.timestamp).toLocaleTimeString();
}

function displayTestResults(data) {
    const container = document.getElementById('test-results-container');
    const testResults = data.test_results || {};

    if (Object.keys(testResults).length === 0) {
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                No test results available.
            </div>
        `;
        return;
    }

    let html = '<div class="row">';

    Object.entries(testResults).forEach(([testName, result]) => {
        const cardClass = result.status === 'pass' ? 'pass' : 
                        result.status === 'fail' ? 'fail' : 'warning';
        const statusClass = result.status === 'pass' ? 'pass' : 
                          result.status === 'fail' ? 'fail' : 'warning';
        const icon = result.status === 'pass' ? 'fa-check-circle' : 
                   result.status === 'fail' ? 'fa-times-circle' : 'fa-exclamation-triangle';

        html += `
            <div class="col-lg-6 mb-3">
                <div class="card test-card ${cardClass}">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">${getTestDisplayName(testName)}</h6>
                        <span class="sync-status ${statusClass}">
                            <i class="fas ${icon} me-1"></i>${result.status.toUpperCase()}
                        </span>
                    </div>
                    <div class="card-body">
                        ${generateTestContent(testName, result)}
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
    
    // Initialize tooltips for the test cards
    initializeTooltips();

    // Create a nicely formatted HTML display instead of raw JSON
    const rawDataDiv = document.getElementById('raw-data');
    let htmlOutput = `
        <div class="mb-3">
            <strong>Test Session:</strong> ${new Date(data.timestamp).toLocaleString()}<br>
            <strong>OKX Endpoint:</strong> ${data.okx_endpoint}<br>
            <strong>Tests Available:</strong> ${data.tests_available}
        </div>
        <h6>Test Results Summary:</h6>
    `;
    
    Object.entries(data.test_results || {}).forEach(([testName, result]) => {
        const statusColor = result.status === 'pass' ? 'success' : result.status === 'fail' ? 'danger' : 'warning';
        const statusIcon = result.status === 'pass' ? 'fa-check-circle' : result.status === 'fail' ? 'fa-times-circle' : 'fa-exclamation-triangle';
        
        htmlOutput += `
            <div class="border-start border-${statusColor} ps-3 mb-3">
                <h6 class="text-${statusColor}">
                    <i class="fas ${statusIcon} me-2"></i>${getTestDisplayName(testName)}
                </h6>
                <small class="text-muted">Status: <span class="text-${statusColor}">${result.status.toUpperCase()}</span></small>
        `;
        
        // Add specific details based on test type with tooltips
        if (result.perfect_matches !== undefined) {
            htmlOutput += `<br><small>✓ 
                <span data-bs-toggle="tooltip" data-bs-placement="top" title="Perfect Matches: Holdings quantities and values that exactly match between OKX API and dashboard display. Mismatches: Discrepancies that could indicate sync issues.">
                    Perfect Matches: ${result.perfect_matches}, Mismatches: ${result.mismatches || 0}
                </span>
            </small>`;
        }
        if (result.calculation_accuracy !== undefined) {
            htmlOutput += `<br><small>✓ 
                <span data-bs-toggle="tooltip" data-bs-placement="top" title="Percentage of P&L calculations that match OKX's native values within acceptable tolerance. 100% indicates perfect mathematical accuracy.">
                    Calculation Accuracy: ${result.calculation_accuracy}%
                </span>
            </small>`;
        }
        if (result.data_is_recent !== undefined) {
            htmlOutput += `<br><small>✓ 
                <span data-bs-toggle="tooltip" data-bs-placement="top" title="Data Recent: Confirms prices are fetched within the last few minutes. Live Holdings: Ensures position data comes directly from OKX rather than cache.">
                    Data Recent: ${result.data_is_recent ? 'Yes' : 'No'}, Live Holdings: ${result.holdings_marked_live ? 'Yes' : 'No'}
                </span>
            </small>`;
        }
        if (result.account_accessible !== undefined) {
            htmlOutput += `<br><small>✓ 
                <span data-bs-toggle="tooltip" data-bs-placement="top" title="Account Access: Verifies API can connect to OKX futures/margin endpoints. Positions: Current number of active derivative positions.">
                    Account Access: ${result.account_accessible ? 'Yes' : 'No'}, Positions: ${result.active_positions}
                </span>
            </small>`;
        }
        
        htmlOutput += `</div>`;
    });
    
    rawDataDiv.innerHTML = htmlOutput;
    
    // Initialize Bootstrap tooltips for all elements
    initializeTooltips();
}

function getTestDisplayName(testName) {
    const names = {
        'holdings_sync': 'Holdings Synchronization',
        'price_freshness': 'Price Data Freshness',
        'strategy_pnl': 'Strategy P&L Testing',
        'unrealized_pnl': 'Unrealized P&L Accuracy',
        'futures_margin': 'Futures/Margin Access',
        'bot_state_sync': 'Bot State Synchronization',
        'bot_runtime_status': 'Bot Runtime Status',
        'cache_disabled': 'Cache Bypass Validation',
        'mode_sandbox_sync': 'Live Mode Verification',
        'portfolio_totals': 'Portfolio Totals Accuracy',
        'price_consistency': 'Price Data Consistency',
        'symbol_roundtrip': 'Symbol Mapping Integrity',
        'target_price_lock': 'Target Price Stability',
        'timestamp_integrity': 'Data Timestamp Validation'
    };
    // Improved test name formatting with global replace and proper title case
    return names[testName] || testName.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function generateTestContent(testName, result) {
    if (result.status === 'error') {
        return `
            <div class="alert alert-danger mb-0">
                <strong>Error:</strong> ${result.error}
            </div>
        `;
    }

    let content = `<p class="text-muted mb-3">${getTestDescription(testName)}</p>`;

    // Bot State Sync - Enhanced display for bot running status
    if ((testName === 'bot_state_sync' || testName === 'bot_runtime_status') && result.status_details) {
        content += `
            <div class="alert ${result.bot_running ? 'alert-success' : 'alert-warning'} mb-3">
                <h6 class="mb-2">🤖 Bot Running Status</h6>
                ${result.status_details.map(detail => `<div>${detail}</div>`).join('')}
            </div>
        `;
        
        content += `
            <div class="row">
                <div class="col-6">
                    <strong>Status:</strong> 
                    <span class="${result.bot_running ? 'text-success' : 'text-warning'}">
                        ${result.bot_running ? 'RUNNING' : 'STOPPED'}
                    </span>
                </div>
                <div class="col-6">
                    <strong>Mode:</strong> 
                    <span class="text-info">${result.bot_mode || 'N/A'}</span>
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-6">
                    <strong>Runtime:</strong> 
                    <span class="text-primary">${result.bot_runtime_human || 'N/A'}</span>
                </div>
                <div class="col-6">
                    <strong>Trading Active:</strong> 
                    <span class="${result.trading_active ? 'text-success' : 'text-warning'}">
                        ${result.trading_active ? 'YES' : 'NO'}
                    </span>
                </div>
            </div>
        `;
        
        if (result.issues && result.issues.length > 0) {
            content += `
                <div class="mt-3">
                    <strong class="text-danger">Issues:</strong>
                    <ul class="mb-0">
                        ${result.issues.map(issue => `<li class="text-danger">${issue}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        return content;
    }

    // Add specific metrics based on test type with tooltips
    if (result.perfect_matches !== undefined) {
        content += `
            <div class="row">
                <div class="col-6">
                    <strong data-bs-toggle="tooltip" data-bs-placement="top" title="Number of holdings where quantities and values exactly match between OKX API and dashboard">Perfect Matches:</strong> 
                    <span class="text-success">${result.perfect_matches}</span>
                </div>
                <div class="col-6">
                    <strong data-bs-toggle="tooltip" data-bs-placement="top" title="Holdings with discrepancies that could indicate synchronization issues">Mismatches:</strong> 
                    <span class="text-danger">${result.mismatches || 0}</span>
                </div>
            </div>
        `;
    }

    if (result.timestamps_different !== undefined) {
        content += `
            <div class="row">
                <div class="col-6">
                    <strong data-bs-toggle="tooltip" data-bs-placement="top" title="Confirms that data timestamps are different between API calls, indicating fresh data retrieval rather than cached responses">Live Updates:</strong> 
                    <span class="${result.timestamps_different ? 'live-indicator' : 'cached-indicator'}">
                        ${result.timestamps_different ? 'YES' : 'NO'}
                    </span>
                </div>
                <div class="col-6">
                    <strong data-bs-toggle="tooltip" data-bs-placement="top" title="Ensures position data is marked as live from OKX rather than cached or estimated values">Holdings Live:</strong> 
                    <span class="${result.holdings_marked_live ? 'live-indicator' : 'cached-indicator'}">
                        ${result.holdings_marked_live ? 'YES' : 'NO'}
                    </span>
                </div>
            </div>
        `;
    }

    if (result.calculation_accuracy !== undefined) {
        content += `
            <div class="row">
                <div class="col-6">
                    <strong data-bs-toggle="tooltip" data-bs-placement="top" title="Percentage of P&L calculations that match OKX's native values within acceptable tolerance. 100% indicates perfect mathematical accuracy">Accuracy:</strong> 
                    <span class="text-primary">${result.calculation_accuracy}%</span>
                </div>
                <div class="col-6">
                    <strong data-bs-toggle="tooltip" data-bs-placement="top" title="Number of individual calculations tested for accuracy against OKX's native P&L values">Test Cases:</strong> 
                    ${result.test_cases || 0}
                </div>
            </div>
        `;
    }

    return content;
}

function getTestDescription(testName) {
    const descriptions = {
        'holdings_sync': 'Verifies that portfolio holdings match exactly between OKX API and dashboard display.',
        'price_freshness': 'Ensures market prices are fetched live from OKX and not served from cache.',
        'strategy_pnl': 'Validates that trading strategy profit/loss calculations are mathematically accurate.',
        'unrealized_pnl': 'Checks that unrealized P&L calculations match OKX account data.',
        'futures_margin': 'Verifies access to futures and margin trading account information.',
        'bot_state_sync': 'Confirms bot and trading state consistency across all system components.',
        'bot_runtime_status': 'Validates bot runtime status, mode, and trading activity consistency.',
        'cache_disabled': 'Validates that live data is fetched directly from OKX without cache interference.',
        'mode_sandbox_sync': 'Ensures the system is correctly configured for live trading mode.',
        'portfolio_totals': 'Validates mathematical accuracy of portfolio total calculations.',
        'price_consistency': 'Compares price data from different OKX API endpoints for consistency.',
        'symbol_roundtrip': 'Tests symbol mapping accuracy between different API formats.',
        'target_price_lock': 'Ensures target price stability and prevents exponential recalculation.',
        'timestamp_integrity': 'Verifies data timestamp accuracy and freshness validation.'
    };
    return descriptions[testName] || 'Validates synchronization and accuracy of OKX data integration.';
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    try {
        // Dispose of any existing tooltips first
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            const existingTooltip = bootstrap.Tooltip.getInstance(el);
            if (existingTooltip) {
                existingTooltip.dispose();
            }
        });

        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipTriggerList.forEach(function (tooltipTriggerEl) {
            new bootstrap.Tooltip(tooltipTriggerEl, {
                delay: { show: 300, hide: 100 },
                placement: 'top',
                html: true
            });
        });
    } catch (error) {
        console.error('Error initializing tooltips:', error);
    }
}

// IMMEDIATE button binding - try multiple approaches
function bindButton() {
    console.log('🔍 Attempting to bind button...');
    const btn = document.getElementById('run-tests-btn');
    console.log('🔍 Button element:', btn);
    
    if (btn) {
        // Remove any existing listeners
        btn.replaceWith(btn.cloneNode(true));
        const newBtn = document.getElementById('run-tests-btn');
        
        newBtn.addEventListener('click', function(e) {
            console.log('🚀 BUTTON CLICKED!');
            e.preventDefault();
            e.stopPropagation();
            runSyncTests();
        });
        
        // Also try mousedown for mobile
        newBtn.addEventListener('mousedown', function(e) {
            console.log('🚀 BUTTON MOUSEDOWN!');
        });
        
        console.log('✅ Button bound successfully');
        return true;
    }
    console.log('❌ Button not found');
    return false;
}

// Try multiple binding attempts
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔄 DOM loaded, initializing...');
    initializeTooltips();
    
    // Try binding immediately
    if (!bindButton()) {
        // Try again after short delay
        setTimeout(bindButton, 100);
        setTimeout(bindButton, 500);
        setTimeout(bindButton, 1000);
    }
    
    // Auto-run tests after 3 seconds
    setTimeout(() => {
        console.log('🔄 Auto-running tests...');
        runSyncTests();
    }, 3000);
});

// Also initialize tooltips when Bootstrap is ready
window.addEventListener('load', function() {
    setTimeout(initializeTooltips, 500);
});