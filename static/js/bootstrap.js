// Dashboard Bootstrap Module - Single point of initialization
import { initDashboard } from './trading_dashboard.js';

// Prevent multiple initialization
if (window.__DASHBOARD_INIT__) {
    console.warn('Dashboard already initialized');
} else {
    window.__DASHBOARD_INIT__ = true;

    // Global error handlers for dashboard debugging
    window.addEventListener('error', (event) => {
        console.error('🔧 Global JavaScript Error:', {
            message: event.message,
            filename: event.filename,
            line: event.lineno,
            column: event.colno,
            error: event.error
        });
        
        // Show error in dashboard status
        const statusEl = document.getElementById('dashboard-status');
        if (statusEl) {
            statusEl.className = 'dashboard-status status-error';
            statusEl.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>JavaScript error detected - Check console';
        }
    });

    window.addEventListener('unhandledrejection', (event) => {
        console.error('🔧 Unhandled Promise Rejection:', event.reason);
        
        // Show error in dashboard status
        const statusEl = document.getElementById('dashboard-status');
        if (statusEl) {
            statusEl.className = 'dashboard-status status-error';
            statusEl.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Promise rejection - Check console';
        }
    });

    // Single initialization function
    function initializeAll() {
        console.log('🚀 Bootstrap: Starting dashboard initialization...');
        
        try {
            // Initialize TradingDashboard
            window.dashboard = initDashboard();
            console.log('✅ Bootstrap: TradingDashboard initialized');
        } catch (error) {
            console.error('❌ Bootstrap: TradingDashboard failed:', error);
        }

        try {
            // Initialize navigation
            initNavigation();
            console.log('✅ Bootstrap: Navigation initialized');
        } catch (error) {
            console.error('❌ Bootstrap: Navigation failed:', error);
        }

        try {
            // Initialize debug system
            initDebugSystem();
            console.log('✅ Bootstrap: Debug system initialized');
        } catch (error) {
            console.error('❌ Bootstrap: Debug system failed:', error);
        }

        console.log('🎯 Bootstrap: All systems initialized');
    }

    // Navigation initialization (extracted from inline script)
    function initNavigation() {
        // Set active navigation
        function setActiveNav() {
            const currentPath = window.location.pathname;
            document.querySelectorAll('.sidebar-nav a').forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === currentPath) {
                    link.classList.add('active');
                }
            });
        }
        
        setActiveNav();
        
        // Auto-refresh system status
        setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                if (status.active) {
                    updateSystemStatus('trading');
                } else {
                    updateSystemStatus('paused');
                }
            } catch (error) {
                updateSystemStatus('error');
                console.warn('System status check failed:', error);
            }
        }, 10000);
    }

    // Debug system initialization
    function initDebugSystem() {
        // Debug mode control
        window.TradingDebug = {
            enabled: localStorage.getItem('debug_mode') === 'true',
            
            enable() {
                this.enabled = true;
                localStorage.setItem('debug_mode', 'true');
                console.log('🔧 Trading Debug: ENABLED');
            },
            
            disable() {
                this.enabled = false;
                localStorage.setItem('debug_mode', 'false');
                console.log('🔧 Trading Debug: DISABLED');
            },
            
            log(message, category = 'INFO', data = null) {
                if (!this.enabled) return;
                const timestamp = new Date().toLocaleTimeString();
                const prefix = `🔧 [${timestamp}] ${category}:`;
                
                if (data) {
                    console.log(prefix, message, data);
                } else {
                    console.log(prefix, message);
                }
            }
        };

        // Page load debugging
        window.TradingDebug.log('DOM Content Loaded');
        window.TradingDebug.log('Page:', window.location.pathname);
        
        // Shortcut commands
        window.debug = {
            on: () => window.TradingDebug.enable(),
            off: () => window.TradingDebug.disable(),
            help: () => console.log('Commands: debug.on(), debug.off(), debug.help()')
        };
    }

    // System status helper
    function updateSystemStatus(status) {
        const statusEl = document.getElementById('systemStatus');
        if (!statusEl) return;
        
        switch (status) {
            case 'trading':
                statusEl.className = 'status-indicator status-trading';
                statusEl.innerHTML = '<i class="fas fa-play-circle"></i> TRADING';
                break;
            case 'paused':
                statusEl.className = 'status-indicator status-paused';
                statusEl.innerHTML = '<i class="fas fa-pause-circle"></i> PAUSED';
                break;
            case 'error':
                statusEl.className = 'status-indicator status-error';
                statusEl.innerHTML = '<i class="fas fa-times-circle"></i> ERROR';
                break;
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeAll);
    } else {
        // DOM already loaded
        initializeAll();
    }
}