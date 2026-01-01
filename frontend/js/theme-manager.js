/**
 * Theme Manager for WAOOAW Portal
 * Handles dark/light theme switching with localStorage persistence
 */

class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('waooaw-theme') || 'dark';
        this.init();
    }

    init() {
        // Apply saved theme on page load
        this.applyTheme(this.currentTheme);
        
        // Listen for storage changes (cross-tab sync)
        window.addEventListener('storage', (e) => {
            if (e.key === 'waooaw-theme' && e.newValue) {
                this.currentTheme = e.newValue;
                this.applyTheme(this.currentTheme);
            }
        });
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        
        // Update toggle switch if it exists
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.checked = theme === 'light';
        }
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.currentTheme = newTheme;
        localStorage.setItem('waooaw-theme', newTheme);
        this.applyTheme(newTheme);
    }

    getCurrentTheme() {
        return this.currentTheme;
    }
}

// Initialize theme manager globally
window.themeManager = new ThemeManager();
