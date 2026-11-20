/**
 * DOM Helper Utilities - Safe DOM manipulation & query wrappers
 */

export const qs = (selector, parent = document) => {
  return parent.querySelector(selector);
};

export const qsa = (selector, parent = document) => {
  return Array.from(parent.querySelectorAll(selector));
};

export const on = (element, event, handler, options = {}) => {
  if (!element) return;
  element.addEventListener(event, handler, options);
};

export const escapeHTML = (str) => {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
};

export const showToast = (message, type = 'success', duration = 3000) => {
  const container = qs('#toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 250);
  }, duration);
};
