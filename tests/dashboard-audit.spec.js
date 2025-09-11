// BASELINE AUDIT: Main Dashboard UI Validation
const fs = require('fs');

class DashboardAuditor {
    constructor() {
        this.results = {
            timestamp: new Date().toISOString(),
            url: 'http://127.0.0.1:5000/',
            kpis: [],
            tables: [],
            issues: [],
            warnings: [],
            summary: {}
        };
    }

    async auditDashboard() {
        console.log('🔍 Starting dashboard audit...');
        
        // Test page accessibility
        await this.testPageLoad();
        
        // Test API endpoints
        await this.testAPIEndpoints();
        
        // Check for common UI issues
        await this.checkUIElements();
        
        this.generateReport();
    }

    async testPageLoad() {
        console.log('📄 Testing dashboard page load...');
        
        try {
            const { exec } = require('child_process');
            const { promisify } = require('util');
            const execAsync = promisify(exec);
            
            // Test if dashboard loads
            const result = await execAsync('curl -s -w "%{http_code}" -o /dev/null "http://127.0.0.1:5000/"');
            const statusCode = result.stdout.trim();
            
            if (statusCode === '200') {
                console.log('✅ Dashboard loads successfully');
                this.results.summary.pageLoads = true;
            } else {
                console.log(`❌ Dashboard returns status ${statusCode}`);
                this.results.issues.push({
                    type: 'ERROR',
                    description: 'Dashboard page fails to load',
                    details: `HTTP status: ${statusCode}`
                });
            }
        } catch (error) {
            console.log('❌ Error testing page load:', error.message);
            this.results.issues.push({
                type: 'ERROR', 
                description: 'Cannot reach dashboard page',
                details: error.message
            });
        }
    }

    async testAPIEndpoints() {
        console.log('🔌 Testing API endpoints...');
        
        const endpoints = [
            '/api/current-holdings',
            '/api/portfolio-analytics', 
            '/api/performance-overview',
            '/api/trades',
            '/api/status'
        ];

        let healthyEndpoints = 0;
        
        for (const endpoint of endpoints) {
            try {
                const { exec } = require('child_process');
                const { promisify } = require('util');
                const execAsync = promisify(exec);
                
                const result = await execAsync(`curl -s -w "%{http_code}" "http://127.0.0.1:5000${endpoint}"`);
                const output = result.stdout;
                const statusCode = output.slice(-3);
                
                if (statusCode === '200') {
                    console.log(`✅ ${endpoint} - OK`);
                    healthyEndpoints++;
                } else {
                    console.log(`❌ ${endpoint} - Status ${statusCode}`);
                    this.results.warnings.push({
                        type: 'WARNING',
                        description: `API endpoint unhealthy: ${endpoint}`,
                        details: `Status: ${statusCode}`
                    });
                }
            } catch (error) {
                console.log(`❌ ${endpoint} - Error: ${error.message}`);
                this.results.warnings.push({
                    type: 'WARNING',
                    description: `API endpoint error: ${endpoint}`,
                    details: error.message
                });
            }
        }
        
        this.results.summary.healthyEndpoints = healthyEndpoints;
        this.results.summary.totalEndpoints = endpoints.length;
    }

    async checkUIElements() {
        console.log('🎯 Testing UI elements...');
        
        try {
            // Check dashboard template for common issues
            const templateContent = fs.readFileSync('templates/dashboard.html', 'utf8');
            
            // Check for stable data attributes
            const dataAttributes = [
                'data-metric',
                'data-value', 
                'data-table',
                'data-kpi',
                'data-currency',
                'data-percentage'
            ];
            
            let dataAttrCount = 0;
            for (const attr of dataAttributes) {
                const matches = (templateContent.match(new RegExp(attr, 'g')) || []).length;
                dataAttrCount += matches;
            }
            
            if (dataAttrCount < 5) {
                this.results.issues.push({
                    type: 'ERROR',
                    description: 'Missing stable data attributes',
                    details: `Only ${dataAttrCount} data attributes found. UI elements lack stable selectors for testing.`,
                    impact: 'Automated testing and maintenance will be unreliable'
                });
            }
            
            // Check for hardcoded fallbacks
            const hardcodedPatterns = [
                /\|\|\s*[0-9]+(\.[0-9]+)?/g,  // || 50, || 1.0, etc
                /\?\s*[0-9]+(\.[0-9]+)?\s*:/g,  // ? 50 :, ? 1.0 :
                /'--'\s*\|\|\s*[0-9]/g,  // '--' || 50
                /defaultValue.*[0-9]/g   // defaultValue: 100
            ];
            
            let hardcodedCount = 0;
            for (const pattern of hardcodedPatterns) {
                const matches = (templateContent.match(pattern) || []).length;
                hardcodedCount += matches;
            }
            
            if (hardcodedCount > 0) {
                this.results.issues.push({
                    type: 'ERROR',
                    description: 'Hardcoded fallback values detected',
                    details: `Found ${hardcodedCount} potential hardcoded fallbacks that may violate authentic data requirements`,
                    impact: 'System may display fake data instead of real OKX values'
                });
            }
            
            // Check for loading state management
            const hasLoadingSkeletons = templateContent.includes('loading-skeleton');
            const hasSpinners = templateContent.includes('fa-spinner') || templateContent.includes('spinner');
            
            if (hasLoadingSkeletons || hasSpinners) {
                const hasProperHiding = templateContent.includes('hideLoadingSkeletons') || 
                                      templateContent.includes('hide()') ||
                                      templateContent.includes('display: none');
                
                if (!hasProperHiding) {
                    this.results.warnings.push({
                        type: 'WARNING',
                        description: 'Loading states may persist',
                        details: 'Found loading elements but unclear hiding mechanism',
                        impact: 'Users may see loading spinners indefinitely'
                    });
                }
            }
            
            // Check for inconsistent number formatting
            const hasToFixed = templateContent.includes('toFixed');
            const hasToLocaleString = templateContent.includes('toLocaleString');
            const hasNumberFormat = templateContent.includes('NumberFormat') || templateContent.includes('Intl');
            
            if (hasToFixed && !hasNumberFormat && !hasToLocaleString) {
                this.results.warnings.push({
                    type: 'WARNING',
                    description: 'Inconsistent number formatting',
                    details: 'Uses basic toFixed() without proper currency/percentage formatting',
                    impact: 'Numbers may display inconsistently across the dashboard'
                });
            }
            
        } catch (error) {
            console.log('❌ Error checking UI elements:', error.message);
            this.results.issues.push({
                type: 'ERROR',
                description: 'Cannot analyze dashboard template',
                details: error.message
            });
        }
        
        console.log('⚠️  Checking for common issues...');
    }

    generateReport() {
        const errorCount = this.results.issues.filter(i => i.type === 'ERROR').length;
        const warningCount = this.results.warnings.length;
        
        // Create audit directory
        if (!fs.existsSync('./audit-dashboard-before')) {
            fs.mkdirSync('./audit-dashboard-before');
        }
        
        // Write JSON report
        fs.writeFileSync('./audit-dashboard-before/ui-audit.json', JSON.stringify(this.results, null, 2));
        
        // Write markdown report
        const markdown = this.generateMarkdown(errorCount, warningCount);
        fs.writeFileSync('./audit-dashboard-before/ui-audit.md', markdown);
        
        // Console output
        console.log('\n📊 AUDIT RESULTS:');
        if (errorCount === 0) {
            console.log(`DASHBOARD AUDIT: PASS(0 errors), WARN(${warningCount})`);
        } else {
            console.log(`DASHBOARD AUDIT: FAIL(${errorCount})/PASS(0), WARN(${warningCount})`);
        }
        
        console.log('\n📁 Artifacts generated:');
        console.log('  - ./audit-dashboard-before/ui-audit.json');
        console.log('  - ./audit-dashboard-before/ui-audit.md');
    }

    generateMarkdown(errorCount, warningCount) {
        return `# Dashboard UI Audit Report - Baseline

## Summary
- **Timestamp**: ${this.results.timestamp}
- **URL**: ${this.results.url}
- **Errors**: ${errorCount}
- **Warnings**: ${warningCount}
- **Status**: ${errorCount === 0 ? '✅ PASS' : '❌ FAIL'}

## Issues Found (${errorCount})
${this.results.issues.map(issue => `
### ❌ ${issue.description}
- **Type**: ${issue.type}
- **Details**: ${issue.details}
- **Impact**: ${issue.impact || 'Needs investigation'}
`).join('\n')}

## Warnings (${warningCount})
${this.results.warnings.map(warning => `
### ⚠️ ${warning.description}
- **Type**: ${warning.type}
- **Details**: ${warning.details}
- **Impact**: ${warning.impact || 'Monitor for issues'}
`).join('\n')}

## System Health
- **Page Loads**: ${this.results.summary.pageLoads ? '✅ Yes' : '❌ No'}
- **API Health**: ${this.results.summary.healthyEndpoints}/${this.results.summary.totalEndpoints} endpoints healthy

## Next Steps
${errorCount > 0 ? '1. Apply repairs to address critical errors' : '1. System appears healthy'}
${warningCount > 0 ? '2. Review warnings and apply preventive fixes' : '2. Monitor for future issues'}
3. Run post-repair audit to verify fixes
4. Update testing framework with stable selectors
`;
    }
}

// Run baseline audit
async function runDashboardAudit() {
    const auditor = new DashboardAuditor();
    await auditor.auditDashboard();
}

if (require.main === module) {
    runDashboardAudit().catch(console.error);
}

module.exports = { DashboardAuditor };