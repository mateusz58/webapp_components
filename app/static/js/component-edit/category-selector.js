/**
 * Enhanced Category Selector Module
 * Handles multi-select category functionality with search and keyboard navigation
 */

class CategorySelector {
    constructor() {
        this.allCategoryOptions = [];
        this.selectedCategoryIds = new Set();
        this.isDropdownOpen = false;
        this.searchDebounceTimer = null;
        this.focusedCategoryIndex = -1;
        
        // DOM elements
        this.categorySearch = null;
        this.categoryDropdown = null;
        this.categoryShowAllBtn = null;
        this.categoryClearSearch = null;
        this.selectedCategories = null;
        
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }
    
    setup() {
        // Get DOM elements
        this.categorySearch = document.getElementById('categorySearch');
        this.categoryDropdown = document.getElementById('categoryDropdown');
        this.categoryShowAllBtn = document.getElementById('categoryShowAllBtn');
        this.categoryClearSearch = document.getElementById('categoryClearSearch');
        this.selectedCategories = document.getElementById('selectedCategories');
        
        if (!this.categorySearch || !this.categoryDropdown) {
            console.log('Category selector elements not found');
            return;
        }
        
        // Cache all category options
        this.allCategoryOptions = Array.from(this.categoryDropdown.querySelectorAll('.category-option'));
        
        // Initialize selected categories from existing hidden inputs or selected category elements
        this.initializeSelectedCategories();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Update initial display
        this.updateSelectedCategoriesDisplay();
        this.updateCategoryOptionsDisplay();
        
        console.log('Category selector initialized with', this.allCategoryOptions.length, 'categories');
    }
    
    initializeSelectedCategories() {
        // Get selected categories from existing hidden inputs
        const hiddenInputs = document.querySelectorAll('input[name="category_ids"]');
        hiddenInputs.forEach(input => {
            if (input.value) {
                this.selectedCategoryIds.add(parseInt(input.value));
            }
        });
        
        // Also check for existing selected category elements (for edit mode)
        const selectedCategoryElements = document.querySelectorAll('.selected-category[data-id]');
        selectedCategoryElements.forEach(element => {
            const categoryId = parseInt(element.dataset.id);
            if (categoryId) {
                this.selectedCategoryIds.add(categoryId);
            }
        });
        
        console.log('Initialized with selected categories:', Array.from(this.selectedCategoryIds));
    }
    
    setupEventListeners() {
        // Search input events
        this.categorySearch.addEventListener('input', (e) => {
            clearTimeout(this.searchDebounceTimer);
            this.searchDebounceTimer = setTimeout(() => {
                this.performCategorySearch(e.target.value.toLowerCase().trim());
            }, 150);
        });
        
        this.categorySearch.addEventListener('keydown', (e) => {
            this.handleCategoryKeyNavigation(e);
        });
        
        this.categorySearch.addEventListener('focus', () => {
            this.showCategoryDropdown();
        });
        
        // Show all button
        if (this.categoryShowAllBtn) {
            this.categoryShowAllBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.categorySearch.value = '';
                this.performCategorySearch('');
                this.showCategoryDropdown();
                this.categorySearch.focus();
            });
        }
        
        // Clear search button
        if (this.categoryClearSearch) {
            this.categoryClearSearch.addEventListener('click', () => {
                this.categorySearch.value = '';
                this.performCategorySearch('');
            });
        }
        
        // Category option clicks
        this.allCategoryOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const categoryId = parseInt(option.dataset.id);
                const categoryName = option.dataset.name;
                
                if (this.selectedCategoryIds.has(categoryId)) {
                    // Don't allow deselecting by clicking again - user must use remove button
                    console.log('Category already selected:', categoryName);
                    return;
                } else {
                    this.addCategorySelection(categoryId, categoryName);
                }
                
                this.updateSelectedCategoriesDisplay();
                this.updateCategoryOptionsDisplay();
                this.categorySearch.value = '';
                this.categorySearch.focus();
            });
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.categorySearch.contains(e.target) && 
                !this.categoryDropdown.contains(e.target) && 
                !this.categoryShowAllBtn.contains(e.target)) {
                this.hideCategoryDropdown();
            }
        });
    }
    
    performCategorySearch(query) {
        let visibleCount = 0;
        let hasExactMatch = false;
        let exactMatchIsSelected = false;
        
        this.allCategoryOptions.forEach(option => {
            const categoryName = option.dataset.name.toLowerCase();
            const isSelected = this.selectedCategoryIds.has(parseInt(option.dataset.id));
            let isVisible = false;
            
            if (query === '') {
                // Show all when no search query
                isVisible = true;
                option.style.order = isSelected ? '1' : '2';
            } else {
                // Smart matching: exact > starts with > contains
                if (categoryName === query) {
                    hasExactMatch = true;
                    exactMatchIsSelected = isSelected;
                    isVisible = true;
                    option.style.order = '1'; // Prioritize exact matches
                } else if (categoryName.startsWith(query)) {
                    isVisible = true;
                    option.style.order = '2'; // Prioritize starts with
                } else if (categoryName.includes(query)) {
                    isVisible = true;
                    option.style.order = '3'; // Then includes
                }
            }
            
            // Apply visibility and selection styling
            option.style.display = isVisible ? 'flex' : 'none';
            option.classList.toggle('selected', isSelected);
            
            if (isVisible) {
                visibleCount++;
                
                // Highlight matching text
                const nameElement = option.querySelector('.category-name');
                if (nameElement && query) {
                    const originalName = option.dataset.name;
                    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
                    nameElement.innerHTML = originalName.replace(regex, '<mark>$1</mark>');
                } else if (nameElement) {
                    nameElement.textContent = option.dataset.name;
                }
            }
        });
        
        // Handle "Create new category" option
        this.handleNewCategoryOption(query, hasExactMatch, exactMatchIsSelected, visibleCount);
        
        // Update dropdown header
        const categoryCount = document.querySelector('.category-count');
        if (categoryCount) {
            const totalShown = visibleCount + (this.shouldShowNewCategoryOption(query, hasExactMatch, exactMatchIsSelected) ? 1 : 0);
            if (query) {
                categoryCount.textContent = `${visibleCount} existing categories match "${query}"`;
            } else {
                categoryCount.textContent = `${this.allCategoryOptions.length} categories available`;
            }
        }
        
        // Show/hide clear search button
        if (this.categoryClearSearch) {
            this.categoryClearSearch.style.display = query ? 'block' : 'none';
        }
        
        // Show duplicate warning or no results message
        this.updateStatusMessages(query, hasExactMatch, exactMatchIsSelected, visibleCount);
        
        // Reset focused index
        this.focusedCategoryIndex = -1;
        this.updateCategoryFocus();
    }
    
    handleCategoryKeyNavigation(e) {
        const visibleOptions = this.allCategoryOptions.filter(option => option.style.display !== 'none');
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.focusedCategoryIndex = Math.min(this.focusedCategoryIndex + 1, visibleOptions.length - 1);
                this.updateCategoryFocus();
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                this.focusedCategoryIndex = Math.max(this.focusedCategoryIndex - 1, -1);
                this.updateCategoryFocus();
                break;
                
            case 'Enter':
                e.preventDefault();
                if (this.focusedCategoryIndex >= 0 && visibleOptions[this.focusedCategoryIndex]) {
                    visibleOptions[this.focusedCategoryIndex].click();
                }
                break;
                
            case 'Escape':
                e.preventDefault();
                this.hideCategoryDropdown();
                this.categorySearch.blur();
                break;
        }
    }
    
    updateCategoryFocus() {
        // Remove focus from all options
        this.allCategoryOptions.forEach(option => option.classList.remove('focused'));
        
        // Add focus to current option
        const visibleOptions = this.allCategoryOptions.filter(option => option.style.display !== 'none');
        if (this.focusedCategoryIndex >= 0 && visibleOptions[this.focusedCategoryIndex]) {
            visibleOptions[this.focusedCategoryIndex].classList.add('focused');
            visibleOptions[this.focusedCategoryIndex].scrollIntoView({ block: 'nearest' });
        }
    }
    
    shouldShowNewCategoryOption(query, hasExactMatch, exactMatchIsSelected) {
        return query && query.trim().length >= 2 && (!hasExactMatch || exactMatchIsSelected);
    }
    
    handleNewCategoryOption(query, hasExactMatch, exactMatchIsSelected, visibleCount) {
        // Remove existing new category option
        const existingNewOption = this.categoryDropdown.querySelector('.category-option-new');
        if (existingNewOption) {
            existingNewOption.remove();
        }
        
        if (this.shouldShowNewCategoryOption(query, hasExactMatch, exactMatchIsSelected)) {
            const newCategoryOption = this.createNewCategoryOption(query.trim());
            this.categoryDropdown.appendChild(newCategoryOption);
        }
    }
    
    createNewCategoryOption(categoryName) {
        const option = document.createElement('div');
        option.className = 'category-option category-option-new';
        option.dataset.action = 'create';
        option.dataset.name = categoryName;
        option.style.order = '999'; // Show at bottom
        
        option.innerHTML = `
            <div class="category-option-content">
                <span class="category-name">
                    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16" style="margin-right: 6px; color: var(--success-color);">
                        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                        <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
                    </svg>
                    Create "${categoryName}"
                </span>
                <span class="category-usage new-category-badge">New category</span>
            </div>
        `;
        
        // Add click handler
        option.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.createNewCategory(categoryName);
        });
        
        return option;
    }
    
    updateStatusMessages(query, hasExactMatch, exactMatchIsSelected, visibleCount) {
        // Handle duplicate warning
        const duplicateWarning = this.categoryDropdown.querySelector('.category-duplicate-warning') || this.createDuplicateWarning();
        
        if (hasExactMatch && exactMatchIsSelected) {
            duplicateWarning.style.display = 'block';
            duplicateWarning.innerHTML = `
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
                </svg>
                <div>
                    <strong>"${query}" is already selected</strong>
                    <small>This category is already added to your component</small>
                </div>
            `;
        } else {
            duplicateWarning.style.display = 'none';
        }
        
        // Handle no results message
        const noResults = this.categoryDropdown.querySelector('.category-no-results') || document.getElementById('categoryNoResults');
        if (noResults) {
            const shouldShowNoResults = visibleCount === 0 && query && !this.shouldShowNewCategoryOption(query, hasExactMatch, exactMatchIsSelected);
            noResults.style.display = shouldShowNoResults ? 'block' : 'none';
        }
    }
    
    createDuplicateWarning() {
        const warning = document.createElement('div');
        warning.className = 'category-duplicate-warning';
        warning.style.display = 'none';
        this.categoryDropdown.appendChild(warning);
        return warning;
    }
    
    async createNewCategory(categoryName) {
        try {
            // Show loading state
            this.categorySearch.disabled = true;
            this.categorySearch.value = `Creating "${categoryName}"...`;
            
            const response = await fetch('/api/categories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: categoryName })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Add the new category to our options
                const newOption = this.createCategoryOptionElement(data.category.id, data.category.name, 0);
                this.categoryDropdown.insertBefore(newOption, this.categoryDropdown.querySelector('.category-option-new'));
                this.allCategoryOptions.push(newOption);
                
                // Select the new category
                this.addCategorySelection(data.category.id, data.category.name);
                this.updateSelectedCategoriesDisplay();
                this.updateCategoryOptionsDisplay();
                
                // Clear search and show success
                this.categorySearch.value = '';
                this.categorySearch.disabled = false;
                this.categorySearch.placeholder = `"${categoryName}" created and added!`;
                
                // Reset placeholder after 3 seconds
                setTimeout(() => {
                    this.categorySearch.placeholder = 'Type to search categories or click arrow to browse all...';
                }, 3000);
                
                this.categorySearch.focus();
                this.performCategorySearch('');
                
            } else {
                throw new Error(data.error || 'Failed to create category');
            }
            
        } catch (error) {
            console.error('Error creating category:', error);
            this.categorySearch.disabled = false;
            this.categorySearch.value = '';
            this.categorySearch.placeholder = `Error: ${error.message}`;
            
            // Reset placeholder after 5 seconds
            setTimeout(() => {
                this.categorySearch.placeholder = 'Type to search categories or click arrow to browse all...';
            }, 5000);
        }
    }
    
    createCategoryOptionElement(id, name, componentCount = 0) {
        const option = document.createElement('div');
        option.className = 'category-option';
        option.dataset.id = id;
        option.dataset.name = name;
        
        option.innerHTML = `
            <span class="category-name">${name}</span>
            <span class="category-usage">${componentCount} components</span>
        `;
        
        // Add click handler
        option.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const categoryId = parseInt(option.dataset.id);
            const categoryName = option.dataset.name;
            
            if (this.selectedCategoryIds.has(categoryId)) {
                console.log('Category already selected:', categoryName);
                return;
            } else {
                this.addCategorySelection(categoryId, categoryName);
            }
            
            this.updateSelectedCategoriesDisplay();
            this.updateCategoryOptionsDisplay();
            this.categorySearch.value = '';
            this.categorySearch.focus();
        });
        
        return option;
    }
    
    addCategorySelection(categoryId, categoryName) {
        if (this.selectedCategoryIds.has(categoryId)) {
            console.log('Category already selected:', categoryName);
            return false;
        }
        
        this.selectedCategoryIds.add(categoryId);
        console.log('Added category:', categoryName);
        
        // Trigger form change event if updateSubmitButtonState exists
        if (typeof updateSubmitButtonState === 'function') {
            updateSubmitButtonState();
        }
        
        return true;
    }
    
    removeCategorySelection(categoryId) {
        this.selectedCategoryIds.delete(categoryId);
        console.log('Removed category:', categoryId);
        
        // Trigger form change event if updateSubmitButtonState exists
        if (typeof updateSubmitButtonState === 'function') {
            updateSubmitButtonState();
        }
    }
    
    updateSelectedCategoriesDisplay() {
        if (!this.selectedCategories) return;
        
        // Clear existing display
        this.selectedCategories.innerHTML = '';
        
        // Create tags for selected categories
        this.selectedCategoryIds.forEach(categoryId => {
            const option = this.allCategoryOptions.find(opt => parseInt(opt.dataset.id) === categoryId);
            if (option) {
                const categoryName = option.dataset.name;
                const tag = this.createCategoryTag(categoryId, categoryName);
                this.selectedCategories.appendChild(tag);
            }
        });
        
        // Update hidden inputs
        this.updateCategoriesHiddenInput();
        
        // Show/hide placeholder
        if (this.selectedCategoryIds.size === 0) {
            const placeholderDiv = document.createElement('div');
            placeholderDiv.className = 'categories-placeholder';
            placeholderDiv.textContent = 'No categories selected';
            this.selectedCategories.appendChild(placeholderDiv);
        }
    }
    
    createCategoryTag(categoryId, categoryName) {
        const tag = document.createElement('span');
        tag.className = 'category-tag';
        tag.innerHTML = `
            <span class="category-tag-name">${categoryName}</span>
            <button type="button" class="category-tag-remove" data-category-id="${categoryId}">
                <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                </svg>
            </button>
        `;
        
        // Add event listener for remove button
        const removeBtn = tag.querySelector('.category-tag-remove');
        removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.removeCategoryTag(categoryId);
        });
        
        return tag;
    }
    
    updateCategoryOptionsDisplay() {
        this.allCategoryOptions.forEach(option => {
            const categoryId = parseInt(option.dataset.id);
            const isSelected = this.selectedCategoryIds.has(categoryId);
            option.classList.toggle('selected', isSelected);
            
            // Add visual indicator for selected categories
            if (isSelected) {
                option.style.backgroundColor = 'var(--primary-color, #3b82f6)';
                option.style.color = 'white';
            } else {
                option.style.backgroundColor = '';
                option.style.color = '';
            }
        });
    }
    
    updateCategoriesHiddenInput() {
        // Remove existing hidden inputs
        const existingInputs = document.querySelectorAll('input[name="category_ids"]');
        existingInputs.forEach(input => input.remove());
        
        // Add new hidden inputs for selected categories
        const form = document.getElementById('componentForm');
        if (form) {
            this.selectedCategoryIds.forEach(categoryId => {
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'category_ids';
                hiddenInput.value = categoryId;
                form.appendChild(hiddenInput);
            });
        }
    }
    
    showCategoryDropdown() {
        if (this.categoryDropdown) {
            this.categoryDropdown.style.display = 'block';
            this.isDropdownOpen = true;
            
            // Trigger CSS animation
            setTimeout(() => {
                this.categoryDropdown.style.opacity = '1';
                this.categoryDropdown.style.transform = 'translateY(0)';
            }, 10);
        }
    }
    
    hideCategoryDropdown() {
        if (this.categoryDropdown) {
            this.categoryDropdown.style.opacity = '0';
            this.categoryDropdown.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                this.categoryDropdown.style.display = 'none';
                this.isDropdownOpen = false;
            }, 200);
        }
    }
    
    // Public method for removing category tags
    removeCategoryTag(categoryId) {
        this.removeCategorySelection(categoryId);
        this.updateSelectedCategoriesDisplay();
        this.updateCategoryOptionsDisplay();
    }
}

// Initialize category selector
let categorySelector = null;

// Global function for backward compatibility
window.removeCategoryTag = function(categoryId) {
    if (categorySelector) {
        categorySelector.removeCategoryTag(categoryId);
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        categorySelector = new CategorySelector();
    });
} else {
    categorySelector = new CategorySelector();
}