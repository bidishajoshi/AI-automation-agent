/**
 * Validator Utilities - Form and payload input validation
 */

export const validateTaskInput = (data) => {
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

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};
