/* Base Component Functionality */

/**
 * Base functionality that's loaded on every page
 */
class BaseApp {
    constructor() {
        this.init();
    }

    /**
     * Initialize base application functionality
     */
    init() {
        this.initializeIcons();
        this.setupFlashMessages();
        this.setupSmoothScrolling();
        this.setupTooltips();
        this.setupGlobalEventListeners();
    }

    /**
     * Initialize Lucide icons
     */
    initializeIcons() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    /**
     * Setup flash message auto-hide functionality
     */
    setupFlashMessages() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            // Auto-hide after 5 seconds
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.style.transition = 'opacity 0.5s ease';
                    alert.style.opacity = '0';
                    setTimeout(() => {
                        if (alert.parentNode) {
                            alert.remove();
                        }
                    }, 500);
                }
            }, 5000);
        });
    }

    /**
     * Setup smooth scrolling for anchor links
     */
    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    e.preventDefault();
                    AppUtils.smoothScrollTo(anchor.getAttribute('href'));
                }
            });
        });
    }

    /**
     * Setup Bootstrap tooltips
     */
    setupTooltips() {
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
    }

    /**
     * Setup global event listeners
     */
    setupGlobalEventListeners() {
        // Global form validation
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.classList.contains('needs-validation')) {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            }
        });

        // Global CSRF token handling for AJAX requests
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (csrfToken) {
            ApiUtils.defaultOptions.headers['X-CSRFToken'] = csrfToken.getAttribute('content');
        }

        // Global escape key handler for modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.modal.show');
                if (activeModal && typeof bootstrap !== 'undefined') {
                    const modal = bootstrap.Modal.getInstance(activeModal);
                    if (modal) {
                        modal.hide();
                    }
                }
            }
        });

        // Global click outside handler for dropdowns
        document.addEventListener('click', (e) => {
            const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
            openDropdowns.forEach(dropdown => {
                const button = dropdown.previousElementSibling;
                if (button && !button.contains(e.target) && !dropdown.contains(e.target)) {
                    dropdown.classList.remove('show');
                    button.setAttribute('aria-expanded', 'false');
                }
            });
        });

        // Global copy-to-clipboard functionality
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-copy]') || e.target.closest('[data-copy]')) {
                e.preventDefault();
                const element = e.target.matches('[data-copy]') ? e.target : e.target.closest('[data-copy]');
                const textToCopy = element.dataset.copy || element.textContent;
                AppUtils.copyToClipboard(textToCopy);
            }
        });

        // Global loading button handling
        document.addEventListener('submit', (e) => {
            const submitButton = e.target.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.disabled) {
                ApiUtils.showLoading(submitButton);
            }
        });
    }

    /**
     * Handle page unload
     */
    handlePageUnload() {
        // Clean up any ongoing processes
        const loadingElements = document.querySelectorAll('.loading');
        loadingElements.forEach(element => {
            ApiUtils.hideLoading(element);
        });
    }
}

/**
 * Initialize base app when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    window.baseApp = new BaseApp();
});

/**
 * Handle page unload
 */
window.addEventListener('beforeunload', () => {
    if (window.baseApp) {
        window.baseApp.handlePageUnload();
    }
});

// Export for use in other modules
window.BaseApp = BaseApp;