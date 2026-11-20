/**
 * Theme Manager - Light/Dark theme switching with persistence
 */

export class ThemeManager {
  constructor() {
    this.storageKey = 'devpulse_theme';
    this.currentTheme = localStorage.getItem(this.storageKey) || 'dark';
  }

  init() {
    this.applyTheme(this.currentTheme);
    const toggleBtn = document.getElementById('themeToggleBtn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => this.toggleTheme());
    }
  }

  toggleTheme() {
    this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    this.applyTheme(this.currentTheme);
    try {
      localStorage.setItem(this.storageKey, this.currentTheme);
    } catch {
      // LocalStorage disabled or in private browsing
    }
  }

  applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
  }
}
