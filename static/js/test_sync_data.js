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
        'available_positions_table': 'Available Positions Table Accuracy'
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
        'timestamp_integrity': 'Verifies data timestamp accuracy and freshness validation.',
        'table_validation': 'Validates that frontend table display matches backend API data exactly.',
        'open_positions_table': 'Checks Open Positions table rows against /api/current-holdings API data.',
        'available_positions_table': 'Verifies Available Positions table matches /api/available-positions API data.'
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

// Also initialize tooltips when Bootstrap is ready
window.addEventListener('load', function() {
    setTimeout(initializeTooltips, 500);
});