/* API Utilities */

/**
 * API interaction utilities with consistent error handling
 */
class ApiUtils {
    /**
     * Default fetch options
     */
    static defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    };

    /**
     * Get CSRF token from cookie
     * @returns {string} CSRF token
     */
    static getCsrfToken() {
        const name = 'csrf_token=';
        const decodedCookie = decodeURIComponent(document.cookie);
        const cookies = decodedCookie.split(';');
        
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.indexOf(name) === 0) {
                return cookie.substring(name.length);
            }
        }
        
        // Fallback to meta tag if cookie not found
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        return metaToken ? metaToken.getAttribute('content') : '';
    }

    /**
     * Make GET request
     * @param {string} url - Request URL
     * @param {Object} options - Additional fetch options
     * @returns {Promise} Response promise
     */
    static async get(url, options = {}) {
        return this.request(url, {
            method: 'GET',
            ...options
        });
    }

    /**
     * Make POST request
     * @param {string} url - Request URL
     * @param {Object} data - Request body data
     * @param {Object} options - Additional fetch options
     * @returns {Promise} Response promise
     */
    static async post(url, data = {}, options = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
            ...options
        });
    }

    /**
     * Make PUT request
     * @param {string} url - Request URL
     * @param {Object} data - Request body data
     * @param {Object} options - Additional fetch options
     * @returns {Promise} Response promise
     */
    static async put(url, data = {}, options = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data),
            ...options
        });
    }

    /**
     * Make DELETE request
     * @param {string} url - Request URL
     * @param {Object} options - Additional fetch options
     * @returns {Promise} Response promise
     */
    static async delete(url, options = {}) {
        return this.request(url, {
            method: 'DELETE',
            ...options
        });
    }

    /**
     * Make form data request (for file uploads)
     * @param {string} url - Request URL
     * @param {FormData} formData - Form data object
     * @param {Object} options - Additional fetch options
     * @returns {Promise} Response promise
     */
    static async postForm(url, formData, options = {}) {
        const formOptions = { ...this.defaultOptions };
        delete formOptions.headers['Content-Type']; // Let browser set multipart boundary

        return this.request(url, {
            method: 'POST',
            body: formData,
            ...formOptions,
            ...options
        });
    }

    /**
     * Base request method with error handling
     * @param {string} url - Request URL
     * @param {Object} options - Fetch options
     * @returns {Promise} Response promise
     */
    static async request(url, options = {}) {
        const csrfToken = this.getCsrfToken();
        
        const config = {
            ...this.defaultOptions,
            ...options,
            headers: {
                ...this.defaultOptions.headers,
                'X-CSRFToken': csrfToken,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                await this.handleErrorResponse(response);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Check if response has content
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    /**
     * Handle error responses
     * @param {Response} response - Fetch response object
     */
    static async handleErrorResponse(response) {
        try {
            const errorData = await response.json();
            const message = errorData.message || errorData.error || `Request failed with status ${response.status}`;
            AppUtils.showFlashMessage(message, 'error');
        } catch {
            AppUtils.showFlashMessage(`Request failed with status ${response.status}`, 'error');
        }
    }

    /**
     * Build query string from object
     * @param {Object} params - Query parameters object
     * @returns {string} Query string
     */
    static buildQueryString(params) {
        const searchParams = new URLSearchParams();
        
        Object.keys(params).forEach(key => {
            const value = params[key];
            if (value !== null && value !== undefined && value !== '') {
                if (Array.isArray(value)) {
                    value.forEach(item => searchParams.append(key, item));
                } else {
                    searchParams.append(key, value);
                }
            }
        });

        return searchParams.toString();
    }

    /**
     * Build URL with query parameters
     * @param {string} baseUrl - Base URL
     * @param {Object} params - Query parameters
     * @returns {string} Complete URL with query string
     */
    static buildUrl(baseUrl, params = {}) {
        const queryString = this.buildQueryString(params);
        return queryString ? `${baseUrl}?${queryString}` : baseUrl;
    }

    /**
     * Show loading state
     * @param {HTMLElement} element - Element to show loading state on
     */
    static showLoading(element) {
        if (element) {
            element.classList.add('loading');
            element.disabled = true;
            
            // Store original content
            if (!element.dataset.originalContent) {
                element.dataset.originalContent = element.innerHTML;
            }
            
            element.innerHTML = '<i class="spinner-border spinner-border-sm me-2"></i>Loading...';
        }
    }

    /**
     * Hide loading state
     * @param {HTMLElement} element - Element to hide loading state from
     */
    static hideLoading(element) {
        if (element && element.dataset.originalContent) {
            element.classList.remove('loading');
            element.disabled = false;
            element.innerHTML = element.dataset.originalContent;
        }
    }

    /**
     * Retry failed requests
     * @param {Function} requestFn - Function that returns a promise
     * @param {number} maxRetries - Maximum number of retries
     * @param {number} delay - Delay between retries in milliseconds
     * @returns {Promise} Request promise
     */
    static async retryRequest(requestFn, maxRetries = 3, delay = 1000) {
        let lastError;
        
        for (let i = 0; i <= maxRetries; i++) {
            try {
                return await requestFn();
            } catch (error) {
                lastError = error;
                
                if (i < maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
                }
            }
        }
        
        throw lastError;
    }
}

// Export for use in other modules
window.ApiUtils = ApiUtils;