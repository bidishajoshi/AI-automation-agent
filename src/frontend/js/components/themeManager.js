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
    const toggleBtn = document.getElementById('themeToggleBtn');
    if (toggleBtn) {
      const nextTheme = theme === 'dark' ? 'light' : 'dark';
      toggleBtn.setAttribute('aria-label', `Switch to ${nextTheme} theme`);
      toggleBtn.setAttribute('title', `Switch to ${nextTheme === 'dark' ? 'Dark' : 'Light'} Theme`);

      const sunSvg = `<svg class="icon icon-sun" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
      const moonSvg = `<svg class="icon icon-moon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;

      toggleBtn.innerHTML = theme === 'dark' ? sunSvg : moonSvg;
    }
  }
}
