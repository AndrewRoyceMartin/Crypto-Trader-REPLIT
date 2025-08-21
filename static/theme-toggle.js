/**
 * Theme Toggle Functionality
 * Provides manual dark/light theme switching with localStorage persistence
 */

class ThemeToggle {
    constructor() {
        this.init();
    }

    init() {
        // Create theme toggle button
        this.createToggleButton();
        
        // Load saved theme or detect system preference
        this.loadTheme();
        
        // Listen for system theme changes
        this.listenForSystemChanges();
    }

    createToggleButton() {
        // Check if button already exists
        if (document.querySelector('.theme-toggle')) {
            return;
        }

        const toggle = document.createElement('button');
        toggle.className = 'theme-toggle';
        toggle.innerHTML = '<i class="fas fa-moon"></i>';
        toggle.title = 'Toggle dark theme';
        toggle.setAttribute('aria-label', 'Toggle dark theme');
        
        toggle.addEventListener('click', () => this.toggleTheme());
        
        document.body.appendChild(toggle);
        this.toggleButton = toggle;
    }

    loadTheme() {
        const savedTheme = localStorage.getItem('theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
            this.setDarkTheme();
        } else {
            this.setLightTheme();
        }
    }

    toggleTheme() {
        const isDark = document.body.classList.contains('dark-theme');
        
        if (isDark) {
            this.setLightTheme();
            localStorage.setItem('theme', 'light');
        } else {
            this.setDarkTheme();
            localStorage.setItem('theme', 'dark');
        }
    }

    setDarkTheme() {
        document.body.classList.add('dark-theme');
        if (this.toggleButton) {
            this.toggleButton.innerHTML = '<i class="fas fa-sun"></i>';
            this.toggleButton.title = 'Switch to light theme';
        }
    }

    setLightTheme() {
        document.body.classList.remove('dark-theme');
        if (this.toggleButton) {
            this.toggleButton.innerHTML = '<i class="fas fa-moon"></i>';
            this.toggleButton.title = 'Switch to dark theme';
        }
    }

    listenForSystemChanges() {
        // Only respond to system changes if user hasn't manually set a preference
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        mediaQuery.addEventListener('change', (e) => {
            const savedTheme = localStorage.getItem('theme');
            
            // Only auto-switch if user hasn't set a manual preference
            if (!savedTheme) {
                if (e.matches) {
                    this.setDarkTheme();
                } else {
                    this.setLightTheme();
                }
            }
        });
    }

    // Public method to set theme programmatically
    setTheme(theme) {
        if (theme === 'dark') {
            this.setDarkTheme();
            localStorage.setItem('theme', 'dark');
        } else if (theme === 'light') {
            this.setLightTheme();
            localStorage.setItem('theme', 'light');
        } else if (theme === 'auto') {
            localStorage.removeItem('theme');
            this.loadTheme();
        }
    }

    // Get current theme
    getCurrentTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            return savedTheme;
        }
        
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        return systemPrefersDark ? 'dark' : 'light';
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.themeToggle = new ThemeToggle();
    });
} else {
    window.themeToggle = new ThemeToggle();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeToggle;
}