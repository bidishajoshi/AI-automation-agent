/**
 * Task Board (Kanban) Component
 */

import { qs, escapeHTML } from '../utils/dom.js';
import { formatCategory, formatDate } from '../utils/formatters.js';

export class TaskBoard {
  constructor(api) {
    this.api = api;
    this.columns = {
      TODO: qs('#todoCards'),
      IN_PROGRESS: qs('#progressCards'),
      VALIDATING: qs('#validatingCards'),
      DONE: qs('#doneCards')
    };
    this.counters = {
      TODO: qs('#todoCounter'),
      IN_PROGRESS: qs('#progressCounter'),
      VALIDATING: qs('#validatingCounter'),
      DONE: qs('#doneCounter')
    };
  }

  renderTasks(tasks, priorityFilter = 'ALL') {
    if (!Array.isArray(tasks)) {
      tasks = [];
    }

    // Reset columns
    Object.values(this.columns).forEach(col => {
      if (col) col.innerHTML = '';
    });

    const counts = { TODO: 0, IN_PROGRESS: 0, VALIDATING: 0, DONE: 0 };

    const filtered = tasks.filter(task => {
      if (priorityFilter === 'ALL') return true;
      return task.priority === priorityFilter;
    });

    filtered.forEach(task => {
      const status = task.status || 'TODO';
      if (counts[status] !== undefined) counts[status]++;

      const col = this.columns[status];
      if (!col) return;

      const card = document.createElement('div');
      card.className = 'task-card';
      card.dataset.taskId = task.id;

      const catInfo = formatCategory(task.category);

      card.innerHTML = `
        <span class="task-category ${catInfo.class}">${escapeHTML(catInfo.label)}</span>
        <h4 class="task-title">${escapeHTML(task.title)}</h4>
        <div class="task-meta">
          <span>${escapeHTML(task.priority)} Priority</span>
          <span>${formatDate(task.updatedAt || task.createdAt)}</span>
        </div>
      `;

      col.appendChild(card);
    });

    // Render empty state if a column has no cards
    Object.keys(this.columns).forEach(status => {
      const col = this.columns[status];
      if (col && counts[status] === 0) {
        const placeholder = document.createElement('div');
        placeholder.className = 'column-empty-state';
        placeholder.textContent = 'No tasks in this stage';
        col.appendChild(placeholder);
      }
    });

    // Update counters
    Object.keys(this.counters).forEach(status => {
      if (this.counters[status]) {
        this.counters[status].textContent = counts[status] || 0;
      }
    });
  }
}
