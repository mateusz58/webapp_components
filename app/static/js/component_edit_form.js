document.addEventListener('DOMContentLoaded', function() {
    // Component Type Properties Data (simplified approach)
    const componentTypeProperties = {
        {% for ct in component_types %}
        '{{ ct.id }}': {
            name: '{{ ct.name }}',
            properties: [
                // We'll load these dynamically via AJAX to avoid JSON serialization issues
            ]
        }{% if not loop.last %},{% endif %}
        {% endfor %}
    };

    // Form Elements
    const form = document.getElementById('componentForm');
    const productNumberInput = document.getElementById('product_number');
    const componentTypeSelect = document.getElementById('component_type_id');
    const supplierSelect = document.getElementById('supplier_id');
    const categorySearch = document.getElementById('categorySearch');
    const categoryDropdown = document.getElementById('categoryDropdown');
    const selectedCategories = document.getElementById('selectedCategories');
    const categoryShowAllBtn = document.getElementById('categoryShowAllBtn');
    const categoryClearSearch = document.getElementById('categoryClearSearch');
    const categoryNoResults = document.getElementById('categoryNoResults');
    const descriptionTextarea = document.getElementById('description');
    const brandSelect = document.getElementById('brand_id');
    const subbrandSelect = document.getElementById('subbrand_id');
    const subbrandGroup = document.getElementById('subbrand_group');
    const newBrandInput = document.getElementById('new_brand_input');
    const newSubbrandInput = document.getElementById('new_subbrand_input');
    const keywordInput = document.getElementById('keyword_input');
    const keywordTags = document.getElementById('keyword_tags');
    const keywordsHiddenInput = document.getElementById('keywords_input');
    const keywordDropdown = document.getElementById('keyword-dropdown');
    const propertiesContainer = document.getElementById('properties_container');
    const noPropertiesMsg = document.getElementById('no_properties');
    const submitBtn = document.getElementById('submit_btn');
    const saveStatus = document.getElementById('save_status');
    const validationSummary = document.getElementById('validationSummary');
    const validationList = document.getElementById('validationList');

    // State
    let selectedKeywords = new Set();
    let validationErrors = {};
    
    // Keyword Autocomplete State
    let keywordSuggestions = [];
    let selectedSuggestionIndex = -1;
    let isDropdownVisible = false;
    let searchTimeout = null;

    // Initialize
    init();

    function init() {
        // Debug: Check if elements exist
        console.log('Keyword input:', keywordInput);
        console.log('Keyword dropdown:', keywordDropdown);
        
        // Initialize existing keywords
        document.querySelectorAll('#keyword_tags .tag').forEach(tag => {
            selectedKeywords.add(tag.dataset.keyword);
        });

        // Initialize preview image with primary picture if editing existing component
        {% if component and component.pictures %}
            {% set primary_picture = component.pictures|selectattr('is_primary', 'eq', true)|first %}
            {% if primary_picture %}
                const previewImage = document.getElementById('preview_image');
                previewImage.innerHTML = '<img src="{{ primary_picture.url }}" style="width: 100%; height: 100%; object-fit: cover;">';
            {% endif %}
        {% endif %}

        // Highlight changed fields if any
        {% if changed_fields %}
            highlightChangedFields();
        {% endif %}

        // Set up event listeners
        setupEventListeners();
    }

    function highlightChangedFields() {
        const changedFields = {{ changed_fields|tojson }};
        
        changedFields.forEach(fieldName => {
            let element = null;
            
            // Map field names to element IDs
            switch(fieldName) {
                case 'product_number':
                    element = document.getElementById('product_number');
                    break;
                case 'description':
                    element = document.getElementById('description');
                    break;
                case 'component_type_id':
                    element = document.getElementById('component_type_id');
                    break;
                case 'supplier_id':
                    element = document.getElementById('supplier_id');
                    break;
                case 'category_id':
                case 'category_ids':
                case 'categories':
                    element = document.getElementById('categorySelector');
                    break;
                case 'keywords':
                    element = document.getElementById('keyword_tags');
                    break;
                case 'brands':
                    element = document.getElementById('brand_id');
                    break;
                case 'properties':
                    element = document.getElementById('properties_container');
                    break;
                case 'images':
                    element = document.getElementById('image_preview_grid');
                    break;
            }
            
            if (element) {
                element.classList.add('field-changed');
                // Remove the highlight class after animation completes
                setTimeout(() => {
                    element.classList.remove('field-changed');
                }, 2000);
            }
        });
    }

    function setupEventListeners() {
        // Form validation
        productNumberInput.addEventListener('input', () => {
            validateField('product_number');
            updatePreview();
        });
        
        componentTypeSelect.addEventListener('change', () => {
            validateField('component_type_id');
            loadComponentTypeProperties(componentTypeSelect.value);
            updatePreview();
        });
        
        supplierSelect.addEventListener('change', () => {
            validateField('supplier_id');
            updatePreview();
        });
        
        setupCategorySelector();

        descriptionTextarea.addEventListener('input', () => {
            updateCharacterCount();
            updatePreview();
        });

        // Brand selection
        brandSelect.addEventListener('change', handleBrandSelection);
        brandSelect.addEventListener('change', () => validateField('brand_id'));
        
        // Subbrand validation
        if (document.getElementById('new_subbrand_name')) {
            document.getElementById('new_subbrand_name').addEventListener('input', validateSubbrandName);
        }

        // Keyword management with autocomplete
        if (keywordInput) {
            console.log('Setting up keyword autocomplete event listeners');
            keywordInput.addEventListener('input', handleKeywordInputChange);
            keywordInput.addEventListener('keydown', handleKeywordInputKeydown);
            keywordInput.addEventListener('focus', handleKeywordInputFocus);
            keywordInput.addEventListener('blur', handleKeywordInputBlur);
        } else {
            console.error('Keyword input element not found!');
        }
        
        if (keywordTags) {
            keywordTags.addEventListener('click', handleKeywordRemove);
        }
        
        // Dropdown event listeners
        if (keywordDropdown) {
            console.log('Setting up dropdown click listener');
            keywordDropdown.addEventListener('click', handleDropdownClick);
        } else {
            console.error('Keyword dropdown element not found!');
        }

        // Form submission
        form.addEventListener('submit', handleSubmit);

        // Auto-save (for edit mode)
        {% if component %}
        let autoSaveTimeout;
        form.addEventListener('input', () => {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                saveStatus.textContent = 'Changes saved automatically';
                setTimeout(() => {
                    saveStatus.textContent = '';
                }, 2000);
            }, 1000);
        });
        {% endif %}
    }

    function validateField(fieldName) {
        const field = document.getElementById(fieldName);
        const errorElement = document.getElementById(fieldName + '_error');
        let isValid = true;
        let errorMessage = '';

        // Clear previous error
        field.classList.remove('error');
        errorElement.classList.add('hidden');
        delete validationErrors[fieldName];

        // Validate based on field
        switch(fieldName) {
            case 'product_number':
                if (!field.value.trim()) {
                    errorMessage = 'Product number is required';
                    isValid = false;
                } else if (field.value.trim().length < 3) {
                    errorMessage = 'Product number must be at least 3 characters';
                    isValid = false;
                }
                break;
            case 'component_type_id':
                if (!field.value) {
                    errorMessage = 'Component type is required';
                    isValid = false;
                }
                break;
            case 'supplier_id':
                // Supplier is now optional - no validation needed
                break;
            case 'category_id':
                // Category is now optional - no validation needed
                break;
            case 'brand_id':
                if (!field.value) {
                    errorMessage = 'Brand is required';
                    isValid = false;
                }
                break;
        }

        if (!isValid) {
            field.classList.add('error');
            errorElement.textContent = errorMessage;
            errorElement.classList.remove('hidden');
            validationErrors[fieldName] = errorMessage;
        }

        updateValidationSummary();
        return isValid;
    }

    function updateValidationSummary() {
        const errorCount = Object.keys(validationErrors).length;
        
        if (errorCount > 0) {
            validationList.innerHTML = '';
            Object.values(validationErrors).forEach(error => {
                const li = document.createElement('li');
                li.textContent = error;
                validationList.appendChild(li);
            });
            validationSummary.classList.remove('hidden');
        } else {
            validationSummary.classList.add('hidden');
        }
    }

    function loadComponentTypeProperties(componentTypeId) {
        if (!componentTypeId) {
            propertiesContainer.innerHTML = '<div id="no_properties" class="text-center" style="grid-column: 1 / -1; padding: 2rem; color: var(--gray-500);"><p>Select a component type to see available properties</p></div>';
            return;
        }

        // Show loading
        propertiesContainer.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 2rem;"><div class="spinner" style="margin: 0 auto;"></div></div>';

        // Load properties via AJAX to avoid JSON serialization issues
        fetch(`/api/component-type/${componentTypeId}/properties`)
            .then(response => response.json())
            .then(properties => {
                renderProperties(properties);
            })
            .catch(() => {
                // Fallback to hardcoded properties if API fails
                renderProperties([]);
            });
    }

    function renderProperties(properties) {
        if (properties.length === 0) {
            propertiesContainer.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--gray-500);"><p>No specific properties for this component type</p></div>';
            return;
        }

        propertiesContainer.innerHTML = '';
        propertiesContainer.style.gridTemplateColumns = 'repeat(auto-fit, minmax(280px, 1fr))';

        properties.forEach(property => {
            const propertyDiv = createPropertyField(property);
            propertiesContainer.appendChild(propertyDiv);
        });
    }

    function createPropertyField(property) {
        const div = document.createElement('div');
        div.className = 'form-group';

        const label = document.createElement('label');
        label.className = 'form-label' + (property.is_required ? ' required' : '');
        label.textContent = property.display_name || property.property_name;
        label.setAttribute('for', property.property_name);

        const currentValue = getCurrentPropertyValue(property.property_name);

        let input;
        if (property.property_type === 'select') {
            input = document.createElement('select');
            input.className = 'form-select';
            
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = `Select ${property.property_name}...`;
            input.appendChild(defaultOption);

            (property.options || []).forEach(option => {
                const optionEl = document.createElement('option');
                optionEl.value = option;
                optionEl.textContent = option;
                if (currentValue === option) optionEl.selected = true;
                input.appendChild(optionEl);
            });
        } else if (property.property_type === 'multiselect') {
            input = document.createElement('select');
            input.className = 'form-select';
            input.multiple = true;
            input.style.minHeight = '100px';

            (property.options || []).forEach(option => {
                const optionEl = document.createElement('option');
                optionEl.value = option;
                optionEl.textContent = option;
                if (Array.isArray(currentValue) && currentValue.includes(option)) {
                    optionEl.selected = true;
                }
                input.appendChild(optionEl);
            });
        } else {
            input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-input';
            input.placeholder = property.placeholder || `Enter ${property.property_name}`;
            input.value = currentValue || '';
        }

        input.id = property.property_name;
        input.name = property.property_name;

        div.appendChild(label);
        div.appendChild(input);

        if (property.placeholder && property.property_type === 'text') {
            const help = document.createElement('div');
            help.className = 'form-help';
            help.textContent = property.placeholder;
            div.appendChild(help);
        }

        return div;
    }

    function getCurrentPropertyValue(propertyName) {
        {% if component and component.properties %}
        const properties = {{ component.properties | tojson | safe }};
        if (properties[propertyName]) {
            return typeof properties[propertyName] === 'object' ? properties[propertyName].value : properties[propertyName];
        }
        {% endif %}
        return '';
    }

    function handleBrandSelection() {
        const brandSelect = document.getElementById('brand_id');
        const subbrandGroup = document.getElementById('subbrand_group');
        const subbrandSelect = document.getElementById('subbrand_id');
        const newBrandInput = document.getElementById('new_brand_input');
        const newSubbrandInput = document.getElementById('new_subbrand_input');
        
        if (brandSelect.value === 'new') {
            // Show new brand input
            newBrandInput.style.display = 'block';
            document.getElementById('new_brand_name').setAttribute('required', 'required');
            
            // Hide subbrand section when creating new brand
            subbrandGroup.style.display = 'none';
            newSubbrandInput.style.display = 'none';
            document.getElementById('new_subbrand_name').removeAttribute('required');
        } else if (brandSelect.value) {
            // Hide new brand input
            newBrandInput.style.display = 'none';
            document.getElementById('new_brand_name').removeAttribute('required');
            
            // Show subbrand section and load subbrands for selected brand
            subbrandGroup.style.display = 'block';
            loadSubbrands(brandSelect.value);
            
            // Hide new subbrand input by default
            newSubbrandInput.style.display = 'none';
            document.getElementById('new_subbrand_name').removeAttribute('required');
        } else {
            // Hide both brand and subbrand inputs
            newBrandInput.style.display = 'none';
            subbrandGroup.style.display = 'none';
            newSubbrandInput.style.display = 'none';
            document.getElementById('new_brand_name').removeAttribute('required');
            document.getElementById('new_subbrand_name').removeAttribute('required');
        }
        
        // Update submit button state
        updateSubmitButtonState();
    }
    
    function handleSubbrandSelection() {
        const subbrandSelect = document.getElementById('subbrand_id');
        const newSubbrandInput = document.getElementById('new_subbrand_input');
        
        if (subbrandSelect.value === 'new') {
            // Show new subbrand input
            newSubbrandInput.style.display = 'block';
            document.getElementById('new_subbrand_name').setAttribute('required', 'required');
        } else {
            // Hide new subbrand input
            newSubbrandInput.style.display = 'none';
            document.getElementById('new_subbrand_name').removeAttribute('required');
        }
        
        // Update submit button state
        updateSubmitButtonState();
    }
    
    function loadSubbrands(brandId) {
        const subbrandSelect = document.getElementById('subbrand_id');
        
        // Clear existing options except default and "new" option
        subbrandSelect.innerHTML = '<option value="">Select a subbrand...</option><option value="new">+ Create New Subbrand</option>';
        
        // Load subbrands via AJAX
        fetch(`/api/brand/${brandId}/subbrands`)
            .then(response => response.json())
            .then(subbrands => {
                // Insert subbrands before the "new" option
                const newOption = subbrandSelect.querySelector('option[value="new"]');
                
                subbrands.forEach(subbrand => {
                    const option = document.createElement('option');
                    option.value = subbrand.id;
                    option.textContent = subbrand.name;
                    subbrandSelect.insertBefore(option, newOption);
                });
            })
            .catch(error => {
                console.error('Error loading subbrands:', error);
            });
    }
    
    function validateSubbrandName() {
        const brandSelect = document.getElementById('brand_id');
        const newSubbrandName = document.getElementById('new_subbrand_name').value.trim();
        const errorElement = document.getElementById('subbrand_error');
        
        if (!newSubbrandName) {
            return true; // Empty is fine, will be caught by required validation
        }
        
        // Check if subbrand name already exists for this brand
        if (brandSelect.value && brandSelect.value !== 'new') {
            fetch(`/api/brand/${brandSelect.value}/subbrands/check`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: newSubbrandName })
            })
            .then(response => response.json())
            .then(data => {
                if (data.exists) {
                    errorElement.textContent = 'A subbrand with this name already exists for this brand';
                    errorElement.classList.remove('hidden');
                    return false;
                } else {
                    errorElement.classList.add('hidden');
                    return true;
                }
            })
            .catch(error => {
                console.error('Error validating subbrand name:', error);
            });
        }
        
        return true;
    }

    // Enhanced Keyword Autocomplete Functions
    
    function handleKeywordInputChange(e) {
        const value = e.target.value.trim();
        console.log('Keyword input changed:', value);
        
        // Clear existing timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        // Debounce search requests
        if (value.length > 0) {
            console.log('Setting timeout to search for:', value);
            searchTimeout = setTimeout(() => {
                searchKeywords(value);
            }, 300);
        } else {
            hideDropdown();
        }
    }
    
    function handleKeywordInputKeydown(e) {
        const value = e.target.value.trim();
        
        switch(e.key) {
            case 'Enter':
                e.preventDefault();
                if (selectedSuggestionIndex >= 0 && keywordSuggestions[selectedSuggestionIndex]) {
                    selectSuggestion(keywordSuggestions[selectedSuggestionIndex]);
                } else if (value) {
                    addKeyword(value);
                }
                break;
                
            case ',':
            case 'Tab':
                e.preventDefault();
                if (value) {
                    addKeyword(value);
                }
                break;
                
            case 'ArrowDown':
                e.preventDefault();
                if (isDropdownVisible) {
                    selectedSuggestionIndex = Math.min(selectedSuggestionIndex + 1, keywordSuggestions.length - 1);
                    updateDropdownHighlight();
                }
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                if (isDropdownVisible) {
                    selectedSuggestionIndex = Math.max(selectedSuggestionIndex - 1, -1);
                    updateDropdownHighlight();
                }
                break;
                
            case 'Escape':
                hideDropdown();
                break;
        }
    }
    
    function handleKeywordInputFocus() {
        const value = keywordInput.value.trim();
        if (value.length > 0) {
            searchKeywords(value);
        } else {
            // Show popular keywords when focused with empty input
            searchKeywords('');
        }
    }
    
    function handleKeywordInputBlur(e) {
        // Delay hiding dropdown to allow for clicks on suggestions
        setTimeout(() => {
            hideDropdown();
        }, 150);
    }
    
    function handleDropdownClick(e) {
        const suggestionItem = e.target.closest('.keyword-suggestion-item');
        const createNewItem = e.target.closest('.keyword-create-new');
        
        if (suggestionItem) {
            const keywordName = suggestionItem.dataset.keyword;
            const suggestion = keywordSuggestions.find(s => s.name === keywordName);
            if (suggestion) {
                selectSuggestion(suggestion);
            }
        } else if (createNewItem) {
            const keywordName = createNewItem.dataset.keyword;
            if (keywordName) {
                addKeyword(keywordName);
                keywordInput.value = '';
                hideDropdown();
                keywordInput.focus();
            }
        }
    }
    
    async function searchKeywords(query) {
        console.log('Searching keywords for:', query);
        try {
            showLoadingInDropdown();
            
            const url = `/api/keyword/search?q=${encodeURIComponent(query)}&limit=8`;
            console.log('Fetching from URL:', url);
            
            const response = await fetch(url);
            console.log('Response status:', response.status);
            
            const data = await response.json();
            console.log('Search results:', data);
            
            if (data.keywords) {
                // Filter out already selected keywords (case insensitive)
                keywordSuggestions = data.keywords.filter(k => !selectedKeywords.has(k.name.toLowerCase()));
                console.log('Filtered suggestions:', keywordSuggestions);
                renderDropdown();
            }
        } catch (error) {
            console.error('Error searching keywords:', error);
            hideDropdown();
        }
    }
    
    function showLoadingInDropdown() {
        if (!keywordDropdown) return;
        
        keywordDropdown.innerHTML = `
            <div class="keyword-loading">
                <div class="spinner"></div>
                <span>Searching keywords...</span>
            </div>
        `;
        showDropdown();
    }
    
    function renderDropdown() {
        if (!keywordDropdown) return;
        
        if (keywordSuggestions.length === 0) {
            const query = keywordInput.value.trim();
            if (query) {
                keywordDropdown.innerHTML = `
                    <div class="keyword-no-results">No existing keywords found</div>
                    <div class="keyword-create-new" data-keyword="${escapeHtml(query)}">
                        <strong>Create new:</strong> "${escapeHtml(query)}"
                    </div>
                `;
            } else {
                keywordDropdown.innerHTML = '<div class="keyword-no-results">Start typing to search keywords</div>';
            }
        } else {
            let html = '';
            keywordSuggestions.forEach((suggestion, index) => {
                const highlightedName = highlightMatch(suggestion.name, keywordInput.value.trim());
                const matchTypeText = getMatchTypeText(suggestion.match_type);
                
                html += `
                    <div class="keyword-suggestion-item ${index === selectedSuggestionIndex ? 'highlighted' : ''}" 
                         data-keyword="${escapeHtml(suggestion.name)}" 
                         data-index="${index}">
                        <div class="keyword-suggestion-content">
                            <div class="keyword-suggestion-name">${highlightedName}</div>
                            <div class="keyword-suggestion-type">${matchTypeText}</div>
                        </div>
                        <div class="keyword-usage-count">${suggestion.usage_count || 0}</div>
                    </div>
                `;
            });
            
            // Add create new option if query doesn't exactly match any suggestion
            const query = keywordInput.value.trim();
            if (query && !keywordSuggestions.some(s => s.name.toLowerCase() === query.toLowerCase())) {
                html += `
                    <div class="keyword-create-new" data-keyword="${escapeHtml(query)}">
                        <strong>Create new:</strong> "${escapeHtml(query)}"
                    </div>
                `;
            }
            
            keywordDropdown.innerHTML = html;
        }
        
        showDropdown();
    }
    
    function selectSuggestion(suggestion) {
        // Always use lowercase for consistency with database storage
        addKeyword(suggestion.name.toLowerCase());
        keywordInput.value = '';
        hideDropdown();
        keywordInput.focus();
    }
    
    function addKeyword(keywordText) {
        const keyword = keywordText.trim().toLowerCase();
        if (keyword && !selectedKeywords.has(keyword)) {
            selectedKeywords.add(keyword);
            
            // Always display and store keywords in lowercase
            const tag = createTag(keyword, keyword, 'keyword');
            keywordTags.appendChild(tag);
            
            keywordInput.value = '';
            updateKeywordsInput();
            hideDropdown();
        }
    }
    
    function showDropdown() {
        if (!keywordDropdown) return;
        
        keywordDropdown.classList.add('show');
        keywordDropdown.style.display = 'block';
        keywordInput.classList.add('keyword-input-with-autocomplete', 'has-suggestions');
        keywordInput.setAttribute('aria-expanded', 'true');
        keywordDropdown.setAttribute('aria-hidden', 'false');
        isDropdownVisible = true;
    }
    
    function hideDropdown() {
        if (!keywordDropdown) return;
        
        keywordDropdown.classList.remove('show');
        keywordDropdown.style.display = 'none';
        keywordInput.classList.remove('has-suggestions');
        keywordInput.setAttribute('aria-expanded', 'false');
        keywordDropdown.setAttribute('aria-hidden', 'true');
        isDropdownVisible = false;
        selectedSuggestionIndex = -1;
    }
    
    function updateDropdownHighlight() {
        if (!keywordDropdown) return;
        
        const items = keywordDropdown.querySelectorAll('.keyword-suggestion-item');
        items.forEach((item, index) => {
            if (index === selectedSuggestionIndex) {
                item.classList.add('highlighted');
            } else {
                item.classList.remove('highlighted');
            }
        });
    }
    
    function highlightMatch(text, query) {
        if (!query.trim()) return escapeHtml(text);
        
        const escapedText = escapeHtml(text);
        const escapedQuery = escapeHtml(query);
        const regex = new RegExp(`(${escapedQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        
        return escapedText.replace(regex, '<span class="keyword-match-highlight">$1</span>');
    }
    
    function getMatchTypeText(matchType) {
        switch(matchType) {
            case 'exact': return 'Exact match';
            case 'starts_with': return 'Starts with';
            case 'fuzzy': return 'Similar';
            case 'popular': return 'Popular';
            default: return 'Match';
        }
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function handleKeywordRemove(e) {
        if (e.target.closest('.tag-remove')) {
            const tag = e.target.closest('.tag');
            const keyword = tag.dataset.keyword;
            selectedKeywords.delete(keyword);
            tag.remove();
            updateKeywordsInput();
        }
    }

    function createTag(text, value, type) {
        const tag = document.createElement('div');
        tag.className = 'tag';
        tag.dataset[type] = value;
        
        const span = document.createElement('span');
        span.textContent = text;
        
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'tag-remove';
        removeBtn.setAttribute('aria-label', `Remove ${text}`);
        removeBtn.innerHTML = '<svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/></svg>';
        
        tag.appendChild(span);
        tag.appendChild(removeBtn);
        
        return tag;
    }

    function updateKeywordsInput() {
        keywordsHiddenInput.value = Array.from(selectedKeywords).join(',');
    }

    function updateCharacterCount() {
        const charCount = document.getElementById('char_count');
        charCount.textContent = descriptionTextarea.value.length;
    }

    // Enhanced Category Selector Functionality
    function setupCategorySelector() {
        if (!categorySearch || !categoryDropdown || !selectedCategories) {
            console.warn('Category selector elements not found');
            return;
        }

        let selectedCategoryIds = new Set();
        let allCategoryOptions = Array.from(categoryDropdown.querySelectorAll('.category-option'));
        let isDropdownOpen = false;
        let searchTimeout = null;
        
        // Initialize with existing categories
        selectedCategories.querySelectorAll('.selected-category').forEach(cat => {
            selectedCategoryIds.add(cat.dataset.id);
        });

        // Enhanced search input handler with debouncing
        categorySearch.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            
            // Clear previous timeout
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
            
            // Debounce search to improve performance
            searchTimeout = setTimeout(() => {
                performSearch(query);
            }, 150);
        });

        function performSearch(query) {
            let visibleCount = 0;
            let hasExactMatch = false;

            allCategoryOptions.forEach(option => {
                const categoryName = option.dataset.name.toLowerCase();
                const isSelected = selectedCategoryIds.has(option.dataset.id);
                
                if (isSelected) {
                    option.style.display = 'none';
                    return;
                }

                let isVisible = false;
                if (query.length === 0) {
                    // Show all unselected categories when no search query
                    isVisible = true;
                } else {
                    // Enhanced matching: exact match, starts with, or contains
                    if (categoryName === query) {
                        hasExactMatch = true;
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

                option.style.display = isVisible ? 'flex' : 'none';
                if (isVisible) visibleCount++;

                // Highlight matching text
                const nameSpan = option.querySelector('.category-name');
                if (nameSpan) {
                    const originalName = option.dataset.name;
                    if (query.length > 0 && isVisible) {
                        const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
                        nameSpan.innerHTML = originalName.replace(regex, '<mark>$1</mark>');
                    } else {
                        nameSpan.textContent = originalName;
                    }
                }
            });

            // Show/hide dropdown and update UI
            if (query.length > 0 || isDropdownOpen) {
                categoryDropdown.style.display = 'block';
                categoryShowAllBtn.classList.add('active');
                isDropdownOpen = true;
                
                // Show/hide clear search button
                if (categoryClearSearch) {
                    categoryClearSearch.style.display = query.length > 0 ? 'block' : 'none';
                }
            } else {
                categoryDropdown.style.display = 'none';
                categoryShowAllBtn.classList.remove('active');
                isDropdownOpen = false;
            }

            // Show/hide no results message
            if (categoryNoResults) {
                categoryNoResults.style.display = (query.length > 0 && visibleCount === 0) ? 'block' : 'none';
            }

            // Auto-complete for exact matches
            if (hasExactMatch && query.length > 2) {
                // Could implement auto-completion here if needed
            }
        }

        // Show all categories button
        if (categoryShowAllBtn) {
            categoryShowAllBtn.addEventListener('click', function() {
                if (isDropdownOpen) {
                    hideDropdown();
                } else {
                    showAllCategories();
                }
            });
        }

        function showAllCategories() {
            categorySearch.value = '';
            performSearch('');
            categorySearch.focus();
            isDropdownOpen = true;
        }

        function hideDropdown() {
            categoryDropdown.style.display = 'none';
            categoryShowAllBtn.classList.remove('active');
            isDropdownOpen = false;
            categorySearch.value = '';
            if (categoryClearSearch) {
                categoryClearSearch.style.display = 'none';
            }
        }

        // Clear search button
        if (categoryClearSearch) {
            categoryClearSearch.addEventListener('click', function() {
                categorySearch.value = '';
                performSearch('');
                categorySearch.focus();
            });
        }

        // Focus handler
        categorySearch.addEventListener('focus', function() {
            if (!isDropdownOpen) {
                showAllCategories();
            }
        });

        // Click outside to close
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.category-input-container')) {
                hideDropdown();
            }
        });

        // Keyboard navigation
        categorySearch.addEventListener('keydown', function(e) {
            const visibleOptions = Array.from(categoryDropdown.querySelectorAll('.category-option:not([style*="display: none"])'));
            let currentIndex = visibleOptions.findIndex(opt => opt.classList.contains('highlighted'));

            switch(e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    if (currentIndex < visibleOptions.length - 1) {
                        if (currentIndex >= 0) visibleOptions[currentIndex].classList.remove('highlighted');
                        visibleOptions[currentIndex + 1].classList.add('highlighted');
                    }
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    if (currentIndex > 0) {
                        visibleOptions[currentIndex].classList.remove('highlighted');
                        visibleOptions[currentIndex - 1].classList.add('highlighted');
                    }
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (currentIndex >= 0) {
                        const option = visibleOptions[currentIndex];
                        if (!selectedCategoryIds.has(option.dataset.id)) {
                            selectCategory(option);
                        }
                    }
                    break;
                case 'Escape':
                    hideDropdown();
                    break;
            }
        });

        // Option click handler
        categoryDropdown.addEventListener('click', function(e) {
            const option = e.target.closest('.category-option');
            if (option && !selectedCategoryIds.has(option.dataset.id)) {
                selectCategory(option);
            }
        });

        // Option hover handler for keyboard navigation
        categoryDropdown.addEventListener('mouseover', function(e) {
            const option = e.target.closest('.category-option');
            if (option) {
                // Remove highlight from all options
                categoryDropdown.querySelectorAll('.category-option').forEach(opt => {
                    opt.classList.remove('highlighted');
                });
                option.classList.add('highlighted');
            }
        });

        function selectCategory(option) {
            addCategory(option.dataset.id, option.dataset.name);
            selectedCategoryIds.add(option.dataset.id);
            categorySearch.value = '';
            performSearch('');
            categorySearch.focus();
        }

        function addCategory(id, name) {
            const categorySpan = document.createElement('span');
            categorySpan.className = 'selected-category';
            categorySpan.dataset.id = id;
            categorySpan.innerHTML = `
                ${name}
                <button type="button" class="remove-category" onclick="removeCategory(${id})">×</button>
                <input type="hidden" name="category_ids" value="${id}">
            `;
            selectedCategories.appendChild(categorySpan);
            selectedCategories.style.display = 'flex';
        }

        // Make removeCategory global
        window.removeCategory = function(categoryId) {
            const categorySpan = selectedCategories.querySelector(`[data-id="${categoryId}"]`);
            if (categorySpan) {
                categorySpan.remove();
                selectedCategoryIds.delete(categoryId.toString());
                
                if (selectedCategories.children.length === 0) {
                    selectedCategories.style.display = 'none';
                }
                
                // Refresh search results to show the unselected category
                performSearch(categorySearch.value.toLowerCase().trim());
            }
        };

        // Utility function to escape regex special characters
        function escapeRegex(string) {
            return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        }

        // Initialize
        updateCategoryVisibility();
        
        function updateCategoryVisibility() {
            performSearch('');
        }
    }

    function handleDragOver(e) {
        e.preventDefault();
        imageUploadZone.classList.add('dragover');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        imageUploadZone.classList.remove('dragover');
    }

    function handleDrop(e) {
        e.preventDefault();
        imageUploadZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        processImages(files);
    }

    function handleImageSelect(e) {
        const files = e.target.files;
        processImages(files);
    }

    function processImages(files) {
        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const imageObj = {
                        id: Date.now() + Math.random(),
                        file: file,
                        name: file.name,
                        url: e.target.result
                    };
                    uploadedImages.push(imageObj);
                    renderImagePreview(imageObj);
                };
                reader.readAsDataURL(file);
            }
        });
    }

    function renderImagePreview(imageObj) {
        const div = document.createElement('div');
        div.className = 'image-preview-item';
        div.dataset.imageId = imageObj.id;
        
        div.innerHTML = `
            <img src="${imageObj.url}" alt="${imageObj.name}" class="image-preview-img">
            <div class="image-preview-actions">
                <button type="button" class="image-action-btn" onclick="removeImage('${imageObj.id}')" title="Remove image">
                    <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                    </svg>
                </button>
            </div>
        `;
        
        imagePreviewGrid.appendChild(div);
        updatePreviewImage();
    }

    function removeImage(imageId) {
        uploadedImages = uploadedImages.filter(img => img.id != imageId);
        const previewItem = document.querySelector(`[data-image-id="${imageId}"]`);
        if (previewItem) previewItem.remove();
        updatePreviewImage();
    }

    function removeExistingImage(btn) {
        const item = btn.closest('.image-preview-item');
        item.style.opacity = '0.5';
        const hiddenInput = item.querySelector('input[name="existing_pictures"]');
        if (hiddenInput) {
            hiddenInput.name = 'remove_pictures';
        }
    }

    function updatePreview() {
        const previewTitle = document.getElementById('preview_title');
        const previewDescription = document.getElementById('preview_description');
        const previewMeta = document.getElementById('preview_meta');
        
        previewTitle.textContent = productNumberInput.value || 'Component Preview';
        previewDescription.textContent = descriptionTextarea.value || 'Description will appear here...';
        
        // Update meta badges
        const metaBadges = [];
        if (componentTypeSelect.value) {
            metaBadges.push(componentTypeSelect.options[componentTypeSelect.selectedIndex].text);
        }
        if (supplierSelect.value) {
            metaBadges.push(supplierSelect.options[supplierSelect.selectedIndex].text);
        }
        if (categorySelect.value) {
            metaBadges.push(categorySelect.options[categorySelect.selectedIndex].text);
        }
        
        previewMeta.innerHTML = metaBadges.map(badge => 
            `<span class="preview-badge">${badge}</span>`
        ).join('');
    }

    function updatePreviewImage() {
        const previewImage = document.getElementById('preview_image');
        if (uploadedImages.length > 0) {
            previewImage.innerHTML = `<img src="${uploadedImages[0].url}" style="width: 100%; height: 100%; object-fit: cover;">`;
        }
    }

    function handleSubmit(e) {
        // Validate required fields
        const isValid = ['product_number', 'component_type_id', 'supplier_id', 'category_id'].every(validateField);
        
        if (!isValid) {
            e.preventDefault();
            document.querySelector('.validation-summary').scrollIntoView({ behavior: 'smooth' });
            return;
        }

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<div class="spinner"></div> Saving...';
    }

    // Variant Management Functions
    let variantCount = {{ component.variants|length if component and component.variants else 0 }};
    
    function getAvailableColorOptions() {
        // Get all colors that are already taken by existing variants
        const takenColors = new Set();
        const existingVariants = document.querySelectorAll('[data-variant-id]');
        
        existingVariants.forEach(variant => {
            const colorSelect = variant.querySelector('[name*="variant_color_"]');
            if (colorSelect && colorSelect.value && colorSelect.value !== 'custom') {
                takenColors.add(colorSelect.value);
            }
        });
        
        // Build options HTML
        let optionsHtml = '<option value="">Select a color...</option>';
        
        {% for color in colors %}
        const isTaken{{ color.id }} = takenColors.has('{{ color.id }}');
        if (isTaken{{ color.id }}) {
            optionsHtml += '<option value="{{ color.id }}" disabled style="color: #999; background-color: #f5f5f5;">{{ color.name }} (Already used)</option>';
        } else {
            optionsHtml += '<option value="{{ color.id }}">{{ color.name }}</option>';
        }
        {% endfor %}
        
        optionsHtml += '<option value="custom">+ Add New Color</option>';
        
        return optionsHtml;
    }

    function addNewVariant() {
        const emptyState = document.getElementById('empty_variants');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
        
        variantCount++;
        const variantId = `new_${variantCount}`;
        const container = document.getElementById('variants_container');
        
        const variantCard = document.createElement('div');
        variantCard.className = 'variant-card';
        variantCard.dataset.variantId = variantId;
        
        variantCard.innerHTML = `
            <div class="variant-header">
                <h4 class="variant-title">New Variant - No SKU</h4>
                <div class="variant-actions">
                    <button type="button" class="btn-icon btn-icon-outline" onclick="toggleVariantPictures('${variantId}')" title="Manage Pictures">
                        <svg style="width: 16px; height: 16px;" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M6.002 5.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z"/>
                            <path d="M2.002 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2h-12zm12 1a1 1 0 0 1 1 1v6.5l-3.777-1.947a.5.5 0 0 0-.577.093l-3.71 3.71-2.66-1.772a.5.5 0 0 0-.63.062L1.002 12V3a1 1 0 0 1 1-1h12z"/>
                        </svg>
                    </button>
                    <button type="button" class="btn-icon btn-icon-danger" onclick="removeVariant('${variantId}')" title="Remove Variant">×</button>
                </div>
            </div>
            
            <div class="variant-form">
                <div class="form-grid form-grid-cols-2">
                    <div class="form-group">
                        <label class="form-label required">Color</label>
                        <select name="new_variant_color_${variantId}" id="color_select_${variantId}" class="form-select" required onchange="handleColorSelection('${variantId}')">
                            ${getAvailableColorOptions()}
                        </select>
                        <div id="custom_color_input_${variantId}" style="display: none;" class="mt-2">
                            <input type="text" 
                                   name="new_variant_custom_color_${variantId}" 
                                   id="custom_color_${variantId}"
                                   class="form-input" 
                                   placeholder="Enter new color name..."
                                   onchange="updateVariantSKU('${variantId}')">
                            <small class="form-help">This will create a new color in the system</small>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Variant SKU</label>
                        <input 
                            type="text" 
                            name="new_variant_sku_${variantId}" 
                            id="variant_sku_${variantId}"
                            class="form-input"
                            readonly
                            style="background: var(--gray-50);"
                            placeholder="Auto-generated">
                    </div>
                </div>
                
                <!-- Picture Miniatures with Actions -->
                <div class="form-group">
                    <div class="pictures-section-header">
                        <label class="form-label">Pictures (0)</label>
                        <button type="button" class="btn btn-outline btn-sm" onclick="addVariantPicture('${variantId}')">
                            <svg style="width: 14px; height: 14px;" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
                            </svg>
                            Add Picture
                        </button>
                    </div>
                    <div class="form-help" style="margin-bottom: 0.5rem; color: var(--gray-600); font-size: 0.75rem;">
                        <strong>Note:</strong> At least one picture is required for each variant
                    </div>
                    <div class="picture-miniatures" id="miniatures_display_${variantId}">
                        <div class="no-pictures" onclick="addVariantPicture('${variantId}')">
                            <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M6.002 5.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z"/>
                                <path d="M2.002 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2h-12zm12 1a1 1 0 0 1 1 1v6.5l-3.777-1.947a.5.5 0 0 0-.577.093l-3.71 3.71-2.66-1.772a.5.5 0 0 0-.63.062L1.002 12V3a1 1 0 0 1 1-1h12z"/>
                            </svg>
                            <span>Click to add pictures</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="variant-pictures" id="variant_pictures_${variantId}" style="display: none;">
                <div class="pictures-header">
                    <h5>Pictures for New Variant</h5>
                    <button type="button" class="btn btn-outline btn-sm" onclick="addVariantPicture('${variantId}')">
                        Add Picture
                    </button>
                </div>
                
                <div class="image-upload-area" id="upload_area_${variantId}">
                    <input type="file" id="variant_images_${variantId}" multiple accept="image/*" style="display: none;" onchange="handleVariantImages('${variantId}', this.files)">
                    <div class="upload-drop-zone" onclick="document.getElementById('variant_images_${variantId}').click()">
                        <svg class="upload-icon" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M8.5 11.5a.5.5 0 0 1-1 0V7.707L6.354 8.854a.5.5 0 1 1-.708-.708l2-2a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1-.708.708L8.5 7.707V11.5z"/>
                            <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"/>
                        </svg>
                        <p>Drop images or click to upload</p>
                    </div>
                </div>
                
                <div class="variant-pictures-grid" id="pictures_grid_${variantId}"></div>
            </div>
        `;
        
        container.appendChild(variantCard);
        
        // Update submit button state after adding new variant
        updateSubmitButtonState();
    }
    
    function removeVariant(variantId) {
        // Check if this is a new variant (not yet saved to database)
        const isNewVariant = variantId.toString().startsWith('new_');
        
        // Only ask for confirmation for existing variants
        const shouldConfirm = !isNewVariant;
        const confirmMessage = shouldConfirm ? 'Are you sure you want to remove this variant and all its pictures?' : null;
        
        if (!shouldConfirm || confirm(confirmMessage)) {
            const card = document.querySelector(`[data-variant-id="${variantId}"]`);
            if (card) {
                card.remove();
                
                // Show empty state if no variants left
                const container = document.getElementById('variants_container');
                if (container.children.length === 0) {
                    const emptyState = document.getElementById('empty_variants');
                    if (emptyState) {
                        emptyState.style.display = 'block';
                    }
                }
                
                // Update submit button state after removing variant
                updateSubmitButtonState();
            }
        }
    }
    
    function toggleVariantPictures(variantId) {
        const picturesSection = document.getElementById(`variant_pictures_${variantId}`);
        if (picturesSection) {
            const isVisible = picturesSection.style.display !== 'none';
            picturesSection.style.display = isVisible ? 'none' : 'block';
        }
    }
    
    function updateVariantSKU(variantId) {
        var colorSelect = document.querySelector('[name*="variant_color_' + variantId + '"]');
        var skuInput = document.getElementById('variant_sku_' + variantId);
        var titleElement = document.querySelector('[data-variant-id="' + variantId + '"] .variant-title');
        var productNumber = document.getElementById('product_number').value;
        var supplierSelect = document.getElementById('supplier_id');
        var skuHelp = document.getElementById('sku_help_' + variantId);
        var skuPreview = document.getElementById('sku_preview_' + variantId);
        
        if (colorSelect && skuInput && productNumber) {
            var colorName = '';
            var supplierCode = supplierSelect ? supplierSelect.options[supplierSelect.selectedIndex].text : '';
            
            // Handle custom color or selected color
            if (colorSelect.value === 'custom') {
                var customColorInput = document.getElementById('custom_color_' + variantId);
                colorName = customColorInput ? customColorInput.value : 'custom';
            } else if (colorSelect.value) {
                var selectedOption = colorSelect.options[colorSelect.selectedIndex];
                colorName = selectedOption.text;
            }
            
            if (colorName) {
                // Generate preview SKU matching database format
                var normalizedProductNumber = productNumber.toLowerCase().replace(/\s+/g, '_');
                var normalizedColorName = colorName.toLowerCase().replace(/\s+/g, '_');
                var previewSku = supplierCode ? 
                    supplierCode.toLowerCase() + '_' + normalizedProductNumber + '_' + normalizedColorName :
                    normalizedProductNumber + '_' + normalizedColorName;
                
                // Store original SKU if not already stored
                if (!skuInput.dataset.originalSku) {
                    skuInput.dataset.originalSku = skuInput.value;
                }
                
                // Always show preview for new variants or when color changes
                skuInput.value = previewSku;
                skuInput.style.color = 'var(--warning-color)';
                if (skuHelp) skuHelp.style.display = 'none';
                if (skuPreview) skuPreview.style.display = 'inline';
                
                // Update title
                if (titleElement) {
                    titleElement.textContent = colorName + ' - ' + previewSku;
                }
                
                // Store current color selection for comparison
                skuInput.dataset.originalColorId = colorSelect.value;
            }
        }
    }
    
    function handleColorSelection(variantId) {
        const colorSelect = document.getElementById(`color_select_${variantId}`);
        const customInput = document.getElementById(`custom_color_input_${variantId}`);
        
        if (colorSelect.value === 'custom') {
            // Show custom color input
            customInput.style.display = 'block';
            colorSelect.removeAttribute('required');
            document.getElementById(`custom_color_${variantId}`).setAttribute('required', 'required');
        } else {
            // Hide custom color input
            customInput.style.display = 'none';
            colorSelect.setAttribute('required', 'required');
            document.getElementById(`custom_color_${variantId}`).removeAttribute('required');
            
            // Check for duplicate color selection
            if (colorSelect.value && isDuplicateColor(variantId, colorSelect.value)) {
                alert('This color is already used by another variant of this component. Please select a different color.');
                colorSelect.value = '';
                return;
            }
        }
        
        // Update SKU preview
        updateVariantSKU(variantId);
        
        // Update submit button state
        updateSubmitButtonState();
    }
    
    function isDuplicateColor(currentVariantId, colorId) {
        // Check existing variants for duplicate colors
        const existingVariants = document.querySelectorAll('[data-variant-id]');
        
        for (let variant of existingVariants) {
            const variantId = variant.dataset.variantId;
            if (variantId === currentVariantId) continue; // Skip current variant
            
            const colorSelect = variant.querySelector('[name*="variant_color_"]');
            if (colorSelect && colorSelect.value === colorId) {
                return true;
            }
        }
        
        return false;
    }
    
    function validateVariantBeforeSubmit(variantId) {
        // Check if variant has at least one picture
        const picturesGrid = document.getElementById(`pictures_grid_${variantId}`);
        const pictures = picturesGrid ? picturesGrid.querySelectorAll('.picture-item') : [];
        
        if (pictures.length === 0) {
            alert('Each variant must have at least one picture. Please add a picture before saving.');
            return false;
        }
        
        // Check color selection
        const colorSelect = document.getElementById(`color_select_${variantId}`);
        const customColorInput = document.getElementById(`custom_color_${variantId}`);
        
        if (colorSelect.value === 'custom') {
            if (!customColorInput.value.trim()) {
                alert('Please enter a name for the new color.');
                customColorInput.focus();
                return false;
            }
            
            // Check if custom color name already exists
            if (isColorNameExists(customColorInput.value.trim())) {
                alert('A color with this name already exists. Please choose a different name.');
                customColorInput.focus();
                return false;
            }
        } else if (!colorSelect.value) {
            alert('Please select a color for this variant.');
            colorSelect.focus();
            return false;
        }
        
        return true;
    }
    
    function isColorNameExists(colorName) {
        // Check against existing colors in the dropdown
        const colorSelects = document.querySelectorAll('[name*="variant_color_"]');
        if (colorSelects.length > 0) {
            const options = colorSelects[0].querySelectorAll('option');
            for (let option of options) {
                if (option.textContent.toLowerCase().trim() === colorName.toLowerCase().trim() && option.value !== 'custom') {
                    return true;
                }
            }
        }
        return false;
    }
    
    function handleVariantImages(variantId, files) {
        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    addVariantPictureToGrid(variantId, {
                        id: Date.now() + Math.random(),
                        file: file,
                        name: file.name,
                        url: e.target.result,
                        isNew: true
                    });
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    function addVariantPictureToGrid(variantId, picture) {
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        if (!grid) return;
        
        // Calculate the next order number
        const existingPictures = grid.querySelectorAll('.picture-item[data-picture-id]:not([data-picture-id^="new_"])');
        const newPictures = grid.querySelectorAll('.picture-item[data-picture-id^="new_"]');
        const nextOrder = existingPictures.length + newPictures.length + 1;
        
        // Generate proper filename convention
        const productNumber = document.getElementById('product_number').value;
        const supplierSelect = document.getElementById('supplier_id');
        const colorSelect = document.querySelector(`[name*="variant_color_${variantId}"]`);
        
        let filename = '';
        if (productNumber && colorSelect && colorSelect.value) {
            const supplierCode = supplierSelect ? supplierSelect.options[supplierSelect.selectedIndex].text : '';
            const colorName = colorSelect.options[colorSelect.selectedIndex].text;
            
            const normalizedProductNumber = productNumber.toLowerCase().replace(/\s+/g, '_');
            const normalizedColorName = colorName.toLowerCase().replace(/\s+/g, '_');
            
            filename = supplierCode ? 
                `${supplierCode.toLowerCase()}_${normalizedProductNumber}_${normalizedColorName}_${nextOrder}` :
                `${normalizedProductNumber}_${normalizedColorName}_${nextOrder}`;
        } else {
            filename = `new_picture_${nextOrder}`;
        }
        
        // Create a new picture div (do not clear grid)
        const pictureDiv = document.createElement('div');
        pictureDiv.className = 'picture-item';
        pictureDiv.dataset.pictureId = picture.id || `new_${Date.now()}_${Math.random()}`;
        pictureDiv.dataset.order = nextOrder;
        
        pictureDiv.innerHTML = `
            <img src="${picture.url}" alt="${picture.name}" onclick="previewPicture('${picture.url}', '${filename}', '${pictureDiv.dataset.pictureId}')" style="cursor: pointer;" title="Click to preview">
            <div class="picture-overlay">
                <button type="button" class="btn-icon btn-icon-danger" onclick="removeVariantPicture('${variantId}', '${pictureDiv.dataset.pictureId}')">×</button>
                <button type="button" class="btn-icon btn-icon-primary" onclick="setPrimaryVariantPicture('${variantId}', '${pictureDiv.dataset.pictureId}')">★</button>
            </div>
            <div class="picture-info">
                <div class="picture-filename" title="${filename}">
                    ${filename}
                </div>
                <small>Order: ${nextOrder} - New picture</small>
            </div>
        `;
        
        grid.appendChild(pictureDiv);
        
        // Store file data for form submission
        if (picture.file) {
            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'file';
            hiddenInput.name = `variant_${variantId}_images`;
            hiddenInput.style.display = 'none';
            
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(picture.file);
            hiddenInput.files = dataTransfer.files;
            
            pictureDiv.appendChild(hiddenInput);
        }
        
        // Update miniatures (will now show all pictures, not just the last one)
        updateVariantMiniatures(variantId);
        
        // Update submit button state after adding picture
        updateSubmitButtonState();
    }
    
    function updateVariantMiniatures(variantId) {
        const miniatureContainer = document.getElementById(`miniatures_display_${variantId}`);
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        
        if (!miniatureContainer) return;
        
        // Clear current miniatures
        miniatureContainer.innerHTML = '';
        
        // Collect all pictures: existing from database + new from grid
        let allPictures = [];
        
        // Get existing pictures from the database (these have numeric IDs and are rendered in HTML)
        const existingPicturesFromDB = document.querySelectorAll(`#pictures_grid_${variantId} .picture-item[data-picture-id]:not([data-picture-id^="new_"])`);
        existingPicturesFromDB.forEach(pictureItem => {
            const img = pictureItem.querySelector('img');
            const isPrimary = pictureItem.querySelector('.primary-badge');
            const pictureId = pictureItem.dataset.pictureId;
            
            if (img && pictureId && !pictureId.startsWith('new_')) {
                allPictures.push({
                    id: pictureId,
                    src: img.src,
                    alt: img.alt,
                    isPrimary: !!isPrimary,
                    isExisting: true
                });
            }
        });
        
        // Get new pictures that were just added (these have IDs starting with "new_")
        const newPicturesFromGrid = document.querySelectorAll(`#pictures_grid_${variantId} .picture-item[data-picture-id^="new_"]`);
        newPicturesFromGrid.forEach((pictureItem, index) => {
            const img = pictureItem.querySelector('img');
            const isPrimary = pictureItem.querySelector('.primary-badge');
            const pictureId = pictureItem.dataset.pictureId;
            
            if (img && pictureId) {
                allPictures.push({
                    id: pictureId,
                    src: img.src,
                    alt: img.alt,
                    isPrimary: !!isPrimary,
                    isExisting: false
                });
            }
        });
        
        const pictureCount = allPictures.length;
        
        // Update picture count in label
        const label = miniatureContainer.closest('.form-group').querySelector('.form-label');
        if (label) {
            label.textContent = `Pictures (${pictureCount})`;
        }
        
        if (pictureCount === 0) {
            miniatureContainer.innerHTML = `
                <div class="no-pictures" onclick="toggleVariantPictures(${variantId})">
                    <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M6.002 5.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z"/>
                        <path d="M2.002 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2h-12zm12 1a1 1 0 0 1 1 1v6.5l-3.777-1.947a.5.5 0 0 0-.577.093l-3.71 3.71-2.66-1.772a.5.5 0 0 0-.63.062L1.002 12V3a1 1 0 0 1 1-1h12z"/>
                    </svg>
                    <span>Click to add pictures</span>
                </div>
            `;
        } else {
            allPictures.forEach((picture, index) => {
                const miniature = document.createElement('div');
                miniature.className = 'miniature-item';
                miniature.dataset.pictureId = picture.id;
                miniature.title = `Order: ${index + 1}${picture.isPrimary ? ' - Primary' : ''}`;
                
                miniature.innerHTML = `
                    <img src="${picture.src}" alt="${picture.alt}" class="miniature-img">
                    <div class="miniature-actions">
                        <button type="button" class="miniature-action-btn delete" onclick="removeVariantPicture('${variantId}', '${picture.id}')" title="Remove">×</button>
                        ${picture.isPrimary ? 
                            '<span class="miniature-action-btn primary" title="Primary">★</span>' : 
                            '<button type="button" class="miniature-action-btn" onclick="setPrimaryVariantPicture(\'' + variantId + '\', \'' + picture.id + '\')" title="Set as primary">☆</button>'
                        }
                    </div>
                `;
                
                miniatureContainer.appendChild(miniature);
            });
        }
    }
    
    function addVariantPicture(variantId) {
        // Trigger file input for this variant
        const fileInput = document.getElementById(`variant_images_${variantId}`);
        if (fileInput) {
            fileInput.click();
        }
    }
    
    function editVariantPicture(variantId, pictureId) {
        // Show the detailed picture management section
        toggleVariantPictures(variantId);
    }
    
    function deleteVariantPicture(variantId, pictureId) {
        if (confirm('Are you sure you want to delete this picture?')) {
            // Check if this is a new picture (not yet saved to database)
            if (pictureId.toString().startsWith('new_')) {
                // Just remove from DOM for new pictures
                const pictureItem = document.querySelector(`[data-picture-id="${pictureId}"]`);
                if (pictureItem) {
                    pictureItem.remove();
                    updateVariantMiniatures(variantId);
                    updateSubmitButtonState();
                }
                return;
            }
            
            // For existing pictures, call backend API to delete from database
            fetch(`/api/picture/${pictureId}/delete`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remove from DOM on success
                    const pictureItem = document.querySelector(`[data-picture-id="${pictureId}"]`);
                    if (pictureItem) {
                        pictureItem.remove();
                        updateVariantMiniatures(variantId);
                        updateSubmitButtonState();
                    }
                    console.log('Picture deleted successfully');
                } else {
                    alert('Failed to delete picture: ' + (data.error || 'Unknown error'));
                    console.error('Delete failed:', data.error);
                }
            })
            .catch(error => {
                alert('Error deleting picture: ' + error.message);
                console.error('Delete error:', error);
            });
        }
    }
    
    function removeVariantPicture(variantId, pictureId) {
        // Find the picture item in the grid
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        if (!grid) return;
        
        const pictureItem = grid.querySelector(`[data-picture-id="${pictureId}"]`);
        if (!pictureItem) return;
        
        if (confirm('Remove this picture?')) {
            // Check if this is a new picture (not yet saved to database)
            if (pictureId.toString().startsWith('new_')) {
                // Just remove from DOM for new pictures
                pictureItem.remove();
                updateVariantMiniatures(variantId);
                updateSubmitButtonState();
                return;
            }
            
            // For existing pictures, call backend API to delete from database
            fetch(`/api/picture/${pictureId}/delete`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remove from grid on success
                    pictureItem.remove();
                    
                    // Update miniatures
                    updateVariantMiniatures(variantId);
                    
                    // Update submit button state
                    updateSubmitButtonState();
                    
                    console.log('Picture deleted successfully');
                } else {
                    alert('Failed to delete picture: ' + (data.error || 'Unknown error'));
                    console.error('Delete failed:', data.error);
                }
            })
            .catch(error => {
                alert('Error deleting picture: ' + error.message);
                console.error('Delete error:', error);
            });
        }
    }
    
    function setPrimaryVariantPicture(variantId, pictureId) {
        // Remove primary status from all pictures in this variant
        const grid = document.getElementById(`pictures_grid_${variantId}`);
        if (grid) {
            grid.querySelectorAll('.primary-badge').forEach(badge => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'btn-icon btn-icon-primary';
                btn.onclick = () => setPrimaryVariantPicture(variantId, badge.closest('.picture-item').dataset.pictureId);
                btn.innerHTML = '★';
                badge.parentNode.replaceChild(btn, badge);
            });
            
            // Set new primary
            const newPrimary = grid.querySelector(`[data-picture-id="${pictureId}"] .btn-icon-primary`);
            if (newPrimary) {
                const badge = document.createElement('span');
                badge.className = 'primary-badge';
                badge.textContent = 'Primary';
                newPrimary.parentNode.replaceChild(badge, newPrimary);
            }
            
            // Update miniatures to reflect primary status
            updateVariantMiniatures(variantId);
        }
    }

    // Global functions for onclick handlers
    window.addNewVariant = addNewVariant;
    window.removeVariant = removeVariant;
    window.toggleVariantPictures = toggleVariantPictures;
    window.updateVariantSKU = updateVariantSKU;
    window.handleVariantImages = handleVariantImages;
    window.removeVariantPicture = removeVariantPicture;
    window.setPrimaryVariantPicture = setPrimaryVariantPicture;
    window.updateVariantMiniatures = updateVariantMiniatures;
    window.addVariantPicture = addVariantPicture;
    window.editVariantPicture = editVariantPicture;
    window.deleteVariantPicture = deleteVariantPicture;
    
    // Add event listener for the add variant button
    document.getElementById('add_variant_btn').addEventListener('click', addNewVariant);
    
    // Add form validation
    document.getElementById('componentForm').addEventListener('submit', function(e) {
        e.preventDefault(); // Prevent default submission
        
        // Validate all variants
        const variants = document.querySelectorAll('[data-variant-id]');
        let isValid = true;
        let errors = [];
        
        for (let variant of variants) {
            const variantId = variant.dataset.variantId;
            if (!validateVariantBeforeSubmit(variantId)) {
                isValid = false;
                errors.push(`Variant ${variantId} is incomplete`);
            }
        }
        
        // Show validation summary if there are errors
        if (!isValid) {
            const validationSummary = document.getElementById('validationSummary');
            const validationList = document.getElementById('validationList');
            
            if (validationSummary && validationList) {
                validationList.innerHTML = errors.map(error => `<li>${error}</li>`).join('');
                validationSummary.classList.remove('hidden');
                validationSummary.scrollIntoView({ behavior: 'smooth' });
            }
            return false;
        }
        
        // Hide validation summary if all is valid
        const validationSummary = document.getElementById('validationSummary');
        if (validationSummary) {
            validationSummary.classList.add('hidden');
        }
        
        // If all validations pass, submit the form
        this.submit();
    });
    
    // Add to global scope
    window.handleColorSelection = handleColorSelection;
    window.validateVariantBeforeSubmit = validateVariantBeforeSubmit;
    window.handleBrandSelection = handleBrandSelection;
    window.handleSubbrandSelection = handleSubbrandSelection;
    window.validateSubbrandName = validateSubbrandName;
    
    // Button State Management
    let originalFormState = null;
    let isFormChanged = false;
    
    function captureOriginalFormState() {
        const form = document.getElementById('componentForm');
        if (!form) return;
        
        const formData = new FormData(form);
        originalFormState = {};
        
        // Capture all form values
        for (let [key, value] of formData.entries()) {
            if (originalFormState[key]) {
                // Handle multiple values (like checkboxes or multiple selects)
                if (!Array.isArray(originalFormState[key])) {
                    originalFormState[key] = [originalFormState[key]];
                }
                originalFormState[key].push(value);
            } else {
                originalFormState[key] = value;
            }
        }
        
        // Capture variant picture counts
        const variants = document.querySelectorAll('[data-variant-id]');
        variants.forEach(variant => {
            const variantId = variant.dataset.variantId;
            const pictures = variant.querySelectorAll('.picture-item');
            originalFormState[`variant_${variantId}_picture_count`] = pictures.length;
        });
    }
    
    function checkFormChanges() {
        if (!originalFormState) return false;
        
        const form = document.getElementById('componentForm');
        if (!form) return false;
        
        const currentFormData = new FormData(form);
        const currentState = {};
        
        // Capture current form values
        for (let [key, value] of currentFormData.entries()) {
            if (currentState[key]) {
                if (!Array.isArray(currentState[key])) {
                    currentState[key] = [currentState[key]];
                }
                currentState[key].push(value);
            } else {
                currentState[key] = value;
            }
        }
        
        // Check variant picture counts
        const variants = document.querySelectorAll('[data-variant-id]');
        variants.forEach(variant => {
            const variantId = variant.dataset.variantId;
            const pictures = variant.querySelectorAll('.picture-item');
            currentState[`variant_${variantId}_picture_count`] = pictures.length;
        });
        
        // Compare states
        for (let key in originalFormState) {
            if (JSON.stringify(originalFormState[key]) !== JSON.stringify(currentState[key])) {
                return true;
            }
        }
        
        for (let key in currentState) {
            if (!(key in originalFormState)) {
                return true;
            }
        }
        
        return false;
    }
    
    function validateAllVariantsHavePictures() {
        const variants = document.querySelectorAll('[data-variant-id]');
        
        for (let variant of variants) {
            const variantId = variant.dataset.variantId;
            const picturesGrid = document.getElementById(`pictures_grid_${variantId}`);
            const pictures = picturesGrid ? picturesGrid.querySelectorAll('.picture-item') : [];
            
            if (pictures.length === 0) {
                return false;
            }
        }
        
        return true;
    }
    
    function updateSubmitButtonState() {
        const submitBtn = document.getElementById('submit_btn');
        if (!submitBtn) return;
        
        const hasChanges = checkFormChanges();
        const allVariantsHavePictures = validateAllVariantsHavePictures();
        
        const shouldEnable = hasChanges && allVariantsHavePictures;
        
        if (shouldEnable) {
            submitBtn.disabled = false;
            submitBtn.style.opacity = '1';
            submitBtn.style.cursor = 'pointer';
            submitBtn.title = '';
        } else {
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.5';
            submitBtn.style.cursor = 'not-allowed';
            
            if (!hasChanges && !allVariantsHavePictures) {
                submitBtn.title = 'No changes made and some variants lack pictures';
            } else if (!hasChanges) {
                submitBtn.title = 'No changes have been made';
            } else if (!allVariantsHavePictures) {
                submitBtn.title = 'All variants must have at least one picture';
            }
        }
    }
    
    // Initialize form state tracking
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(() => {
            captureOriginalFormState();
            updateSubmitButtonState();
        }, 100);
        
        // Add change listeners to form
        const form = document.getElementById('componentForm');
        if (form) {
            form.addEventListener('input', updateSubmitButtonState);
            form.addEventListener('change', updateSubmitButtonState);
        }
        
        // Set up mutation observer to watch for variant changes
        const variantsContainer = document.getElementById('variants_container');
        if (variantsContainer) {
            const observer = new MutationObserver(updateSubmitButtonState);
            observer.observe(variantsContainer, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['data-picture-id']
            });
        }
    });
    
    // Picture Preview Function
    function previewPicture(imageUrl, imageName, pictureId) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('picturePreviewModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'picturePreviewModal';
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="picturePreviewTitle">Picture Preview</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center">
                            <img id="picturePreviewImage" src="" alt="" class="img-fluid" style="max-height: 70vh;">
                            <div class="mt-3">
                                <strong>Filename:</strong> <span id="picturePreviewFilename"></span>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
        
        // Set image and filename
        document.getElementById('picturePreviewImage').src = imageUrl;
        document.getElementById('picturePreviewImage').alt = imageName;
        document.getElementById('picturePreviewFilename').textContent = imageName;
        document.getElementById('picturePreviewTitle').textContent = `Picture Preview - ${imageName}`;
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
    
    // Add to global scope
    window.previewPicture = previewPicture;

});
