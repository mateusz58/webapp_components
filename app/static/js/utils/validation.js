/* Form Validation Utilities */

/**
 * Form validation utilities and rules
 */
class ValidationUtils {
    /**
     * Common validation rules
     */
    static rules = {
        required: (value) => value.trim() !== '',
        email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
        minLength: (value, length) => value.length >= length,
        maxLength: (value, length) => value.length <= length,
        pattern: (value, pattern) => pattern.test(value),
        numeric: (value) => /^\d+$/.test(value),
        alphanumeric: (value) => /^[a-zA-Z0-9]+$/.test(value),
        supplierCode: (value) => /^[A-Z0-9]{3,10}$/.test(value)
    };

    /**
     * Validate a single field
     * @param {HTMLElement} field - Form field element
     * @param {Array} validationRules - Array of validation rules
     * @returns {Array} Array of error messages
     */
    static validateField(field, validationRules) {
        const value = field.value.trim();
        const errors = [];

        validationRules.forEach(rule => {
            const { type, message, ...params } = rule;
            
            if (type === 'required' && !this.rules.required(value)) {
                errors.push(message || 'This field is required');
            } else if (value && this.rules[type]) {
                if (!this.rules[type](value, params.value || params.length || params.pattern)) {
                    errors.push(message || this.getDefaultMessage(type, params));
                }
            }
        });

        this.updateFieldUI(field, errors);
        return errors;
    }

    /**
     * Validate entire form
     * @param {HTMLFormElement} form - Form element
     * @param {Object} fieldRules - Object mapping field names to validation rules
     * @returns {Object} Validation result with isValid boolean and errors object
     */
    static validateForm(form, fieldRules) {
        const errors = {};
        let isValid = true;

        Object.keys(fieldRules).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                const fieldErrors = this.validateField(field, fieldRules[fieldName]);
                if (fieldErrors.length > 0) {
                    errors[fieldName] = fieldErrors;
                    isValid = false;
                }
            }
        });

        return { isValid, errors };
    }

    /**
     * Update field UI based on validation result
     * @param {HTMLElement} field - Form field element
     * @param {Array} errors - Array of error messages
     */
    static updateFieldUI(field, errors) {
        const hasValue = field.value.trim() !== '';
        
        // Remove existing validation classes
        field.classList.remove('is-valid', 'is-invalid');
        
        // Remove existing error messages
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }

        if (errors.length > 0) {
            field.classList.add('is-invalid');
            this.showFieldError(field, errors[0]);
        } else if (hasValue) {
            field.classList.add('is-valid');
        }
    }

    /**
     * Show error message for field
     * @param {HTMLElement} field - Form field element
     * @param {string} message - Error message
     */
    static showFieldError(field, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    /**
     * Get default error message for validation type
     * @param {string} type - Validation type
     * @param {Object} params - Validation parameters
     * @returns {string} Default error message
     */
    static getDefaultMessage(type, params) {
        const messages = {
            email: 'Please enter a valid email address',
            minLength: `Minimum ${params.value || params.length} characters required`,
            maxLength: `Maximum ${params.value || params.length} characters allowed`,
            numeric: 'Please enter numbers only',
            alphanumeric: 'Please enter letters and numbers only',
            supplierCode: 'Please enter a valid supplier code (3-10 uppercase letters/numbers)'
        };
        return messages[type] || 'Invalid input';
    }

    /**
     * Setup real-time validation for form
     * @param {HTMLFormElement} form - Form element
     * @param {Object} fieldRules - Object mapping field names to validation rules
     */
    static setupRealTimeValidation(form, fieldRules) {
        Object.keys(fieldRules).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                // Validate on blur
                field.addEventListener('blur', () => {
                    this.validateField(field, fieldRules[fieldName]);
                });

                // Clear validation on focus (but keep valid state)
                field.addEventListener('focus', () => {
                    const existingError = field.parentNode.querySelector('.invalid-feedback');
                    if (existingError) {
                        existingError.remove();
                    }
                    field.classList.remove('is-invalid');
                });

                // Validate on input for immediate feedback
                field.addEventListener('input', AppUtils.debounce(() => {
                    this.validateField(field, fieldRules[fieldName]);
                }, 300));
            }
        });
    }

    /**
     * Common field validation rules
     */
    static commonRules = {
        supplierCode: [
            { type: 'required', message: 'Supplier code is required' },
            { type: 'supplierCode', message: 'Please enter a valid supplier code (e.g., SUPP001)' }
        ],
        email: [
            { type: 'email', message: 'Please enter a valid email address' }
        ],
        required: [
            { type: 'required', message: 'This field is required' }
        ],
        description: [
            { type: 'maxLength', value: 500, message: 'Description must be less than 500 characters' }
        ]
    };
}

// Export for use in other modules
window.ValidationUtils = ValidationUtils;