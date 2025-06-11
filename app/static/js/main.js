// app/static/js/main.js
// Enhanced JavaScript for Shopify Analytics Dashboard

(function() {
    'use strict';

    // Application namespace
    window.ShopifyAnalytics = window.ShopifyAnalytics || {};

    // Configuration
    const CONFIG = {
        API_BASE_URL: '',
        DEBOUNCE_DELAY: 300,
        ANIMATION_DURATION: 300,
        MAX_FILTER_SELECTIONS: 10
    };

    // Utility functions
    const Utils = {
        // Debounce function for search inputs
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Show loading state
        showLoading: function(element) {
            if (element) {
                element.classList.add('loading');
                element.style.pointerEvents = 'none';
            }
        },

        // Hide loading state
        hideLoading: function(element) {
            if (element) {
                element.classList.remove('loading');
                element.style.pointerEvents = 'auto';
            }
        },

        // Show toast notification
        showToast: function(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
            toast.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.body.appendChild(toast);

            // Auto remove after 5 seconds
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 5000);
        },

        // Format numbers with commas
        formatNumber: function(num) {
            return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        },

        // Animate counter
        animateCounter: function(element, target, duration = 1000) {
            const start = parseInt(element.textContent.replace(/,/g, '')) || 0;
            const increment = (target - start) / (duration / 16);
            let current = start;

            const timer = setInterval(() => {
                current += increment;
                if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
                    element.textContent = this.formatNumber(target);
                    clearInterval(timer);
                } else {
                    element.textContent = this.formatNumber(Math.floor(current));
                }
            }, 16);
        }
    };

    // Filter Management
    const FilterManager = {
        init: function() {
            this.setupDynamicFilters();
            this.setupSearchFilter();
            this.setupFilterPresets();
            this.setupFormValidation();
            this.restoreFilterState();
        },

        // Setup dynamic shop-based filtering
        setupDynamicFilters: function() {
            const shopSelect = document.getElementById('shop_ids');
            const vendorSelect = document.getElementById('vendors');
            const typeSelect = document.getElementById('product_types');

            if (shopSelect && vendorSelect && typeSelect) {
                shopSelect.addEventListener('change',
                    Utils.debounce(() => {
                        this.updateDependentFilters(shopSelect, vendorSelect, typeSelect);
                    }, CONFIG.DEBOUNCE_DELAY)
                );
            }
        },

        // Update vendors and types based on selected shops
        updateDependentFilters: function(shopSelect, vendorSelect, typeSelect) {
            const selectedShops = Array.from(shopSelect.selectedOptions).map(opt => opt.value);

            if (selectedShops.length === 0) return;

            Utils.showLoading(vendorSelect);
            Utils.showLoading(typeSelect);

            // Update vendors
            this.fetchFilterOptions('/api/vendors', selectedShops)
                .then(vendors => {
                    this.updateSelectOptions(vendorSelect, vendors);
                    Utils.hideLoading(vendorSelect);
                })
                .catch(error => {
                    console.error('Error fetching vendors:', error);
                    Utils.hideLoading(vendorSelect);
                    Utils.showToast('Failed to load vendors', 'danger');
                });

            // Update product types
            this.fetchFilterOptions('/api/product-types', selectedShops)
                .then(types => {
                    this.updateSelectOptions(typeSelect, types);
                    Utils.hideLoading(typeSelect);
                })
                .catch(error => {
                    console.error('Error fetching product types:', error);
                    Utils.hideLoading(typeSelect);
                    Utils.showToast('Failed to load product types', 'danger');
                });
        },

        // Fetch filter options from API
        fetchFilterOptions: function(endpoint, shopIds) {
            const params = new URLSearchParams();
            shopIds.forEach(id => params.append('shop_ids[]', id));

            return fetch(`${endpoint}?${params.toString()}`)
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                });
        },

        // Update select element options
        updateSelectOptions: function(selectElement, options) {
            const currentValues = Array.from(selectElement.selectedOptions).map(opt => opt.value);
            selectElement.innerHTML = '';

            options.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option;
                optionElement.textContent = option;
                if (currentValues.includes(option)) {
                    optionElement.selected = true;
                }
                selectElement.appendChild(optionElement);
            });
        },

        // Setup search with debouncing
        setupSearchFilter: function() {
            const searchInput = document.getElementById('search_term');
            if (searchInput) {
                const debouncedSearch = Utils.debounce((value) => {
                    this.performSearch(value);
                }, CONFIG.DEBOUNCE_DELAY);

                searchInput.addEventListener('input', (e) => {
                    debouncedSearch(e.target.value);
                });
            }
        },

        // Perform search (could trigger auto-submit or highlight)
        performSearch: function(term) {
            if (term.length > 2) {
                // Auto-search functionality
                const form = document.getElementById('filterForm');
                if (form && document.querySelector('[data-auto-search]')) {
                    form.submit();
                }
            }
        },

        // Setup filter presets
        setupFilterPresets: function() {
            const presetButtons = document.querySelectorAll('[data-filter-preset]');
            presetButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    const preset = button.dataset.filterPreset;
                    this.applyFilterPreset(preset);
                });
            });
        },

        // Apply predefined filter combinations
        applyFilterPreset: function(preset) {
            const presets = {
                'missing-data': {
                    missing_sku: true,
                    missing_barcode: true,
                    missing_images: true
                },
                'inventory-issues': {
                    zero_inventory: true,
                    available_for_sale_only: true
                },
                'seo-issues': {
                    missing_title_tag: true,
                    missing_description_tag: true
                },
                'recent-products': {
                    created_days_ago: 7
                }
            };

            const filters = presets[preset];
            if (filters) {
                Object.entries(filters).forEach(([key, value]) => {
                    const element = document.querySelector(`[name="${key}"]`);
                    if (element) {
                        if (element.type === 'checkbox') {
                            element.checked = value;
                        } else {
                            element.value = value;
                        }
                    }
                });

                // Submit form automatically
                const form = document.getElementById('filterForm');
                if (form) form.submit();
            }
        },

        // Form validation
        setupFormValidation: function() {
            const form = document.getElementById('filterForm');
            if (form) {
                form.addEventListener('submit', (e) => {
                    if (!this.validateForm(form)) {
                        e.preventDefault();
                        Utils.showToast('Please check your filter inputs', 'warning');
                    }
                });
            }
        },

        // Validate form inputs
        validateForm: function(form) {
            const numericInputs = form.querySelectorAll('input[type="number"]');
            let isValid = true;

            numericInputs.forEach(input => {
                const value = parseInt(input.value);
                if (input.value && (isNaN(value) || value < 0)) {
                    input.classList.add('is-invalid');
                    isValid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });

            return isValid;
        },

        // Save and restore filter state
        saveFilterState: function() {
            const form = document.getElementById('filterForm');
            if (form) {
                const formData = new FormData(form);
                const state = {};
                for (let [key, value] of formData.entries()) {
                    state[key] = value;
                }
                localStorage.setItem('shopify_analytics_filters', JSON.stringify(state));
            }
        },

        restoreFilterState: function() {
            try {
                const state = JSON.parse(localStorage.getItem('shopify_analytics_filters'));
                if (state) {
                    Object.entries(state).forEach(([key, value]) => {
                        const element = document.querySelector(`[name="${key}"]`);
                        if (element && !element.value) { // Don't override URL parameters
                            element.value = value;
                        }
                    });
                }
            } catch (error) {
                console.warn('Failed to restore filter state:', error);
            }
        }
    };

    // Product Management
    const ProductManager = {
        init: function() {
            this.setupProductDetails();
            this.setupBulkActions();
            this.setupExportFunctionality();
        },

        // Setup product details modal
        setupProductDetails: function() {
            const detailButtons = document.querySelectorAll('[data-product-id]');
            detailButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    const productId = button.dataset.productId;
                    this.showProductDetails(productId);
                });
            });
        },

        // Show product details in modal
        showProductDetails: function(productId) {
            const modal = document.getElementById('productDetailsModal');
            const content = document.getElementById('productDetailsContent');

            if (modal && content) {
                content.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';

                // Show modal
                const modalInstance = new bootstrap.Modal(modal);
                modalInstance.show();

                // Fetch product details
                fetch(`/api/product-details/${productId}`)
                    .then(response => {
                        if (!response.ok) throw new Error('Product not found');
                        return response.json();
                    })
                    .then(data => {
                        this.renderProductDetails(content, data);
                    })
                    .catch(error => {
                        content.innerHTML = `<div class="alert alert-danger">Error loading product details: ${error.message}</div>`;
                    });
            }
        },

        // Render product details HTML
        renderProductDetails: function(container, data) {
            const html = `
                <div class="row">
                    <div class="col-md-6">
                        <h6 class="border-bottom pb-2">Product Information</h6>
                        <table class="table table-sm">
                            <tr><td><strong>ID:</strong></td><td>${data.product_id}</td></tr>
                            <tr><td><strong>Title:</strong></td><td>${data.title}</td></tr>
                            <tr><td><strong>Handle:</strong></td><td>${data.handle}</td></tr>
                            <tr><td><strong>Vendor:</strong></td><td>${data.vendor || 'N/A'}</td></tr>
                            <tr><td><strong>Type:</strong></td><td>${data.type || 'N/A'}</td></tr>
                            <tr><td><strong>Status:</strong></td><td>
                                <span class="badge status-${data.status}">${data.status}</span>
                            </td></tr>
                            <tr><td><strong>Shop:</strong></td><td>${data.shop}</td></tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6 class="border-bottom pb-2">Variants (${data.variants.length})</h6>
                        <div style="max-height: 300px; overflow-y: auto;">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>SKU</th>
                                        <th>Inventory</th>
                                        <th>Available</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.variants.map(variant => `
                                        <tr>
                                            <td>${variant.variant_sku || '<em>No SKU</em>'}</td>
                                            <td>${variant.variant_inventory_quantity || 0}</td>
                                            <td>${variant.variant_available_for_sale ?
                                                '<span class="text-success">Yes</span>' :
                                                '<span class="text-danger">No</span>'}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
            container.innerHTML = html;
        },

        // Setup bulk actions
        setupBulkActions: function() {
            const selectAllCheckbox = document.getElementById('selectAll');
            const itemCheckboxes = document.querySelectorAll('.item-checkbox');
            const bulkActionButtons = document.querySelectorAll('.bulk-action');

            if (selectAllCheckbox) {
                selectAllCheckbox.addEventListener('change', (e) => {
                    itemCheckboxes.forEach(checkbox => {
                        checkbox.checked = e.target.checked;
                    });
                    this.updateBulkActionButtons();
                });
            }

            itemCheckboxes.forEach(checkbox => {
                checkbox.addEventListener('change', () => {
                    this.updateBulkActionButtons();
                });
            });
        },

        // Update bulk action button states
        updateBulkActionButtons: function() {
            const checkedItems = document.querySelectorAll('.item-checkbox:checked');
            const bulkActionButtons = document.querySelectorAll('.bulk-action');

            bulkActionButtons.forEach(button => {
                button.disabled = checkedItems.length === 0;
            });

            // Update count display
            const countDisplay = document.querySelector('.selected-count');
            if (countDisplay) {
                countDisplay.textContent = `${checkedItems.length} selected`;
            }
        },

        // Setup export functionality
        setupExportFunctionality: function() {
            const exportButtons = document.querySelectorAll('[data-export]');
            exportButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    const format = button.dataset.export;
                    this.exportData(format);
                });
            });
        },

        // Export data in specified format
        exportData: function(format) {
            const form = document.getElementById('filterForm');
            if (form) {
                // Save current action and target
                const originalAction = form.action;
                const originalTarget = form.target;

                // Set export parameters
                form.action = `/export${format === 'json' ? '-json' : ''}`;
                form.target = '_blank';

                // Submit form
                form.submit();

                // Restore original values
                setTimeout(() => {
                    form.action = originalAction;
                    form.target = originalTarget;
                }, 100);

                Utils.showToast(`Exporting data as ${format.toUpperCase()}...`, 'info');
            }
        }
    };

    // Analytics Dashboard
    const AnalyticsDashboard = {
        init: function() {
            this.setupCounterAnimations();
            this.setupCharts();
            this.setupRealTimeUpdates();
        },

        // Animate dashboard counters
        setupCounterAnimations: function() {
            const counters = document.querySelectorAll('[data-counter]');
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const counter = entry.target;
                        const target = parseInt(counter.dataset.counter.replace(/,/g, ''));
                        Utils.animateCounter(counter, target);
                        observer.unobserve(counter);
                    }
                });
            });

            counters.forEach(counter => observer.observe(counter));
        },

        // Setup charts (if Chart.js is available)
        setupCharts: function() {
            if (typeof Chart !== 'undefined') {
                this.createCompletionChart();
                this.createTrendChart();
            }
        },

        // Create metafield completion chart
        createCompletionChart: function() {
            const ctx = document.getElementById('completionChart');
            if (ctx && window.metafieldData) {
                const data = window.metafieldData;
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: Object.keys(data).map(key => key.replace('Metafield: ', '')),
                        datasets: [{
                            data: Object.values(data).map(item => item.percentage),
                            backgroundColor: [
                                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                                '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            }
        },

        // Create trend chart
        createTrendChart: function() {
            const ctx = document.getElementById('trendChart');
            if (ctx) {
                // Sample trend data - replace with real data
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                        datasets: [{
                            label: 'Data Completeness',
                            data: [65, 70, 75, 78, 82, 85],
                            borderColor: '#36A2EB',
                            backgroundColor: 'rgba(54, 162, 235, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100
                            }
                        }
                    }
                });
            }
        },

        // Setup real-time updates
        setupRealTimeUpdates: function() {
            // Placeholder for WebSocket or polling implementation
            setInterval(() => {
                this.updateDashboardStats();
            }, 300000); // Update every 5 minutes
        },

        // Update dashboard statistics
        updateDashboardStats: function() {
            // Implementation for real-time updates
            console.log('Updating dashboard stats...');
        }
    };

    // Initialize application
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize all modules
        FilterManager.init();
        ProductManager.init();
        AnalyticsDashboard.init();

        // Setup global event handlers
        setupGlobalHandlers();

        // Show welcome message on first visit
        if (!localStorage.getItem('shopify_analytics_visited')) {
            Utils.showToast('Welcome to Shopify Analytics Dashboard!', 'success');
            localStorage.setItem('shopify_analytics_visited', 'true');
        }

        console.log('Shopify Analytics Dashboard initialized');
    });

    // Global event handlers
    function setupGlobalHandlers() {
        // Handle form auto-save
        const forms = document.querySelectorAll('form[data-auto-save]');
        forms.forEach(form => {
            form.addEventListener('change', () => {
                FilterManager.saveFilterState();
            });
        });

        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search focus
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('search_term');
                if (searchInput) searchInput.focus();
            }

            // Ctrl/Cmd + E for export
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                ProductManager.exportData('csv');
            }
        });

        // Handle responsive table scrolling
        const tables = document.querySelectorAll('.table-responsive');
        tables.forEach(table => {
            table.addEventListener('scroll', function() {
                const scrollLeft = this.scrollLeft;
                const scrollWidth = this.scrollWidth - this.clientWidth;
                const scrollPercentage = scrollLeft / scrollWidth;

                // Add visual indicators for scrollable content
                this.style.setProperty('--scroll-percentage', scrollPercentage);
            });
        });

        // Handle theme toggle (if implemented)
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                document.body.classList.toggle('dark-theme');
                const isDark = document.body.classList.contains('dark-theme');
                localStorage.setItem('theme-preference', isDark ? 'dark' : 'light');
            });

            // Restore theme preference
            const savedTheme = localStorage.getItem('theme-preference');
            if (savedTheme === 'dark') {
                document.body.classList.add('dark-theme');
            }
        }
    }

    // Expose utilities to global scope
    window.ShopifyAnalytics.Utils = Utils;
    window.ShopifyAnalytics.FilterManager = FilterManager;
    window.ShopifyAnalytics.ProductManager = ProductManager;

})();