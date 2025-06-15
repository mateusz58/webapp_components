/**
 * Performance optimization utilities for the frontend
 */

class PerformanceOptimizer {
    constructor() {
        this.imageObserver = null;
        this.debounceTimers = new Map();
        this.cache = new Map();
        this.requestQueue = [];
        this.isProcessingQueue = false;
        
        this.init();
    }
    
    init() {
        this.setupLazyLoading();
        this.setupInfiniteScroll();
        this.setupRequestBatching();
        this.preloadCriticalResources();
    }
    
    /**
     * Lazy loading for images
     */
    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            this.imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        const src = img.dataset.src;
                        
                        if (src) {
                            img.src = src;
                            img.classList.remove('lazy-loading');
                            img.classList.add('lazy-loaded');
                            this.imageObserver.unobserve(img);
                        }
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.1
            });
            
            // Observe all lazy images
            this.observeLazyImages();
        }
    }
    
    observeLazyImages() {
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => {
            img.classList.add('lazy-loading');
            this.imageObserver.observe(img);
        });
    }
    
    /**
     * Infinite scroll for large lists
     */
    setupInfiniteScroll() {
        const loadMoreTrigger = document.getElementById('load-more-trigger');
        if (!loadMoreTrigger) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !this.isLoadingMore) {
                    this.loadMoreItems();
                }
            });
        }, {
            rootMargin: '100px'
        });
        
        observer.observe(loadMoreTrigger);
    }
    
    async loadMoreItems() {
        if (this.isLoadingMore) return;
        
        this.isLoadingMore = true;
        const currentPage = parseInt(document.querySelector('[data-current-page]')?.dataset.currentPage || '1');
        const nextPage = currentPage + 1;
        
        try {
            const response = await fetch(`${window.location.pathname}?page=${nextPage}&ajax=1`);
            const data = await response.json();
            
            if (data.html) {
                const container = document.querySelector('.components-grid, .suppliers-list');
                if (container) {
                    container.insertAdjacentHTML('beforeend', data.html);
                    
                    // Update current page
                    document.querySelector('[data-current-page]').dataset.currentPage = nextPage;
                    
                    // Observe new lazy images
                    this.observeLazyImages();
                    
                    // Hide load more trigger if no more pages
                    if (!data.has_next) {
                        document.getElementById('load-more-trigger').style.display = 'none';
                    }
                }
            }
        } catch (error) {
            console.error('Error loading more items:', error);
        } finally {
            this.isLoadingMore = false;
        }
    }
    
    /**
     * Debounced function execution
     */
    debounce(func, delay, key) {
        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
        }
        
        const timer = setTimeout(() => {
            func();
            this.debounceTimers.delete(key);
        }, delay);
        
        this.debounceTimers.set(key, timer);
    }
    
    /**
     * Cached AJAX requests
     */
    async cachedFetch(url, options = {}) {
        const cacheKey = `${url}_${JSON.stringify(options)}`;
        
        // Check cache first
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            // Return cached data if less than 5 minutes old
            if (Date.now() - cached.timestamp < 300000) {
                return cached.data;
            }
        }
        
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            
            // Cache the response
            this.cache.set(cacheKey, {
                data: data,
                timestamp: Date.now()
            });
            
            return data;
        } catch (error) {
            console.error('Fetch error:', error);
            throw error;
        }
    }
    
    /**
     * Batch API requests to reduce server load
     */
    setupRequestBatching() {
        this.batchInterval = setInterval(() => {
            if (this.requestQueue.length > 0 && !this.isProcessingQueue) {
                this.processBatchedRequests();
            }
        }, 100); // Process batches every 100ms
    }
    
    addToBatch(request) {
        this.requestQueue.push(request);
    }
    
    async processBatchedRequests() {
        if (this.isProcessingQueue || this.requestQueue.length === 0) return;
        
        this.isProcessingQueue = true;
        const batch = this.requestQueue.splice(0, 10); // Process up to 10 requests at once
        
        try {
            const promises = batch.map(request => 
                this.cachedFetch(request.url, request.options)
                    .then(data => ({ success: true, data, request }))
                    .catch(error => ({ success: false, error, request }))
            );
            
            const results = await Promise.all(promises);
            
            results.forEach(result => {
                if (result.success && result.request.callback) {
                    result.request.callback(result.data);
                } else if (!result.success && result.request.errorCallback) {
                    result.request.errorCallback(result.error);
                }
            });
        } catch (error) {
            console.error('Batch processing error:', error);
        } finally {
            this.isProcessingQueue = false;
        }
    }
    
    /**
     * Preload critical resources
     */
    preloadCriticalResources() {
        // Preload commonly used API endpoints
        const criticalEndpoints = [
            '/api/components/search',
            '/api/suppliers/search',
            '/api/brands/search'
        ];
        
        criticalEndpoints.forEach(endpoint => {
            // Add to cache with empty query to warm it up
            this.cachedFetch(`${endpoint}?q=`).catch(() => {
                // Ignore errors for preloading
            });
        });
    }
    
    /**
     * Optimize form submissions
     */
    optimizeFormSubmission(form) {
        form.addEventListener('submit', (e) => {
            // Disable submit button to prevent double submission
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'Processing...';
                
                // Re-enable after 3 seconds as fallback
                setTimeout(() => {
                    submitButton.disabled = false;
                    submitButton.textContent = submitButton.dataset.originalText || 'Submit';
                }, 3000);
            }
        });
    }
    
    /**
     * Virtual scrolling for very large lists
     */
    setupVirtualScrolling(container, itemHeight = 100, bufferSize = 5) {
        if (!container) return;
        
        const items = Array.from(container.children);
        const totalItems = items.length;
        
        if (totalItems < 50) return; // Don't virtualize small lists
        
        const containerHeight = container.clientHeight;
        const visibleItems = Math.ceil(containerHeight / itemHeight);
        const totalHeight = totalItems * itemHeight;
        
        // Create virtual container
        const virtualContainer = document.createElement('div');
        virtualContainer.style.height = `${totalHeight}px`;
        virtualContainer.style.position = 'relative';
        
        container.appendChild(virtualContainer);
        
        // Hide original items
        items.forEach(item => item.style.display = 'none');
        
        let startIndex = 0;
        let endIndex = visibleItems + bufferSize;
        
        const updateVisibleItems = () => {
            const scrollTop = container.scrollTop;
            startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - bufferSize);
            endIndex = Math.min(totalItems, startIndex + visibleItems + (bufferSize * 2));
            
            // Clear virtual container
            virtualContainer.innerHTML = '';
            
            // Add visible items
            for (let i = startIndex; i < endIndex; i++) {
                const item = items[i].cloneNode(true);
                item.style.position = 'absolute';
                item.style.top = `${i * itemHeight}px`;
                item.style.display = 'block';
                virtualContainer.appendChild(item);
            }
        };
        
        // Initial render
        updateVisibleItems();
        
        // Update on scroll
        container.addEventListener('scroll', () => {
            this.debounce(updateVisibleItems, 16, 'virtual-scroll'); // ~60fps
        });
    }
    
    /**
     * Cleanup resources
     */
    destroy() {
        if (this.imageObserver) {
            this.imageObserver.disconnect();
        }
        
        if (this.batchInterval) {
            clearInterval(this.batchInterval);
        }
        
        this.debounceTimers.forEach(timer => clearTimeout(timer));
        this.debounceTimers.clear();
        this.cache.clear();
    }
}

// Initialize performance optimizer when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.performanceOptimizer = new PerformanceOptimizer();
    
    // Optimize all forms
    document.querySelectorAll('form').forEach(form => {
        window.performanceOptimizer.optimizeFormSubmission(form);
    });
    
    // Setup virtual scrolling for large lists
    const largeList = document.querySelector('.large-list, .components-grid');
    if (largeList) {
        window.performanceOptimizer.setupVirtualScrolling(largeList);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.performanceOptimizer) {
        window.performanceOptimizer.destroy();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceOptimizer;
}