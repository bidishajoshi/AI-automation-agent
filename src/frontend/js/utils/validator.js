/**
 * Validator Utilities - Form and payload input validation
 */

export const sanitizeInput = (text) => {
  if (typeof text !== 'string') return '';
  return text.replace(/[<>]/g, '').trim();
};

export const validateTaskInput = (data) => {
  if (!data || typeof data !== 'object') {
    return {
      isValid: false,
      errors: { form: 'Input payload must be a non-null object' }
    };
  }

  const errors = {};

  if (!data.title || typeof data.title !== 'string' || data.title.trim().length < 5) {
    errors.title = 'Task title must be at least 5 characters long';
  }

  const validCategories = [
    'RESPONSIVE_CSS',
    'ACCESSIBILITY',
    'ERROR_HANDLING',
    'UI_POLISH',
    'OPTIMIZATION',
    'BUG_FIX'
  ];

  if (!data.category || !validCategories.includes(data.category)) {
    errors.category = 'Invalid task category selected';
  }

  const validPriorities = ['HIGH', 'MEDIUM', 'LOW'];
  if (!data.priority || !validPriorities.includes(data.priority)) {
    errors.priority = 'Invalid task priority';
  }

  if (data.targetFile && typeof data.targetFile === 'string') {
    const trimmed = data.targetFile.trim();
    if (trimmed.includes('..') || /[<>:"|?*]/.test(trimmed)) {
      errors.targetFile = 'Target file path contains invalid characters or traversal sequence';
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};
