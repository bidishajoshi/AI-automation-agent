/**
 * Formatters - Formatting helpers for metrics, dates, and badges
 */

export const formatDate = (isoString) => {
  if (!isoString) return 'N/A';
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return isoString;
  }
};

export const formatCategory = (category) => {
  const map = {
    RESPONSIVE_CSS: { label: 'CSS / Responsive', class: 'cat-responsive' },
    ACCESSIBILITY: { label: 'Accessibility', class: 'cat-a11y' },
    ERROR_HANDLING: { label: 'Error Handling', class: 'cat-error' },
    UI_POLISH: { label: 'UI Polish', class: 'cat-polish' },
    OPTIMIZATION: { label: 'Optimization', class: 'cat-opt' },
    BUG_FIX: { label: 'Bug Fix', class: 'cat-error' }
  };
  return map[category] || { label: category || 'General', class: 'cat-polish' };
};

export const truncate = (text, maxLength = 60) => {
  if (!text) return '';
  return text.length > maxLength ? text.slice(0, maxLength) + '...' : text;
};
