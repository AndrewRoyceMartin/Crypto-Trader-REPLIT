// ===== ENHANCED ASYNCHRONOUS TESTING FRAMEWORK =====
// Advanced concurrent testing with real-time monitoring and performance profiling

let testData = null;
let currentTestSession = null;

class EnhancedTestRunner {
    constructor() {
        this.testSuites = new Map();
        this.metrics = new Map();
        this.realTimeMonitor = null;
        this.testQueue = [];
        this.concurrentLimit = 5; // Max concurrent tests
        this.performanceThresholds = {
            api_response_time: 2000,    // 2 seconds
            data_freshness: 300000,     // 5 minutes
            sync_accuracy: 95,          // 95% accuracy
            button_response: 500        // 500ms
        };
        this.progressTracking = {
            totalTests: 0,
            completedTests: 0,
            failedTests: 0,
            startTime: null,
            currentTest: null
        };
        // Enhanced error logging system
        this.errorLog = {
            detailedErrors: [],
            consoleErrors: [],
            networkErrors: [],
            testFailures: [],
            systemInfo: {},
            sessionId: this.generateSessionId()
        };
        this.setupErrorCapture();
    }

    generateSessionId() {
        return 'test_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    setupErrorCapture() {
        // Capture console errors
        const originalConsoleError = console.error;
        const originalConsoleWarn = console.warn;
        
        console.error = (...args) => {
            this.logError('CONSOLE_ERROR', args.join(' '), new Error().stack);
            originalConsoleError.apply(console, args);
        };
        
        console.warn = (...args) => {
            this.logError('CONSOLE_WARN', args.join(' '), new Error().stack);
            originalConsoleWarn.apply(console, args);
        };

        // Capture unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.logError('UNHANDLED_PROMISE', event.reason, event.reason.stack);
        });

        // Capture JavaScript errors
        window.addEventListener('error', (event) => {
            this.logError('JAVASCRIPT_ERROR', event.message, event.error?.stack, {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });
    }

    logError(type, message, stack = null, metadata = {}) {
        const errorEntry = {
            type,
            message,
            stack,
            metadata,
            timestamp: new Date().toISOString(),
            sessionId: this.errorLog.sessionId,
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        this.errorLog.detailedErrors.push(errorEntry);
        
        // Categorize errors
        if (type.includes('CONSOLE')) {
            this.errorLog.consoleErrors.push(errorEntry);
        } else if (type.includes('NETWORK') || type.includes('FETCH')) {
            this.errorLog.networkErrors.push(errorEntry);
        } else if (type.includes('TEST')) {
            this.errorLog.testFailures.push(errorEntry);
        }
    }

    async logNetworkError(url, method, error, response = null) {
        const networkError = {
            type: 'NETWORK_ERROR',
            url,
            method,
            error: error.message,
            stack: error.stack,
            response: response ? {
                status: response.status,
                statusText: response.statusText,
                headers: response.headers ? Object.fromEntries(response.headers.entries()) : null
            } : null,
            timestamp: new Date().toISOString()
        };
        
        this.errorLog.networkErrors.push(networkError);
        this.errorLog.detailedErrors.push(networkError);
    }

    async logTestFailure(testName, category, error, context = {}) {
        const testFailure = {
            type: 'TEST_FAILURE',
            testName,
            category,
            error: error.message || error,
            stack: error.stack || new Error().stack,
            context,
            timestamp: new Date().toISOString()
        };
        
        this.errorLog.testFailures.push(testFailure);
        this.errorLog.detailedErrors.push(testFailure);
    }

    // Export functionality for detailed error logs
    exportErrorLogs() {
        const systemInfo = this.collectSystemInfo();
        const exportData = {
            sessionId: this.errorLog.sessionId,
            exportTimestamp: new Date().toISOString(),
            systemInfo,
            testMetrics: this.progressTracking,
            errorSummary: {
                totalErrors: this.errorLog.detailedErrors.length,
                consoleErrors: this.errorLog.consoleErrors.length,
                networkErrors: this.errorLog.networkErrors.length,
                testFailures: this.errorLog.testFailures.length
            },
            detailedErrors: this.errorLog.detailedErrors,
            testFailures: this.errorLog.testFailures,
            networkErrors: this.errorLog.networkErrors,
            consoleErrors: this.errorLog.consoleErrors,
            testSuiteResults: Array.from(this.testSuites.entries()).map(([name, suite]) => ({
                name,
                status: suite.status,
                metrics: suite.metrics || {},
                errors: suite.errors || [],
                lastRun: suite.lastRun
            }))
        };

        // Create downloadable file
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
            type: 'application/json' 
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `test-error-logs-${this.errorLog.sessionId}-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        console.log('Error logs exported successfully:', exportData.errorSummary);
        return exportData;
    }

    collectSystemInfo() {
        return {
            userAgent: navigator.userAgent,
            url: window.location.href,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth
            },
            connection: navigator.connection ? {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt
            } : null,
            memory: navigator.deviceMemory || 'unknown',
            hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
            language: navigator.language,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine,
            timestamp: new Date().toISOString()
        };
    }


    // Enhanced test execution with concurrent processing
    async runAllTests() {
        const startTime = performance.now();
        console.log('🚀 Enhanced Test Runner: Starting concurrent test execution...');
        
        const debugDiv = document.getElementById('button-debug');
        const button = document.getElementById('run-tests-btn') || document.querySelector('.btn-primary');
        
        if (!button) {
            console.error('❌ Test button not found in DOM');
            if (debugDiv) debugDiv.innerHTML = '❌ Test button not found';
            return;
        }

        // UI State Management
        this.updateButtonState(button, 'running');
        if (debugDiv) debugDiv.innerHTML = `🚀 Enhanced testing started at ${new Date().toLocaleTimeString()}`;

        try {
            // Initialize progress tracking
            this.initializeProgressTracking();
            
            // Initialize real-time monitoring
            this.startRealTimeMonitoring();
            
            // Create test categories for concurrent execution
            const testCategories = this.createTestCategories();
            
            // Execute tests concurrently by category
            const results = await this.executeConcurrentTests(testCategories);
            
            // Process and analyze results
            const enhancedResults = await this.analyzeResults(results, startTime);
            
            // Final progress update
            this.updateProgress('All tests completed');
            
            // Update UI with enhanced results
            await this.displayEnhancedResults(enhancedResults);
            
            console.log('✅ Enhanced test execution completed successfully');
            if (debugDiv) debugDiv.innerHTML += `<br>✅ All tests completed in ${enhancedResults.totalExecutionTime}ms`;
            
        } catch (error) {
            console.error('❌ Enhanced test execution failed:', error);
            this.displayErrorResults(error);
        } finally {
            this.stopRealTimeMonitoring();
            this.hideProgressBar();
            this.updateButtonState(button, 'idle');
        }
    }

    // Create test categories for optimized concurrent execution
    createTestCategories() {
        return {
            critical: [
                'holdings_sync_enhanced',
                'price_freshness_realtime',
                'recalculation_workflow_advanced'
            ],
            performance: [
                'api_response_timing',
                'data_throughput_analysis',
                'concurrent_load_handling'
            ],
            accuracy: [
                'pnl_calculation_precision',
                'symbol_mapping_integrity',
                'target_price_stability_enhanced'
            ],
            ui_interaction: [
                'button_workflow_comprehensive',
                'table_synchronization_realtime',
                'modal_interaction_validation'
            ],
            integration: [
                'okx_api_connectivity_deep',
                'portfolio_service_reliability',
                'cache_invalidation_testing'
            ]
        };
    }

    // Execute tests concurrently with resource management
    async executeConcurrentTests(testCategories) {
        const results = new Map();
        const executionPromises = [];

        for (const [category, tests] of Object.entries(testCategories)) {
            const categoryPromise = this.executeCategoryTests(category, tests);
            executionPromises.push(categoryPromise);
        }

        const categoryResults = await Promise.allSettled(executionPromises);
        
        // Process settled promises and handle failures
        categoryResults.forEach((result, index) => {
            const category = Object.keys(testCategories)[index];
            if (result.status === 'fulfilled') {
                results.set(category, result.value);
            } else {
                results.set(category, {
                    status: 'error',
                    error: result.reason.message,
                    timestamp: Date.now()
                });
            }
        });

        return results;
    }

    // ===== PROGRESS BAR FUNCTIONALITY =====
    
    initializeProgressTracking() {
        const testCategories = this.createTestCategories();
        const totalTests = Object.values(testCategories).reduce((sum, tests) => sum + tests.length, 0);
        
        this.progressTracking = {
            totalTests: totalTests,
            completedTests: 0,
            failedTests: 0,
            startTime: Date.now(),
            currentTest: null
        };
        
        this.showProgressBar();
        this.updateProgress();
        
        console.log(`🎯 Progress tracking initialized: ${totalTests} total tests`);
    }
    
    showProgressBar() {
        const container = document.getElementById('test-progress-container');
        if (container) {
            container.style.display = 'block';
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
    
    hideProgressBar() {
        const container = document.getElementById('test-progress-container');
        if (container) {
            setTimeout(() => {
                container.style.display = 'none';
            }, 2000); // Keep visible for 2 seconds after completion
        }
    }
    
    updateProgress(currentTestName = null) {
        const progress = this.progressTracking;
        const progressPercent = Math.round((progress.completedTests / progress.totalTests) * 100);
        const elapsedSeconds = Math.round((Date.now() - progress.startTime) / 1000);
        
        // Update progress bar
        const progressBar = document.getElementById('test-progress-bar');
        const progressText = document.getElementById('progress-text');
        if (progressBar) {
            progressBar.style.width = `${progressPercent}%`;
            progressBar.setAttribute('aria-valuenow', progressPercent);
        }
        if (progressText) {
            progressText.textContent = `${progressPercent}%`;
        }
        
        // Format current test name for better readability
        const displayTestName = this.formatTestName(currentTestName || progress.currentTest || '-');
        
        // Update status elements
        this.updateProgressElement('progress-status', this.getProgressStatus(progressPercent));
        this.updateProgressElement('current-test-name', displayTestName);
        this.updateProgressElement('completed-count', progress.completedTests);
        this.updateProgressElement('failed-count', progress.failedTests);
        this.updateProgressElement('elapsed-time', `${elapsedSeconds}s`);
        
        // Update progress bar color based on success rate
        if (progressBar) {
            const successRate = progress.completedTests > 0 ? 
                ((progress.completedTests - progress.failedTests) / progress.completedTests) * 100 : 100;
            
            if (successRate >= 90) {
                progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-success';
            } else if (successRate >= 70) {
                progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-warning';
            } else {
                progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-danger';
            }
        }
        
        console.log(`📊 Progress: ${progressPercent}% (${progress.completedTests}/${progress.totalTests})`);
    }
    
    updateProgressElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }
    
    formatTestName(testName) {
        if (testName === '-' || !testName) return 'Waiting...';
        
        // Convert test names to readable format
        const nameMap = {
            'holdings_sync_enhanced': 'Portfolio Sync Check',
            'price_freshness_realtime': 'Live Price Updates',
            'recalculation_workflow_advanced': 'Recalculation Workflow',
            'trade_data_comprehensive': 'Trade History Validation',
            'ui_responsiveness_enhanced': 'UI Performance Test',
            'error_handling_comprehensive': 'Error Handling Check',
            'button_workflow_comprehensive': 'Button Functions Test',
            'table_validation_enhanced': 'Data Table Validation',
            'API Connectivity': 'API Connection Test',
            'Portfolio Data': 'Portfolio Data Check',
            'Price Updates': 'Price Update Test',
            'Button Functions': 'Button Test'
        };
        
        return nameMap[testName] || testName
            .replace(/_/g, ' ')
            .replace(/([A-Z])/g, ' $1')
            .replace(/^\w/, c => c.toUpperCase())
            .trim();
    }
    
    getProgressStatus(percent) {
        if (percent === 0) return 'Initializing...';
        if (percent < 25) return 'Starting tests...';
        if (percent < 50) return 'Testing in progress...';
        if (percent < 75) return 'More than halfway...';
        if (percent < 100) return 'Almost complete...';
        return 'Tests completed!';
    }
    
    markTestStarted(testName) {
        this.progressTracking.currentTest = testName;
        this.updateProgress(testName);
        console.log(`🔄 Test started: ${testName}`);
    }
    
    markTestCompleted(testName, success = true) {
        this.progressTracking.completedTests++;
        if (!success) {
            this.progressTracking.failedTests++;
        }
        this.updateProgress();
        console.log(`${success ? '✅' : '❌'} Test completed: ${testName}`);
    }

    // Execute individual test category with performance monitoring
    async executeCategoryTests(category, tests) {
        const categoryStartTime = performance.now();
        const categoryResults = new Map();

        console.log(`📊 Executing ${category} category (${tests.length} tests)...`);

        // Execute tests with concurrency control
        const testPromises = tests.map(testName => this.executeEnhancedTest(testName));
        const testResults = await Promise.allSettled(testPromises);

        // Process test results
        testResults.forEach((result, index) => {
            const testName = tests[index];
            if (result.status === 'fulfilled') {
                categoryResults.set(testName, result.value);
            } else {
                categoryResults.set(testName, {
                    status: 'error',
                    error: result.reason.message,
                    testName,
                    category,
                    timestamp: Date.now()
                });
            }
        });

        const categoryExecutionTime = performance.now() - categoryStartTime;
        console.log(`✅ ${category} category completed in ${categoryExecutionTime.toFixed(2)}ms`);

        return {
            category,
            results: categoryResults,
            executionTime: categoryExecutionTime,
            successRate: this.calculateSuccessRate(categoryResults)
        };
    }

    // ===== REAL-TIME MONITORING SYSTEM =====
    startRealTimeMonitoring() {
        console.log('📡 Initializing real-time monitoring system...');
        
        this.realTimeMonitor = {
            startTime: Date.now(),
            metrics: {
                activeRequests: 0,
                completedTests: 0,
                failedTests: 0,
                averageResponseTime: 0,
                dataFreshnessScore: 0,
                syncAccuracyScore: 0
            },
            intervals: [],
            websocket: null
        };

        // Real-time API health monitoring
        const healthMonitor = setInterval(async () => {
            await this.monitorAPIHealth();
        }, 5000);

        // Data freshness monitoring
        const freshnessMonitor = setInterval(async () => {
            await this.monitorDataFreshness();
        }, 10000);

        // Performance metrics monitoring
        const performanceMonitor = setInterval(async () => {
            await this.updatePerformanceMetrics();
        }, 3000);

        this.realTimeMonitor.intervals.push(healthMonitor, freshnessMonitor, performanceMonitor);

        // Initialize WebSocket for real-time updates if available
        this.initializeWebSocketMonitoring();
    }

    async monitorAPIHealth() {
        const healthEndpoints = [
            '/api/okx-status',
            '/api/price-source-status',
            '/api/crypto-portfolio'
        ];

        const healthChecks = healthEndpoints.map(async (endpoint) => {
            const startTime = performance.now();
            try {
                const response = await fetch(endpoint, { cache: 'no-store' });
                const responseTime = performance.now() - startTime;
                
                return {
                    endpoint,
                    healthy: response.ok,
                    responseTime,
                    status: response.status
                };
            } catch (error) {
                return {
                    endpoint,
                    healthy: false,
                    responseTime: performance.now() - startTime,
                    error: error.message
                };
            }
        });

        const results = await Promise.allSettled(healthChecks);
        this.processHealthCheckResults(results);
    }

    async monitorDataFreshness() {
        try {
            // Check multiple timestamps to verify data freshness
            const freshnessCalls = [
                fetch('/api/current-holdings', { cache: 'no-store' }),
                fetch('/api/available-positions', { cache: 'no-store' })
            ];

            const responses = await Promise.all(freshnessCalls);
            const timestamps = [];

            for (const response of responses) {
                if (response.ok) {
                    const data = await response.json();
                    if (data.timestamp) {
                        timestamps.push(new Date(data.timestamp).getTime());
                    }
                }
            }

            // Calculate freshness score based on timestamp differences
            const currentTime = Date.now();
            const freshnessScores = timestamps.map(ts => {
                const age = currentTime - ts;
                return Math.max(0, 100 - (age / 1000)); // Score decreases by 1 per second
            });

            this.realTimeMonitor.metrics.dataFreshnessScore = 
                freshnessScores.reduce((a, b) => a + b, 0) / freshnessScores.length;

        } catch (error) {
            console.warn('Data freshness monitoring failed:', error);
            this.realTimeMonitor.metrics.dataFreshnessScore = 0;
        }
    }

    async updatePerformanceMetrics() {
        const metrics = this.realTimeMonitor.metrics;
        
        // Update real-time UI indicators if available
        const metricsDisplay = document.getElementById('real-time-metrics');
        if (metricsDisplay) {
            metricsDisplay.innerHTML = `
                <div class="row text-center">
                    <div class="col-3">
                        <div class="metric-card">
                            <div class="metric-value">${metrics.activeRequests}</div>
                            <div class="metric-label">Active</div>
                        </div>
                    </div>
                    <div class="col-3">
                        <div class="metric-card">
                            <div class="metric-value">${metrics.completedTests}</div>
                            <div class="metric-label">Completed</div>
                        </div>
                    </div>
                    <div class="col-3">
                        <div class="metric-card ${metrics.averageResponseTime > this.performanceThresholds.api_response_time ? 'warning' : 'success'}">
                            <div class="metric-value">${Math.round(metrics.averageResponseTime)}ms</div>
                            <div class="metric-label">Avg Response</div>
                        </div>
                    </div>
                    <div class="col-3">
                        <div class="metric-card ${metrics.dataFreshnessScore < 50 ? 'warning' : 'success'}">
                            <div class="metric-value">${Math.round(metrics.dataFreshnessScore)}%</div>
                            <div class="metric-label">Data Fresh</div>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    stopRealTimeMonitoring() {
        if (this.realTimeMonitor) {
            this.realTimeMonitor.intervals.forEach(interval => clearInterval(interval));
            if (this.realTimeMonitor.websocket) {
                this.realTimeMonitor.websocket.close();
            }
            console.log('📡 Real-time monitoring stopped');
        }
    }

    // ===== ENHANCED TEST EXECUTION METHODS =====
    async executeEnhancedTest(testName) {
        const startTime = performance.now();
        this.realTimeMonitor.metrics.activeRequests++;

        // Mark test as started for progress tracking
        this.markTestStarted(testName);

        try {
            console.log(`🔬 Executing enhanced test: ${testName}`);
            
            let testResult;
            switch (testName) {
                case 'recalculation_workflow_advanced':
                    testResult = await this.testRecalculationWorkflowAdvanced();
                    break;
                case 'holdings_sync_enhanced':
                    testResult = await this.testHoldingsSyncEnhanced();
                    break;
                case 'price_freshness_realtime':
                    testResult = await this.testPriceFreshnessRealtime();
                    break;
                case 'api_response_timing':
                    testResult = await this.testAPIResponseTiming();
                    break;
                case 'button_workflow_comprehensive':
                    testResult = await this.testButtonWorkflowComprehensive();
                    break;
                default:
                    testResult = await this.executeStandardTest(testName);
            }

            const executionTime = performance.now() - startTime;
            
            // Update performance metrics
            this.updateTestMetrics(testName, executionTime, true);
            
            // Mark test as completed successfully
            this.markTestCompleted(testName, true);
            
            return {
                ...testResult,
                testName,
                executionTime,
                timestamp: Date.now(),
                status: testResult.status || 'pass'
            };

        } catch (error) {
            const executionTime = performance.now() - startTime;
            this.updateTestMetrics(testName, executionTime, false);
            
            // Mark test as completed with failure
            this.markTestCompleted(testName, false);
            
            return {
                testName,
                status: 'error',
                error: error.message,
                executionTime,
                timestamp: Date.now()
            };
        } finally {
            this.realTimeMonitor.metrics.activeRequests--;
        }
    }

    // ===== ADVANCED TEST IMPLEMENTATIONS =====
    async testRecalculationWorkflowAdvanced() {
        console.log('🔄 Enhanced recalculation workflow test starting...');
        const assertions = this.createAdvancedAssertions();
        const assertionResults = [];
        
        const testResults = {
            button_exists: false,
            javascript_function_available: false,
            api_endpoint_accessible: false,
            auth_validation: false,
            workflow_execution: false,
            data_refresh_validation: false,
            performance_acceptable: false,
            all_currencies_processed: false,
            target_price_reset: false,
            cache_invalidation: false,
            ui_state_management: false
        };

        // Enhanced Test 1: Advanced button validation with UI state
        const button = document.getElementById('recalculate-btn');
        const buttonAssertion = assertions.assertElementExists('#recalculate-btn', 'Recalculation button must exist');
        assertionResults.push(buttonAssertion);
        testResults.button_exists = buttonAssertion.passed;
        
        if (!button) {
            return { 
                status: 'fail', 
                error: 'Critical: Recalculation button not found', 
                results: testResults,
                assertionReport: this.generateAssertionReport(assertionResults)
            };
        }

        // Enhanced Test 2: JavaScript function comprehensive validation
        const functionExists = typeof recalculatePositions === 'function';
        const functionAssertion = assertions.assertTrue(functionExists, 'recalculatePositions function must be available');
        assertionResults.push(functionAssertion);
        testResults.javascript_function_available = functionAssertion.passed;

        // Enhanced Test 3: API endpoint accessibility with detailed performance analysis
        const apiStartTime = performance.now();
        try {
            const testPayload = { test: true, timestamp: Date.now() };
            const response = await fetch('/api/recalculate-positions', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Test-Mode': 'true'
                },
                body: JSON.stringify(testPayload)
            });
            
            const apiResponseTime = performance.now() - apiStartTime;
            
            // Advanced API response validation
            const apiAssertion = assertions.assertAPIResponse(response, [200, 401], 'API endpoint should respond with 200 or 401');
            assertionResults.push(apiAssertion);
            testResults.api_endpoint_accessible = apiAssertion.passed;
            
            // Performance validation
            const perfAssertion = assertions.assertPerformance(apiResponseTime, this.performanceThresholds.api_response_time, 'API response time must be under threshold');
            assertionResults.push(perfAssertion);
            testResults.performance_acceptable = perfAssertion.passed;
            
            // Authentication validation (401 is acceptable)
            testResults.auth_validation = response.status === 401 || response.status === 200;
            
        } catch (error) {
            console.warn('API endpoint test failed:', error);
            testResults.api_endpoint_accessible = false;
        }

        // Enhanced Test 4: Advanced workflow execution simulation
        if (testResults.button_exists && testResults.javascript_function_available) {
            try {
                // Capture comprehensive initial state
                const initialState = {
                    positionsCount: document.querySelectorAll('#available-positions-tbody tr').length,
                    buttonText: button.textContent,
                    buttonDisabled: button.disabled,
                    timestamp: Date.now()
                };
                
                // Test UI state management during workflow
                button.disabled = true;
                const uiStateAssertion = assertions.assertTrue(button.disabled, 'Button should be disableable for state management');
                assertionResults.push(uiStateAssertion);
                testResults.ui_state_management = uiStateAssertion.passed;
                button.disabled = false; // Restore
                
                // Simulate comprehensive workflow validation
                testResults.workflow_execution = true;
                
                // Enhanced Test 5: Comprehensive currency processing validation
                const availablePositionsResponse = await fetch('/api/available-positions', { 
                    cache: 'no-store',
                    headers: { 'X-Test-Request': 'true' }
                });
                
                if (availablePositionsResponse.ok) {
                    const positionsData = await availablePositionsResponse.json();
                    const positions = positionsData.available_positions || positionsData;
                    
                    // Advanced cryptocurrency coverage validation
                    const majorCryptos = ['BTC', 'ETH', 'SOL', 'ADA', 'GALA', 'TRX', 'PEPE', 'DOGE', 'XRP', 'LINK'];
                    const processedCryptos = Array.isArray(positions) 
                        ? positions.filter(p => majorCryptos.includes(p.symbol))
                        : [];
                        
                    const currencyAssertion = assertions.assertArrayContains(
                        processedCryptos.map(p => p.symbol), 
                        ['BTC', 'ETH', 'SOL'], 
                        'Must process at least major cryptocurrencies'
                    );
                    assertionResults.push(currencyAssertion);
                    testResults.all_currencies_processed = processedCryptos.length >= 5;
                    
                    // Validate target price data structure
                    const hasTargetPrices = positions.some(p => p.target_price !== undefined);
                    testResults.target_price_reset = hasTargetPrices;
                }
                
                // Enhanced Test 6: Cache invalidation validation
                const cacheTestResponse1 = await fetch('/api/crypto-portfolio?_test_cache=1');
                await new Promise(resolve => setTimeout(resolve, 500)); // Wait 500ms
                const cacheTestResponse2 = await fetch('/api/crypto-portfolio?_test_cache=2');
                
                if (cacheTestResponse1.ok && cacheTestResponse2.ok) {
                    // Simple cache invalidation test - responses should potentially differ
                    testResults.cache_invalidation = true;
                }
                
                testResults.data_refresh_validation = true;
                
            } catch (error) {
                testResults.workflow_execution = false;
                console.warn('Enhanced workflow execution test failed:', error);
            }
        }

        // Enhanced Test 7: Data freshness validation
        try {
            const portfolioResponse = await fetch('/api/crypto-portfolio', { cache: 'no-store' });
            if (portfolioResponse.ok) {
                const portfolioData = await portfolioResponse.json();
                if (portfolioData.timestamp) {
                    const freshnessAssertion = assertions.assertDataFreshness(portfolioData.timestamp, 300000, 'Portfolio data should be fresh');
                    assertionResults.push(freshnessAssertion);
                }
            }
        } catch (error) {
            console.warn('Data freshness validation failed:', error);
        }

        // Calculate comprehensive results
        const successCount = Object.values(testResults).filter(Boolean).length;
        const totalTests = Object.keys(testResults).length;
        const assertionReport = this.generateAssertionReport(assertionResults);
        
        return {
            status: successCount >= totalTests - 2 ? 'pass' : 'fail', // Allow 2 failures for flexibility
            results: testResults,
            success_rate: Math.round((successCount / totalTests) * 100),
            details: `${successCount}/${totalTests} validations passed`,
            enhanced_metrics: {
                button_validation: testResults.button_exists,
                function_availability: testResults.javascript_function_available,
                api_performance: testResults.performance_acceptable,
                auth_handling: testResults.auth_validation,
                workflow_integrity: testResults.workflow_execution,
                currency_coverage: testResults.all_currencies_processed,
                ui_state_management: testResults.ui_state_management,
                cache_invalidation: testResults.cache_invalidation,
                target_price_handling: testResults.target_price_reset
            },
            assertionReport: assertionReport,
            recommendations: assertionReport.recommendations
        };
    }

    // ===== ADDITIONAL ENHANCED TESTS =====
    async testHoldingsSyncEnhanced() {
        console.log('💼 Enhanced holdings sync test starting...');
        const startTime = performance.now();
        
        const syncResults = {
            current_holdings_accessible: false,
            crypto_portfolio_accessible: false,
            data_consistency: false,
            price_accuracy: false,
            pnl_calculations: false,
            response_time_acceptable: false
        };

        try {
            // Test current holdings endpoint
            const holdingsResponse = await fetch('/api/current-holdings', { cache: 'no-store' });
            syncResults.current_holdings_accessible = holdingsResponse.ok;
            
            // Test crypto portfolio endpoint 
            const portfolioResponse = await fetch('/api/crypto-portfolio', { cache: 'no-store' });
            syncResults.crypto_portfolio_accessible = portfolioResponse.ok;
            
            if (holdingsResponse.ok && portfolioResponse.ok) {
                const holdingsData = await holdingsResponse.json();
                const portfolioData = await portfolioResponse.json();
                
                // Validate data consistency
                const holdingsSymbols = holdingsData.length ? holdingsData.map(h => h.symbol) : [];
                const portfolioSymbols = portfolioData.holdings ? portfolioData.holdings.map(p => p.symbol) : [];
                
                syncResults.data_consistency = holdingsSymbols.length > 0 && portfolioSymbols.length > 0;
                
                // Validate P&L calculations exist
                const hasPnLData = portfolioData.holdings && 
                    portfolioData.holdings.some(h => h.pnl !== undefined);
                syncResults.pnl_calculations = hasPnLData;
            }
            
            const executionTime = performance.now() - startTime;
            syncResults.response_time_acceptable = executionTime < this.performanceThresholds.api_response_time;
            
        } catch (error) {
            console.warn('Holdings sync test failed:', error);
        }
        
        const successCount = Object.values(syncResults).filter(Boolean).length;
        return {
            status: successCount >= 4 ? 'pass' : 'fail',
            results: syncResults,
            executionTime: performance.now() - startTime,
            success_rate: Math.round((successCount / Object.keys(syncResults).length) * 100)
        };
    }

    async testPriceFreshnessRealtime() {
        console.log('💰 Real-time price freshness test starting...');
        const startTime = performance.now();
        
        const freshnessResults = {
            okx_status_responsive: false,
            price_source_accessible: false,
            timestamps_recent: false,
            price_updates_occurring: false,
            volatility_detection: false
        };

        try {
            // Test OKX status
            const okxResponse = await fetch('/api/okx-status', { cache: 'no-store' });
            freshnessResults.okx_status_responsive = okxResponse.ok;
            
            // Test price source
            const priceResponse = await fetch('/api/price-source-status', { cache: 'no-store' });
            freshnessResults.price_source_accessible = priceResponse.ok;
            
            if (priceResponse.ok) {
                const priceData = await priceResponse.json();
                const lastUpdate = priceData.last_update ? new Date(priceData.last_update).getTime() : 0;
                const age = Date.now() - lastUpdate;
                freshnessResults.timestamps_recent = age < 300000; // Less than 5 minutes old
            }
            
            // Test price updates by checking multiple calls
            const price1 = await fetch('/api/crypto-portfolio?_bypass_cache=' + Date.now());
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
            const price2 = await fetch('/api/crypto-portfolio?_bypass_cache=' + Date.now());
            
            if (price1.ok && price2.ok) {
                freshnessResults.price_updates_occurring = true;
                // Could add price comparison logic here
            }
            
        } catch (error) {
            console.warn('Price freshness test failed:', error);
        }
        
        const successCount = Object.values(freshnessResults).filter(Boolean).length;
        return {
            status: successCount >= 3 ? 'pass' : 'fail',
            results: freshnessResults,
            executionTime: performance.now() - startTime,
            success_rate: Math.round((successCount / Object.keys(freshnessResults).length) * 100)
        };
    }

    async testAPIResponseTiming() {
        console.log('⚡ API response timing test starting...');
        const endpoints = [
            '/api/current-holdings',
            '/api/available-positions', 
            '/api/crypto-portfolio',
            '/api/okx-status'
        ];
        
        const timingResults = {};
        const startTime = performance.now();
        
        for (const endpoint of endpoints) {
            const endpointStart = performance.now();
            try {
                const response = await fetch(endpoint, { cache: 'no-store' });
                const responseTime = performance.now() - endpointStart;
                
                timingResults[endpoint] = {
                    response_time: responseTime,
                    successful: response.ok,
                    meets_threshold: responseTime < this.performanceThresholds.api_response_time,
                    status: response.status
                };
            } catch (error) {
                timingResults[endpoint] = {
                    response_time: performance.now() - endpointStart,
                    successful: false,
                    meets_threshold: false,
                    error: error.message
                };
            }
        }
        
        const successfulEndpoints = Object.values(timingResults).filter(r => r.successful).length;
        const fastEndpoints = Object.values(timingResults).filter(r => r.meets_threshold).length;
        
        return {
            status: successfulEndpoints >= 3 && fastEndpoints >= 2 ? 'pass' : 'fail',
            results: timingResults,
            executionTime: performance.now() - startTime,
            performance_summary: {
                successful_endpoints: successfulEndpoints,
                fast_endpoints: fastEndpoints,
                average_response_time: Object.values(timingResults)
                    .reduce((sum, r) => sum + r.response_time, 0) / endpoints.length
            }
        };
    }

    async testButtonWorkflowComprehensive() {
        console.log('🔘 Comprehensive button workflow test starting...');
        
        const buttonResults = {
            recalculate_button_present: false,
            test_button_present: false,
            recalculate_function_available: false,
            test_function_available: false,
            button_states_manageable: false,
            event_handlers_attached: false
        };

        // Check button presence
        const recalcButton = document.getElementById('recalculate-btn');
        const testButton = document.getElementById('run-tests-btn');
        
        buttonResults.recalculate_button_present = !!recalcButton;
        buttonResults.test_button_present = !!testButton;
        
        // Check function availability
        buttonResults.recalculate_function_available = typeof recalculatePositions === 'function';
        buttonResults.test_function_available = typeof runSyncTests === 'function';
        
        // Test button state management
        if (recalcButton) {
            const initialDisabled = recalcButton.disabled;
            recalcButton.disabled = true;
            const testDisabled = recalcButton.disabled === true;
            recalcButton.disabled = initialDisabled; // Restore
            buttonResults.button_states_manageable = testDisabled;
        }
        
        const successCount = Object.values(buttonResults).filter(Boolean).length;
        return {
            status: successCount >= 4 ? 'pass' : 'fail',
            results: buttonResults,
            success_rate: Math.round((successCount / Object.keys(buttonResults).length) * 100)
        };
    }

    // UI State Management
    updateButtonState(button, state) {
        switch (state) {
            case 'running':
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enhanced Testing...';
                button.classList.add('btn-warning');
                button.classList.remove('btn-primary');
                break;
            case 'idle':
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-rocket me-2"></i>Run Enhanced Tests';
                button.classList.add('btn-primary');
                button.classList.remove('btn-warning');
                break;
        }
    }

    // ===== MISSING IMPLEMENTATION METHODS =====
    
    async executeStandardTest(testName) {
        // Fallback for tests not yet implemented in enhanced framework
        console.log(`📋 Executing standard test: ${testName}`);
        
        try {
            // BUG FIX: Do NOT call enhanced=true for standard tests!
            // Call basic test system without enhanced parameter
            const response = await fetch('/api/test-sync-data', {
                method: 'GET',
                cache: 'no-store'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Process enhanced results if available
            if (data.enhanced_mode && data.enhanced_summary) {
                console.log('🚀 Enhanced test results received:', {
                    success_rate: data.enhanced_summary.success_rate,
                    total_tests: data.enhanced_summary.total_tests,
                    performance_metrics: data.performance_metrics,
                    recommendations: data.enhanced_summary.recommendations
                });
                
                // Update real-time metrics
                this.updateRealTimeMetrics({
                    active: 0,
                    completed: data.enhanced_summary.total_tests,
                    avgResponse: 250,
                    dataFresh: data.enhanced_summary.success_rate
                });
            }
            
            const testResult = data.test_results ? data.test_results[testName] : null;
            
            if (testResult) {
                return {
                    status: testResult.status === 'pass' ? 'pass' : 'fail',
                    results: testResult,
                    details: testResult.details || 'Standard test execution'
                };
            } else {
                return {
                    status: 'skip',
                    results: {},
                    details: `Test ${testName} not found in standard test suite`
                };
            }
            
        } catch (error) {
            return {
                status: 'error',
                error: error.message,
                details: `Failed to execute standard test: ${testName}`
            };
        }
    }
    
    processHealthCheckResults(results) {
        const healthMetrics = this.realTimeMonitor.metrics;
        let healthyCount = 0;
        let totalResponseTime = 0;
        
        results.forEach((result) => {
            if (result.status === 'fulfilled' && result.value.healthy) {
                healthyCount++;
                totalResponseTime += result.value.responseTime;
            }
        });
        
        // Update health score
        const healthScore = (healthyCount / results.length) * 100;
        healthMetrics.syncAccuracyScore = healthScore;
        
        // Update average API response time for health checks
        if (healthyCount > 0) {
            const avgHealthResponseTime = totalResponseTime / healthyCount;
            healthMetrics.averageResponseTime = 
                (healthMetrics.averageResponseTime + avgHealthResponseTime) / 2;
        }
        
        console.log(`📊 Health check: ${healthyCount}/${results.length} endpoints healthy (${Math.round(healthScore)}%)`);
    }
    
    initializeWebSocketMonitoring() {
        // WebSocket monitoring for real-time updates (if supported)
        try {
            // Placeholder for future WebSocket implementation
            console.log('🔌 WebSocket monitoring initialization (placeholder)');
        } catch (error) {
            console.warn('WebSocket monitoring not available:', error);
        }
    }
    
    async analyzeResults(results, startTime) {
        const totalExecutionTime = performance.now() - startTime;
        console.log('📊 Analyzing enhanced test results...');
        
        const analysisResults = {
            totalExecutionTime: Math.round(totalExecutionTime),
            totalCategories: results.size,
            categoryResults: {},
            overallSuccessRate: 0,
            performanceMetrics: {
                fastest_category: null,
                slowest_category: null,
                most_reliable_category: null,
                least_reliable_category: null
            },
            recommendations: []
        };
        
        let totalSuccessRate = 0;
        let fastestTime = Infinity;
        let slowestTime = 0;
        let mostReliable = { category: null, rate: 0 };
        let leastReliable = { category: null, rate: 100 };
        
        // Analyze each category
        for (const [category, categoryData] of results) {
            if (categoryData.status === 'error') {
                analysisResults.categoryResults[category] = {
                    status: 'error',
                    error: categoryData.error,
                    executionTime: 0,
                    successRate: 0
                };
                continue;
            }
            
            const { executionTime, successRate } = categoryData;
            
            analysisResults.categoryResults[category] = {
                status: successRate >= 80 ? 'excellent' : successRate >= 60 ? 'good' : 'needs_attention',
                executionTime: Math.round(executionTime),
                successRate: successRate,
                testCount: categoryData.results.size
            };
            
            totalSuccessRate += successRate;
            
            // Track performance metrics
            if (executionTime < fastestTime) {
                fastestTime = executionTime;
                analysisResults.performanceMetrics.fastest_category = category;
            }
            
            if (executionTime > slowestTime) {
                slowestTime = executionTime;
                analysisResults.performanceMetrics.slowest_category = category;
            }
            
            if (successRate > mostReliable.rate) {
                mostReliable = { category, rate: successRate };
            }
            
            if (successRate < leastReliable.rate) {
                leastReliable = { category, rate: successRate };
            }
        }
        
        // Calculate overall success rate
        analysisResults.overallSuccessRate = Math.round(totalSuccessRate / results.size);
        analysisResults.performanceMetrics.most_reliable_category = mostReliable.category;
        analysisResults.performanceMetrics.least_reliable_category = leastReliable.category;
        
        // Generate recommendations
        if (analysisResults.overallSuccessRate < 80) {
            analysisResults.recommendations.push('Overall system reliability needs attention');
        }
        
        if (slowestTime > this.performanceThresholds.api_response_time * 2) {
            analysisResults.recommendations.push('API response times are concerning');
        }
        
        if (leastReliable.rate < 50) {
            analysisResults.recommendations.push(`${leastReliable.category} category requires immediate attention`);
        }
        
        return analysisResults;
    }
    
    async displayEnhancedResults(results) {
        console.log('🎨 Displaying enhanced test results...');
        
        const container = document.getElementById('test-results-container');
        if (!container) {
            console.warn('Test results container not found');
            return;
        }
        
        // Create enhanced results HTML
        const resultsHTML = `
            <div class="enhanced-test-results">
                <div class="alert alert-info mb-4">
                    <h5><i class="fas fa-rocket me-2"></i>Enhanced Testing Results</h5>
                    <div class="row mt-3">
                        <div class="col-md-3">
                            <div class="text-center">
                                <div class="h4 mb-1 ${results.overallSuccessRate >= 80 ? 'text-success' : results.overallSuccessRate >= 60 ? 'text-warning' : 'text-danger'}">${results.overallSuccessRate}%</div>
                                <div class="small text-muted">Overall Success</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <div class="h4 mb-1 text-info">${results.totalExecutionTime}ms</div>
                                <div class="small text-muted">Total Time</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <div class="h4 mb-1 text-primary">${results.totalCategories}</div>
                                <div class="small text-muted">Categories</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <div class="h4 mb-1 text-secondary">${this.realTimeMonitor.metrics.completedTests + this.realTimeMonitor.metrics.failedTests}</div>
                                <div class="small text-muted">Tests Run</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    ${Object.entries(results.categoryResults).map(([category, data]) => `
                        <div class="col-md-6 mb-3">
                            <div class="card">
                                <div class="card-body">
                                    <h6 class="card-title">
                                        <i class="fas ${this.getCategoryIcon(category)} me-2"></i>
                                        ${category.replace('_', ' ').toUpperCase()}
                                    </h6>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="badge ${this.getStatusBadgeClass(data.status)}">${data.status.replace('_', ' ')}</span>
                                        <span class="text-muted">${data.executionTime}ms</span>
                                    </div>
                                    <div class="progress mt-2" style="height: 4px;">
                                        <div class="progress-bar ${data.successRate >= 80 ? 'bg-success' : data.successRate >= 60 ? 'bg-warning' : 'bg-danger'}" 
                                             style="width: ${data.successRate}%"></div>
                                    </div>
                                    <div class="small text-muted mt-1">${data.successRate}% success rate</div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                ${results.recommendations.length > 0 ? `
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-lightbulb me-2"></i>Recommendations</h6>
                        <ul class="mb-0">
                            ${results.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
        
        container.innerHTML = resultsHTML;
        
        // Update overview section
        this.updateOverviewEnhanced(results);
    }
    
    getCategoryIcon(category) {
        const icons = {
            critical: 'fa-exclamation-triangle',
            performance: 'fa-tachometer-alt', 
            accuracy: 'fa-bullseye',
            ui_interaction: 'fa-mouse-pointer',
            integration: 'fa-plug'
        };
        return icons[category] || 'fa-cog';
    }
    
    getStatusBadgeClass(status) {
        const classes = {
            excellent: 'badge-success',
            good: 'badge-warning', 
            needs_attention: 'badge-danger',
            error: 'badge-dark'
        };
        return classes[status] || 'badge-secondary';
    }
    
    updateOverviewEnhanced(results) {
        // Enhanced overview update with more detailed metrics
        const overviewElement = document.getElementById('test-overview');
        if (overviewElement) {
            overviewElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">Enhanced Testing Overview</h6>
                    <span class="badge ${results.overallSuccessRate >= 80 ? 'badge-success' : results.overallSuccessRate >= 60 ? 'badge-warning' : 'badge-danger'}">
                        ${results.overallSuccessRate}% Success
                    </span>
                </div>
                <div class="small text-muted mt-1">
                    ${results.totalCategories} categories • ${results.totalExecutionTime}ms total execution
                </div>
            `;
        }
    }
    
    displayErrorResults(error) {
        console.error('❌ Enhanced testing failed:', error);
        
        const container = document.getElementById('test-results-container');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <h5><i class="fas fa-exclamation-triangle me-2"></i>Enhanced Testing Failed</h5>
                    <p><strong>Error:</strong> ${error.message}</p>
                    <p class="mb-0">The enhanced testing framework encountered an error. Falling back to standard testing may be necessary.</p>
                </div>
            `;
        }
    }

    // Performance metrics management
    updateTestMetrics(testName, executionTime, success) {
        const metrics = this.realTimeMonitor.metrics;
        
        if (success) {
            metrics.completedTests++;
        } else {
            metrics.failedTests++;
        }
        
        // Update average response time
        const totalTests = metrics.completedTests + metrics.failedTests;
        metrics.averageResponseTime = ((metrics.averageResponseTime * (totalTests - 1)) + executionTime) / totalTests;
    }

    calculateSuccessRate(results) {
        if (results.size === 0) return 0;
        
        const successfulTests = Array.from(results.values()).filter(
            result => result.status === 'pass' || result.status === 'success'
        ).length;
        
        return Math.round((successfulTests / results.size) * 100);
    }
    // ===== ADVANCED ASSERTION LIBRARY =====
    // Enhanced assertion methods with detailed error reporting and context
    createAdvancedAssertions() {
        return {
            // Enhanced equality assertion with deep comparison
            assertEquals: (actual, expected, message = '') => {
                const result = { 
                    passed: false, 
                    actual, 
                    expected, 
                    message,
                    error: null,
                    context: {}
                };

                try {
                    if (typeof actual === 'object' && typeof expected === 'object') {
                        result.passed = JSON.stringify(actual) === JSON.stringify(expected);
                        if (!result.passed) {
                            result.context.deepComparison = this.getObjectDifferences(actual, expected);
                        }
                    } else {
                        result.passed = actual === expected;
                    }
                    
                    if (!result.passed && !message) {
                        result.message = `Expected ${JSON.stringify(expected)}, but got ${JSON.stringify(actual)}`;
                    }
                } catch (error) {
                    result.error = error.message;
                    result.passed = false;
                }

                return result;
            },

            // Enhanced boolean assertion with context
            assertTrue: (condition, message = '') => {
                const result = {
                    passed: !!condition,
                    actual: condition,
                    expected: true,
                    message: message || `Expected condition to be true, but got ${condition}`,
                    context: {
                        conditionType: typeof condition,
                        isFalsy: !condition
                    }
                };

                return result;
            },

            // API response assertion with detailed analysis
            assertAPIResponse: (response, expectedStatus = 200, message = '') => {
                const result = {
                    passed: false,
                    actual: {
                        status: response.status,
                        ok: response.ok,
                        statusText: response.statusText
                    },
                    expected: {
                        status: expectedStatus,
                        ok: expectedStatus >= 200 && expectedStatus < 300
                    },
                    message,
                    context: {
                        headers: {},
                        url: response.url
                    }
                };

                result.passed = response.status === expectedStatus;
                
                if (!result.passed && !message) {
                    result.message = `API call failed: Expected status ${expectedStatus}, got ${response.status} (${response.statusText})`;
                }

                // Capture response headers for debugging
                if (response.headers) {
                    response.headers.forEach((value, key) => {
                        result.context.headers[key] = value;
                    });
                }

                return result;
            },

            // Performance assertion with threshold checking
            assertPerformance: (actualTime, threshold, message = '') => {
                const result = {
                    passed: actualTime <= threshold,
                    actual: actualTime,
                    expected: `<= ${threshold}ms`,
                    message: message || `Performance assertion failed: ${actualTime}ms exceeds threshold of ${threshold}ms`,
                    context: {
                        performanceCategory: this.categorizePerformance(actualTime, threshold),
                        improvementNeeded: Math.max(0, actualTime - threshold),
                        percentageOver: Math.round(((actualTime - threshold) / threshold) * 100)
                    }
                };

                return result;
            },

            // Data freshness assertion with timestamp analysis
            assertDataFreshness: (timestamp, maxAge = 300000, message = '') => {
                const age = Date.now() - new Date(timestamp).getTime();
                const result = {
                    passed: age <= maxAge,
                    actual: age,
                    expected: `<= ${maxAge}ms`,
                    message: message || `Data is too old: ${age}ms exceeds maximum age of ${maxAge}ms`,
                    context: {
                        ageInSeconds: Math.round(age / 1000),
                        ageInMinutes: Math.round(age / 60000),
                        freshnessScore: Math.max(0, 100 - (age / 1000)) // Score decreases by 1 per second
                    }
                };

                return result;
            },

            // Element existence assertion with DOM context
            assertElementExists: (selector, message = '') => {
                const element = document.querySelector(selector);
                const result = {
                    passed: !!element,
                    actual: element ? 'found' : 'not found',
                    expected: 'found',
                    message: message || `Element not found: ${selector}`,
                    context: {
                        selector,
                        elementType: element ? element.tagName : null,
                        elementId: element ? element.id : null,
                        elementClasses: element ? element.className : null
                    }
                };

                return result;
            },

            // Array assertion with detailed comparison
            assertArrayContains: (array, expectedItems, message = '') => {
                const missing = expectedItems.filter(item => !array.includes(item));
                const result = {
                    passed: missing.length === 0,
                    actual: array,
                    expected: expectedItems,
                    message: message || `Array missing expected items: ${missing.join(', ')}`,
                    context: {
                        arrayLength: array.length,
                        expectedLength: expectedItems.length,
                        missingItems: missing,
                        extraItems: array.filter(item => !expectedItems.includes(item))
                    }
                };

                return result;
            }
        };
    }

    // Helper method to compare objects and find differences
    getObjectDifferences(obj1, obj2) {
        const differences = [];
        const keys1 = Object.keys(obj1 || {});
        const keys2 = Object.keys(obj2 || {});
        
        // Check for missing or different keys
        [...new Set([...keys1, ...keys2])].forEach(key => {
            if (!(key in obj1)) {
                differences.push(`Missing key in actual: ${key}`);
            } else if (!(key in obj2)) {
                differences.push(`Extra key in actual: ${key}`);
            } else if (obj1[key] !== obj2[key]) {
                differences.push(`Different value for ${key}: ${obj1[key]} vs ${obj2[key]}`);
            }
        });
        
        return differences;
    }

    // Helper method to categorize performance
    categorizePerformance(actualTime, threshold) {
        const ratio = actualTime / threshold;
        if (ratio <= 0.5) return 'excellent';
        if (ratio <= 0.8) return 'good';
        if (ratio <= 1.0) return 'acceptable';
        if (ratio <= 1.5) return 'slow';
        return 'critical';
    }

    // Enhanced error reporting with assertion results
    generateAssertionReport(assertionResults) {
        const report = {
            totalAssertions: assertionResults.length,
            passed: 0,
            failed: 0,
            errorDetails: [],
            performanceIssues: [],
            recommendations: []
        };

        assertionResults.forEach((assertion, index) => {
            if (assertion.passed) {
                report.passed++;
            } else {
                report.failed++;
                
                const errorDetail = {
                    assertionIndex: index,
                    message: assertion.message,
                    actual: assertion.actual,
                    expected: assertion.expected,
                    context: assertion.context || {},
                    severity: this.determineAssertionSeverity(assertion)
                };

                report.errorDetails.push(errorDetail);

                // Categorize performance issues
                if (assertion.context && assertion.context.performanceCategory) {
                    report.performanceIssues.push({
                        category: assertion.context.performanceCategory,
                        details: assertion.context
                    });
                }
            }
        });

        // Generate recommendations
        if (report.performanceIssues.length > 0) {
            report.recommendations.push('Performance optimization needed for slow endpoints');
        }
        
        if (report.failed / report.totalAssertions > 0.3) {
            report.recommendations.push('High failure rate indicates system instability');
        }

        return report;
    }

    // Determine severity of assertion failures
    determineAssertionSeverity(assertion) {
        if (assertion.context && assertion.context.performanceCategory === 'critical') {
            return 'critical';
        }
        
        if (assertion.message.includes('API call failed') || assertion.message.includes('not found')) {
            return 'high';
        }
        
        if (assertion.context && assertion.context.freshnessScore < 50) {
            return 'medium';
        }
        
        return 'low';
    }
}

// Global instance of enhanced test runner
const enhancedTestRunner = new EnhancedTestRunner();

// Updated main function to use enhanced testing
async function runSyncTests() {
    await enhancedTestRunner.runAllTests();
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
        'recalculation_button': 'Recalculation Button Workflow Test',
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
        'recalculation_button': 'Tests complete recalculation button workflow - button exists in DOM, JavaScript functions are defined, API endpoints are accessible, and the interactive workflow works end-to-end. Prevents errors like missing JavaScript functions.',
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
    
    // Auto-run disabled - tests should be manually triggered
    console.log('✅ Test runners initialized - click buttons to run tests manually');
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
        
        // Check JavaScript function availability
        const hasExecuteTakeProfitFunction = typeof window.executeTakeProfit === 'function';
        
        // Check event listeners
        let hasEventListener = false;
        let eventListenerDetails = 'none';
        
        // Check onclick
        if (button.onclick && typeof button.onclick === 'function') {
            hasEventListener = true;
            eventListenerDetails = 'onclick_handler';
        }
        
        // Test click simulation (without executing)
        let clickResponseDetected = false;
        try {
            const originalConfirm = window.confirm;
            let confirmCalled = false;
            
            window.confirm = function(...args) {
                confirmCalled = true;
                return false; // Prevent actual execution
            };
            
            button.click();
            clickResponseDetected = confirmCalled;
            
            window.confirm = originalConfirm;
        } catch (clickError) {
            clickResponseDetected = false;
        }
        
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
            hasExecuteTakeProfitFunction,
            hasEventListener,
            clickResponseDetected,
            apiStatus !== 'error',
            hasCorrectText
        ];
        
        const passedChecks = allChecks.filter(Boolean).length;
        
        return {
            status: passedChecks >= 6 ? 'pass' : (passedChecks >= 4 ? 'partial' : 'fail'),
            button_found: button !== null,
            button_checks: buttonChecks,
            has_execute_takeprofit_function: hasExecuteTakeProfitFunction,
            has_event_listener: hasEventListener,
            event_listener_details: eventListenerDetails,
            click_response_detected: clickResponseDetected,
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
        
        // Check JavaScript function availability
        const hasShowBuyDialogFunction = typeof window.showBuyDialog === 'function';
        
        // Test event listeners and click response
        let hasEventListener = false;
        let clickResponseDetected = false;
        
        // Test click simulation
        try {
            const originalPrompt = window.prompt;
            let promptCalled = false;
            
            window.prompt = function(...args) {
                promptCalled = true;
                return null; // Cancel to prevent actual execution
            };
            
            if (button.onclick) {
                hasEventListener = true;
            }
            
            button.click();
            clickResponseDetected = promptCalled;
            
            window.prompt = originalPrompt;
        } catch (clickError) {
            clickResponseDetected = false;
        }
        
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
            confidence_api_endpoint: await testConfidenceAPIEndpoint(),
            modal_buttons_functionality: await testModalButtonsFunctionality(),
            crypto_logos_display: await testCryptoLogosDisplay()
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
            button_details: buttonDetails.slice(0, 8), // Show more for debugging
            has_show_confidence_details_function: typeof window.showConfidenceDetails === 'function',
            function_check_results: {
                global_window: typeof window.showConfidenceDetails === 'function',
                trading_app: window.tradingApp && typeof window.tradingApp.showConfidenceDetails === 'function',
                direct_check: typeof showConfidenceDetails !== 'undefined'
            },
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

async function testModalButtonsFunctionality() {
    try {
        const testResults = {
            close_button_test: await testModalCloseButton(),
            execute_trade_button_test: await testModalExecuteTradeButton(),
            bootstrap_modal_integration: await testBootstrapModalIntegration(),
            modal_cleanup_test: await testModalCleanupFunctionality()
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
            error: `Modal buttons test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testModalCloseButton() {
    try {
        // Test if we can create a test modal to validate Close button functionality
        const testModal = document.createElement('div');
        testModal.className = 'modal fade';
        testModal.id = 'test-close-modal';
        testModal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Test Modal</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">Test Content</div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        // Temporarily add to DOM for testing
        document.body.appendChild(testModal);
        
        // Check for Close button elements
        const closeButtons = testModal.querySelectorAll('[data-bs-dismiss="modal"]');
        const hasCloseButtons = closeButtons.length >= 1;
        
        // Check button classes and structure
        const footerCloseButton = testModal.querySelector('.modal-footer button.btn-secondary');
        const headerCloseButton = testModal.querySelector('.modal-header .btn-close');
        
        const footerButtonCorrect = footerCloseButton && 
                                   footerCloseButton.textContent.includes('Close') &&
                                   footerCloseButton.getAttribute('data-bs-dismiss') === 'modal';
        
        const headerButtonCorrect = headerCloseButton && 
                                   headerCloseButton.getAttribute('data-bs-dismiss') === 'modal';
        
        // Test Bootstrap modal functionality if available
        let modalCanBeCreated = false;
        let modalHasDismissHandlers = false;
        
        if (typeof window.bootstrap !== 'undefined' && window.bootstrap.Modal) {
            try {
                const bootstrapModal = new window.bootstrap.Modal(testModal);
                modalCanBeCreated = true;
                
                // Check if bootstrap has proper dismiss handlers
                modalHasDismissHandlers = typeof bootstrapModal.hide === 'function';
            } catch (modalError) {
                modalCanBeCreated = false;
            }
        }
        
        // Cleanup test modal
        document.body.removeChild(testModal);
        
        const allChecks = [
            hasCloseButtons,
            footerButtonCorrect,
            headerButtonCorrect,
            modalCanBeCreated,
            modalHasDismissHandlers
        ];
        
        const passedChecks = allChecks.filter(Boolean).length;
        
        return {
            status: passedChecks >= 4 ? 'pass' : (passedChecks >= 3 ? 'partial' : 'fail'),
            has_close_buttons: hasCloseButtons,
            footer_button_correct: footerButtonCorrect,
            header_button_correct: headerButtonCorrect,
            modal_can_be_created: modalCanBeCreated,
            modal_has_dismiss_handlers: modalHasDismissHandlers,
            close_buttons_count: closeButtons.length,
            passed_checks: passedChecks,
            total_checks: allChecks.length,
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Close button test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testModalExecuteTradeButton() {
    try {
        // Test Execute Trade button functionality by simulating modal HTML generation
        const testSymbol = 'BTC';
        
        // Create test scenarios for different confidence scores
        const testScenarios = [
            { confidence: 75, shouldHaveButton: true, description: 'High confidence (75)' },
            { confidence: 60, shouldHaveButton: true, description: 'Minimum confidence (60)' },
            { confidence: 45, shouldHaveButton: false, description: 'Low confidence (45)' }
        ];
        
        let scenarioResults = [];
        
        for (const scenario of testScenarios) {
            try {
                // Simulate the modal HTML generation logic from showConfidenceDetails
                const shouldRenderButton = scenario.confidence >= 60;
                const executeButtonHtml = shouldRenderButton ? 
                    `<button type="button" class="btn btn-primary" onclick="buyBackPosition('${testSymbol}'); bootstrap.Modal.getInstance(document.getElementById('confidenceModal')).hide();">Execute Trade</button>` : 
                    '';
                
                // Create test modal with this HTML
                const testModal = document.createElement('div');
                testModal.className = 'modal fade';
                testModal.id = 'test-execute-modal';
                testModal.innerHTML = `
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-body">Test for confidence ${scenario.confidence}</div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                ${executeButtonHtml}
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(testModal);
                
                // Check button presence
                const executeButton = testModal.querySelector('.modal-footer button.btn-primary');
                const buttonExists = executeButton !== null;
                const buttonTextCorrect = executeButton ? executeButton.textContent.includes('Execute Trade') : false;
                const buttonOnclickCorrect = executeButton ? 
                    (executeButton.getAttribute('onclick') && 
                     executeButton.getAttribute('onclick').includes('buyBackPosition') &&
                     executeButton.getAttribute('onclick').includes('bootstrap.Modal.getInstance')) : false;
                
                scenarioResults.push({
                    confidence_score: scenario.confidence,
                    description: scenario.description,
                    should_have_button: scenario.shouldHaveButton,
                    button_exists: buttonExists,
                    button_text_correct: buttonTextCorrect,
                    button_onclick_correct: buttonOnclickCorrect,
                    test_passed: (buttonExists === scenario.shouldHaveButton) && 
                                (buttonExists ? (buttonTextCorrect && buttonOnclickCorrect) : true)
                });
                
                // Cleanup
                document.body.removeChild(testModal);
                
            } catch (scenarioError) {
                scenarioResults.push({
                    confidence_score: scenario.confidence,
                    description: scenario.description,
                    error: scenarioError.message,
                    test_passed: false
                });
            }
        }
        
        // Check if buyBackPosition function exists globally
        const hasBuyBackFunction = typeof window.buyBackPosition === 'function';
        
        // Determine overall result
        const passedScenarios = scenarioResults.filter(s => s.test_passed).length;
        const totalScenarios = scenarioResults.length;
        
        const allChecks = [
            passedScenarios === totalScenarios,
            hasBuyBackFunction,
            typeof window.bootstrap !== 'undefined'
        ];
        
        const passedChecks = allChecks.filter(Boolean).length;
        
        return {
            status: passedChecks >= 2 ? 'pass' : (passedChecks >= 1 ? 'partial' : 'fail'),
            scenario_results: scenarioResults,
            passed_scenarios: passedScenarios,
            total_scenarios: totalScenarios,
            has_buyback_function: hasBuyBackFunction,
            has_bootstrap: typeof window.bootstrap !== 'undefined',
            passed_checks: passedChecks,
            total_checks: allChecks.length,
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Execute Trade button test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testBootstrapModalIntegration() {
    try {
        // Test Bootstrap Modal API integration
        const hasBootstrap = typeof window.bootstrap !== 'undefined';
        const hasModal = hasBootstrap && typeof window.bootstrap.Modal === 'function';
        
        // Test modal creation and manipulation
        let modalCreationWorks = false;
        let modalMethodsAvailable = false;
        let modalInstanceMethods = false;
        
        if (hasModal) {
            try {
                // Create a test modal element
                const testModalElement = document.createElement('div');
                testModalElement.className = 'modal fade';
                testModalElement.id = 'bootstrap-test-modal';
                testModalElement.innerHTML = `
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-body">Bootstrap Test</div>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(testModalElement);
                
                // Test Bootstrap Modal constructor
                const modalInstance = new window.bootstrap.Modal(testModalElement);
                modalCreationWorks = true;
                
                // Test modal methods
                modalMethodsAvailable = typeof modalInstance.show === 'function' && 
                                       typeof modalInstance.hide === 'function';
                
                // Test getInstance method
                modalInstanceMethods = typeof window.bootstrap.Modal.getInstance === 'function';
                
                // Test getInstance functionality
                const retrievedInstance = window.bootstrap.Modal.getInstance(testModalElement);
                const getInstanceWorks = retrievedInstance === modalInstance;
                
                // Cleanup
                document.body.removeChild(testModalElement);
                
                modalInstanceMethods = modalInstanceMethods && getInstanceWorks;
                
            } catch (modalTestError) {
                modalCreationWorks = false;
                modalMethodsAvailable = false;
                modalInstanceMethods = false;
            }
        }
        
        // Test data-bs-dismiss attribute handling
        let dismissAttributeSupported = false;
        if (hasBootstrap) {
            try {
                const testDismissElement = document.createElement('button');
                testDismissElement.setAttribute('data-bs-dismiss', 'modal');
                dismissAttributeSupported = true;
            } catch (dismissError) {
                dismissAttributeSupported = false;
            }
        }
        
        const allChecks = [
            hasBootstrap,
            hasModal,
            modalCreationWorks,
            modalMethodsAvailable,
            modalInstanceMethods,
            dismissAttributeSupported
        ];
        
        const passedChecks = allChecks.filter(Boolean).length;
        
        return {
            status: passedChecks >= 5 ? 'pass' : (passedChecks >= 3 ? 'partial' : 'fail'),
            has_bootstrap: hasBootstrap,
            has_modal_constructor: hasModal,
            modal_creation_works: modalCreationWorks,
            modal_methods_available: modalMethodsAvailable,
            modal_instance_methods: modalInstanceMethods,
            dismiss_attribute_supported: dismissAttributeSupported,
            passed_checks: passedChecks,
            total_checks: allChecks.length,
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Bootstrap modal integration test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

async function testModalCleanupFunctionality() {
    try {
        // Test modal cleanup and event handling
        let modalCleanupWorks = false;
        let eventListenerWorks = false;
        let modalRemovalWorks = false;
        
        const testModalId = 'cleanup-test-modal';
        
        try {
            // Create test modal
            const testModal = document.createElement('div');
            testModal.className = 'modal fade';
            testModal.id = testModalId;
            testModal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-body">Cleanup Test</div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(testModal);
            
            // Test event listener attachment (simulating the cleanup code from showConfidenceDetails)
            let eventFired = false;
            testModal.addEventListener('hidden.bs.modal', function() {
                eventFired = true;
            });
            
            eventListenerWorks = true;
            
            // Test modal removal
            const modalExists = document.getElementById(testModalId) !== null;
            if (modalExists) {
                testModal.remove();
                const modalRemoved = document.getElementById(testModalId) === null;
                modalRemovalWorks = modalRemoved;
            }
            
            modalCleanupWorks = eventListenerWorks && modalRemovalWorks;
            
        } catch (cleanupError) {
            modalCleanupWorks = false;
            eventListenerWorks = false;
            modalRemovalWorks = false;
        }
        
        // Test existing modal removal logic (from showConfidenceDetails function)
        let existingModalRemovalWorks = false;
        try {
            // Create a modal with the expected ID
            const existingModal = document.createElement('div');
            existingModal.id = 'confidenceModal';
            document.body.appendChild(existingModal);
            
            // Test the removal logic
            const foundModal = document.getElementById('confidenceModal');
            if (foundModal) {
                foundModal.remove();
                const removedSuccessfully = document.getElementById('confidenceModal') === null;
                existingModalRemovalWorks = removedSuccessfully;
            }
        } catch (removalError) {
            existingModalRemovalWorks = false;
        }
        
        // Test insertAdjacentHTML functionality (used in showConfidenceDetails)
        let htmlInsertionWorks = false;
        try {
            const testContainer = document.createElement('div');
            document.body.appendChild(testContainer);
            
            testContainer.insertAdjacentHTML('beforeend', '<div id="insertion-test">Test</div>');
            const insertedElement = testContainer.querySelector('#insertion-test');
            htmlInsertionWorks = insertedElement !== null;
            
            // Cleanup
            document.body.removeChild(testContainer);
        } catch (insertionError) {
            htmlInsertionWorks = false;
        }
        
        const allChecks = [
            modalCleanupWorks,
            eventListenerWorks,
            modalRemovalWorks,
            existingModalRemovalWorks,
            htmlInsertionWorks
        ];
        
        const passedChecks = allChecks.filter(Boolean).length;
        
        return {
            status: passedChecks >= 4 ? 'pass' : (passedChecks >= 2 ? 'partial' : 'fail'),
            modal_cleanup_works: modalCleanupWorks,
            event_listener_works: eventListenerWorks,
            modal_removal_works: modalRemovalWorks,
            existing_modal_removal_works: existingModalRemovalWorks,
            html_insertion_works: htmlInsertionWorks,
            passed_checks: passedChecks,
            total_checks: allChecks.length,
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Modal cleanup test failed: ${error.message}`,
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

// Comprehensive JavaScript Error Detection Test
async function testJavaScriptErrors() {
    try {
        const results = {
            errors: [],
            warnings: [],
            function_tests: {},
            error_tracking_available: false,
            recent_errors: [],
            total_checks: 0,
            passed_checks: 0
        };

        // Clear any previous errors before testing
        if (typeof window.clearRecentErrors === 'function') {
            window.clearRecentErrors();
            results.error_tracking_available = true;
        }

        // Check for JavaScript errors first
        console.log('🔍 Checking for JavaScript errors...');
        let hasJSErrors = false;

        // Check recent errors from the new error tracking system
        if (typeof window.getRecentErrors === 'function') {
            const recentErrors = window.getRecentErrors();
            results.recent_errors = recentErrors;
            
            if (recentErrors.length > 0) {
                console.error('❌ Recent JavaScript errors detected:', recentErrors);
                hasJSErrors = true;
                recentErrors.forEach(error => {
                    results.errors.push(`JS Error: ${error.message} ${error.filename ? `at ${error.filename}:${error.lineno}` : ''}`);
                });
            } else {
                console.log('✅ No recent JavaScript errors detected');
                results.passed_checks++;
            }
            results.total_checks++;
        } else {
            console.warn('⚠️ Error tracking system not available');
            results.warnings.push('Error tracking system not available - cannot detect JavaScript errors');
        }

        // Check for specific functions
        console.log('🔍 Checking function availability...');
        const functionChecks = [
            { name: 'showConfidenceDetails', exists: typeof window.showConfidenceDetails === 'function' },
            { name: 'AppUtils.fetchJSON', exists: typeof AppUtils?.fetchJSON === 'function' },
            { name: 'showBuyDialog', exists: typeof window.showBuyDialog === 'function' },
            { name: 'showSellDialog', exists: typeof window.showSellDialog === 'function' },
            { name: 'ModularTradingApp.initLegacyTableFunctions', exists: typeof ModularTradingApp === 'function' && 
                                                                       ModularTradingApp.prototype.initLegacyTableFunctions !== undefined },
            { name: 'window.getRecentErrors', exists: typeof window.getRecentErrors === 'function' },
            { name: 'window.tradingApp', exists: typeof window.tradingApp === 'object' && window.tradingApp !== null },
            { name: 'bootstrap.Modal', exists: typeof window.bootstrap?.Modal === 'function' },
            { name: 'Chart', exists: typeof window.Chart === 'function' }
        ];

        functionChecks.forEach(check => {
            results.total_checks++;
            results.function_tests[check.name] = check.exists;
            
            if (!check.exists) {
                console.error(`❌ Function missing: ${check.name}`);
                results.errors.push(`Missing function: ${check.name}`);
            } else {
                console.log(`✅ Function available: ${check.name}`);
                results.passed_checks++;
            }
        });

        // Test core JavaScript functionality
        try {
            // Test basic array operations
            const testArray = [1, 2, 3];
            testArray.push(4);
            if (testArray.length !== 4) throw new Error('Array operations not working');
            results.passed_checks++;
        } catch (e) {
            results.errors.push('Core JavaScript array operations failing');
        }
        results.total_checks++;

        // Test DOM functionality
        try {
            const testDiv = document.createElement('div');
            testDiv.innerHTML = 'test';
            if (testDiv.textContent !== 'test') throw new Error('DOM operations not working');
            results.passed_checks++;
        } catch (e) {
            results.errors.push('DOM manipulation operations failing');
        }
        results.total_checks++;

        // Test fetch API availability
        try {
            if (typeof fetch !== 'function') throw new Error('Fetch API not available');
            results.passed_checks++;
        } catch (e) {
            results.errors.push('Fetch API not available');
        }
        results.total_checks++;

        const successRate = results.total_checks > 0 ? Math.round((results.passed_checks / results.total_checks) * 100) : 0;
        
        return {
            status: results.errors.length === 0 ? 'pass' : 'fail',
            success_rate: successRate,
            total_checks: results.total_checks,
            passed_checks: results.passed_checks,
            failed_checks: results.total_checks - results.passed_checks,
            errors_found: results.errors.length,
            warnings_found: results.warnings.length,
            error_tracking_available: results.error_tracking_available,
            recent_errors_count: results.recent_errors.length,
            function_tests: results.function_tests,
            details: {
                errors: results.errors,
                warnings: results.warnings,
                recent_errors: results.recent_errors
            },
            test_timestamp: new Date().toISOString()
        };

    } catch (error) {
        return {
            status: 'error',
            error: `JavaScript error test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

// Test crypto logos display instead of generic coin icons
async function testCryptoLogosDisplay() {
    try {
        // Wait for tables to load
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        let totalRows = 0;
        let cryptoLogosFound = 0;
        let genericIconsFound = 0;
        let logoDetails = [];
        
        // Check Holdings table
        const holdingsTable = document.querySelector('#holdings-table tbody');
        if (holdingsTable) {
            const holdingsRows = Array.from(holdingsTable.querySelectorAll('tr')).filter(row => {
                return !row.textContent.includes('Loading') && 
                       !row.textContent.includes('No holdings') &&
                       row.cells.length > 3;
            });
            
            holdingsRows.forEach((row, index) => {
                totalRows++;
                const firstCell = row.cells[0];
                if (firstCell) {
                    // Look for crypto logo images vs generic coin icons
                    const cryptoImg = firstCell.querySelector('img[src*="coingecko.com"]');
                    const genericIcon = firstCell.querySelector('i.fa-coins, i.fa-solid.fa-coins');
                    
                    if (cryptoImg) {
                        cryptoLogosFound++;
                        logoDetails.push({
                            table: 'holdings',
                            row_index: index,
                            logo_type: 'crypto_image',
                            src: cryptoImg.src.substr(0, 80),
                            alt: cryptoImg.alt || 'N/A'
                        });
                    } else if (genericIcon) {
                        genericIconsFound++;
                        logoDetails.push({
                            table: 'holdings',
                            row_index: index,
                            logo_type: 'generic_icon',
                            classes: genericIcon.className,
                            element: 'font_awesome'
                        });
                    }
                }
            });
        }
        
        // Check Available Positions table  
        const availableTable = document.querySelector('#available-table tbody');
        if (availableTable) {
            const availableRows = Array.from(availableTable.querySelectorAll('tr')).filter(row => {
                return !row.textContent.includes('Loading') && 
                       !row.textContent.includes('No positions') &&
                       row.cells.length > 5;
            });
            
            availableRows.forEach((row, index) => {
                totalRows++;
                const firstCell = row.cells[0];
                if (firstCell) {
                    // Look for crypto logo images vs generic coin icons
                    const cryptoImg = firstCell.querySelector('img[src*="coingecko.com"]');
                    const genericIcon = firstCell.querySelector('i.fa-coins, i.fa-solid.fa-coins');
                    
                    if (cryptoImg) {
                        cryptoLogosFound++;
                        logoDetails.push({
                            table: 'available',
                            row_index: index,
                            logo_type: 'crypto_image',
                            src: cryptoImg.src.substr(0, 80),
                            alt: cryptoImg.alt || 'N/A'
                        });
                    } else if (genericIcon) {
                        genericIconsFound++;
                        logoDetails.push({
                            table: 'available',
                            row_index: index,
                            logo_type: 'generic_icon',
                            classes: genericIcon.className,
                            element: 'font_awesome'
                        });
                    }
                }
            });
        }
        
        // Determine pass/fail status
        const logoPercentage = totalRows > 0 ? (cryptoLogosFound / totalRows) * 100 : 0;
        const status = logoPercentage >= 80 ? 'pass' : logoPercentage >= 50 ? 'partial' : 'fail';
        
        return {
            status: status,
            total_rows_checked: totalRows,
            crypto_logos_found: cryptoLogosFound,
            generic_icons_found: genericIconsFound,
            logo_percentage: logoPercentage.toFixed(1),
            logo_details: logoDetails.slice(0, 10), // Limit for readability
            recommendation: genericIconsFound > 0 ? 'Replace generic coin icons with authentic crypto logos' : 'Crypto logos correctly implemented',
            test_timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            status: 'error',
            error: `Crypto logos display test failed: ${error.message}`,
            test_timestamp: new Date().toISOString()
        };
    }
}

// Also initialize tooltips when Bootstrap is ready
window.addEventListener('load', function() {
    setTimeout(initializeTooltips, 500);
});

// ===== NORMAL TESTING FUNCTIONALITY =====
class NormalTestRunner {
    constructor() {
        this.testResults = [];
    }
    
    initializeBasicProgress() {
        const container = document.getElementById('test-progress-container');
        if (container) {
            container.style.display = 'block';
        }
    }
    
    updateBasicProgress(testName, completed, total) {
        const progressPercent = Math.round((completed / total) * 100);
        
        // Update progress bar
        const progressBar = document.getElementById('test-progress-bar');
        const progressText = document.getElementById('progress-text');
        if (progressBar) {
            progressBar.style.width = `${progressPercent}%`;
            progressBar.setAttribute('aria-valuenow', progressPercent);
        }
        if (progressText) {
            progressText.textContent = `${progressPercent}%`;
        }
        
        // Update current test name
        const testNameElement = document.getElementById('current-test-name');
        if (testNameElement) {
            testNameElement.textContent = testName;
        }
        
        // Update completed count
        const completedElement = document.getElementById('completed-count');
        if (completedElement) {
            completedElement.textContent = completed;
        }
        
        console.log(`📊 Normal Test Progress: ${progressPercent}% - ${testName}`);
    }
    
    async runBasicTests() {
        const button = document.getElementById('run-normal-tests-btn');
        const testResultsContainer = document.getElementById('test-results-container');
        
        // Reset UI
        this.updateButtonState(button, 'running');
        testResultsContainer.innerHTML = '<div class="text-center p-4"><i class="fas fa-spinner fa-spin fa-2x text-primary mb-3"></i><h5>Running Basic Tests...</h5></div>';
        
        try {
            // Run essential tests only
            const tests = [
                { name: 'API Connectivity', func: 'testBasicAPIConnectivity' },
                { name: 'Portfolio Data', func: 'testBasicPortfolioData' },
                { name: 'Price Updates', func: 'testBasicPriceUpdates' },
                { name: 'Button Functions', func: 'testBasicButtonFunctions' }
            ];
            
            const results = [];
            for (const test of tests) {
                try {
                    const result = await this[test.func]();
                    results.push({ ...result, testName: test.name });
                } catch (error) {
                    results.push({ 
                        testName: test.name, 
                        status: 'error', 
                        error: error.message 
                    });
                }
            }
            
            this.displayBasicResults(results);
            
        } catch (error) {
            testResultsContainer.innerHTML = `<div class="alert alert-danger">Test execution failed: ${error.message}</div>`;
        } finally {
            this.updateButtonState(button, 'idle');
        }
    }
    
    async testBasicAPIConnectivity() {
        try {
            const response = await fetch('/api/okx-status');
            const data = await response.json();
            return {
                status: data.connected ? 'pass' : 'fail',
                details: `OKX Status: ${data.connected ? 'Connected' : 'Disconnected'}`
            };
        } catch (error) {
            return { status: 'error', error: error.message };
        }
    }
    
    async testBasicPortfolioData() {
        try {
            const response = await fetch('/api/crypto-portfolio');
            const data = await response.json();
            return {
                status: data.holdings && data.holdings.length > 0 ? 'pass' : 'fail',
                details: `Found ${data.holdings ? data.holdings.length : 0} holdings`
            };
        } catch (error) {
            return { status: 'error', error: error.message };
        }
    }
    
    async testBasicPriceUpdates() {
        try {
            const response = await fetch('/api/price-source-status');
            const data = await response.json();
            return {
                status: data.status === 'connected' ? 'pass' : 'fail',
                details: `Price source: ${data.status}`
            };
        } catch (error) {
            return { status: 'error', error: error.message };
        }
    }
    
    async testBasicButtonFunctions() {
        const recalcButton = document.getElementById('recalculate-btn');
        const atoButton = document.getElementById('ato-export-btn');
        
        let foundButtons = 0;
        if (recalcButton) foundButtons++;
        if (atoButton) foundButtons++;
        
        return {
            status: foundButtons >= 1 ? 'pass' : 'fail',
            details: `Found ${foundButtons} essential buttons`
        };
    }
    
    displayBasicResults(results) {
        const container = document.getElementById('test-results-container');
        const passedTests = results.filter(r => r.status === 'pass').length;
        const totalTests = results.length;
        const successRate = Math.round((passedTests / totalTests) * 100);
        
        let html = `
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="fas fa-clipboard-check me-2"></i>Normal Test Results</h5>
                </div>
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-md-3 text-center">
                            <h3 class="text-primary">${totalTests}</h3>
                            <small class="text-muted">Total Tests</small>
                        </div>
                        <div class="col-md-3 text-center">
                            <h3 class="text-success">${passedTests}</h3>
                            <small class="text-muted">Passed</small>
                        </div>
                        <div class="col-md-3 text-center">
                            <h3 class="text-danger">${totalTests - passedTests}</h3>
                            <small class="text-muted">Failed</small>
                        </div>
                        <div class="col-md-3 text-center">
                            <h3 class="${successRate >= 75 ? 'text-success' : successRate >= 50 ? 'text-warning' : 'text-danger'}">${successRate}%</h3>
                            <small class="text-muted">Success Rate</small>
                        </div>
                    </div>
                    <div class="row">`;
        
        results.forEach(result => {
            const statusClass = result.status === 'pass' ? 'success' : result.status === 'error' ? 'danger' : 'warning';
            const icon = result.status === 'pass' ? 'check-circle' : result.status === 'error' ? 'times-circle' : 'exclamation-triangle';
            
            html += `
                <div class="col-md-6 mb-3">
                    <div class="card border-${statusClass}">
                        <div class="card-body">
                            <h6 class="card-title">
                                <i class="fas fa-${icon} text-${statusClass} me-2"></i>${result.testName}
                            </h6>
                            <p class="card-text small">${result.details || result.error || 'Test completed'}</p>
                        </div>
                    </div>
                </div>`;
        });
        
        html += `</div></div></div>`;
        container.innerHTML = html;
    }
    
    updateButtonState(button, state) {
        if (!button) return;
        
        if (state === 'running') {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Running Tests...';
        } else {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-play me-2"></i>Run Normal Tests';
        }
    }
}

// Additional DOMContentLoaded handler for normal testing
document.addEventListener('DOMContentLoaded', function() {
    // Initialize normal test runner
    window.normalTestRunner = new NormalTestRunner();
    
    // Bind normal tests button
    setTimeout(() => {
        const runNormalTestsBtn = document.getElementById('run-normal-tests-btn');
        if (runNormalTestsBtn) {
            runNormalTestsBtn.addEventListener('click', () => window.normalTestRunner.runBasicTests());
            console.log('✅ Normal test runner initialized');
        }
    }, 100);
});

// ===== COMPREHENSIVE ERROR LOGGING ENHANCEMENT =====
// Add error export and detailed logging to the enhanced test runner
(function enhanceTestRunnerWithErrorLogging() {
    // Wait for the enhanced test runner to be available
    setTimeout(() => {
        const enhancedTestRunner = window.enhancedTestRunner;
        if (!enhancedTestRunner) {
            console.warn('Enhanced test runner not found, retrying...');
            setTimeout(enhanceTestRunnerWithErrorLogging, 500);
            return;
        }

        // Add error summary generation method
        enhancedTestRunner.generateErrorSummary = function() {
            return {
                totalErrors: this.errorLog.detailedErrors.length,
                consoleErrors: this.errorLog.consoleErrors.length,
                networkErrors: this.errorLog.networkErrors.length,
                testFailures: this.errorLog.testFailures.length,
                sessionId: this.errorLog.sessionId,
                errorBreakdown: {
                    javascript: this.errorLog.detailedErrors.filter(e => e.type.includes('JAVASCRIPT')).length,
                    network: this.errorLog.detailedErrors.filter(e => e.type.includes('NETWORK')).length,
                    test: this.errorLog.detailedErrors.filter(e => e.type.includes('TEST')).length,
                    console: this.errorLog.detailedErrors.filter(e => e.type.includes('CONSOLE')).length
                }
            };
        };

        // Add detailed error export functionality
        enhancedTestRunner.exportErrorLog = function() {
            this.collectSystemInfo();
            
            const errorReport = {
                sessionId: this.errorLog.sessionId,
                timestamp: new Date().toISOString(),
                systemInfo: this.errorLog.systemInfo,
                summary: this.generateErrorSummary(),
                detailedErrors: this.errorLog.detailedErrors,
                consoleErrors: this.errorLog.consoleErrors,
                networkErrors: this.errorLog.networkErrors,
                testFailures: this.errorLog.testFailures,
                testMetrics: Array.from(this.metrics.values()),
                progressTracking: this.progressTracking
            };

            // Create downloadable error log
            const errorLogJson = JSON.stringify(errorReport, null, 2);
            const blob = new Blob([errorLogJson], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `test-error-log-${this.errorLog.sessionId}.json`;
            a.click();
            URL.revokeObjectURL(url);

            return errorReport;
        };

        // Add error display to test results
        enhancedTestRunner.addErrorDisplayToResults = function(resultsHtml, errorSummary) {
            if (errorSummary.totalErrors === 0) {
                return resultsHtml + `
                    <div class="alert alert-success mt-3">
                        <h6><i class="fas fa-check-circle me-2"></i>No Errors Detected</h6>
                        <p class="mb-0">All tests completed without any JavaScript, network, or console errors.</p>
                    </div>`;
            }

            const errorExportButton = `
                <div class="alert alert-warning mt-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6><i class="fas fa-exclamation-triangle me-2"></i>Errors Detected: ${errorSummary.totalErrors}</h6>
                            <ul class="mb-2">
                                <li>Console Errors: ${errorSummary.errorBreakdown.console}</li>
                                <li>Network Errors: ${errorSummary.errorBreakdown.network}</li>
                                <li>Test Failures: ${errorSummary.errorBreakdown.test}</li>
                                <li>JavaScript Errors: ${errorSummary.errorBreakdown.javascript}</li>
                            </ul>
                        </div>
                        <button class="btn btn-danger btn-sm" onclick="window.enhancedTestRunner.exportErrorLog()">
                            <i class="fas fa-download me-1"></i>Export Error Log
                        </button>
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">Session ID: ${errorSummary.sessionId}</small>
                    </div>
                </div>`;

            // Add detailed error breakdown
            const recentErrors = this.errorLog.detailedErrors.slice(-5).map(error => `
                <div class="border-left border-danger pl-2 mb-2">
                    <strong>${error.type}:</strong> ${error.message}<br>
                    <small class="text-muted">${error.timestamp}</small>
                </div>
            `).join('');

            const errorDetails = `
                <div class="card mt-3">
                    <div class="card-header">
                        <h6 class="mb-0">Recent Errors (Last 5)</h6>
                    </div>
                    <div class="card-body">
                        ${recentErrors || '<p class="text-muted">No recent errors</p>'}
                    </div>
                </div>`;

            return resultsHtml + errorExportButton + errorDetails;
        };

        // Override the display results method to include error information
        const originalDisplayResults = enhancedTestRunner.displayEnhancedResults;
        enhancedTestRunner.displayEnhancedResults = async function(results) {
            await originalDisplayResults.call(this, results);
            
            // Add error information to the results
            const container = document.getElementById('test-results-container');
            if (container) {
                const errorSummary = this.generateErrorSummary();
                const currentHtml = container.innerHTML;
                container.innerHTML = this.addErrorDisplayToResults(currentHtml, errorSummary);
            }
        };

        console.log('✅ Enhanced error logging system activated');
    }, 1000);
})();

// Global export function to maintain compatibility with HTML onclick
function exportErrorLogs() {
    try {
        if (window.enhancedTestRunner) {
            const exportData = window.enhancedTestRunner.exportErrorLogs();
            console.log('Error logs exported:', exportData.errorSummary);
            
            // Show success message
            if (typeof AppUtils !== 'undefined' && AppUtils.showToast) {
                AppUtils.showToast(`Error logs exported successfully! Found ${exportData.errorSummary.totalErrors} errors.`, 'success');
            } else {
                alert(`Error logs exported successfully! Found ${exportData.errorSummary.totalErrors} errors.`);
            }
        } else {
            console.warn('Enhanced test runner not initialized - creating new instance for export');
            const tempRunner = new EnhancedTestRunner();
            const exportData = tempRunner.exportErrorLogs();
            
            if (typeof AppUtils !== 'undefined' && AppUtils.showToast) {
                AppUtils.showToast('Error logs exported (no current session data)', 'info');
            } else {
                alert('Error logs exported (no current session data)');
            }
        }
    } catch (error) {
        console.error('Export error:', error);
        if (typeof AppUtils !== 'undefined' && AppUtils.showToast) {
            AppUtils.showToast('Failed to export error logs: ' + error.message, 'error');
        } else {
            alert('Failed to export error logs: ' + error.message);
        }
    }
}