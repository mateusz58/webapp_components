/* Form Validation Components */

/**
 * Supplier Form Validation
 * Handles validation for supplier forms
 */
class SupplierFormValidator {
    constructor(formSelector = 'form') {
        this.form = document.querySelector(formSelector);
        this.supplierCodeInput = document.getElementById('supplier_code');
        this.init();
    }

    init() {
        if (!this.form || !this.supplierCodeInput) return;
        
        this.setupValidation();
        this.setupInitialState();
        this.setupSubmitHandler();
    }

    /**
     * Setup real-time validation
     */
    setupValidation() {
        // Supplier code validation on input
        this.supplierCodeInput.addEventListener('input', () => {
            this.validateSupplierCode();
        });

        // Validate on blur for better UX
        this.supplierCodeInput.addEventListener('blur', () => {
            this.validateSupplierCode();
        });
    }

    /**
     * Setup initial validation state
     */
    setupInitialState() {
        if (this.supplierCodeInput.value.trim() !== '') {
            this.validateSupplierCode();
        }
    }

    /**
     * Setup form submit handler
     */
    setupSubmitHandler() {
        this.form.addEventListener('submit', (event) => {
            if (!this.validateForm()) {
                event.preventDefault();
                this.showValidationError('Please provide a valid supplier code.');
            }
        });
    }

    /**
     * Validate supplier code field
     */
    validateSupplierCode() {
        const value = this.supplierCodeInput.value.trim();
        const isValid = value !== '' && ValidationUtils.rules.supplierCode(value);

        this.updateFieldValidation(this.supplierCodeInput, isValid);
        return isValid;
    }

    /**
     * Validate entire form
     */
    validateForm() {
        return this.validateSupplierCode();
    }

    /**
     * Update field validation UI
     */
    updateFieldValidation(field, isValid) {
        field.classList.remove('is-valid', 'is-invalid');
        
        if (field.value.trim() !== '') {
            if (isValid) {
                field.classList.add('is-valid');
            } else {
                field.classList.add('is-invalid');
            }
        }
    }

    /**
     * Show validation error message
     */
    showValidationError(message) {
        // Remove existing error messages
        const existingAlert = this.form.querySelector('.alert-danger');
        if (existingAlert) {
            existingAlert.remove();
        }

        // Create new error message
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger mt-3';
        alertDiv.textContent = message;
        this.form.prepend(alertDiv);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

/**
 * Generic Form Validator
 * Handles validation for any form with defined rules
 */
class GenericFormValidator {
    constructor(formSelector, validationRules) {
        this.form = document.querySelector(formSelector);
        this.rules = validationRules;
        this.init();
    }

    init() {
        if (!this.form) return;
        
        this.setupValidation();
        this.setupSubmitHandler();
    }

    /**
     * Setup validation for all fields
     */
    setupValidation() {
        Object.keys(this.rules).forEach(fieldName => {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.addEventListener('input', () => {
                    ValidationUtils.validateField(field, this.rules[fieldName]);
                });

                field.addEventListener('blur', () => {
                    ValidationUtils.validateField(field, this.rules[fieldName]);
                });
            }
        });
    }

    /**
     * Setup form submit handler
     */
    setupSubmitHandler() {
        this.form.addEventListener('submit', (event) => {
            const result = ValidationUtils.validateForm(this.form, this.rules);
            
            if (!result.isValid) {
                event.preventDefault();
                this.showValidationErrors(result.errors);
            }
        });
    }

    /**
     * Show validation errors
     */
    showValidationErrors(errors) {
        const errorMessages = Object.values(errors)
            .flat()
            .slice(0, 3); // Show max 3 errors

        if (errorMessages.length > 0) {
            AppUtils.showFlashMessage(
                `Please fix the following errors: ${errorMessages.join(', ')}`,
                'error'
            );
        }
    }
}

/**
 * Auto-initialize form validators when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize supplier form validator if on supplier form page
    const supplierForm = document.querySelector('#supplier-form, form[action*="supplier"]');
    if (supplierForm) {
        new SupplierFormValidator('form');
    }

    // Initialize other specific form validators
    const componentForm = document.querySelector('#component-form');
    if (componentForm) {
        const componentRules = {
            'product_number': ValidationUtils.commonRules.required,
            'description': ValidationUtils.commonRules.description,
            'supplier_id': ValidationUtils.commonRules.required,
            'category_id': ValidationUtils.commonRules.required
        };
        new GenericFormValidator('#component-form', componentRules);
    }

    // Initialize generic validation for forms with class 'needs-validation'
    const validationForms = document.querySelectorAll('.needs-validation');
    validationForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Show first validation error
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    AppUtils.showFlashMessage('Please fill in all required fields correctly', 'error');
                }
            }
            form.classList.add('was-validated');
        });
    });
});

// Export for use in other modules
window.SupplierFormValidator = SupplierFormValidator;
window.GenericFormValidator = GenericFormValidator;