/**
 * Main Application Orchestrator - DevPulse
 */

import { qs, on, showToast } from './utils/dom.js';
import { validateTaskInput } from './utils/validator.js';
import { ThemeManager } from './components/themeManager.js';
import { Dashboard } from './components/dashboard.js';
import { TaskBoard } from './components/taskBoard.js';
import { Analytics } from './components/analytics.js';
import { ApiClient } from './api.js';

class App {
  constructor() {
    this.api = new ApiClient();
    this.themeManager = new ThemeManager();
    this.dashboard = new Dashboard();
    this.taskBoard = new TaskBoard(this.api);
    this.analytics = new Analytics();
    this.tasks = [];
  }

  async init() {
    this.themeManager.init();
    this.setupNavigation();
    this.setupModal();
    this.setupSearch();
    this.setupFilters();
    this.setupKeyboardShortcuts();
    await this.refreshData();
  }

  setupNavigation() {
    // Sidebar responsive toggle
    const toggleBtn = qs('#sidebarToggle');
    const sidebar = qs('#appSidebar');
    if (toggleBtn && sidebar) {
      on(toggleBtn, 'click', () => {
        sidebar.classList.toggle('sidebar-open');
      });
    }

    // View switching
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
      on(link, 'click', (e) => {
        e.preventDefault();
        const view = link.dataset.view;
        this.switchView(view);

        navLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');

        // Close sidebar on mobile
        if (sidebar) sidebar.classList.remove('sidebar-open');
      });
    });

    const refreshBtn = qs('#refreshDataBtn');
    if (refreshBtn) {
      on(refreshBtn, 'click', async () => {
        await this.refreshData();
        showToast('Data synced with cloud agent');
      });
    }
  }

  switchView(view) {
    const dashboardSection = qs('#dashboardSection');
    const historySection = qs('#historySection');

    if (view === 'dashboard' || view === 'tasks') {
      if (dashboardSection) dashboardSection.style.display = 'block';
      if (historySection) historySection.style.display = 'none';
    } else if (view === 'history' || view === 'analytics') {
      if (dashboardSection) dashboardSection.style.display = 'none';
      if (historySection) {
        historySection.style.display = 'block';
        if (this.history) this.analytics.renderHistory(this.history);
      }
    }
  }

  setupModal() {
    const openBtn = qs('#openNewTaskModalBtn');
    const closeBtn = qs('#closeModalBtn');
    const cancelBtn = qs('#cancelModalBtn');
    const modal = qs('#taskModal');
    const form = qs('#taskForm');

    const openModal = () => {
      if (modal) {
        modal.classList.add('open');
        modal.setAttribute('aria-hidden', 'false');
      }
    };

    const closeModal = () => {
      if (modal) {
        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
        if (form) form.reset();
      }
    };

    if (openBtn) on(openBtn, 'click', openModal);
    if (closeBtn) on(closeBtn, 'click', closeModal);
    if (cancelBtn) on(cancelBtn, 'click', closeModal);

    if (form) {
      on(form, 'submit', async (e) => {
        e.preventDefault();
        const titleInput = qs('#taskTitleInput');
        const categorySelect = qs('#taskCategorySelect');
        const prioritySelect = qs('#taskPrioritySelect');
        const targetFileInput = qs('#taskTargetFile');

        const payload = {
          title: titleInput ? titleInput.value.trim() : '',
          category: categorySelect ? categorySelect.value : 'RESPONSIVE_CSS',
          priority: prioritySelect ? prioritySelect.value : 'MEDIUM',
          targetFile: targetFileInput ? targetFileInput.value.trim() : ''
        };

        const validation = validateTaskInput(payload);
        if (!validation.isValid) {
          showToast(validation.errors.title || 'Please fill required fields', 'error');
          return;
        }

        await this.api.createTask(payload);
        showToast('Task queued successfully!');
        closeModal();
        await this.refreshData();
      });
    }
  }

  setupSearch() {
    const searchInput = qs('#globalSearch');
    if (searchInput) {
      let debounceTimer = null;
      on(searchInput, 'input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          const query = e.target.value.toLowerCase().trim();
          const filtered = this.tasks.filter(t => 
            t.title.toLowerCase().includes(query) ||
            (t.category && t.category.toLowerCase().includes(query))
          );
          this.taskBoard.renderTasks(filtered);
        }, 200);
      });
    }
  }


  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const modal = qs('#taskModal');
        if (modal && modal.classList.contains('open')) {
          modal.classList.remove('open');
          modal.setAttribute('aria-hidden', 'true');
        }
      } else if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        const search = qs('#globalSearch');
        if (search) search.focus();
      }
    });
  }

  setupFilters() {
    const priorityFilter = qs('#priorityFilter');
    if (priorityFilter) {
      on(priorityFilter, 'change', (e) => {
        this.taskBoard.renderTasks(this.tasks, e.target.value);
      });
    }
  }

  async refreshData() {
    const [tasks, metrics, history] = await Promise.all([
      this.api.getTasks(),
      this.api.getMetrics(),
      this.api.getHistory()
    ]);
    this.tasks = tasks;
    this.history = history;
    this.taskBoard.renderTasks(this.tasks);
    this.dashboard.updateMetrics(metrics);
    this.analytics.renderHistory(this.history);
  }
}

// Bootstrap application on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  const app = new App();
  app.init().catch(err => console.error('App init error:', err));
});
