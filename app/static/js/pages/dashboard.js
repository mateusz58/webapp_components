// Dashboard Component JavaScript

function componentDashboard() {
    return {
        viewMode: localStorage.getItem('componentViewMode') || 'grid',
        searchQuery: '',
        selectedComponents: [],
        activeQuickFilter: 'all',

        // Multi-select filters
        filters: {
            componentTypes: [],
            suppliers: [],
            brands: []
        },

        // Multi-select dropdown states
        dropdownStates: {
            componentTypes: false,
            categories: false,
            suppliers: false,
            brands: false
        },

        // Search within dropdowns
        dropdownSearch: {
            componentTypes: '',
            categories: '',
            suppliers: '',
            brands: ''
        },

        componentsOnPage: window.componentsOnPage || [],

        init() {
            // Initialize searchQuery from template
            if (window.searchQuery) {
                this.searchQuery = window.searchQuery;
            }

            // Initialize filters from template
            if (window.currentFilters) {
                this.filters.componentTypes = window.currentFilters.component_type_ids || [];
                this.filters.suppliers = window.currentFilters.supplier_ids || [];
                this.filters.brands = window.currentFilters.brand_ids || [];
            }

            // Initialize activeQuickFilter from template
            if (window.activeQuickFilter) {
                this.activeQuickFilter = window.activeQuickFilter;
            }

            this.$watch('viewMode', (value) => {
                localStorage.setItem('componentViewMode', value);
                setTimeout(() => {
                    lucide.createIcons();
                    // Re-initialize variant preview and keyword expansion after view mode change
                    if (window.enableVariantImagePreview) {
                        window.enableVariantImagePreview();
                    }
                    if (window.enableKeywordExpansion) {
                        window.enableKeywordExpansion();
                    }
                }, 100);
            });

            // Close dropdowns when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.multi-select-wrapper')) {
                    this.closeAllDropdowns();
                }
            });

            // Initialize filters from URL parameters
            this.initializeFiltersFromUrl();
            
            // Initialize variant image preview and keyword expansion
            setTimeout(() => {
                if (window.enableVariantImagePreview) {
                    window.enableVariantImagePreview();
                }
                if (window.enableKeywordExpansion) {
                    window.enableKeywordExpansion();
                }
            }, 100);
        },

        initializeFiltersFromUrl() {
            // Convert string arrays to proper format if needed
            Object.keys(this.filters).forEach(key => {
                if (this.filters[key] && Array.isArray(this.filters[key])) {
                    this.filters[key] = this.filters[key].map(val => val.toString());
                }
            });
        },

        // Multi-select dropdown methods
        toggleMultiSelect(filterType) {
            // Close other dropdowns
            Object.keys(this.dropdownStates).forEach(key => {
                if (key !== filterType) {
                    this.dropdownStates[key] = false;
                }
            });
            // Toggle current dropdown
            this.dropdownStates[filterType] = !this.dropdownStates[filterType];
        },

        closeAllDropdowns() {
            Object.keys(this.dropdownStates).forEach(key => {
                this.dropdownStates[key] = false;
            });
        },

        selectOption(filterType, optionValue, optionText) {
            console.log(`selectOption called: ${filterType}, ${optionValue}, ${optionText}`);
            
            if (!this.filters[filterType]) {
                this.filters[filterType] = [];
            }

            const index = this.filters[filterType].indexOf(optionValue.toString());
            if (index > -1) {
                // Remove if already selected
                this.filters[filterType].splice(index, 1);
                console.log(`Removed ${optionValue} from ${filterType}`);
            } else {
                // Add if not selected
                this.filters[filterType].push(optionValue.toString());
                console.log(`Added ${optionValue} to ${filterType}`);
            }

            console.log(`Updated ${filterType} filters:`, this.filters[filterType]);
        },

        isOptionSelected(filterType, optionValue) {
            return this.filters[filterType] &&
                   this.filters[filterType].includes(optionValue.toString());
        },

        getSelectedText(filterType, maxShow = 1) {
            if (!this.filters[filterType] || this.filters[filterType].length === 0) {
                return '';
            }

            if (this.filters[filterType].length === 1) {
                return this.getOptionText(this.getSelectName(filterType), this.filters[filterType][0]);
            }

            return `${this.filters[filterType].length} selected`;
        },

        getSelectName(filterType) {
            const mapping = {
                'componentTypes': 'component_type_id',
                'categories': 'category_id',
                'suppliers': 'supplier_id',
                'brands': 'brand_id'
            };
            return mapping[filterType];
        },

        getOptionText(selectName, optionValue) {
            // This function needs to be defined in the template since it uses Jinja2 variables
            if (window.getOptionTextMapping && window.getOptionTextMapping[selectName]) {
                const mapping = window.getOptionTextMapping[selectName];
                return mapping[optionValue] || optionValue;
            }
            return optionValue;
        },

        removeFilter(filterType, index) {
            if (this.filters[filterType] && this.filters[filterType][index] !== undefined) {
                this.filters[filterType].splice(index, 1);
                this.performSearch();
            }
        },

        clearAllFilters() {
            this.filters = {
                componentTypes: [],
                categories: [],
                suppliers: [],
                brands: []
            };
            this.searchQuery = '';
            this.performSearch();
        },

        hasActiveFilters() {
            return Object.values(this.filters).some(filter => filter && filter.length > 0) ||
                   this.searchQuery.length > 0;
        },

        selectAllOptions(filterType) {
            console.log(`selectAllOptions called for ${filterType}`);
            
            // Get all available values from window object
            if (window.filterOptions && window.filterOptions[filterType]) {
                this.filters[filterType] = [...window.filterOptions[filterType]];
                console.log(`Set all values for ${filterType}:`, this.filters[filterType]);
            }
        },

        deselectAllOptions(filterType) {
            console.log(`deselectAllOptions called for ${filterType}`);
            this.filters[filterType] = [];
            console.log(`${filterType} after deselect all:`, this.filters[filterType]);
        },

        filterDropdownOptions(filterType, options) {
            const searchTerm = this.dropdownSearch[filterType].toLowerCase();
            if (!searchTerm) return options;

            return options.filter(option =>
                option.text.toLowerCase().includes(searchTerm)
            );
        },

        performSearch() {
            // Update the actual form inputs
            this.updateFormInputs();

            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.$refs.filterForm.submit();
            }, 300);
        },

        async handleFormSubmit(event) {
            console.log('Form submission started');
            console.log('Current filters:', this.filters);
            
            // Wait for Alpine.js to update the DOM
            await this.$nextTick();
            
            // Additional wait to ensure DOM is updated
            await new Promise(resolve => setTimeout(resolve, 50));
            
            // Log the actual form data that will be sent
            const formData = new FormData(event.target);
            console.log('Form data being submitted:');
            for (let [key, value] of formData.entries()) {
                console.log(`${key}: ${value}`);
            }
            
            // Now submit the form
            event.target.submit();
        },

        updateFormInputs() {
            // This method is now mainly for debugging
            console.log('updateFormInputs called');
            console.log('Component types:', this.filters.componentTypes);
            console.log('Suppliers:', this.filters.suppliers);
            console.log('Brands:', this.filters.brands);
        },

        quickFilter(type) {
            this.activeQuickFilter = type;
            const url = new URL(window.location);

            // Remove pagination when filtering
            url.searchParams.delete('page');
            url.searchParams.delete('show_all');

            switch(type) {
                case 'approved':
                    url.searchParams.set('status', 'approved');
                    break;
                case 'pending':
                    url.searchParams.set('status', 'pending');
                    break;
                case 'recent':
                    url.searchParams.set('recent', '7');
                    url.searchParams.delete('status');
                    break;
                default:
                    url.searchParams.delete('status');
                    url.searchParams.delete('recent');
            }

            window.location.href = url.toString();
        },

        toggleSelection(componentId) {
            const index = this.selectedComponents.indexOf(componentId);
            if (index > -1) {
                this.selectedComponents.splice(index, 1);
            } else {
                this.selectedComponents.push(componentId);
            }
        },

        toggleSelectAll(event) {
            if (event.target.checked) {
                this.selectedComponents = Array.from(new Set([...this.selectedComponents, ...this.componentsOnPage]));
            } else {
                this.selectedComponents = this.selectedComponents.filter(id => !this.componentsOnPage.includes(id));
            }
        },

        clearSelection() {
            this.selectedComponents = [];
        },

        bulkAction(action) {
            if (this.selectedComponents.length === 0) return;

            switch(action) {
                case 'export':
                    const exportUrl = `/api/components/export?ids=${this.selectedComponents.join(',')}`;
                    window.open(exportUrl, '_blank');
                    break;
                case 'delete':
                    if (confirm(`Delete ${this.selectedComponents.length} component(s)?`)) {
                        fetch('/api/components/bulk-delete', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': document.querySelector('[name=csrf_token]')?.value
                            },
                            body: JSON.stringify({ ids: this.selectedComponents })
                        }).then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                window.location.reload();
                            } else {
                                alert('Error: ' + data.error);
                            }
                        }).catch(error => {
                            alert('Error deleting components: ' + error);
                        });
                    }
                    break;
            }
        },

        navigateToComponent(componentId) {
            window.location.href = `/component/${componentId}`;
        }
    }
}

// Utility functions
function changePerPage(value) {
    const url = new URL(window.location);
    url.searchParams.set('per_page', value);
    url.searchParams.delete('page');
    url.searchParams.delete('show_all');
    window.location.href = url.toString();
}

function confirmShowAll(count) {
    if (count > 500) {
        return confirm(`This will show all ${count} components on one page, which may slow down your browser. Continue?`);
    }
    return true;
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons();

    // Auto-hide flash messages after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert-modern');
        alerts.forEach(alert => {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) closeBtn.click();
        });
    }, 5000);
});