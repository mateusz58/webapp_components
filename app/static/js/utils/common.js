/* Common Utility Functions */

/**
 * Common utilities used across the application
 */
class AppUtils {
    /**
     * Show flash message with auto-hide
     * @param {string} message - Message to display
     * @param {string} type - Message type (success, error, warning, info)
     * @param {number} duration - Auto-hide duration in milliseconds (default: 5000)
     */
    static showFlashMessage(message, type = 'info', duration = 5000) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at the top of main content
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.insertBefore(alertDiv, mainContent.firstChild);
        }

        // Auto-hide after duration
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    }

    /**
     * Smooth scroll to element
     * @param {string} selector - CSS selector of target element
     * @param {number} offset - Offset from top (default: navbar height)
     */
    static smoothScrollTo(selector, offset = 60) {
        const element = document.querySelector(selector);
        if (element) {
            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - offset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    }

    /**
     * Debounce function calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @param {boolean} immediate - Execute immediately on first call
     */
    static debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }

    /**
     * Format date for display
     * @param {Date|string} date - Date to format
     * @param {string} format - Format type ('short', 'long', 'relative')
     */
    static formatDate(date, format = 'short') {
        if (!date) return 'N/A';
        
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        
        switch (format) {
            case 'short':
                return dateObj.toLocaleDateString();
            case 'long':
                return dateObj.toLocaleDateString('en-US', { 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                });
            case 'relative':
                return this.getRelativeTime(dateObj);
            default:
                return dateObj.toLocaleDateString();
        }
    }

    /**
     * Get relative time string
     * @param {Date} date - Date to get relative time for
     */
    static getRelativeTime(date) {
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days} day${days !== 1 ? 's' : ''} ago`;
        if (hours > 0) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
        if (minutes > 0) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
        return 'Just now';
    }

    /**
     * Validate form field
     * @param {HTMLElement} field - Form field to validate
     * @param {Array} rules - Validation rules
     */
    static validateField(field, rules) {
        const value = field.value.trim();
        const errors = [];

        rules.forEach(rule => {
            switch (rule.type) {
                case 'required':
                    if (!value) errors.push(rule.message || 'This field is required');
                    break;
                case 'minLength':
                    if (value.length < rule.value) {
                        errors.push(rule.message || `Minimum ${rule.value} characters required`);
                    }
                    break;
                case 'email':
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (value && !emailRegex.test(value)) {
                        errors.push(rule.message || 'Please enter a valid email address');
                    }
                    break;
                case 'pattern':
                    if (value && !rule.pattern.test(value)) {
                        errors.push(rule.message || 'Invalid format');
                    }
                    break;
            }
        });

        // Update field UI
        if (errors.length > 0) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
        } else if (value) {
            field.classList.add('is-valid');
            field.classList.remove('is-invalid');
        }

        return errors;
    }

    /**
     * Handle AJAX errors
     * @param {Response} response - Fetch response object
     * @param {string} defaultMessage - Default error message
     */
    static async handleAjaxError(response, defaultMessage = 'An error occurred') {
        try {
            const errorData = await response.json();
            const message = errorData.message || defaultMessage;
            this.showFlashMessage(message, 'error');
        } catch {
            this.showFlashMessage(defaultMessage, 'error');
        }
    }

    /**
     * Copy text to clipboard
     * @param {string} text - Text to copy
     */
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showFlashMessage('Copied to clipboard', 'success', 2000);
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showFlashMessage('Copied to clipboard', 'success', 2000);
        }
    }
}

// Export for use in other modules
window.AppUtils = AppUtils;