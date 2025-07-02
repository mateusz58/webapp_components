/**
 * Component Edit Form Handler
 * Main JavaScript for component creation and editing functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('componentForm');
    const validationSummary = document.getElementById('validationSummary');
    const validationList = document.getElementById('validationList');
    const submitBtn = document.getElementById('submitBtn');
    const propertiesContainer = document.getElementById('properties_container');
    
    let validationErrors = {};

    // Pass template data to JavaScript
    if (window.availableColors) {
        // Colors are already set from template
    }

    if (window.componentTypes) {
        // Component types are already set from template
    }

    // Form validation and submission
    form.addEventListener('submit', function(e) {
        console.log('🚀 Form submission attempted');
        const isValid = validateForm();
        console.log('🔍 Form validation result:', isValid);
        
        if (!isValid) {
            console.log('❌ Form validation failed - preventing submission');
            e.preventDefault();
            return false;
        }
        
        console.log('✅ Form validation passed - proceeding with submission');
        
        if (window.isEditMode) {
            // For editing, prevent default and show change summary modal first
            e.preventDefault();
            if (typeof showChangeSummaryModal === 'function') {
                showChangeSummaryModal();
            } else {
                // Fallback: direct submission if modal function not available
                submitFormDirectly();
            }
        } else {
            // For new components, handle creation and then variants via API
            e.preventDefault();
            handleNewComponentSubmission();
        }
    });
    
    async function submitFormDirectly() {
        try {
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<div class="spinner"></div> Processing picture changes...';
            
            // Process staged picture changes first (for edit mode)
            if (window.isEditMode && window.variantManager && typeof window.variantManager.processStagedChanges === 'function') {
                const success = await window.variantManager.processStagedChanges();
                if (!success) {
                    // If picture processing failed, stop form submission
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = window.isEditMode ? 'Update Component' : 'Create Component';
                    return;
                }
            }
            
            // Ensure variant files are properly attached before submission (for new components)
            if (!window.isEditMode && window.variantManager && typeof window.variantManager.updateFormFiles === 'function') {
                window.variantManager.updateFormFiles();
            }
            
            // Update loading state
            submitBtn.innerHTML = '<div class="spinner"></div> Saving...';
            
            // Submit form
            form.submit();
        } catch (error) {
            console.error('Error during form submission:', error);
            
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.innerHTML = window.isEditMode ? 'Update Component' : 'Create Component';
            
            // Show error message
            if (window.variantManager && typeof window.variantManager.showErrorMessage === 'function') {
                window.variantManager.showErrorMessage(`Failed to submit form: ${error.message}`);
            } else {
                alert(`Failed to submit form: ${error.message}`);
            }
        }
    }
    
    // Make submitFormDirectly available globally for modal
    window.submitFormDirectly = submitFormDirectly;
    
    // Handle new component creation with API-based variant management
    async function handleNewComponentSubmission() {
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<div class="spinner"></div> Creating Component with Variants...';
            
            // Use the comprehensive API endpoint that handles everything at once
            const formData = new FormData(form);
            
            // Add CSRF token to headers for API call
            const csrfToken = document.querySelector('[name="csrf_token"]')?.value;
            
            const response = await fetch('/api/component/create', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });
            
            if (response.ok) {
                // Component and variants created successfully via API
                const result = await response.json();
                
                if (result.success) {
                    const componentId = result.component.id;
                    const variantCount = result.component.variants_count || 0;
                    
                    console.log(`✅ Component ${componentId} created with ${variantCount} variants`);
                    
                    // Show success message and redirect to loading page
                    submitBtn.innerHTML = `<div class="spinner"></div> Success! Redirecting to loading page...`;
                    
                    // Redirect to loading page (API now provides the URL)
                    setTimeout(() => {
                        if (result.redirect_url) {
                            window.location.href = result.redirect_url;
                        } else {
                            // Fallback to direct component detail if no loading page URL
                            window.location.href = `/component/${componentId}`;
                        }
                    }, 1000);
                } else {
                    throw new Error(result.error || 'Component creation failed');
                }
            } else {
                const errorText = await response.text();
                throw new Error(`Server error: ${response.status} - ${errorText}`);
            }
            
        } catch (error) {
            console.error('Error creating component:', error);
            showError(`Failed to create component: ${error.message}`);
            
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Create Component';
        }
    }
    
    // Show error message
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.style.marginBottom = '1rem';
        errorDiv.innerHTML = `
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        // Insert at top of form
        form.insertBefore(errorDiv, form.firstChild);
        
        // Remove after 10 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 10000);
    }

    // Real-time validation
    form.addEventListener('input', function(e) {
        if (e.target.classList.contains('form-input') || e.target.classList.contains('form-select')) {
            // Debounce validation for product number to avoid excessive API calls
            if (e.target.name === 'product_number') {
                clearTimeout(e.target.validationTimer);
                e.target.validationTimer = setTimeout(() => {
                    validateField(e.target);
                    updateSubmitButtonState();
                }, 500); // 500ms delay
            } else {
                validateField(e.target);
                updateSubmitButtonState();
            }
        }
    });

    // Real-time variant validation when files are added
    form.addEventListener('change', function(e) {
        if (e.target.type === 'file' && e.target.name && e.target.name.includes('variant_images')) {
            updateSubmitButtonState();
        }
        if (e.target.name && (e.target.name.includes('variant_color') || e.target.name.includes('variant_custom_color'))) {
            updateSubmitButtonState();
        }
    });

    // Also validate when supplier changes (affects product number uniqueness)
    const supplierSelect = document.getElementById('supplier_id');
    if (supplierSelect) {
        supplierSelect.addEventListener('change', function() {
            const productNumberField = document.getElementById('product_number');
            if (productNumberField && productNumberField.value.trim()) {
                validateField(productNumberField);
            }
        });
    }

    // Component type change handler
    const componentTypeSelect = document.getElementById('component_type_id');
    if (componentTypeSelect) {
        componentTypeSelect.addEventListener('change', function() {
            loadComponentTypeProperties(this.value);
        });
        
        // Load properties for initially selected type
        if (componentTypeSelect.value) {
            loadComponentTypeProperties(componentTypeSelect.value);
        }
    }

    // Initial submit button state check
    updateSubmitButtonState();

    // Make updateSubmitButtonState available globally for variant manager
    window.updateSubmitButtonState = updateSubmitButtonState;

    function validateForm() {
        validationErrors = {};
        let isValid = true;

        // Clear previous validation
        document.querySelectorAll('.form-input, .form-select').forEach(field => {
            field.classList.remove('error');
        });
        document.querySelectorAll('.form-error').forEach(error => {
            error.classList.add('hidden');
        });

        // Validate required fields
        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (!validateField(field)) {
                isValid = false;
            }
        });

        // Validate component variants
        if (!validateComponentVariants()) {
            isValid = false;
        }

        updateValidationSummary();
        return isValid;
    }

    function validateComponentVariants() {
        let isValid = true;
        let hasVariants = false;
        const variantErrors = [];

        // Check existing variants (edit mode)
        const existingVariants = document.querySelectorAll('[data-variant-id]:not([data-variant-id^="new_"])');
        existingVariants.forEach(variantCard => {
            const variantId = variantCard.dataset.variantId;
            const colorSelect = variantCard.querySelector(`[name="variant_color_${variantId}"]`);
            
            if (colorSelect && colorSelect.value) {
                hasVariants = true;
                
                // Check if variant has pictures
                const picturesGrid = variantCard.querySelector(`#pictures_grid_${variantId}`);
                const existingPictures = variantCard.querySelectorAll('.picture-item').length;
                const newPictureFiles = variantCard.querySelector(`[name="variant_images_${variantId}[]"]`);
                const hasNewFiles = newPictureFiles && newPictureFiles.files && newPictureFiles.files.length > 0;
                
                if (existingPictures === 0 && !hasNewFiles) {
                    const colorName = colorSelect.options[colorSelect.selectedIndex]?.text || 'Unknown';
                    variantErrors.push(`Variant "${colorName}" must have at least one picture.`);
                    isValid = false;
                }
            }
        });

        // Check new variants
        const newVariants = document.querySelectorAll('[data-variant-id^="new_"]');
        newVariants.forEach(variantCard => {
            const variantId = variantCard.dataset.variantId;
            const colorSelect = variantCard.querySelector(`[name="variant_color_${variantId}"]`);
            const customColorInput = variantCard.querySelector(`[name="variant_custom_color_${variantId}"]`);
            
            // Check if color is selected
            const hasColor = (colorSelect && colorSelect.value) || 
                            (customColorInput && customColorInput.value.trim());
            
            if (hasColor) {
                hasVariants = true;
                
                // Check if variant has pictures
                const pictureFiles = variantCard.querySelector(`[name="variant_images_${variantId}[]"]`);
                const hasFiles = pictureFiles && pictureFiles.files && pictureFiles.files.length > 0;
                
                if (!hasFiles) {
                    const colorName = customColorInput && customColorInput.value.trim() ? 
                                    customColorInput.value.trim() : 
                                    (colorSelect.options[colorSelect.selectedIndex]?.text || 'Unknown');
                    variantErrors.push(`Variant "${colorName}" must have at least one picture.`);
                    isValid = false;
                }
            }
        });

        // Check if component has at least one variant
        if (!hasVariants) {
            variantErrors.push('Component must have at least one color variant.');
            isValid = false;
        }

        // Add variant errors to validation errors
        if (variantErrors.length > 0) {
            validationErrors['variants'] = variantErrors.join(' ');
        }

        return isValid;
    }

    function validateField(field) {
        const fieldName = field.name;
        const errorElement = document.getElementById(fieldName + '_error');
        let isValid = true;
        let errorMessage = '';

        // Clear previous error
        field.classList.remove('error');
        if (errorElement) {
            errorElement.classList.add('hidden');
            delete validationErrors[fieldName];
        }

        // Field-specific validation
        switch (fieldName) {
            case 'product_number':
                if (!field.value.trim()) {
                    errorMessage = 'Product number is required';
                    isValid = false;
                } else if (field.value.trim().length < 2) {
                    errorMessage = 'Product number must be at least 2 characters';
                    isValid = false;
                } else {
                    // Dynamic validation - check for potential duplicates
                    validateProductNumberUniqueness(field);
                }
                break;
            case 'component_type_id':
                if (!field.value) {
                    errorMessage = 'Component type is required';
                    isValid = false;
                }
                break;
        }

        if (!isValid && errorElement) {
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

    function updateSubmitButtonState() {
        // Check if form has critical errors that should disable submit
        const hasVariants = checkHasVariants();
        const hasRequiredFieldErrors = checkRequiredFields();
        const variantValidationDetails = getVariantValidationDetails();
        
        const isFormValid = hasVariants && !hasRequiredFieldErrors && variantValidationDetails.allVariantsValid;
        
        // Update variant validation status
        updateVariantValidationStatus(hasVariants, variantValidationDetails);
        
        // Update submit button
        if (isFormValid) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('btn-danger', 'btn-warning');
            submitBtn.classList.add('btn-primary');
            submitBtn.innerHTML = `
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M15.964.686a.5.5 0 0 0-.65-.65L.767 5.855H.766l-.452.18a.5.5 0 0 0-.082.887l.41.26.001.002 4.995 3.178 3.178 4.995.002.002.26.41a.5.5 0 0 0 .886-.083l6-15Zm-1.833 1.89L6.637 10.07l-.215-.338a.5.5 0 0 0-.154-.154l-.338-.215 7.494-7.494 1.178-.471-.47 1.178Z"/>
                </svg>
                ${window.isEditMode ? 'Update Component' : 'Create Component'}
            `;
        } else {
            submitBtn.disabled = true;
            submitBtn.classList.remove('btn-primary', 'btn-warning');
            submitBtn.classList.add('btn-danger');
            
            if (!hasVariants) {
                submitBtn.innerHTML = `
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
                    </svg>
                    Add at least one variant
                `;
            } else {
                submitBtn.innerHTML = `
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
                    </svg>
                    Fix validation errors
                `;
            }
        }
    }

    function updateVariantValidationStatus(hasVariants, validationDetails) {
        const statusElement = document.getElementById('variant_validation_status');
        const textElement = document.getElementById('variant_status_text');
        
        if (!statusElement || !textElement) return;
        
        if (!hasVariants) {
            // No variants at all
            statusElement.className = 'alert alert-warning';
            statusElement.style.border = '1px solid #ffcc00';
            statusElement.style.background = '#fff8e1';
            textElement.innerHTML = 'Add at least one variant with pictures to enable form submission';
            statusElement.querySelector('svg').style.color = '#ff9800';
        } else if (!validationDetails.allVariantsValid) {
            // Has variants but some are invalid
            statusElement.className = 'alert alert-warning';
            statusElement.style.border = '1px solid #ffcc00';
            statusElement.style.background = '#fff8e1';
            const issues = [];
            if (validationDetails.variantsWithoutColors > 0) {
                issues.push(`${validationDetails.variantsWithoutColors} variant(s) need colors`);
            }
            if (validationDetails.variantsWithoutPictures > 0) {
                issues.push(`${validationDetails.variantsWithoutPictures} variant(s) need pictures`);
            }
            textElement.innerHTML = `Fix issues: ${issues.join(', ')}`;
            statusElement.querySelector('svg').style.color = '#ff9800';
        } else {
            // All variants valid
            statusElement.className = 'alert alert-success';
            statusElement.style.border = '1px solid #4caf50';
            statusElement.style.background = '#e8f5e8';
            textElement.innerHTML = `✓ Ready for submission - ${validationDetails.validVariantCount} variant(s) configured correctly`;
            statusElement.querySelector('svg').style.color = '#4caf50';
            statusElement.querySelector('svg').innerHTML = '<path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/>';
        }
    }

    function getVariantValidationDetails() {
        let validVariantCount = 0;
        let variantsWithoutColors = 0;
        let variantsWithoutPictures = 0;
        
        // Check existing variants (edit mode)
        const existingVariants = document.querySelectorAll('[data-variant-id]:not([data-variant-id^="new_"])');
        existingVariants.forEach(variantCard => {
            const variantId = variantCard.dataset.variantId;
            const colorSelect = variantCard.querySelector(`[name="variant_color_${variantId}"]`);
            
            if (colorSelect && colorSelect.value) {
                // Has color, check pictures
                const existingPictures = variantCard.querySelectorAll('.picture-item').length;
                const newPictureFiles = variantCard.querySelector(`[name="variant_images_${variantId}[]"]`);
                const hasNewFiles = newPictureFiles && newPictureFiles.files && newPictureFiles.files.length > 0;
                
                if (existingPictures > 0 || hasNewFiles) {
                    validVariantCount++;
                } else {
                    variantsWithoutPictures++;
                }
            } else {
                variantsWithoutColors++;
            }
        });

        // Check new variants
        const newVariants = document.querySelectorAll('[data-variant-id^="new_"]');
        newVariants.forEach(variantCard => {
            const variantId = variantCard.dataset.variantId;
            const colorSelect = variantCard.querySelector(`[name="variant_color_${variantId}"]`);
            const customColorInput = variantCard.querySelector(`[name="variant_custom_color_${variantId}"]`);
            
            const hasColor = (colorSelect && colorSelect.value) || 
                            (customColorInput && customColorInput.value.trim());
            
            if (hasColor) {
                // Has color, check pictures
                const pictureFiles = variantCard.querySelector(`[name="variant_images_${variantId}[]"]`);
                const hasFiles = pictureFiles && pictureFiles.files && pictureFiles.files.length > 0;
                
                if (hasFiles) {
                    validVariantCount++;
                } else {
                    variantsWithoutPictures++;
                }
            } else {
                variantsWithoutColors++;
            }
        });
        
        return {
            validVariantCount,
            variantsWithoutColors,
            variantsWithoutPictures,
            allVariantsValid: variantsWithoutColors === 0 && variantsWithoutPictures === 0 && validVariantCount > 0
        };
    }

    function checkHasVariants() {
        let hasVariants = false;
        
        // Check existing variants (edit mode)
        const existingVariants = document.querySelectorAll('[data-variant-id]:not([data-variant-id^="new_"])');
        existingVariants.forEach(variantCard => {
            const variantId = variantCard.dataset.variantId;
            const colorSelect = variantCard.querySelector(`[name="variant_color_${variantId}"]`);
            if (colorSelect && colorSelect.value) {
                hasVariants = true;
            }
        });

        // Check new variants
        const newVariants = document.querySelectorAll('[data-variant-id^="new_"]');
        newVariants.forEach(variantCard => {
            const variantId = variantCard.dataset.variantId;
            const colorSelect = variantCard.querySelector(`[name="variant_color_${variantId}"]`);
            const customColorInput = variantCard.querySelector(`[name="variant_custom_color_${variantId}"]`);
            
            const hasColor = (colorSelect && colorSelect.value) || 
                            (customColorInput && customColorInput.value.trim());
            if (hasColor) {
                hasVariants = true;
            }
        });
        
        return hasVariants;
    }

    function checkRequiredFields() {
        const productNumber = document.getElementById('product_number');
        const componentType = document.getElementById('component_type_id');
        
        const hasErrors = !productNumber?.value?.trim() || 
                         !componentType?.value ||
                         Object.keys(validationErrors).length > 0;
        
        return hasErrors;
    }

    function loadComponentTypeProperties(componentTypeId) {
        if (!componentTypeId) {
            const noPropertiesDiv = document.getElementById('no_properties');
            if (noPropertiesDiv) {
                noPropertiesDiv.style.display = 'block';
            }
            propertiesContainer.innerHTML = '';
            return;
        }

        // Hide no properties message
        const noPropertiesDiv = document.getElementById('no_properties');
        if (noPropertiesDiv) {
            noPropertiesDiv.style.display = 'none';
        }

        // Show loading
        propertiesContainer.innerHTML = '<div class="text-center" style="padding: 2rem;"><div class="spinner" style="margin: 0 auto;"></div></div>';

        // Load properties via AJAX
        fetch(`/api/component-type/${componentTypeId}/properties`)
            .then(response => response.json())
            .then(properties => {
                renderProperties(properties);
            })
            .catch(() => {
                renderProperties([]);
            });
    }

    function renderProperties(properties) {
        if (properties.length === 0) {
            propertiesContainer.innerHTML = '<div class="text-center" style="padding: 2rem; color: var(--gray-500);"><p>No specific properties for this component type</p></div>';
            return;
        }

        propertiesContainer.innerHTML = '';
        const propertyGrid = document.createElement('div');
        propertyGrid.className = 'properties-grid';
        
        properties.forEach(property => {
            const propertyDiv = createPropertyField(property);
            propertyGrid.appendChild(propertyDiv);
        });
        
        propertiesContainer.appendChild(propertyGrid);
    }

    function createPropertyField(property) {
        const div = document.createElement('div');
        div.className = 'form-group';

        const label = document.createElement('label');
        label.className = 'form-label' + (property.is_required ? ' required' : '');
        label.textContent = property.display_name || property.property_name;
        label.setAttribute('for', property.property_name);

        let input;
        switch (property.property_type) {
            case 'text':
                input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-input';
                break;
            case 'number':
                input = document.createElement('input');
                input.type = 'number';
                input.className = 'form-input';
                break;
            case 'select':
                input = document.createElement('select');
                input.className = 'form-select';
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Select...';
                input.appendChild(defaultOption);
                
                if (property.options && Array.isArray(property.options)) {
                    property.options.forEach(option => {
                        const optionElement = document.createElement('option');
                        optionElement.value = option;
                        optionElement.textContent = option;
                        input.appendChild(optionElement);
                    });
                }
                break;
            case 'textarea':
                input = document.createElement('textarea');
                input.className = 'form-textarea';
                input.rows = 3;
                break;
            default:
                input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-input';
        }

        input.name = `property_${property.property_name}`;
        input.id = property.property_name;
        if (property.is_required) {
            input.required = true;
        }

        // Set existing value if editing - handled by template

        div.appendChild(label);
        div.appendChild(input);

        return div;
    }

    // Global picture preview function
    function previewPicture(imageUrl, imageName, pictureId) {
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
                            <img id="picturePreviewImage" src="" alt="" class="img-fluid">
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

    // Product number uniqueness validation
    function validateProductNumberUniqueness(productNumberField) {
        const productNumber = productNumberField.value.trim();
        const supplierSelect = document.getElementById('supplier_id');
        const supplierId = supplierSelect ? supplierSelect.value : '';
        const errorElement = document.getElementById('product_number_error');
        const helpElement = document.getElementById('product_number_help');
        
        if (!productNumber || productNumber.length < 2) {
            return; // Basic validation will handle this
        }
        
        // Clear previous async validation
        if (productNumberField.asyncValidationTimer) {
            clearTimeout(productNumberField.asyncValidationTimer);
        }
        
        // Show checking indicator
        if (helpElement) {
            helpElement.innerHTML = 'Checking availability...';
            helpElement.style.color = '#6c757d';
        }
        
        // Set timeout for async validation
        productNumberField.asyncValidationTimer = setTimeout(() => {
            fetch('/api/component/validate-product-number', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_number: productNumber,
                    supplier_id: supplierId,
                    component_id: window.componentId || null
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.available) {
                    // Product number is available
                    productNumberField.classList.remove('error');
                    if (errorElement) {
                        errorElement.classList.add('hidden');
                        delete validationErrors['product_number'];
                    }
                    if (helpElement) {
                        if (supplierId) {
                            helpElement.innerHTML = '✓ Available for this supplier';
                            helpElement.style.color = '#28a745';
                        } else {
                            helpElement.innerHTML = '✓ Available (no supplier selected)';
                            helpElement.style.color = '#28a745';
                        }
                    }
                } else {
                    // Product number is taken
                    productNumberField.classList.add('error');
                    if (errorElement) {
                        errorElement.textContent = data.message || 'Product number already exists';
                        errorElement.classList.remove('hidden');
                    }
                    if (helpElement) {
                        helpElement.innerHTML = '✗ Already taken';
                        helpElement.style.color = '#dc3545';
                    }
                    validationErrors['product_number'] = data.message || 'Product number already exists';
                }
                updateValidationSummary();
            })
            .catch(error => {
                console.error('Validation error:', error);
                if (helpElement) {
                    helpElement.innerHTML = 'Unique identifier (e.g., F-WL001, S-WL0001)';
                    helpElement.style.color = '';
                }
            });
        }, 300); // 300ms delay for API call
    }
    
    // Make function globally available
    window.validateProductNumberUniqueness = validateProductNumberUniqueness;

});