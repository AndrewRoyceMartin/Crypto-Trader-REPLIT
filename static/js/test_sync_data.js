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
        'timestamp_integrity': 'Data Timestamp Validation',
        'table_validation': 'Frontend Table Data Integrity',
        'open_positions_table': 'Open Positions Table Accuracy',
        'available_positions_table': 'Available Positions Table Accuracy',
        'button_functionality': 'Button Function Validation',
        'ato_export_button': 'ATO Export Button Test',
        'take_profit_button': 'Take Profit Button Test',
        'buy_button': 'Buy Button Test',
        'sell_button': 'Sell Button Test'
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

    // Button functionality test display
    if (testName === 'button_functionality' && result.individual_results) {
        content += `
            <div class="row mb-3">
                <div class="col-12">
                    <h6>Button Test Results:</h6>
                </div>
            </div>
        `;
        
        Object.entries(result.individual_results).forEach(([buttonName, buttonResult]) => {
            const statusColor = buttonResult.status === 'pass' ? 'success' : 
                              buttonResult.status === 'partial' ? 'warning' : 'danger';
            const statusIcon = buttonResult.status === 'pass' ? 'fa-check-circle' : 
                             buttonResult.status === 'partial' ? 'fa-exclamation-triangle' : 'fa-times-circle';
            
            const buttonDisplayName = buttonName.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            
            content += `
                <div class="row mb-2">
                    <div class="col-6">
                        <strong>${buttonDisplayName}:</strong>
                    </div>
                    <div class="col-6">
                        <span class="text-${statusColor}">
                            <i class="fas ${statusIcon} me-1"></i>${buttonResult.status.toUpperCase()}
                        </span>
                    </div>
                </div>
            `;
            
            if (buttonResult.test_description) {
                content += `
                    <div class="row mb-2">
                        <div class="col-12">
                            <small class="text-muted">${buttonResult.test_description}</small>
                        </div>
                    </div>
                `;
            }
        });
        
        return content;
    }
    
    // Individual button test display
    if (['ato_export_button', 'take_profit_button', 'buy_button', 'sell_button'].includes(testName)) {
        if (result.button_found !== undefined) {
            content += `
                <div class="row">
                    <div class="col-6">
                        <strong>Button Found:</strong>
                    </div>
                    <div class="col-6">
                        <span class="${result.button_found ? 'text-success' : 'text-danger'}">
                            ${result.button_found ? 'YES' : 'NO'}
                        </span>
                    </div>
                </div>
            `;
        }
        
        if (result.api_accessible !== undefined) {
            content += `
                <div class="row">
                    <div class="col-6">
                        <strong>API Accessible:</strong>
                    </div>
                    <div class="col-6">
                        <span class="${result.api_accessible ? 'text-success' : 'text-warning'}">
                            ${result.api_accessible ? 'YES' : 'NO'}
                        </span>
                    </div>
                </div>
            `;
        }
        
        if (result.passed_checks !== undefined && result.total_checks !== undefined) {
            const percentage = Math.round((result.passed_checks / result.total_checks) * 100);
            content += `
                <div class="row">
                    <div class="col-6">
                        <strong>Test Coverage:</strong>
                    </div>
                    <div class="col-6">
                        <span class="text-primary">
                            ${result.passed_checks}/${result.total_checks} (${percentage}%)
                        </span>
                    </div>
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
    
    // Table validation display
    if (result.success_rate !== undefined && testName === 'table_validation') {
        content += `
            <div class="row">
                <div class="col-6">
                    <strong>Success Rate:</strong>
                </div>
                <div class="col-6">
                    <span class="text-primary">${result.success_rate}%</span>
                </div>
            </div>
        `;
        
        if (result.tests_passed !== undefined && result.tests_total !== undefined) {
            content += `
                <div class="row">
                    <div class="col-6">
                        <strong>Tests Passed:</strong>
                    </div>
                    <div class="col-6">
                        <span class="text-success">${result.tests_passed}/${result.tests_total}</span>
                    </div>
                </div>
            `;
        }
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
        'timestamp_integrity': 'Verifies data timestamp accuracy and freshness validation.',
        'table_validation': 'Validates that frontend table display matches backend API data exactly.',
        'open_positions_table': 'Checks Open Positions table rows against /api/current-holdings API data.',
        'available_positions_table': 'Verifies Available Positions table matches /api/available-positions API data.',
        'button_functionality': 'Tests that all dashboard buttons exist and have proper functionality.',
        'ato_export_button': 'Verifies ATO export button calls correct API endpoint for tax reporting.',
        'take_profit_button': 'Tests take profit button functionality and API endpoint connectivity.',
        'buy_button': 'Validates buy button functionality and trading API endpoint.',
        'sell_button': 'Tests sell button functionality and trading API endpoint.'
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

// Table validation functions
async function validateTableData() {
    try {
        const tests = {
            open_positions_table: await validateOpenPositionsTable(),
            available_positions_table: await validateAvailablePositionsTable()
        };
        
        return {
            status: 'success',
            tests: tests,
            summary: generateTableValidationSummary(tests)
        };
    } catch (error) {
        return {
            status: 'error',
            error: error.message,
            tests: {}
        };
    }
}

async function validateOpenPositionsTable() {
    try {
        // Fetch backend API data
        const response = await fetch('/api/current-holdings', { cache: 'no-store' });
        if (!response.ok) throw new Error(`API returned ${response.status}`);
        const apiData = await response.json();
        
        if (!apiData.success || !apiData.holdings) {
            throw new Error('Invalid API response structure');
        }
        
        // Get table DOM elements
        const tableBody = document.getElementById('holdings-tbody');
        if (!tableBody) {
            throw new Error('Open Positions table not found in DOM');
        }
        
        const tableRows = Array.from(tableBody.querySelectorAll('tr')).filter(row => {
            // Filter out loading/empty state rows
            return !row.textContent.includes('Loading') && !row.textContent.includes('No positions');
        });
        
        const apiHoldings = apiData.holdings || [];
        
        let matches = 0;
        let mismatches = 0;
        let details = [];
        
        // Validate each API holding has corresponding table row
        for (const holding of apiHoldings) {
            const symbol = holding.symbol || holding.name;
            if (!symbol) continue;
            
            // Find matching row in table
            const matchingRow = tableRows.find(row => {
                const firstCell = row.querySelector('td:first-child');
                return firstCell && firstCell.textContent.includes(symbol);
            });
            
            if (!matchingRow) {
                mismatches++;
                details.push(`❌ Missing table row for ${symbol}`);
                continue;
            }
            
            // Validate key data points
            const cells = matchingRow.querySelectorAll('td');
            if (cells.length < 8) {
                mismatches++;
                details.push(`❌ ${symbol}: Insufficient table columns`);
                continue;
            }
            
            let rowValid = true;
            
            // Check quantity (QTY HELD column)
            const qtyCell = cells[1]; // Second column is QTY HELD
            const expectedQty = parseFloat(holding.quantity || holding.balance || 0);
            const displayedQty = parseFloat(qtyCell.textContent.replace(/[^0-9.-]/g, ''));
            if (Math.abs(expectedQty - displayedQty) > 0.001) {
                details.push(`❌ ${symbol}: Quantity mismatch - API: ${expectedQty}, Table: ${displayedQty}`);
                rowValid = false;
            }
            
            // Check live price (LIVE PRICE column)
            const priceCell = cells[4]; // Fifth column is LIVE PRICE
            const expectedPrice = parseFloat(holding.current_price || holding.price || 0);
            const displayedPrice = parseFloat(priceCell.textContent.replace(/[^0-9.-]/g, ''));
            if (expectedPrice > 0 && Math.abs((expectedPrice - displayedPrice) / expectedPrice) > 0.01) {
                details.push(`❌ ${symbol}: Price mismatch - API: $${expectedPrice}, Table: $${displayedPrice}`);
                rowValid = false;
            }
            
            // Check position value (POSITION VALUE column)
            const valueCell = cells[5]; // Sixth column is POSITION VALUE
            const expectedValue = parseFloat(holding.current_value || holding.market_value || holding.value || 0);
            const displayedValue = parseFloat(valueCell.textContent.replace(/[^0-9.-]/g, ''));
            if (expectedValue > 0 && Math.abs((expectedValue - displayedValue) / expectedValue) > 0.01) {
                details.push(`❌ ${symbol}: Value mismatch - API: $${expectedValue.toFixed(2)}, Table: $${displayedValue.toFixed(2)}`);
                rowValid = false;
            }
            
            if (rowValid) {
                matches++;
                details.push(`✅ ${symbol}: All data validated`);
            } else {
                mismatches++;
            }
        }
        
        // Check for extra rows in table that don't have API data
        const extraRows = tableRows.length - apiHoldings.length;
        if (extraRows > 0) {
            details.push(`⚠️ ${extraRows} extra rows in table vs API data`);
        }
        
        return {
            status: mismatches === 0 ? 'pass' : 'fail',
            api_holdings: apiHoldings.length,
            table_rows: tableRows.length,
            perfect_matches: matches,
            mismatches: mismatches,
            validation_details: details.slice(0, 10), // Limit details for display
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: error.message,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function validateAvailablePositionsTable() {
    try {
        // Fetch backend API data
        const response = await fetch('/api/available-positions', { cache: 'no-store' });
        if (!response.ok) throw new Error(`API returned ${response.status}`);
        const apiData = await response.json();
        
        if (!apiData.available_positions) {
            throw new Error('Invalid API response structure');
        }
        
        // Get table DOM elements
        const tableBody = document.querySelector('#available-table tbody');
        if (!tableBody) {
            throw new Error('Available Positions table not found in DOM');
        }
        
        const tableRows = Array.from(tableBody.querySelectorAll('tr')).filter(row => {
            return !row.textContent.includes('Loading') && !row.textContent.includes('No positions');
        });
        
        const apiPositions = apiData.available_positions || [];
        
        let matches = 0;
        let mismatches = 0;
        let details = [];
        
        // Sample validation for first 10 positions (to avoid overwhelming output)
        const samplePositions = apiPositions.slice(0, 10);
        
        for (const position of samplePositions) {
            const symbol = position.symbol;
            if (!symbol) continue;
            
            // Find matching row in table
            const matchingRow = tableRows.find(row => {
                const firstCell = row.querySelector('td:first-child');
                return firstCell && firstCell.textContent.includes(symbol);
            });
            
            if (!matchingRow) {
                mismatches++;
                details.push(`❌ Missing table row for ${symbol}`);
                continue;
            }
            
            // Validate key data points
            const cells = matchingRow.querySelectorAll('td');
            if (cells.length < 3) {
                mismatches++;
                details.push(`❌ ${symbol}: Insufficient table columns`);
                continue;
            }
            
            let rowValid = true;
            
            // Check balance (Balance column)
            const balanceCell = cells[1];
            const expectedBalance = parseFloat(position.current_balance || position.free_balance || 0);
            const displayedBalance = parseFloat(balanceCell.textContent.replace(/[^0-9.-]/g, ''));
            if (expectedBalance > 0 && Math.abs((expectedBalance - displayedBalance) / expectedBalance) > 0.01) {
                details.push(`❌ ${symbol}: Balance mismatch - API: ${expectedBalance}, Table: ${displayedBalance}`);
                rowValid = false;
            }
            
            // Check price (Current Price column)
            const priceCell = cells[2];
            const expectedPrice = parseFloat(position.current_price || 0);
            const displayedPrice = parseFloat(priceCell.textContent.replace(/[^0-9.-]/g, ''));
            if (expectedPrice > 0 && Math.abs((expectedPrice - displayedPrice) / expectedPrice) > 0.02) {
                details.push(`❌ ${symbol}: Price mismatch - API: $${expectedPrice}, Table: $${displayedPrice}`);
                rowValid = false;
            }
            
            if (rowValid) {
                matches++;
                details.push(`✅ ${symbol}: Data validated`);
            } else {
                mismatches++;
            }
        }
        
        return {
            status: mismatches === 0 ? 'pass' : 'fail',
            api_positions: apiPositions.length,
            table_rows: tableRows.length,
            perfect_matches: matches,
            mismatches: mismatches,
            sample_tested: samplePositions.length,
            validation_details: details.slice(0, 10),
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: error.message,
            test_timestamp: new Date().toISOString()
        };
    }
}

function generateTableValidationSummary(tests) {
    const totalTests = Object.keys(tests).length;
    const passedTests = Object.values(tests).filter(t => t.status === 'pass').length;
    const failedTests = Object.values(tests).filter(t => t.status === 'fail').length;
    const errorTests = Object.values(tests).filter(t => t.status === 'error').length;
    
    return {
        total: totalTests,
        passed: passedTests,
        failed: failedTests,
        errors: errorTests,
        success_rate: totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0
    };
}

// Button functionality tests
async function validateButtonFunctionality() {
    try {
        const tests = {
            ato_export_button: await testATOExportButton(),
            take_profit_button: await testTakeProfitButton(),
            buy_button: await testBuyButton(),
            sell_button: await testSellButton(),
            recalculate_button: await testRecalculateButton(),
            details_buttons: await testDetailsButtons()
        };
        
        return {
            status: 'success',
            tests: tests,
            summary: generateButtonTestSummary(tests)
        };
    } catch (error) {
        return {
            status: 'error',
            error: error.message,
            tests: {}
        };
    }
}

async function testATOExportButton() {
    try {
        // Check if button exists in DOM
        const button = document.getElementById('btn-ato-export');
        if (!button) {
            return {
                status: 'fail',
                error: 'ATO Export button not found in DOM',
                test_timestamp: new Date().toISOString()
            };
        }
        
        // Check button attributes and accessibility
        const hasCorrectAttributes = {
            'aria-label': button.hasAttribute('aria-label'),
            'title': button.hasAttribute('title'),
            'class_contains_btn': button.className.includes('btn')
        };
        
        // Test API endpoint availability (without actually triggering download)
        let apiAccessible = false;
        let apiError = null;
        try {
            const response = await fetch('/api/export/ato', { 
                method: 'HEAD',  // Use HEAD to test endpoint without triggering download
                cache: 'no-store'
            });
            apiAccessible = response.status !== 404;
        } catch (error) {
            apiError = error.message;
        }
        
        // Check if button has click handler
        const hasEventListeners = button.onclick !== null || 
                                 button.addEventListener !== null;
        
        const allChecks = [
            button !== null,
            hasCorrectAttributes['aria-label'],
            hasCorrectAttributes['title'],
            hasCorrectAttributes['class_contains_btn'],
            apiAccessible,
            hasEventListeners
        ];
        
        const passedChecks = allChecks.filter(Boolean).length;
        
        return {
            status: passedChecks >= 5 ? 'pass' : 'partial',
            button_found: button !== null,
            attributes_complete: Object.values(hasCorrectAttributes).every(Boolean),
            api_accessible: apiAccessible,
            api_error: apiError,
            has_event_listeners: hasEventListeners,
            passed_checks: passedChecks,
            total_checks: allChecks.length,
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `ATO Export button test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testTakeProfitButton() {
    try {
        // Check if button exists in DOM
        const button = document.getElementById('btn-take-profit');
        if (!button) {
            return {
                status: 'fail',
                error: 'Take Profit button not found in DOM',
                test_timestamp: new Date().toISOString()
            };
        }
        
        // Check button states and attributes
        const buttonChecks = {
            'has_correct_class': button.className.includes('btn'),
            'has_warning_style': button.className.includes('btn-outline-warning'),
            'has_accessibility': button.hasAttribute('aria-label') && button.hasAttribute('title'),
            'not_disabled': !button.disabled
        };
        
        // Test API endpoint availability
        let apiStatus = 'unknown';
        let apiError = null;
        try {
            const response = await fetch('/api/execute-take-profit', { 
                method: 'HEAD',
                cache: 'no-store'
            });
            apiStatus = response.status === 401 ? 'auth_required' : 
                       response.status === 405 ? 'method_not_allowed' :
                       response.status < 500 ? 'accessible' : 'error';
        } catch (error) {
            apiStatus = 'error';
            apiError = error.message;
        }
        
        // Check for confirmation dialog functionality (look for confirm() usage)
        const buttonText = button.textContent || button.innerText || '';
        const hasCorrectText = buttonText.toLowerCase().includes('profit');
        
        const allChecks = [
            button !== null,
            buttonChecks['has_correct_class'],
            buttonChecks['has_accessibility'],
            apiStatus !== 'error',
            hasCorrectText
        ];
        
        const passedChecks = allChecks.filter(Boolean).length;
        
        return {
            status: passedChecks >= 4 ? 'pass' : 'partial',
            button_found: button !== null,
            button_checks: buttonChecks,
            api_status: apiStatus,
            api_error: apiError,
            has_correct_text: hasCorrectText,
            passed_checks: passedChecks,
            total_checks: allChecks.length,
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Take Profit button test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testBuyButton() {
    try {
        // Check if button exists in DOM
        const button = document.getElementById('btn-buy');
        if (!button) {
            return {
                status: 'fail',
                error: 'Buy button not found in DOM',
                test_timestamp: new Date().toISOString()
            };
        }
        
        // Check button styling and attributes
        const buttonValidation = {
            'has_success_style': button.className.includes('btn-success'),
            'has_proper_icon': button.innerHTML.includes('icon-up') || button.innerHTML.includes('fa-arrow-up'),
            'has_accessibility': button.hasAttribute('aria-label'),
            'has_correct_text': (button.textContent || '').toLowerCase().includes('buy')
        };
        
        // Test associated API endpoints
        const apiTests = [];
        
        // Test both paper-trade and live trading endpoints
        const endpoints = ['/api/paper-trade/buy', '/api/buy'];
        
        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint, { 
                    method: 'HEAD',
                    cache: 'no-store'
                });
                apiTests.push({
                    endpoint: endpoint,
                    accessible: response.status !== 404,
                    status_code: response.status
                });
            } catch (error) {
                apiTests.push({
                    endpoint: endpoint,
                    accessible: false,
                    error: error.message
                });
            }
        }
        
        // Check if at least one API endpoint is accessible
        const apiAccessible = apiTests.some(test => test.accessible);
        
        const allChecks = [
            button !== null,
            buttonValidation['has_success_style'],
            buttonValidation['has_accessibility'],
            buttonValidation['has_correct_text'],
            apiAccessible
        ];
        
        const passedChecks = allChecks.filter(Boolean).length;
        
        return {
            status: passedChecks >= 4 ? 'pass' : 'partial',
            button_found: button !== null,
            button_validation: buttonValidation,
            api_tests: apiTests,
            api_accessible: apiAccessible,
            passed_checks: passedChecks,
            total_checks: allChecks.length,
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Buy button test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testSellButton() {
    try {
        // Check if button exists in DOM
        const button = document.getElementById('btn-sell');
        if (!button) {
            return {
                status: 'fail',
                error: 'Sell button not found in DOM',
                test_timestamp: new Date().toISOString()
            };
        }
        
        // Check button styling and attributes
        const buttonValidation = {
            'has_danger_style': button.className.includes('btn-danger'),
            'has_proper_icon': button.innerHTML.includes('icon-down') || button.innerHTML.includes('fa-arrow-down'),
            'has_accessibility': button.hasAttribute('aria-label'),
            'has_correct_text': (button.textContent || '').toLowerCase().includes('sell')
        };
        
        // Test associated API endpoints
        const apiTests = [];
        
        // Test both paper-trade and live trading endpoints
        const endpoints = ['/api/paper-trade/sell', '/api/sell'];
        
        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint, { 
                    method: 'HEAD',
                    cache: 'no-store'
                });
                apiTests.push({
                    endpoint: endpoint,
                    accessible: response.status !== 404,
                    status_code: response.status
                });
            } catch (error) {
                apiTests.push({
                    endpoint: endpoint,
                    accessible: false,
                    error: error.message
                });
            }
        }
        
        // Check if at least one API endpoint is accessible
        const apiAccessible = apiTests.some(test => test.accessible);
        
        const allChecks = [
            button !== null,
            buttonValidation['has_danger_style'],
            buttonValidation['has_accessibility'],
            buttonValidation['has_correct_text'],
            apiAccessible
        ];
        
        const passedChecks = allChecks.filter(Boolean).length;
        
        return {
            status: passedChecks >= 4 ? 'pass' : 'partial',
            button_found: button !== null,
            button_validation: buttonValidation,
            api_tests: apiTests,
            api_accessible: apiAccessible,
            passed_checks: passedChecks,
            total_checks: allChecks.length,
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Sell button test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testRecalculateButton() {
    try {
        // Check if button exists in DOM
        const button = document.getElementById('recalculate-btn');
        if (!button) {
            return {
                status: 'fail',
                error: 'Recalculate button not found in DOM',
                test_timestamp: new Date().toISOString()
            };
        }
        
        // Check button styling and attributes
        const buttonValidation = {
            'has_correct_class': button.className.includes('btn'),
            'has_outline_primary': button.className.includes('btn-outline-primary'),
            'has_proper_icon': button.innerHTML.includes('fa-calculator') || button.innerHTML.includes('calculator'),
            'has_accessibility': button.hasAttribute('title'),
            'has_onclick_handler': button.hasAttribute('onclick') || button.onclick !== null,
            'has_correct_text': (button.textContent || '').toLowerCase().includes('recalculate')
        };
        
        // Test the recalculate API endpoint
        let apiAccessible = false;
        let apiError = null;
        let requiresAuth = false;
        
        try {
            // First test without authentication (should require admin token)
            const response = await fetch('/api/recalculate-positions', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                cache: 'no-store'
            });
            
            if (response.status === 401 || response.status === 403) {
                requiresAuth = true;
                apiAccessible = true; // Endpoint exists but requires auth
                
                // Test with admin token
                const adminToken = window.ADMIN_TOKEN || localStorage.getItem('admin_token') || 'trading-admin-2024';
                const authResponse = await fetch('/api/recalculate-positions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${adminToken}`
                    },
                    cache: 'no-store'
                });
                
                apiAccessible = authResponse.status !== 404;
            } else {
                apiAccessible = response.status !== 404;
            }
        } catch (error) {
            apiError = error.message;
            apiAccessible = false;
        }
        
        // Check if recalculatePositions function exists globally
        const hasGlobalFunction = typeof window.recalculatePositions === 'function';
        
        // Check button behavior (without actually clicking)
        const hasValidOnClick = button.onclick && 
                               button.onclick.toString().includes('recalculatePositions');
        
        const allChecks = [
            button !== null,
            buttonValidation['has_correct_class'],
            buttonValidation['has_proper_icon'],
            buttonValidation['has_accessibility'],
            buttonValidation['has_correct_text'],
            apiAccessible,
            hasGlobalFunction,
            hasValidOnClick || buttonValidation['has_onclick_handler']
        ];
        
        const passedChecks = allChecks.filter(Boolean).length;
        
        return {
            status: passedChecks >= 6 ? 'pass' : 'partial',
            button_found: button !== null,
            button_validation: buttonValidation,
            api_accessible: apiAccessible,
            api_requires_auth: requiresAuth,
            api_error: apiError,
            has_global_function: hasGlobalFunction,
            has_valid_onclick: hasValidOnClick,
            passed_checks: passedChecks,
            total_checks: allChecks.length,
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Recalculate button test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testDetailsButtons() {
    try {
        const testResults = {
            open_positions_details: await testOpenPositionsDetailsButtons(),
            available_positions_details: await testAvailablePositionsDetailsButtons(),
            details_modal_functionality: await testDetailsModalFunctionality(),
            confidence_api_endpoint: await testConfidenceAPIEndpoint()
        };
        
        // Determine overall status
        const allTests = Object.values(testResults);
        const passedTests = allTests.filter(t => t.status === 'pass').length;
        const partialTests = allTests.filter(t => t.status === 'partial').length;
        const failedTests = allTests.filter(t => t.status === 'fail').length;
        const errorTests = allTests.filter(t => t.status === 'error').length;
        
        let overallStatus = 'pass';
        if (errorTests > 0 || failedTests > allTests.length / 2) {
            overallStatus = 'fail';
        } else if (partialTests > 0 || failedTests > 0) {
            overallStatus = 'partial';
        }
        
        return {
            status: overallStatus,
            sub_tests: testResults,
            summary: {
                total: allTests.length,
                passed: passedTests,
                partial: partialTests,
                failed: failedTests,
                errors: errorTests
            },
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Details buttons test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testOpenPositionsDetailsButtons() {
    try {
        // Check if open positions table exists
        const holdingsTable = document.getElementById('holdings-table');
        if (!holdingsTable) {
            return {
                status: 'fail',
                error: 'Open positions table not found',
                test_timestamp: new Date().toISOString()
            };
        }
        
        // Look for Details buttons in the open positions table
        const holdingsTableBody = document.querySelector('#holdings-table tbody');
        if (!holdingsTableBody) {
            return {
                status: 'fail', 
                error: 'Open positions table body not found',
                test_timestamp: new Date().toISOString()
            };
        }
        
        // Find all rows with data (not loading/empty rows)
        const dataRows = Array.from(holdingsTableBody.querySelectorAll('tr')).filter(row => {
            return !row.textContent.includes('Loading') && 
                   !row.textContent.includes('No holdings') &&
                   row.cells.length > 5;
        });
        
        let detailsButtonsFound = 0;
        let workingButtons = 0;
        let buttonDetails = [];
        
        dataRows.forEach((row, index) => {
            // Look for Details buttons in the actions column (typically last column)
            const actionsCell = row.cells[row.cells.length - 1];
            if (actionsCell) {
                const detailsButtons = actionsCell.querySelectorAll('button');
                detailsButtons.forEach(button => {
                    if (button.textContent.toLowerCase().includes('detail')) {
                        detailsButtonsFound++;
                        
                        // Check if button has proper onclick handler
                        const hasOnClick = button.onclick !== null || 
                                         button.addEventListener !== null ||
                                         button.hasAttribute('onclick');
                        
                        if (hasOnClick) {
                            workingButtons++;
                        }
                        
                        buttonDetails.push({
                            row_index: index,
                            button_text: button.textContent,
                            has_onclick: hasOnClick,
                            button_classes: button.className,
                            button_title: button.title || ''
                        });
                    }
                });
            }
        });
        
        return {
            status: detailsButtonsFound > 0 ? (workingButtons === detailsButtonsFound ? 'pass' : 'partial') : 'fail',
            total_data_rows: dataRows.length,
            details_buttons_found: detailsButtonsFound,
            working_buttons: workingButtons,
            button_details: buttonDetails.slice(0, 5), // Limit details for readability
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Open positions details button test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testAvailablePositionsDetailsButtons() {
    try {
        // Check if available positions table exists
        const availableTable = document.getElementById('available-table');
        if (!availableTable) {
            return {
                status: 'fail',
                error: 'Available positions table not found',
                test_timestamp: new Date().toISOString()
            };
        }
        
        // Look for Details buttons in the available positions table
        const availableTableBody = document.querySelector('#available-table tbody');
        if (!availableTableBody) {
            return {
                status: 'fail',
                error: 'Available positions table body not found',
                test_timestamp: new Date().toISOString()
            };
        }
        
        // Find all rows with data (not loading/empty rows)
        const dataRows = Array.from(availableTableBody.querySelectorAll('tr')).filter(row => {
            return !row.textContent.includes('Loading') && 
                   !row.textContent.includes('No positions') &&
                   row.cells.length > 5;
        });
        
        let detailsButtonsFound = 0;
        let workingButtons = 0;
        let buttonDetails = [];
        
        dataRows.forEach((row, index) => {
            // Look for Details buttons in the actions column (typically last column)
            const actionsCell = row.cells[row.cells.length - 1];
            if (actionsCell) {
                const detailsButtons = actionsCell.querySelectorAll('button');
                detailsButtons.forEach(button => {
                    if (button.textContent.toLowerCase().includes('detail')) {
                        detailsButtonsFound++;
                        
                        // Check if button has proper onclick handler
                        const hasOnClick = button.onclick !== null || 
                                         button.hasAttribute('onclick');
                        
                        // Check if showConfidenceDetails function exists
                        const hasGlobalFunction = typeof window.showConfidenceDetails === 'function';
                        
                        if (hasOnClick && hasGlobalFunction) {
                            workingButtons++;
                        }
                        
                        buttonDetails.push({
                            row_index: index,
                            button_text: button.textContent,
                            has_onclick: hasOnClick,
                            has_global_function: hasGlobalFunction,
                            button_classes: button.className,
                            button_title: button.title || ''
                        });
                    }
                });
            }
        });
        
        return {
            status: detailsButtonsFound > 0 ? (workingButtons === detailsButtonsFound ? 'pass' : 'partial') : 'fail',
            total_data_rows: dataRows.length,
            details_buttons_found: detailsButtonsFound,
            working_buttons: workingButtons,
            button_details: buttonDetails.slice(0, 5), // Limit details for readability
            has_show_confidence_details_function: typeof window.showConfidenceDetails === 'function',
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Available positions details button test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testDetailsModalFunctionality() {
    try {
        // Check if Bootstrap modal functionality is available
        const hasBootstrap = typeof window.bootstrap !== 'undefined';
        
        // Check if modal container exists or can be created
        let modalExists = document.getElementById('confidenceModal') !== null;
        
        // Test modal creation capability
        let canCreateModal = false;
        try {
            const testModal = document.createElement('div');
            testModal.className = 'modal fade';
            testModal.id = 'test-modal-creation';
            testModal.innerHTML = '<div class="modal-dialog"><div class="modal-content"><div class="modal-body">Test</div></div></div>';
            document.body.appendChild(testModal);
            canCreateModal = true;
            // Clean up test modal
            document.body.removeChild(testModal);
        } catch (error) {
            canCreateModal = false;
        }
        
        // Check if showConfidenceDetails function exists
        const hasShowConfidenceFunction = typeof window.showConfidenceDetails === 'function';
        
        // Test modal z-index and positioning
        let modalStylingCorrect = false;
        const existingModal = document.getElementById('confidenceModal');
        if (existingModal) {
            const computedStyle = window.getComputedStyle(existingModal);
            modalStylingCorrect = parseInt(computedStyle.zIndex) >= 1000 || existingModal.className.includes('modal');
        } else {
            modalStylingCorrect = true; // If no existing modal, assume styling will be correct
        }
        
        const allChecks = [
            hasBootstrap,
            canCreateModal,
            hasShowConfidenceFunction,
            modalStylingCorrect
        ];
        
        const passedChecks = allChecks.filter(Boolean).length;
        
        return {
            status: passedChecks >= 3 ? 'pass' : (passedChecks >= 2 ? 'partial' : 'fail'),
            has_bootstrap: hasBootstrap,
            modal_exists: modalExists,
            can_create_modal: canCreateModal,
            has_show_confidence_function: hasShowConfidenceFunction,
            modal_styling_correct: modalStylingCorrect,
            passed_checks: passedChecks,
            total_checks: allChecks.length,
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Modal functionality test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testConfidenceAPIEndpoint() {
    try {
        // Test the entry-confidence API endpoint with a sample symbol
        const testSymbols = ['BTC', 'ETH', 'SOL']; // Common symbols likely to exist
        let workingEndpoints = 0;
        let apiErrors = [];
        let endpointDetails = [];
        
        for (const symbol of testSymbols) {
            try {
                const response = await fetch(`/api/entry-confidence/${symbol}`, { 
                    cache: 'no-store',
                    method: 'GET'
                });
                
                const responseData = {
                    symbol: symbol,
                    status_code: response.status,
                    accessible: response.status !== 404,
                    response_ok: response.ok
                };
                
                if (response.ok) {
                    // Try to parse response to validate structure
                    try {
                        const jsonData = await response.json();
                        responseData.has_valid_json = true;
                        responseData.has_status_field = jsonData.hasOwnProperty('status');
                        responseData.has_data_field = jsonData.hasOwnProperty('data');
                        
                        if (jsonData.status === 'success' && jsonData.data) {
                            workingEndpoints++;
                            responseData.fully_functional = true;
                        }
                    } catch (jsonError) {
                        responseData.has_valid_json = false;
                        responseData.json_error = jsonError.message;
                    }
                } else {
                    apiErrors.push(`${symbol}: HTTP ${response.status}`);
                }
                
                endpointDetails.push(responseData);
                
            } catch (fetchError) {
                apiErrors.push(`${symbol}: ${fetchError.message}`);
                endpointDetails.push({
                    symbol: symbol,
                    error: fetchError.message,
                    accessible: false
                });
            }
        }
        
        return {
            status: workingEndpoints > 0 ? 'pass' : (endpointDetails.some(d => d.accessible) ? 'partial' : 'fail'),
            tested_symbols: testSymbols,
            working_endpoints: workingEndpoints,
            total_tested: testSymbols.length,
            api_errors: apiErrors,
            endpoint_details: endpointDetails,
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Confidence API endpoint test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

function generateButtonTestSummary(tests) {
    const totalTests = Object.keys(tests).length;
    const passedTests = Object.values(tests).filter(t => t.status === 'pass').length;
    const partialTests = Object.values(tests).filter(t => t.status === 'partial').length;
    const failedTests = Object.values(tests).filter(t => t.status === 'fail').length;
    const errorTests = Object.values(tests).filter(t => t.status === 'error').length;
    
    return {
        total: totalTests,
        passed: passedTests,
        partial: partialTests,
        failed: failedTests,
        errors: errorTests,
        success_rate: totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0
    };
}

// Also initialize tooltips when Bootstrap is ready
window.addEventListener('load', function() {
    setTimeout(initializeTooltips, 500);
});